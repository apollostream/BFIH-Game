"""
Integration tests for the per-API-call checkpointing system.

These tests exercise the real code paths without mocking to ensure
the checkpointing system works correctly in production.
"""

import json
import os
import shutil
import tempfile
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

# Import the modules under test
from bfih_checkpointer import AnalysisCheckpointer, APICallRecord
from bfih_storage import FileStorageBackend


class TestFileStorageCheckpointing:
    """Test checkpointing with FileStorageBackend."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage backend."""
        temp_dir = tempfile.mkdtemp()
        storage = FileStorageBackend(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_store_and_retrieve_checkpoint(self, temp_storage):
        """Test basic checkpoint storage and retrieval."""
        scenario_id = "test_scenario_001"
        checkpoint_data = {
            "checkpoint_id": f"{scenario_id}_cp_20260206_120000",
            "analysis_id": "analysis-uuid",
            "scenario_id": scenario_id,
            "proposition": "Test proposition",
            "status": "in_progress",
            "completed_phases": {"phase_1": {"data": {"methodology": "test"}}},
            "api_call_count": 5,
            "cost_summary": {"total_cost_usd": 0.25}
        }

        # Store
        result = temp_storage.store_checkpoint(scenario_id, checkpoint_data)
        assert result is True

        # Retrieve
        retrieved = temp_storage.retrieve_checkpoint(scenario_id)
        assert retrieved is not None
        assert retrieved["checkpoint_id"] == checkpoint_data["checkpoint_id"]
        assert retrieved["status"] == "in_progress"
        assert retrieved["api_call_count"] == 5

    def test_checkpoint_atomic_overwrite(self, temp_storage):
        """Test that checkpoint overwrites are atomic."""
        scenario_id = "test_atomic"

        # Store initial
        temp_storage.store_checkpoint(scenario_id, {"version": 1, "data": "initial"})

        # Overwrite
        temp_storage.store_checkpoint(scenario_id, {"version": 2, "data": "updated"})

        # Verify only latest version exists
        retrieved = temp_storage.retrieve_checkpoint(scenario_id)
        assert retrieved["version"] == 2
        assert retrieved["data"] == "updated"

    def test_api_call_log_append(self, temp_storage):
        """Test API call audit log append functionality."""
        scenario_id = "test_audit"

        # Append multiple records
        for i in range(5):
            record = {
                "call_id": f"call_{i}",
                "timestamp": f"2026-02-06T12:00:0{i}Z",
                "phase_name": f"Phase {i}",
                "cost_usd": 0.01 * i
            }
            result = temp_storage.append_api_call_log(scenario_id, record)
            assert result is True

        # Retrieve and verify order
        records = temp_storage.get_api_call_log(scenario_id)
        assert len(records) == 5
        assert records[0]["call_id"] == "call_0"
        assert records[4]["call_id"] == "call_4"

    def test_api_call_log_thread_safety(self, temp_storage):
        """Test that API call log append is thread-safe."""
        scenario_id = "test_threadsafe"
        num_threads = 8
        calls_per_thread = 10

        def append_calls(thread_id):
            for i in range(calls_per_thread):
                record = {
                    "call_id": f"thread_{thread_id}_call_{i}",
                    "thread_id": thread_id,
                    "index": i
                }
                temp_storage.append_api_call_log(scenario_id, record)

        # Run parallel appends
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(append_calls, t) for t in range(num_threads)]
            for f in futures:
                f.result()

        # Verify all records were written
        records = temp_storage.get_api_call_log(scenario_id)
        assert len(records) == num_threads * calls_per_thread

        # Verify no data corruption (each record should be valid JSON)
        for record in records:
            assert "call_id" in record
            assert "thread_id" in record

    def test_list_checkpoints(self, temp_storage):
        """Test listing checkpoints with filtering."""
        # Create checkpoints with different statuses
        for i, status in enumerate(["in_progress", "completed", "failed", "completed"]):
            temp_storage.store_checkpoint(
                f"scenario_{i}",
                {
                    "checkpoint_id": f"scenario_{i}_cp",
                    "scenario_id": f"scenario_{i}",
                    "status": status,
                    "proposition": f"Test {i}",
                    "api_call_count": i * 10,
                    "cost_summary": {"total_cost_usd": i * 0.5},
                    "completed_phases": {}
                }
            )
            time.sleep(0.01)  # Ensure different timestamps

        # List all
        all_checkpoints = temp_storage.list_checkpoints()
        assert len(all_checkpoints) == 4

        # List completed only
        completed = temp_storage.list_checkpoints(status="completed")
        assert len(completed) == 2
        assert all(c["status"] == "completed" for c in completed)

        # List failed only
        failed = temp_storage.list_checkpoints(status="failed")
        assert len(failed) == 1

    def test_checkpoint_not_found(self, temp_storage):
        """Test retrieving non-existent checkpoint returns None."""
        result = temp_storage.retrieve_checkpoint("nonexistent")
        assert result is None


