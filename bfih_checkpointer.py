"""
BFIH Backend: Per-API-Call Checkpointing System

Provides granular checkpointing for:
1. Resume from exact failure point (not just phase boundaries)
2. Full audit trail of all LLM interactions
3. Cost transparency at API call level
4. Graceful failure with actionable recovery instructions

Dual-Layer Design:
- Layer 1: API Call Audit Log (JSONLines - append only, ~2-5KB per call)
- Layer 2: Phase Checkpoint (atomic JSON overwrite, ~200-500KB total)
"""

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from bfih_storage import StorageBackend

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class APICallRecord:
    """
    Record of a single LLM API call for audit logging.

    Each call is logged as an independent JSON record in the audit log.
    Designed to be append-only for thread safety during parallel execution.
    """
    call_id: str
    analysis_id: str
    scenario_id: str
    timestamp: str
    phase_name: str
    method: str  # e.g., "_run_phase", "_run_structured_phase", "_run_reasoning_phase"
    model: str
    prompt_hash: str  # SHA256 hash of prompt (not full prompt for storage efficiency)
    prompt_length: int
    status: str  # "success", "error", "timeout"
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost_usd: float
    duration_ms: int

    # Optional fields for parallel execution tracking
    parallel_batch_id: Optional[str] = None
    parallel_index: Optional[int] = None

    # Error tracking
    error_message: Optional[str] = None
    error_type: Optional[str] = None

    # Optional schema info for structured outputs
    schema_name: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class PhaseData:
    """Data for a completed phase, stored in the checkpoint."""
    phase_id: str
    completed_at: str
    duration_ms: int
    api_calls: int
    cost_usd: float

    # Phase-specific data (truncated for storage efficiency)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResumePoint:
    """Information about where to resume analysis."""
    phase: str
    sub_phase: Optional[str] = None
    completed_items: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================================
# CHECKPOINTER
# ============================================================================

