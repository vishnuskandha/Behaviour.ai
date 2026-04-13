import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

from config import N_ESTIMATORS, RANDOM_STATE

class CustomerSegmentationPipeline:
    """Wrapper for the sklearn Pipeline."""
    
    @staticmethod
    def create_pipeline() -> Pipeline:
        """Creates and returns the un-fitted sklearn Pipeline."""
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=N_ESTIMATORS,
                random_state=RANDOM_STATE,
                n_jobs=-1
            ))
        ])
        return pipeline
