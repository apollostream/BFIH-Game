"""
BFIH Backend: Testing Utilities
Unit tests, integration tests, and mock data generators

Test with: pytest
Coverage: pytest --cov=bfih
"""

import pytest
import json
from typing import Dict
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from bfih_orchestrator_fixed import (
    BFIHOrchestrator,
    BFIHAnalysisRequest,
    BFIHAnalysisResult,
    VectorStoreManager
)
from bfih_storage import StorageManager, FileStorageBackend
from bfih_api_server import app


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_scenario_config():
    """Provide sample scenario configuration"""
    return {
        "paradigms": [
            {
                "id": "K1",
                "name": "Secular-Individualist",
                "description": "Success driven by individual grit"
            },
            {
                "id": "K2",
                "name": "Religious-Communitarian",
                "description": "Success driven by community networks"
            }
        ],
        "hypotheses": [
            {
                "id": "H0",
                "name": "Unknown",
                "domains": [],
                "associated_paradigms": ["K1", "K2"],
                "is_catch_all": True
            },
            {
                "id": "H1",
                "name": "Founder Grit",
                "domains": ["Psychological"],
                "associated_paradigms": ["K1"]
            },
            {
                "id": "H2",
                "name": "Faith Networks",
                "domains": ["Theological"],
                "associated_paradigms": ["K2"]
            }
        ],
        "priors_by_paradigm": {
            "K1": {"H0": 0.1, "H1": 0.6, "H2": 0.3},
            "K2": {"H0": 0.1, "H1": 0.3, "H2": 0.6}
        }
    }


@pytest.fixture
def sample_analysis_request(sample_scenario_config):
    """Provide sample analysis request"""
    return BFIHAnalysisRequest(
        scenario_id="s_test_001",
        proposition="Why did Startup X succeed?",
        scenario_config=sample_scenario_config,
        user_id="user_test_001"
    )


@pytest.fixture
def sample_analysis_result(sample_analysis_request):
    """Provide sample analysis result"""
    return BFIHAnalysisResult(
        analysis_id="analysis_test_001",
        scenario_id=sample_analysis_request.scenario_id,
        proposition=sample_analysis_request.proposition,
        report="""# BFIH Analysis Report

## Executive Summary
Test analysis report with sample conclusions.

## Paradigm-Specific Posteriors
- K1: H1=0.65, H2=0.25, H0=0.10
- K2: H1=0.20, H2=0.70, H0=0.10
""",
        posteriors={
            "K1": {"H0": 0.10, "H1": 0.65, "H2": 0.25},
            "K2": {"H0": 0.10, "H1": 0.20, "H2": 0.70}
        },
        metadata={
            "model": "gpt-4o",
            "web_searches": 5,
            "file_searches": 2,
            "code_executions": 1
        },
        created_at=datetime.utcnow().isoformat()
    )


@pytest.fixture
def storage_manager(tmp_path):
    """Provide storage manager with temporary directory"""
    return StorageManager(backend=FileStorageBackend(base_dir=str(tmp_path)))