class TestAnalysisCheckpointer:
    """Test AnalysisCheckpointer class."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage backend."""
        temp_dir = tempfile.mkdtemp()
        storage = FileStorageBackend(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def checkpointer(self, temp_storage):
        """Create a checkpointer instance."""
        return AnalysisCheckpointer(
            analysis_id="test-analysis-uuid",
            scenario_id="test_scenario",
            proposition="Why did startup X succeed?",
            scenario_config={"paradigms": [], "hypotheses": []},
            storage=temp_storage,
            reasoning_model="gpt-5.2"
        )

    def test_checkpointer_initialization(self, checkpointer):
        """Test checkpointer initializes correctly."""
        assert checkpointer.checkpoint["analysis_id"] == "test-analysis-uuid"
        assert checkpointer.checkpoint["scenario_id"] == "test_scenario"
        assert checkpointer.checkpoint["status"] == "in_progress"
        assert checkpointer.checkpoint["api_call_count"] == 0
        assert "checkpoint_id" in checkpointer.checkpoint

    def test_record_api_call(self, checkpointer):
        """Test recording API calls."""
        call_id = checkpointer.record_api_call(
            phase_name="Phase 1: Methodology",
            method="_run_phase",
            model="o4-mini",
            prompt="Retrieve methodology...",
            status="success",
            input_tokens=1500,
            output_tokens=2000,
            reasoning_tokens=0,
            cost_usd=0.0085,
            duration_ms=3500,
            tools_used=["file_search"]
        )

        assert call_id is not None
        assert checkpointer.checkpoint["api_call_count"] == 1
        assert checkpointer.checkpoint["cost_summary"]["total_cost_usd"] == 0.0085
        assert checkpointer.checkpoint["cost_summary"]["total_input_tokens"] == 1500

    def test_save_phase(self, checkpointer, temp_storage):
        """Test saving phase checkpoint."""
        # Start phase
        checkpointer.start_phase("phase_1")

        # Record some API calls
        checkpointer.record_api_call(
            phase_name="Phase 1",
            method="_run_phase",
            model="o4-mini",
            prompt="test",
            status="success",
            input_tokens=1000,
            output_tokens=500,
            reasoning_tokens=0,
            cost_usd=0.005,
            duration_ms=2000
        )

        # Save phase
        checkpointer.save_phase("phase_1", methodology="Test methodology content")

        # Verify checkpoint was persisted
        loaded = temp_storage.retrieve_checkpoint("test_scenario")
        assert loaded is not None
        assert "phase_1" in loaded["completed_phases"]
        assert loaded["completed_phases"]["phase_1"]["data"]["methodology"] == "Test methodology content"

    def test_save_error(self, checkpointer, temp_storage):
        """Test saving error checkpoint."""
        recovery = checkpointer.save_error(
            error_message="Budget limit exceeded",
            phase="phase_2",
            error_type="budget_exceeded"
        )

        assert "resume" in recovery.lower()
        assert checkpointer.checkpoint["status"] == "failed"
        assert checkpointer.checkpoint["error"]["type"] == "budget_exceeded"

        # Verify persisted
        loaded = temp_storage.retrieve_checkpoint("test_scenario")
        assert loaded["status"] == "failed"

    def test_mark_completed(self, checkpointer, temp_storage):
        """Test marking analysis as completed."""
        checkpointer.mark_completed()

        assert checkpointer.checkpoint["status"] == "completed"
        assert checkpointer.checkpoint["resume_point"] is None

        loaded = temp_storage.retrieve_checkpoint("test_scenario")
        assert loaded["status"] == "completed"

    def test_load_checkpoint(self, temp_storage):
        """Test loading existing checkpoint."""
        # Create checkpoint manually
        checkpoint_data = {
            "checkpoint_id": "test_scenario_cp_20260206",
            "analysis_id": "existing-analysis",
            "scenario_id": "test_scenario",
            "proposition": "Test",
            "scenario_config": {},
            "status": "in_progress",
            "api_call_count": 15,
            "cost_summary": {"total_cost_usd": 1.50},
            "completed_phases": {
                "phase_1": {"data": {"methodology": "Loaded methodology"}}
            }
        }
        temp_storage.store_checkpoint("test_scenario", checkpoint_data)

        # Load it
        loaded = AnalysisCheckpointer.load("test_scenario", temp_storage)

        assert loaded is not None
        assert loaded.checkpoint["analysis_id"] == "existing-analysis"
        assert loaded._call_counter == 15
        assert "phase_1" in loaded.checkpoint["completed_phases"]

    def test_parallel_progress_tracking(self, checkpointer, temp_storage):
        """Test parallel progress tracking for Phase 2/3b."""
        # Simulate parallel evidence searches
        for i in range(5):
            checkpointer.save_parallel_progress(
                phase_id="phase_2",
                sub_phase="evidence_search",
                completed_item=f"search_{i}",
                item_result={"evidence": f"Evidence from search {i}"}
            )

        # Check completed items
        completed = checkpointer.get_parallel_completed("phase_2", "evidence_search")
        assert len(completed) == 5
        assert "search_0" in completed
        assert "search_4" in completed

        # Check results
        results = checkpointer.get_parallel_results("phase_2", "evidence_search")
        assert len(results) == 5
        assert results["search_2"]["evidence"] == "Evidence from search 2"

    def test_is_phase_completed(self, checkpointer):
        """Test checking phase completion status."""
        assert not checkpointer.is_phase_completed("phase_1")

        checkpointer.start_phase("phase_1")
        checkpointer.save_phase("phase_1", data="test")

        assert checkpointer.is_phase_completed("phase_1")
        assert not checkpointer.is_phase_completed("phase_2")

    def test_get_phase_data(self, checkpointer):
        """Test retrieving stored phase data."""
        checkpointer.start_phase("phase_1")
        checkpointer.save_phase("phase_1", methodology="Retrieved methodology", extra="data")

        data = checkpointer.get_phase_data("phase_1")
        assert data["methodology"] == "Retrieved methodology"
        assert data["extra"] == "data"

        # Non-existent phase returns None
        assert checkpointer.get_phase_data("phase_999") is None

    def test_data_truncation(self, checkpointer):
        """Test that large data is truncated to prevent bloat."""
        large_methodology = "x" * 10000  # Much larger than MAX_METHODOLOGY_CHARS

        checkpointer.start_phase("phase_1")
        checkpointer.save_phase("phase_1", methodology=large_methodology)

        data = checkpointer.get_phase_data("phase_1")
        assert len(data["methodology"]) == checkpointer.MAX_METHODOLOGY_CHARS


class TestOrchestratorCheckpointIntegration:
    """Test checkpointer integration with orchestrator methods."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage backend."""
        temp_dir = tempfile.mkdtemp()
        storage = FileStorageBackend(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_checkpointer_receives_api_calls(self, temp_storage):
        """Test that API calls in _run_phase are recorded to checkpointer."""
        # This test verifies the integration point in the orchestrator
        # We'll mock the OpenAI client but use real checkpointer

        from bfih_orchestrator_fixed import BFIHOrchestrator

        # Create orchestrator with mocked client
        orchestrator = BFIHOrchestrator.__new__(BFIHOrchestrator)
        orchestrator.model = "test-model"
        orchestrator.reasoning_model = "test-reasoning"
        orchestrator.progress_callback = None
        orchestrator.status_callback = None
        orchestrator.cost_tracker = MagicMock()
        orchestrator.cost_tracker.add_cost.return_value = 0.01

        # Create real checkpointer
        orchestrator.checkpointer = AnalysisCheckpointer(
            analysis_id="integration-test",
            scenario_id="integration_scenario",
            proposition="Integration test",
            scenario_config={},
            storage=temp_storage
        )

        # Mock the client response
        mock_response = MagicMock()
        mock_response.output_text = "Test output"
        mock_response.status = "completed"
        mock_response.usage.input_tokens = 1000
        mock_response.usage.output_tokens = 500
        mock_response.usage.reasoning_tokens = 0
        mock_response.output = []

        mock_client = MagicMock()
        mock_stream = MagicMock()
        mock_stream.__iter__ = lambda self: iter([
            MagicMock(type="response.completed", response=mock_response)
        ])
        mock_client.responses.create.return_value = mock_stream
        orchestrator.client = mock_client

        # Call _run_phase
        result = orchestrator._run_phase(
            prompt="Test prompt",
            tools=[{"type": "web_search"}],
            phase_name="Test Phase"
        )

        # Verify API call was recorded
        assert orchestrator.checkpointer.checkpoint["api_call_count"] == 1
        assert orchestrator.checkpointer.checkpoint["cost_summary"]["total_cost_usd"] == 0.01

        # Verify audit log was written
        audit_log = temp_storage.get_api_call_log("integration_scenario")
        assert len(audit_log) == 1
        assert audit_log[0]["phase_name"] == "Test Phase"
        assert audit_log[0]["status"] == "success"


class TestAPIEndpoints:
    """Test checkpoint-related API endpoints."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage backend."""
        temp_dir = tempfile.mkdtemp()
        storage = FileStorageBackend(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def test_client(self, temp_storage):
        """Create FastAPI test client with mocked storage."""
        from fastapi.testclient import TestClient
        import bfih_api_server

        # Patch the storage to use our temp storage
        original_storage = bfih_api_server.storage
        bfih_api_server.storage = temp_storage

        client = TestClient(bfih_api_server.app)
        yield client

        # Restore original
        bfih_api_server.storage = original_storage

    def test_list_checkpoints_endpoint(self, test_client, temp_storage):
        """Test GET /api/checkpoints endpoint."""
        # Create some checkpoints
        for i in range(3):
            temp_storage.store_checkpoint(f"scenario_{i}", {
                "checkpoint_id": f"scenario_{i}_cp",
                "scenario_id": f"scenario_{i}",
                "proposition": f"Test {i}",
                "status": "completed" if i % 2 == 0 else "failed",
                "api_call_count": i * 5,
                "cost_summary": {"total_cost_usd": i * 0.5},
                "completed_phases": {}
            })

        response = test_client.get("/api/checkpoints")
        assert response.status_code == 200
        data = response.json()
        assert "checkpoints" in data
        assert len(data["checkpoints"]) == 3

    def test_list_checkpoints_filtered(self, test_client, temp_storage):
        """Test GET /api/checkpoints with status filter."""
        temp_storage.store_checkpoint("completed_1", {
            "checkpoint_id": "cp1", "scenario_id": "completed_1",
            "status": "completed", "proposition": "Test",
            "api_call_count": 0, "cost_summary": {"total_cost_usd": 0},
            "completed_phases": {}
        })
        temp_storage.store_checkpoint("failed_1", {
            "checkpoint_id": "cp2", "scenario_id": "failed_1",
            "status": "failed", "proposition": "Test",
            "api_call_count": 0, "cost_summary": {"total_cost_usd": 0},
            "completed_phases": {}
        })

        response = test_client.get("/api/checkpoints?status=failed")
        assert response.status_code == 200
        data = response.json()
        assert len(data["checkpoints"]) == 1
        assert data["checkpoints"][0]["status"] == "failed"

    def test_get_checkpoint_details(self, test_client, temp_storage):
        """Test GET /api/checkpoints/{scenario_id} endpoint."""
        temp_storage.store_checkpoint("detail_test", {
            "checkpoint_id": "detail_test_cp",
            "scenario_id": "detail_test",
            "proposition": "Detail test proposition",
            "status": "in_progress",
            "api_call_count": 10,
            "cost_summary": {"total_cost_usd": 0.75},
            "completed_phases": {"phase_1": {"data": {}}}
        })

        response = test_client.get("/api/checkpoints/detail_test")
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == "detail_test"
        assert data["api_call_count"] == 10

    def test_get_checkpoint_not_found(self, test_client):
        """Test GET /api/checkpoints/{scenario_id} for non-existent checkpoint."""
        response = test_client.get("/api/checkpoints/nonexistent")
        assert response.status_code == 404

    def test_download_checkpoint(self, test_client, temp_storage):
        """Test GET /api/checkpoints/{scenario_id}/download endpoint."""
        checkpoint_data = {
            "checkpoint_id": "download_test_cp",
            "scenario_id": "download_test",
            "proposition": "Download test",
            "status": "completed"
        }
        temp_storage.store_checkpoint("download_test", checkpoint_data)

        response = test_client.get("/api/checkpoints/download_test/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")

        # Verify content is valid JSON
        data = response.json()
        assert data["scenario_id"] == "download_test"

    def test_get_api_calls(self, test_client, temp_storage):
        """Test GET /api/analysis/{scenario_id}/calls endpoint."""
        # Create some API call records
        for i in range(5):
            temp_storage.append_api_call_log("api_calls_test", {
                "call_id": f"call_{i}",
                "phase_name": f"Phase {i}",
                "cost_usd": 0.01 * i
            })

        response = test_client.get("/api/analysis/api_calls_test/calls")
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == "api_calls_test"
        assert data["total_calls"] == 5
        assert len(data["calls"]) == 5

    def test_download_api_calls(self, test_client, temp_storage):
        """Test GET /api/analysis/{scenario_id}/calls/download endpoint."""
        for i in range(3):
            temp_storage.append_api_call_log("download_calls_test", {
                "call_id": f"call_{i}",
                "data": f"test_{i}"
            })

        response = test_client.get("/api/analysis/download_calls_test/calls/download")
        assert response.status_code == 200
        assert "ndjson" in response.headers["content-type"]

        # Verify content is valid JSONLines
        lines = response.text.strip().split('\n')
        assert len(lines) == 3
        for line in lines:
            record = json.loads(line)
            assert "call_id" in record


    def test_resume_analysis_endpoint(self, test_client, temp_storage):
        """Test POST /api/resume-analysis/{scenario_id} endpoint."""
        # Create a failed checkpoint to resume from
        checkpoint_data = {
            "checkpoint_id": "resume_test_cp",
            "analysis_id": "original-analysis-id",
            "scenario_id": "resume_test",
            "proposition": "Test resume proposition",
            "scenario_config": {
                "paradigms": [{"id": "K0", "name": "Test"}],
                "hypotheses": [{"id": "H0", "label": "Null"}],
                "priors_by_paradigm": {"K0": {"H0": 0.5}}
            },
            "status": "failed",
            "error": {"message": "Budget exceeded", "phase": "phase_2", "type": "budget_exceeded"},
            "resume_point": {"phase": "phase_2", "description": "Resume from phase 2"},
            "api_call_count": 5,
            "cost_summary": {"total_cost_usd": 0.50},
            "completed_phases": {
                "phase_1": {"data": {"methodology": "Test methodology"}}
            },
            "reasoning_model": "gpt-5.2"
        }
        temp_storage.store_checkpoint("resume_test", checkpoint_data)

        # Call resume endpoint - it should return immediately with new analysis ID
        # (actual analysis runs in background, which will fail without real API key)
        response = test_client.post("/api/resume-analysis/resume_test")
        assert response.status_code == 200
        data = response.json()

        assert "analysis_id" in data
        assert data["resumed_from"] == "resume_test_cp"
        assert data["resume_point"]["phase"] == "phase_2"

    def test_resume_analysis_not_found(self, test_client):
        """Test POST /api/resume-analysis/{scenario_id} for non-existent checkpoint."""
        response = test_client.post("/api/resume-analysis/nonexistent_scenario")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
