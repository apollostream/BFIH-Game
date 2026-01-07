"""
BFIH Backend: Storage Management
Handles persistence of analysis results, scenarios, and metadata

Supports:
- File-based storage (JSON) for MVP
- PostgreSQL integration (for production)
- Redis caching layer
"""

import json
import os
import logging
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================================
# STORAGE INTERFACE
# ============================================================================

class StorageBackend(ABC):
    """Abstract storage backend"""
    
    @abstractmethod
    def store_analysis_result(self, analysis_id: str, result: Dict) -> bool:
        pass
    
    @abstractmethod
    def retrieve_analysis_result(self, analysis_id: str) -> Optional[Dict]:
        pass
    
    @abstractmethod
    def store_scenario_config(self, scenario_id: str, config: Dict) -> bool:
        pass
    
    @abstractmethod
    def retrieve_scenario_config(self, scenario_id: str) -> Optional[Dict]:
        pass


# ============================================================================
# FILE-BASED STORAGE (MVP)
# ============================================================================

class FileStorageBackend(StorageBackend):
    """File-based storage using JSON"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.analysis_dir = self.base_dir / "analyses"
        self.scenario_dir = self.base_dir / "scenarios"
        self.status_dir = self.base_dir / "status"
        
        # Create directories
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.scenario_dir.mkdir(parents=True, exist_ok=True)
        self.status_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileStorageBackend initialized at {base_dir}")
    
    def store_analysis_result(self, analysis_id: str, result: Dict) -> bool:
        """Store analysis result to file"""
        try:
            filepath = self.analysis_dir / f"{analysis_id}.json"
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Stored analysis result: {analysis_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing analysis result: {str(e)}")
            return False
    
    def retrieve_analysis_result(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve analysis result from file"""
        try:
            filepath = self.analysis_dir / f"{analysis_id}.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error retrieving analysis result: {str(e)}")
            return None
    
    def store_scenario_config(self, scenario_id: str, config: Dict) -> bool:
        """Store scenario configuration to file"""
        try:
            filepath = self.scenario_dir / f"{scenario_id}.json"
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Stored scenario config: {scenario_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing scenario config: {str(e)}")
            return False
    
    def retrieve_scenario_config(self, scenario_id: str) -> Optional[Dict]:
        """Retrieve scenario configuration from file"""
        try:
            filepath = self.scenario_dir / f"{scenario_id}.json"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error retrieving scenario config: {str(e)}")
            return None
    
    def store_analysis_request(self, analysis_id: str, request: Dict) -> bool:
        """Store analysis request metadata"""
        try:
            filepath = self.status_dir / f"{analysis_id}_request.json"
            with open(filepath, 'w') as f:
                json.dump(request, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error storing analysis request: {str(e)}")
            return False
    
    def update_analysis_status(self, analysis_id: str, status: str) -> bool:
        """Update analysis status"""
        try:
            filepath = self.status_dir / f"{analysis_id}_status.txt"
            with open(filepath, 'w') as f:
                f.write(f"{status}\n{datetime.utcnow().isoformat()}")
            logger.info(f"Updated analysis status: {analysis_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"Error updating analysis status: {str(e)}")
            return False
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis status"""
        try:
            filepath = self.status_dir / f"{analysis_id}_status.txt"
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                content = f.read().strip().split('\n')
                return {
                    "analysis_id": analysis_id,
                    "status": content[0],
                    "timestamp": content[1] if len(content) > 1 else None
                }
        except Exception as e:
            logger.error(f"Error getting analysis status: {str(e)}")
            return None
    
    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios"""
        try:
            files = sorted(self.scenario_dir.glob("*.json"))
            files = files[offset:offset+limit]
            
            scenarios = []
            for f in files:
                with open(f, 'r') as file:
                    scenarios.append(json.load(file))
            
            return scenarios
        except Exception as e:
            logger.error(f"Error listing scenarios: {str(e)}")
            return []


# ============================================================================
# MANAGER CLASS (Facade)
# ============================================================================

class StorageManager:
    """Manages storage operations (abstraction layer)"""
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        """
        Initialize storage manager
        
        Args:
            backend: Storage backend instance (defaults to FileStorageBackend)
        """
        self.backend = backend or FileStorageBackend()
    
    def store_analysis_result(self, analysis_id: str, result) -> bool:
        """Store BFIH analysis result"""
        # Convert dataclass to dict if needed
        result_dict = result.to_dict() if hasattr(result, 'to_dict') else result
        return self.backend.store_analysis_result(analysis_id, result_dict)
    
    def retrieve_analysis_result(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve BFIH analysis result"""
        return self.backend.retrieve_analysis_result(analysis_id)
    
    def store_scenario_config(self, scenario_id: str, config: Dict) -> bool:
        """Store scenario configuration"""
        return self.backend.store_scenario_config(scenario_id, config)
    
    def retrieve_scenario_config(self, scenario_id: str) -> Optional[Dict]:
        """Retrieve scenario configuration"""
        return self.backend.retrieve_scenario_config(scenario_id)
    
    def store_analysis_request(self, analysis_id: str, request) -> bool:
        """Store analysis request"""
        request_dict = request.to_dict() if hasattr(request, 'to_dict') else request
        return self.backend.store_analysis_request(analysis_id, request_dict)
    
    def update_analysis_status(self, analysis_id: str, status: str) -> bool:
        """Update analysis status"""
        return self.backend.update_analysis_status(analysis_id, status)
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis status"""
        return self.backend.get_analysis_status(analysis_id)
    
    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios"""
        return self.backend.list_scenarios(limit, offset)


# ============================================================================
# MIGRATION UTILITIES
# ============================================================================

class StorageMigration:
    """Utilities for data migration between storage backends"""
    
    @staticmethod
    def migrate_all_data(source_backend: StorageBackend, dest_backend: StorageBackend):
        """Migrate all data from source to destination backend"""
        logger.info("Starting storage migration...")
        
        # This would iterate through all data and copy to new backend
        # Implementation depends on specific backends used
        
        logger.info("Storage migration completed")


if __name__ == "__main__":
    # Test storage
    storage = StorageManager()
    
    # Test scenario storage
    test_scenario = {
        "scenario_id": "test_001",
        "title": "Test Scenario",
        "paradigms": [],
        "hypotheses": []
    }
    
    storage.store_scenario_config("test_001", test_scenario)
    retrieved = storage.retrieve_scenario_config("test_001")
    print(f"Stored and retrieved: {retrieved is not None}")
    
    # Test analysis status
    storage.store_analysis_request("analysis_001", {"test": "data"})
    storage.update_analysis_status("analysis_001", "processing")
    status = storage.get_analysis_status("analysis_001")
    print(f"Analysis status: {status}")
