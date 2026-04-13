"""
BehaviourAI - Customer Behaviour Analytics Platform

Flask application providing ML-powered customer segmentation and analytics.
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

from config import (
    DATA_FILE, REAL_DATA_FILE, MODEL_FILE, SCALER_FILE,
    FEATURES, TARGET, N_ESTIMATORS, TEST_SIZE, RANDOM_STATE,
    KMEANS_N_CLUSTERS, KMEANS_N_INIT, SEGMENT_MAP, RECOMMENDATIONS,
    CLUSTER_FEATURES, MAX_CLUSTER_SAMPLE, LOG_LEVEL, USE_REAL_DATA, DATABASE_URL
)
from data.database import DatabaseManager
from ml.pipeline import CustomerSegmentationPipeline
from ml.registry import ModelRegistry

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BehaviourAnalyticsApp:
    """
    Main application class encapsulating all ML logic and data management.
    Thread-safe design: each instance maintains its own state.
    """

    def __init__(self):
        self.app = Flask(__name__)
        self._db: Optional[DatabaseManager] = DatabaseManager()
        self._df: Optional[pd.DataFrame] = None
        self._registry = ModelRegistry()
        self._kmeans_scaler: Optional[StandardScaler] = None
        self._metrics = {"total_requests": 0, "predictions": 0, "errors": 0}

        self._register_routes()
        logger.info("BehaviourAnalyticsApp initialized")

    @property
    def df(self) -> pd.DataFrame:
        """Lazy-load dataframe if not already loaded."""
        if self._df is None:
            self._load_data()
        return self._df

    def _load_data(self) -> None:
        """Load data from database."""
        try:
            self._df = self._db.load_all_data()
            logger.info(f"Loaded {len(self._df)} records from database")
        except Exception as e:
            logger.error(f"Failed to load data from database: {e}")
            raise RuntimeError(f"Failed to load data: {e}")

    def load_or_generate_data(self) -> pd.DataFrame:
        """Public method to ensure data is loaded."""
        return self.df

    def train_model(self) -> Dict[str, Any]:
        """
        Train RandomForest classifier on customer behavior data.

        Returns:
            Dictionary with training results including accuracy
        """
        try:
            logger.info("Starting model training...")
            df = self.df

            # Validate features exist in dataframe
            missing_features = [f for f in FEATURES if f not in df.columns]
            if missing_features:
                raise ValueError(f"Missing features in data: {missing_features}")

            if TARGET not in df.columns:
                raise ValueError(f"Target column '{TARGET}' not found in data")

            X = df[FEATURES]
            y = df[TARGET]

            # Check for NaN values
            if X.isna().any().any():
                logger.warning("Missing values detected in features - filling with 0")
                X = X.fillna(0)

            # Train/test split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=TEST_SIZE,
                random_state=RANDOM_STATE,
                stratify=y
            )

            # Train model
            pipeline = CustomerSegmentationPipeline.create_pipeline()
            pipeline.fit(X_train, y_train)

            # Evaluate
            y_pred = pipeline.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            acc_percent = round(acc * 100, 2)

            report = classification_report(y_test, y_pred, output_dict=True)
            conf_matrix = confusion_matrix(y_test, y_pred).tolist()

            metrics = {
                "accuracy": acc_percent,
                "precision_macro": round((report.get("macro avg", {})).get("precision", 0) * 100, 2),
                "recall_macro": round((report.get("macro avg", {})).get("recall", 0) * 100, 2),
                "f1_macro": round((report.get("macro avg", {})).get("f1-score", 0) * 100, 2),
                "confusion_matrix": conf_matrix
            }

            # Persist model
            version = self._registry.register_model(pipeline, metrics)

            logger.info(f"Model training completed. Accuracy: {acc_percent}%")
            return {
                "status": "success",
                "accuracy": acc_percent,
                "precision_macro": metrics["precision_macro"],
                "recall_macro": metrics["recall_macro"],
                "f1_macro": metrics["f1_macro"],
                "message": f"Model trained with {len(df)} records",
                "total_records": len(df),
                "train_size": len(X_train),
                "test_size": len(X_test),
                "version": version
            }

        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": "Model training failed"
            }

    def predict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict customer segment for given behavioral metrics.

        Args:
            data: Dictionary with keys matching FEATURES

        Returns:
            Dictionary with segment, confidence, and recommendations
        """
        try:
            # Ensure model is trained
            active_info = self._registry.get_active()
            if not active_info:
                logger.info("No persisted model found, training new model...")
                train_result = self.train_model()
                if train_result["status"] != "success":
                    raise RuntimeError(f"Model training failed: {train_result.get('error')}")
                active_info = self._registry.get_active()

            pipeline = active_info["pipeline"]

            # Input validation
            validated_data = self._validate_prediction_input(data)

            # Prepare feature dataframe
            feature_df = pd.DataFrame([{
                "clicks": validated_data["clicks"],
                "time_spent": validated_data["time_spent"],
                "purchase_count": validated_data["purchase_count"],
                "page_views": validated_data["page_views"],
                "cart_additions": validated_data["cart_additions"]
            }])

            # Predict
            pred = pipeline.predict(feature_df)[0]
            proba = pipeline.predict_proba(feature_df)[0]

            segment = SEGMENT_MAP.get(pred, str(pred))
            confidence = round(float(max(proba)) * 100, 1)
            recommendations = RECOMMENDATIONS.get(pred, [])

            logger.info(f"Prediction: segment={segment}, confidence={confidence}%")
            return {
                "segment": segment,
                "confidence": confidence,
                "recommendations": recommendations,
                "version": active_info.get("version")
            }

        except ValueError as e:
            logger.warning(f"Invalid input for prediction: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Invalid input data"
            }
        except Exception as e:
            logger.error(f"Prediction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "message": "Prediction failed"
            }

    def _validate_prediction_input(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Validate and sanitize prediction input.

        Args:
            data: Raw input dictionary

        Returns:
            Cleaned and validated feature dictionary

        Raises:
            ValueError: If validation fails
        """
        required_fields = FEATURES
        validated = {}

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

            try:
                value = float(data[field])
            except (TypeError, ValueError):
                raise ValueError(f"Field '{field}' must be a number")

            if value < 0:
                raise ValueError(f"Field '{field}' must be non-negative")

            # Reasonable upper bounds
            max_values = {
                "clicks": 1000,
                "time_spent": 1440,  # 24 hours in minutes
                "purchase_count": 100,
                "page_views": 1000,
                "cart_additions": 100
            }

            if value > max_values[field]:
                raise ValueError(f"Field '{field}' exceeds maximum value ({max_values[field]})")

            validated[field] = value

        return validated

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate aggregate statistics from database."""
        try:
            stats = self._db.get_statistics()
            logger.debug("Statistics calculated")
            return stats
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
            raise

    def get_clusters(self, max_points: int = MAX_CLUSTER_SAMPLE) -> List[Dict[str, Any]]:
        """
        Perform K-Means clustering on behavioral features.

        Args:
            max_points: Maximum number of data points to return

        Returns:
            List of point dictionaries with x, y, cluster, user_id
        """
        try:
            df = self.df

            # Validate clustering features exist
            missing = [f for f in CLUSTER_FEATURES if f not in df.columns]
            if missing:
                raise ValueError(f"Missing clustering features: {missing}")

            X = df[CLUSTER_FEATURES]

            # Scale
            self._kmeans_scaler = StandardScaler()
            X_scaled = self._kmeans_scaler.fit_transform(X)

            # Cluster
            kmeans = KMeans(
                n_clusters=KMEANS_N_CLUSTERS,
                random_state=RANDOM_STATE,
                n_init=KMEANS_N_INIT
            )
            labels = kmeans.fit_predict(X_scaled)

            # Build results (limit to max_points for performance)
            result = []
            sample_size = min(len(df), max_points)
            indices = np.random.choice(len(df), size=sample_size, replace=False) if len(df) > max_points else range(len(df))

            for i in indices:
                result.append({
                    "x": float(df["clicks"].iloc[i]),
                    "y": float(df["time_spent"].iloc[i]),
                    "cluster": int(labels[i]),
                    "user_id": str(df["user_id"].iloc[i])
                })

            logger.info(f"Clustering completed: {len(result)} points, {KMEANS_N_CLUSTERS} clusters")
            return result

        except Exception as e:
            logger.error(f"Clustering failed: {e}", exc_info=True)
            raise

    def get_trends(self) -> List[Dict[str, Any]]:
        """Calculate monthly trends from database."""
        try:
            trends = self._db.get_monthly_trends()
            logger.debug("Trends calculated")
            return trends
        except Exception as e:
            logger.error(f"Failed to calculate trends: {e}")
            raise

    def _register_routes(self) -> None:
        """Register all Flask routes."""

        @self.app.before_request
        def require_api_key():
            if request.path.startswith('/api/') and request.path not in ('/api/health', '/api/info', '/api/docs'):
                from config import API_KEY
                if API_KEY and request.headers.get("X-API-Key") != API_KEY:
                    return jsonify({"status": "error", "message": "Unauthorized: Invalid or missing API Key"}), 401

        @self.app.after_request
        def track_metrics(response):
            self._metrics["total_requests"] += 1
            if response.status_code >= 400:
                self._metrics["errors"] += 1
            return response

        @self.app.route("/admin/metrics")
        def admin_metrics():
            """Monitoring dashboard metrics."""
            active_info = self._registry.get_active()
            return jsonify({
                "status": "success",
                "metrics": self._metrics,
                "model_version": active_info["version"] if active_info else None
            })

        @self.app.route("/")
        def index():
            """Render landing page."""
            return render_template("index.html")

        @self.app.route("/dashboard")
        def dashboard():
            """Render analytics dashboard."""
            return render_template("dashboard.html")

        @self.app.route("/api/train", methods=["POST"])
        def api_train():
            """
            Train or retrain the RandomForest model.

            Returns:
                JSON with training status, accuracy, and message
            """
            try:
                result = self.train_model()
                status_code = 200 if result.get("status") == "success" else 500
                return jsonify(result), status_code
            except Exception as e:
                logger.error(f"Training endpoint error: {e}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Training failed"
                }), 500

        @self.app.route("/api/stats")
        def api_stats():
            """Get aggregate statistics."""
            try:
                stats = self.get_statistics()
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Stats endpoint error: {e}")
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to calculate stats"
                }), 500

        @self.app.route("/api/cluster")
        def api_cluster():
            """Get K-Means clustering results."""
            try:
                result = self.get_clusters()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Cluster endpoint error: {e}")
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Clustering failed"
                }), 500

        @self.app.route("/api/trends")
        def api_trends():
            """Get monthly trend data."""
            try:
                trends = self.get_trends()
                return jsonify(trends)
            except Exception as e:
                logger.error(f"Trends endpoint error: {e}")
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Failed to load trends"
                }), 500

        @self.app.route("/api/predict", methods=["POST"])
        def api_predict():
            """
            Predict customer segment from behavioral metrics.

            Expected JSON body:
                {
                    "clicks": number,
                    "time_spent": number,
                    "purchase_count": number,
                    "page_views": number,
                    "cart_additions": number
                }

            Returns:
                JSON with segment, confidence, and recommendations
            """
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "status": "error",
                        "error": "No JSON data provided",
                        "message": "Request body must be JSON"
                    }), 400

                result = self.predict(data)

                if result.get("status") != "error":
                    self._metrics["predictions"] += 1

                status_code = 200 if result.get("status") != "error" else 400
                return jsonify(result), status_code

            except Exception as e:
                logger.error(f"Prediction endpoint error: {e}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "Prediction failed"
                }), 500

        @self.app.route("/api/health")
        def health_check():
            """Health check endpoint for monitoring."""
            return jsonify({
                "status": "healthy",
                "service": "behaviour-analytics",
                "data_loaded": self._df is not None,
                "model_loaded": self._registry.get_active() is not None
            })

        @self.app.route("/api/model-info")
        def model_info():
            """Get active model version and metrics."""
            active_info = self._registry.get_active()
            if not active_info:
                return jsonify({"status": "error", "message": "No active model"}), 404
                
            return jsonify({
                "status": "success",
                "version": active_info["version"],
                "metrics": active_info["metadata"].get("metrics", {}),
                "created_at": active_info["metadata"].get("created_at")
            })

        @self.app.route("/api/info")
        def api_info():
            """API information and capabilities."""
            return jsonify({
                "name": "BehaviourAI Analytics API",
                "version": "1.0.0",
                "features": FEATURES,
                "target": TARGET,
                "segments": SEGMENT_MAP,
                "endpoints": {
                    "/api/train": "POST - Train model",
                    "/api/stats": "GET - Aggregate statistics",
                    "/api/cluster": "GET - Clustering results",
                    "/api/trends": "GET - Monthly trends",
                    "/api/predict": "POST - Predict segment",
                    "/api/health": "GET - Health check",
                    "/api/info": "GET - API documentation"
                }
            })

    def run(self, host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
        """Run the Flask application."""
        logger.info(f"Starting BehaviourAnalyticsApp on {host}:{port} (debug={debug})")
        self.app.run(host=host, port=port, debug=debug)


# Create application instance
application = BehaviourAnalyticsApp()
app = application.app  # Expose for gunicorn and testing


if __name__ == "__main__":
    application.run(debug=True, port=5000)