@pytest.fixture
def test_client():
    """Provide FastAPI test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ============================================================================
# UNIT TESTS: Data Models
# ============================================================================

class TestDataModels:
    """Test data model serialization"""
    
    def test_analysis_request_to_dict(self, sample_analysis_request):
        """Test converting analysis request to dict"""
        result = sample_analysis_request.to_dict()
        
        assert isinstance(result, dict)
        assert result["scenario_id"] == "s_test_001"
        assert result["proposition"] == "Why did Startup X succeed?"
        assert "scenario_config" in result
    
    def test_analysis_result_to_dict(self, sample_analysis_result):
        """Test converting analysis result to dict"""
        result = sample_analysis_result.to_dict()
        
        assert isinstance(result, dict)
        assert result["analysis_id"] == "analysis_test_001"
        assert "report" in result
        assert "posteriors" in result
        assert "metadata" in result


# ============================================================================
# UNIT TESTS: Storage
# ============================================================================

class TestStorageManager:
    """Test storage operations"""
    
    def test_store_and_retrieve_scenario(self, storage_manager, sample_scenario_config):
        """Test storing and retrieving scenario"""
        scenario_id = "test_scenario_001"
        
        # Store
        success = storage_manager.store_scenario_config(scenario_id, sample_scenario_config)
        assert success is True
        
        # Retrieve
        retrieved = storage_manager.retrieve_scenario_config(scenario_id)
        assert retrieved is not None
        assert retrieved["paradigms"] == sample_scenario_config["paradigms"]
    
    def test_store_and_retrieve_analysis_result(self, storage_manager, sample_analysis_result):
        """Test storing and retrieving analysis result"""
        analysis_id = sample_analysis_result.analysis_id

        # Store
        success = storage_manager.store_analysis_result(analysis_id, sample_analysis_result)
        assert success is True

        # Retrieve
        retrieved = storage_manager.retrieve_analysis_result(analysis_id)
        assert retrieved is not None
        assert retrieved["analysis_id"] == analysis_id
    
    def test_analysis_status_tracking(self, storage_manager):
        """Test analysis status tracking"""
        analysis_id = "status_test_001"
        
        # Store request
        storage_manager.store_analysis_request(analysis_id, {"test": "data"})
        
        # Update status
        storage_manager.update_analysis_status(analysis_id, "processing")
        status = storage_manager.get_analysis_status(analysis_id)
        assert status["status"] == "processing"
        
        # Update again
        storage_manager.update_analysis_status(analysis_id, "completed")
        status = storage_manager.get_analysis_status(analysis_id)
        assert status["status"] == "completed"
    
    def test_list_scenarios(self, storage_manager, sample_scenario_config):
        """Test listing scenarios"""
        # Store multiple scenarios
        for i in range(5):
            storage_manager.store_scenario_config(f"scenario_{i:03d}", sample_scenario_config)
        
        # List
        scenarios = storage_manager.list_scenarios(limit=10, offset=0)
        assert len(scenarios) >= 5


# ============================================================================
# UNIT TESTS: Orchestrator (with mocks)
# ============================================================================

class TestBFIHOrchestrator:
    """Test BFIH orchestrator with mocked API"""
    
    @patch('bfih_orchestrator_fixed.client')
    def test_orchestrator_initialization(self, mock_client):
        """Test orchestrator initialization"""
        orchestrator = BFIHOrchestrator(vector_store_id="vs_test_001")
        
        assert orchestrator.model == "gpt-4o"
        assert orchestrator.vector_store_id == "vs_test_001"
    
    @patch('bfih_orchestrator_fixed.client')
    def test_build_orchestration_prompt(self, mock_client, sample_analysis_request):
        """Test orchestration prompt building"""
        orchestrator = BFIHOrchestrator()
        prompt = orchestrator._build_orchestration_prompt(sample_analysis_request)
        
        assert isinstance(prompt, str)
        assert "Why did Startup X succeed?" in prompt
        assert "Phase 1:" in prompt
        assert "Phase 5:" in prompt
        assert "BFIH Report Generation" in prompt


# ============================================================================
# INTEGRATION TESTS: API Endpoints
# ============================================================================

class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "timestamp" in response.json()
    
    def test_submit_analysis_request(self, test_client, sample_analysis_request):
        """Test submitting analysis request"""
        request_data = {
            "scenario_id": sample_analysis_request.scenario_id,
            "proposition": sample_analysis_request.proposition,
            "scenario_config": sample_analysis_request.scenario_config,
            "user_id": sample_analysis_request.user_id
        }
        
        response = test_client.post("/api/bfih-analysis", json=request_data)
        
        assert response.status_code == 200
        result = response.json()
        assert "analysis_id" in result
        assert result["status"] == "processing"
    
    def test_submit_analysis_missing_fields(self, test_client):
        """Test submitting analysis with missing fields"""
        request_data = {
            "scenario_id": "s_001"
            # Missing proposition and scenario_config
        }

        response = test_client.post("/api/bfih-analysis", json=request_data)

        assert response.status_code == 400
        assert "required fields" in response.json()["error"].lower()
    
    def test_store_scenario(self, test_client, sample_scenario_config):
        """Test storing scenario"""
        scenario_data = {
            "scenario_id": "s_api_test_001",
            "title": "Test Scenario",
            "scenario_config": sample_scenario_config
        }
        
        response = test_client.post("/api/scenario", json=scenario_data)
        
        assert response.status_code == 200
        assert response.json()["status"] == "stored"
    
    def test_get_scenario(self, test_client, sample_scenario_config):
        """Test retrieving scenario"""
        # First store it
        scenario_data = {
            "scenario_id": "s_get_test_001",
            "title": "Get Test",
            "scenario_config": sample_scenario_config
        }
        test_client.post("/api/scenario", json=scenario_data)
        
        # Then retrieve it
        response = test_client.get("/api/scenario/s_get_test_001")
        
        assert response.status_code == 200
        assert response.json()["scenario_id"] == "s_get_test_001"


# ============================================================================
# MOCK DATA GENERATORS
# ============================================================================

class MockDataGenerator:
    """Generate mock data for testing"""
    
    @staticmethod
    def generate_analysis_report(analysis_id: str, scenario_id: str) -> str:
        """Generate mock BFIH report"""
        return f"""# BFIH Analysis Report

## Analysis ID: {analysis_id}
## Scenario ID: {scenario_id}

## Executive Summary
This is a mock analysis report for testing purposes.

## Hypothesis Posteriors

| Hypothesis | Prior | Likelihood | Posterior |
|-----------|-------|-----------|-----------|
| H1 | 0.50 | 0.75 | 0.60 |
| H2 | 0.30 | 0.40 | 0.25 |
| H3 | 0.20 | 0.20 | 0.15 |

## Sensitivity Analysis
Robust to ±20% prior variation.

## Conclusion
Analysis completed successfully.
"""
    
    @staticmethod
    def generate_mock_posteriors(paradigm_count: int = 2, hypothesis_count: int = 3) -> Dict:
        """Generate mock posterior probabilities"""
        import numpy as np
        
        posteriors = {}
        for p in range(paradigm_count):
            paradigm_id = f"K{p+1}"
            values = np.random.dirichlet(np.ones(hypothesis_count))
            posteriors[paradigm_id] = {
                f"H{h}": float(values[h])
                for h in range(hypothesis_count)
            }
        
        return posteriors


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and load tests"""
    
    def test_storage_performance(self, storage_manager, sample_scenario_config):
        """Test storage performance for multiple operations"""
        import time
        
        start = time.time()
        
        for i in range(100):
            storage_manager.store_scenario_config(f"perf_test_{i:04d}", sample_scenario_config)
        
        elapsed = time.time() - start
        
        # Should complete 100 operations in under 5 seconds
        assert elapsed < 5.0
        print(f"Stored 100 scenarios in {elapsed:.2f} seconds")


if __name__ == "__main__":
    # Run tests with: pytest tests.py -v
    pytest.main([__file__, "-v", "--tb=short"])
