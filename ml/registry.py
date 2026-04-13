import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import joblib

from config import MODEL_DIR

class ModelRegistry:
    """Manages model versioning, metadata, and active aliases."""
    
    def __init__(self, registry_dir: str = str(MODEL_DIR)):
        self.registry_dir = Path(registry_dir)
        self.registry_file = self.registry_dir / "registry.json"
        self.current_link = self.registry_dir / "current"
        self._ensure_setup()
        
    def _ensure_setup(self):
        """Ensure the registry directory and file exist."""
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        if not self.registry_file.exists():
            self._save_registry({"versions": [], "active_version": None})
            
    def _load_registry(self) -> Dict[str, Any]:
        with open(self.registry_file, 'r') as f:
            return json.load(f)
            
    def _save_registry(self, data: Dict[str, Any]):
        with open(self.registry_file, 'w') as f:
            json.dump(data, f, indent=4)
            
    def get_next_version(self) -> str:
        """Determines the next version string like 'v1', 'v2'."""
        data = self._load_registry()
        versions = data.get("versions", [])
        if not versions:
            return "v1"
        
        highest_v = 0
        for v in versions:
            if v.startswith("v"):
                try:
                    num = int(v[1:])
                    highest_v = max(highest_v, num)
                except ValueError:
                    pass
        return f"v{highest_v + 1}"

    def register_model(self, pipeline: Any, metrics: Dict[str, Any]) -> str:
        """Saves a new model pipeline and its metadata, making it active by default."""
        version = self.get_next_version()
        version_dir = self.registry_dir / version
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Save pipeline
        pipeline_file = version_dir / "pipeline.pkl"
        joblib.dump(pipeline, pipeline_file)
        
        # Save metadata
        metadata = {
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)
            
        # Update registry
        reg_data = self._load_registry()
        reg_data["versions"].append(version)
        self._save_registry(reg_data)
        
        # Make it active
        self.activate(version)
        return version
        
    def activate(self, version: str) -> None:
        """Sets the specified version as the active 'current' model."""
        reg_data = self._load_registry()
        if version not in reg_data["versions"]:
            raise ValueError(f"Version {version} does not exist in registry.")
            
        reg_data["active_version"] = version
        self._save_registry(reg_data)
        
        # Windows symlink fallback: we just copy or keep track via registry.json
        # Symlinks on Windows require admin privileges generally. 
        # Using registry.json as source of truth for 'current' is safer across OSes.
        
    def get_active(self) -> Optional[Dict[str, Any]]:
        """Returns the active model pipeline and its metadata."""
        reg_data = self._load_registry()
        active_version = reg_data.get("active_version")
        if not active_version:
            return None
            
        version_dir = self.registry_dir / active_version
        
        if not (version_dir / "pipeline.pkl").exists():
            return None
            
        pipeline = joblib.load(version_dir / "pipeline.pkl")
        
        metadata = {}
        if (version_dir / "metadata.json").exists():
            with open(version_dir / "metadata.json", "r") as f:
                metadata = json.load(f)
                
        return {
            "version": active_version,
            "pipeline": pipeline,
            "metadata": metadata
        }
        
    def list_versions(self) -> Dict[str, Any]:
        """Lists all registered versions and the currently active one."""
        return self._load_registry()