class AnalysisCheckpointer:
    """
    Manages checkpointing for a single BFIH analysis.

    Provides:
    - Per-API-call audit logging (JSONLines, append-only)
    - Phase-level checkpoints (atomic JSON overwrite)
    - Error recovery with actionable instructions
    - Resume capability from any failure point
    """

    # Maximum size for stored phase data (to prevent bloat)
    MAX_METHODOLOGY_CHARS = 5000
    MAX_EVIDENCE_TEXT_CHARS = 10000
    MAX_LIKELIHOODS_TEXT_CHARS = 10000

    def __init__(
        self,
        analysis_id: str,
        scenario_id: str,
        proposition: str,
        scenario_config: Dict,
        storage: 'StorageBackend',
        reasoning_model: str = "gpt-5.2"
    ):
        """
        Initialize a new checkpointer for an analysis.

        Args:
            analysis_id: Unique analysis ID (UUID)
            scenario_id: Scenario ID (e.g., "auto_8d5aeaf4")
            proposition: The research question being analyzed
            scenario_config: Full scenario configuration
            storage: Storage backend for persistence
            reasoning_model: Model being used for analysis
        """
        self.storage = storage
        self._call_counter = 0
        self._phase_start_time: Optional[float] = None
        self._phase_api_calls: int = 0
        self._phase_cost: float = 0.0

        # Initialize checkpoint data structure
        now = datetime.now(timezone.utc).isoformat()
        self.checkpoint = {
            "checkpoint_id": f"{scenario_id}_cp_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "analysis_id": analysis_id,
            "scenario_id": scenario_id,
            "proposition": proposition,
            "scenario_config": scenario_config,
            "reasoning_model": reasoning_model,
            "created_at": now,
            "updated_at": now,
            "status": "in_progress",
            "error": None,

            "cost_summary": {
                "total_cost_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_reasoning_tokens": 0
            },
            "api_call_count": 0,

            "completed_phases": {},
            "resume_point": None
        }

        logger.info(f"Checkpointer initialized: {self.checkpoint['checkpoint_id']}")

    @classmethod
    def load(cls, scenario_id: str, storage: 'StorageBackend') -> Optional['AnalysisCheckpointer']:
        """
        Load an existing checkpoint for resume.

        Args:
            scenario_id: Scenario ID to load checkpoint for
            storage: Storage backend

        Returns:
            AnalysisCheckpointer instance with restored state, or None if not found
        """
        checkpoint_data = storage.retrieve_checkpoint(scenario_id)
        if not checkpoint_data:
            logger.warning(f"No checkpoint found for scenario: {scenario_id}")
            return None

        # Create instance and restore state
        instance = cls.__new__(cls)
        instance.storage = storage
        instance.checkpoint = checkpoint_data
        instance._call_counter = checkpoint_data.get("api_call_count", 0)
        instance._phase_start_time = None
        instance._phase_api_calls = 0
        instance._phase_cost = 0.0

        logger.info(f"Checkpoint loaded: {checkpoint_data.get('checkpoint_id')}")
        logger.info(f"Status: {checkpoint_data.get('status')}, Completed phases: {list(checkpoint_data.get('completed_phases', {}).keys())}")

        return instance

    def _hash_prompt(self, prompt: str) -> str:
        """Generate SHA256 hash of prompt for audit log."""
        return f"sha256:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:16]}"

    def start_phase(self, phase_id: str):
        """Mark the start of a phase for timing."""
        self._phase_start_time = time.time()
        self._phase_api_calls = 0
        self._phase_cost = 0.0
        logger.debug(f"Phase started: {phase_id}")

    def record_api_call(
        self,
        phase_name: str,
        method: str,
        model: str,
        prompt: str,
        status: str,
        input_tokens: int,
        output_tokens: int,
        reasoning_tokens: int,
        cost_usd: float,
        duration_ms: int,
        parallel_batch_id: Optional[str] = None,
        parallel_index: Optional[int] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        schema_name: Optional[str] = None,
        tools_used: Optional[List[str]] = None
    ) -> str:
        """
        Record an API call to the audit log.

        This appends a single line to the JSONLines audit log.
        Thread-safe for parallel execution.

        Returns:
            The call_id of the recorded call
        """
        call_id = str(uuid.uuid4())[:8]
        self._call_counter += 1
        self._phase_api_calls += 1
        self._phase_cost += cost_usd

        record = APICallRecord(
            call_id=call_id,
            analysis_id=self.checkpoint["analysis_id"],
            scenario_id=self.checkpoint["scenario_id"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase_name=phase_name,
            method=method,
            model=model,
            prompt_hash=self._hash_prompt(prompt),
            prompt_length=len(prompt),
            status=status,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            parallel_batch_id=parallel_batch_id,
            parallel_index=parallel_index,
            error_message=error_message,
            error_type=error_type,
            schema_name=schema_name,
            tools_used=tools_used or []
        )

        # Append to audit log (thread-safe)
        try:
            self.storage.append_api_call_log(
                self.checkpoint["scenario_id"],
                record.to_dict()
            )
        except Exception as e:
            logger.warning(f"Failed to append API call log: {e}")

        # Update running totals
        self.checkpoint["api_call_count"] = self._call_counter
        self.checkpoint["cost_summary"]["total_cost_usd"] += cost_usd
        self.checkpoint["cost_summary"]["total_input_tokens"] += input_tokens
        self.checkpoint["cost_summary"]["total_output_tokens"] += output_tokens
        self.checkpoint["cost_summary"]["total_reasoning_tokens"] += reasoning_tokens

        logger.debug(f"API call recorded: {call_id} ({phase_name}, ${cost_usd:.4f})")
        return call_id

    def save_phase(
        self,
        phase_id: str,
        **phase_data
    ):
        """
        Save a phase checkpoint after phase completion.

        This atomically overwrites the checkpoint file.

        Args:
            phase_id: Phase identifier (e.g., "phase_1", "phase_2", "phase_3b")
            **phase_data: Phase-specific data to store
        """
        duration_ms = int((time.time() - self._phase_start_time) * 1000) if self._phase_start_time else 0

        # Truncate large text fields
        if "methodology" in phase_data and phase_data["methodology"]:
            phase_data["methodology"] = phase_data["methodology"][:self.MAX_METHODOLOGY_CHARS]
        if "evidence_text" in phase_data and phase_data["evidence_text"]:
            phase_data["evidence_text"] = phase_data["evidence_text"][:self.MAX_EVIDENCE_TEXT_CHARS]
        if "likelihoods_text" in phase_data and phase_data["likelihoods_text"]:
            phase_data["likelihoods_text"] = phase_data["likelihoods_text"][:self.MAX_LIKELIHOODS_TEXT_CHARS]

        phase_record = PhaseData(
            phase_id=phase_id,
            completed_at=datetime.now(timezone.utc).isoformat(),
            duration_ms=duration_ms,
            api_calls=self._phase_api_calls,
            cost_usd=self._phase_cost,
            data=phase_data
        )

        self.checkpoint["completed_phases"][phase_id] = phase_record.to_dict()
        self.checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Update resume point
        self.checkpoint["resume_point"] = self._get_next_resume_point(phase_id)

        # Persist checkpoint
        try:
            self.storage.store_checkpoint(
                self.checkpoint["scenario_id"],
                self.checkpoint
            )
            logger.info(f"Phase checkpoint saved: {phase_id} (${self._phase_cost:.4f}, {self._phase_api_calls} calls)")
        except Exception as e:
            logger.error(f"Failed to save phase checkpoint: {e}")
            raise

        # Reset phase counters
        self._phase_start_time = None
        self._phase_api_calls = 0
        self._phase_cost = 0.0

    def save_parallel_progress(
        self,
        phase_id: str,
        sub_phase: str,
        completed_item: str,
        item_result: Any
    ):
        """
        Save progress during parallel execution (e.g., Phase 2 evidence searches, Phase 3b calibrations).

        This allows resuming from the exact item in a parallel batch.

        Args:
            phase_id: Parent phase (e.g., "phase_2", "phase_3b")
            sub_phase: Sub-phase identifier (e.g., "evidence_search", "calibration")
            completed_item: Identifier of the completed item
            item_result: Result data for the item
        """
        # Initialize parallel tracking if needed
        parallel_key = f"{phase_id}_parallel_{sub_phase}"
        if parallel_key not in self.checkpoint.get("parallel_progress", {}):
            if "parallel_progress" not in self.checkpoint:
                self.checkpoint["parallel_progress"] = {}
            self.checkpoint["parallel_progress"][parallel_key] = {
                "completed_items": [],
                "results": {}
            }

        progress = self.checkpoint["parallel_progress"][parallel_key]
        if completed_item not in progress["completed_items"]:
            progress["completed_items"].append(completed_item)
        progress["results"][completed_item] = item_result

        # Update resume point
        self.checkpoint["resume_point"] = ResumePoint(
            phase=phase_id,
            sub_phase=sub_phase,
            completed_items=progress["completed_items"],
            description=f"Resume {sub_phase} from item after {completed_item}"
        ).to_dict()

        self.checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Persist incrementally (every 3 items to balance durability vs performance)
        if len(progress["completed_items"]) % 3 == 0:
            try:
                self.storage.store_checkpoint(
                    self.checkpoint["scenario_id"],
                    self.checkpoint
                )
                logger.debug(f"Parallel progress saved: {completed_item} ({len(progress['completed_items'])} total)")
            except Exception as e:
                logger.warning(f"Failed to save parallel progress: {e}")

    def get_parallel_completed(self, phase_id: str, sub_phase: str) -> List[str]:
        """Get list of completed items for a parallel sub-phase."""
        parallel_key = f"{phase_id}_parallel_{sub_phase}"
        progress = self.checkpoint.get("parallel_progress", {}).get(parallel_key, {})
        return progress.get("completed_items", [])

    def get_parallel_results(self, phase_id: str, sub_phase: str) -> Dict[str, Any]:
        """Get results for completed items in a parallel sub-phase."""
        parallel_key = f"{phase_id}_parallel_{sub_phase}"
        progress = self.checkpoint.get("parallel_progress", {}).get(parallel_key, {})
        return progress.get("results", {})

    def save_error(
        self,
        error_message: str,
        phase: str,
        error_type: str = "unknown"
    ):
        """
        Save error checkpoint with recovery instructions.

        Args:
            error_message: The error message
            phase: Phase where error occurred
            error_type: Type of error (e.g., "api_error", "timeout", "budget_exceeded")
        """
        recovery = self._get_recovery_instructions(error_type, phase)

        self.checkpoint["status"] = "failed"
        self.checkpoint["error"] = {
            "message": error_message,
            "phase": phase,
            "type": error_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.checkpoint["resume_point"] = ResumePoint(
            phase=phase,
            description=recovery
        ).to_dict()
        self.checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Persist checkpoint
        try:
            self.storage.store_checkpoint(
                self.checkpoint["scenario_id"],
                self.checkpoint
            )
            logger.info(f"Error checkpoint saved: {phase} - {error_type}")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to save error checkpoint: {e}")

        return recovery

    def mark_completed(self):
        """Mark the analysis as successfully completed."""
        self.checkpoint["status"] = "completed"
        self.checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.checkpoint["resume_point"] = None

        try:
            self.storage.store_checkpoint(
                self.checkpoint["scenario_id"],
                self.checkpoint
            )
            logger.info(f"Analysis marked complete: {self.checkpoint['checkpoint_id']}")
        except Exception as e:
            logger.warning(f"Failed to mark checkpoint complete: {e}")

    def _get_next_resume_point(self, completed_phase: str) -> Optional[dict]:
        """Determine the next phase to resume from after completing a phase."""
        phase_order = [
            "phase_0a",  # Paradigms
            "phase_0b",  # Hypotheses
            "phase_0c",  # Priors
            "phase_1",   # Methodology
            "phase_2",   # Evidence
            "phase_3a",  # Clustering
            "phase_3b",  # Calibrated likelihoods
            "phase_4",   # Bayesian computation
            "phase_5",   # Report
        ]

        try:
            idx = phase_order.index(completed_phase)
            if idx + 1 < len(phase_order):
                next_phase = phase_order[idx + 1]
                return ResumePoint(
                    phase=next_phase,
                    description=f"Resume from {next_phase}"
                ).to_dict()
        except ValueError:
            pass

        return None

    def _get_recovery_instructions(self, error_type: str, phase: str) -> str:
        """Generate actionable recovery instructions based on error type."""
        instructions = {
            "budget_exceeded": (
                f"Budget limit reached during {phase}. To resume:\n"
                f"1. Increase budget limit in request\n"
                f"2. Call POST /api/resume-analysis/{self.checkpoint['scenario_id']}\n"
                f"Completed work has been saved and will not be repeated."
            ),
            "api_error": (
                f"API error during {phase}. To resume:\n"
                f"1. Check OpenAI API status at status.openai.com\n"
                f"2. Verify API key is valid and has sufficient quota\n"
                f"3. Call POST /api/resume-analysis/{self.checkpoint['scenario_id']}\n"
                f"Completed work has been saved."
            ),
            "timeout": (
                f"Request timed out during {phase}. To resume:\n"
                f"1. Check network connectivity\n"
                f"2. Verify OpenAI service is responsive\n"
                f"3. Call POST /api/resume-analysis/{self.checkpoint['scenario_id']}\n"
                f"Partial work has been saved."
            ),
            "auth_error": (
                f"Authentication failed during {phase}. To fix:\n"
                f"1. Verify your OpenAI API key is valid\n"
                f"2. Check that your API key has not been revoked\n"
                f"3. Run /api/setup with a valid API key\n"
                f"4. Call POST /api/resume-analysis/{self.checkpoint['scenario_id']}"
            ),
            "unknown": (
                f"Unexpected error during {phase}. To resume:\n"
                f"1. Check server logs for details\n"
                f"2. Call POST /api/resume-analysis/{self.checkpoint['scenario_id']}\n"
                f"Completed work has been saved."
            )
        }
        return instructions.get(error_type, instructions["unknown"])

    def is_phase_completed(self, phase_id: str) -> bool:
        """Check if a phase has already been completed."""
        return phase_id in self.checkpoint.get("completed_phases", {})

    def get_phase_data(self, phase_id: str) -> Optional[Dict]:
        """Get stored data for a completed phase."""
        phase_record = self.checkpoint.get("completed_phases", {}).get(phase_id)
        if phase_record:
            return phase_record.get("data", {})
        return None

    def get_checkpoint_summary(self) -> Dict:
        """Get a summary of the current checkpoint state."""
        return {
            "checkpoint_id": self.checkpoint["checkpoint_id"],
            "scenario_id": self.checkpoint["scenario_id"],
            "status": self.checkpoint["status"],
            "api_call_count": self.checkpoint["api_call_count"],
            "cost_summary": self.checkpoint["cost_summary"],
            "completed_phases": list(self.checkpoint.get("completed_phases", {}).keys()),
            "resume_point": self.checkpoint.get("resume_point"),
            "updated_at": self.checkpoint["updated_at"]
        }
