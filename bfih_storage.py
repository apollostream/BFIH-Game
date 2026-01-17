"""
BFIH Backend: Storage Management
Handles persistence of analysis results, scenarios, and metadata

Supports:
- File-based storage (JSON) for MVP
- Google Cloud Storage (for production)
- PostgreSQL integration (optional)
- Redis caching layer
"""

import json
import os
import logging
import threading
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import GCS - optional dependency
try:
    from google.cloud import storage as gcs
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.info("google-cloud-storage not installed, GCS backend unavailable")


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
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)

            # Fallback: search by scenario_id field
            return self._find_analysis_by_scenario_id(analysis_id)
        except Exception as e:
            logger.error(f"Error retrieving analysis result: {str(e)}")
            return None

    def _find_analysis_by_scenario_id(self, scenario_id: str) -> Optional[Dict]:
        """Search through analyses to find one matching the given scenario_id"""
        try:
            for filepath in self.analysis_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    if data.get('scenario_id') == scenario_id:
                        logger.info(f"Found analysis by scenario_id search: {scenario_id}")
                        # Cache it under scenario_id for future lookups
                        self.store_analysis_result(scenario_id, data)
                        return data
                except Exception:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error searching analyses by scenario_id: {e}")
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
        """Get analysis status with staleness detection.

        Returns a dict with:
        - analysis_id: The analysis ID
        - status: Current status string
        - timestamp: ISO timestamp of last update
        - is_stale: True if status hasn't been updated in 5+ minutes while still processing
        """
        try:
            filepath = self.status_dir / f"{analysis_id}_status.txt"
            if not filepath.exists():
                return None

            with open(filepath, 'r') as f:
                content = f.read().strip().split('\n')

            status = content[0]
            timestamp = content[1] if len(content) > 1 else None

            # Detect staleness: if processing and not updated in 5+ minutes
            # Also check progress log - if there are recent log entries, backend is working
            is_stale = False
            if timestamp and status.startswith('processing'):
                try:
                    updated = datetime.fromisoformat(timestamp)
                    status_age_seconds = (datetime.utcnow() - updated).total_seconds()

                    if status_age_seconds > 300:  # Status is old, check progress log
                        # Check if progress log has recent entries
                        progress_log = self.get_progress_log(analysis_id)
                        if progress_log:
                            last_log = progress_log[-1]
                            last_log_time = datetime.fromisoformat(last_log.get('timestamp', ''))
                            log_age_seconds = (datetime.utcnow() - last_log_time).total_seconds()
                            is_stale = log_age_seconds > 300  # Only stale if log is also old
                        else:
                            is_stale = True  # No progress log, use status staleness
                except ValueError:
                    pass  # Invalid timestamp, can't determine staleness

            return {
                "analysis_id": analysis_id,
                "status": status,
                "timestamp": timestamp,
                "is_stale": is_stale
            }
        except Exception as e:
            logger.error(f"Error getting analysis status: {str(e)}")
            return None
    
    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios with summary information"""
        try:
            files = sorted(self.scenario_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            files = files[offset:offset+limit]

            scenarios = []
            for f in files:
                with open(f, 'r') as file:
                    data = json.load(file)

                    # Handle two formats:
                    # 1. Wrapper format: {scenario_id, title, scenario_config: {...}}
                    # 2. Direct format: {scenario_metadata: {...}, scenario_narrative: {...}}
                    if 'scenario_config' in data:
                        # Wrapper format - extract from nested config
                        config = data.get('scenario_config', {})
                        metadata = config.get('scenario_metadata', {})
                        narrative = config.get('scenario_narrative', {})
                        wrapper_id = data.get('scenario_id')
                        creator = data.get('creator', '')
                    else:
                        # Direct format
                        config = data
                        metadata = config.get('scenario_metadata', {})
                        narrative = config.get('scenario_narrative', {})
                        wrapper_id = None
                        creator = metadata.get('creator', '')

                    # Get title from multiple possible locations (prefer research_question as it's the proposition)
                    title = (
                        narrative.get('research_question') or
                        narrative.get('title') or
                        metadata.get('title') or
                        config.get('proposition') or
                        f"Analysis {metadata.get('scenario_id', f.stem)}"
                    )

                    # Get scenario_id
                    scenario_id = wrapper_id or metadata.get('scenario_id') or config.get('scenario_id') or f.stem

                    # Get topic from domain or extract from metadata
                    topic = metadata.get('topic') or metadata.get('domain', 'general')

                    # Get model from config or metadata
                    model = (
                        data.get('model') or
                        config.get('reasoning_model') or
                        metadata.get('model') or
                        ''
                    )

                    summary = {
                        'scenario_id': scenario_id,
                        'title': title,
                        'domain': metadata.get('domain', 'general'),
                        'topic': topic,
                        'difficulty_level': metadata.get('difficulty_level', 'medium'),
                        'created_date': metadata.get('created_date', ''),
                        'creator': creator or metadata.get('creator', 'anonymous'),
                        'model': model,
                    }
                    scenarios.append(summary)

            return scenarios
        except Exception as e:
            logger.error(f"Error listing scenarios: {str(e)}")
            return []

    def store_visualization(self, scenario_id: str, png_content: bytes) -> Optional[str]:
        """
        Store PNG visualization to local file and return path.

        Args:
            scenario_id: The scenario/analysis ID
            png_content: The PNG file content (binary)

        Returns:
            Path to the PNG file, or None on failure
        """
        try:
            viz_dir = self.base_dir / "visualizations"
            viz_dir.mkdir(parents=True, exist_ok=True)
            filepath = viz_dir / f"{scenario_id}-evidence-flow.png"
            with open(filepath, 'wb') as f:
                f.write(png_content)
            logger.info(f"Stored visualization: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error storing visualization: {str(e)}")
            return None

    def cancel_analysis(self, analysis_id: str) -> bool:
        """Mark an analysis as cancelled by creating a cancellation flag file."""
        try:
            filepath = self.status_dir / f"{analysis_id}_cancelled.txt"
            with open(filepath, 'w') as f:
                f.write(datetime.utcnow().isoformat())
            logger.info(f"Analysis cancelled: {analysis_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling analysis: {str(e)}")
            return False

    def is_analysis_cancelled(self, analysis_id: str) -> bool:
        """Check if an analysis has been cancelled."""
        filepath = self.status_dir / f"{analysis_id}_cancelled.txt"
        return filepath.exists()

    def append_progress_log(self, analysis_id: str, message: str) -> bool:
        """Append a progress message to the analysis log. Keeps last 20 messages."""
        try:
            filepath = self.status_dir / f"{analysis_id}_progress.json"
            messages = []
            if filepath.exists():
                with open(filepath, 'r') as f:
                    messages = json.load(f)

            messages.append({
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            })
            # Keep only last 20 messages
            messages = messages[-20:]

            with open(filepath, 'w') as f:
                json.dump(messages, f)
            return True
        except Exception as e:
            logger.error(f"Error appending progress log: {str(e)}")
            return False

    def get_progress_log(self, analysis_id: str) -> List[Dict]:
        """Get the progress log messages for an analysis."""
        try:
            filepath = self.status_dir / f"{analysis_id}_progress.json"
            if not filepath.exists():
                return []
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading progress log: {str(e)}")
            return []


# ============================================================================
# GOOGLE CLOUD STORAGE BACKEND (Production)
# ============================================================================

class GCSStorageBackend(StorageBackend):
    """Google Cloud Storage backend for persistent, shared storage"""

    def __init__(self, bucket_name: str, prefix: str = "bfih"):
        if not GCS_AVAILABLE:
            raise RuntimeError("google-cloud-storage package not installed")

        self.client = gcs.Client()
        self.bucket = self.client.bucket(bucket_name)
        self.prefix = prefix

        # Paths within the bucket
        self.analysis_prefix = f"{prefix}/analyses"
        self.scenario_prefix = f"{prefix}/scenarios"
        self.status_prefix = f"{prefix}/status"

        # Thread-safe lock for append operations (prevents race conditions)
        self._append_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()  # Lock for creating per-analysis locks

        logger.info(f"GCSStorageBackend initialized: gs://{bucket_name}/{prefix}")

    def _get_blob(self, path: str):
        """Get a blob reference"""
        return self.bucket.blob(path)

    def _read_json(self, path: str) -> Optional[Dict]:
        """Read JSON from GCS (fresh read, no caching)"""
        try:
            blob = self._get_blob(path)
            # Force fresh read by not using exists() first - just try to download
            try:
                content = blob.download_as_text()
                return json.loads(content)
            except Exception as download_error:
                if "404" in str(download_error) or "Not Found" in str(download_error):
                    return None
                raise
        except Exception as e:
            logger.error(f"Error reading from GCS {path}: {str(e)}")
            return None

    def _write_json(self, path: str, data: Dict) -> bool:
        """Write JSON to GCS"""
        try:
            blob = self._get_blob(path)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type='application/json'
            )
            return True
        except Exception as e:
            logger.error(f"Error writing to GCS {path}: {str(e)}")
            return False

    def _write_text(self, path: str, text: str) -> bool:
        """Write text to GCS"""
        try:
            blob = self._get_blob(path)
            blob.upload_from_string(text, content_type='text/plain')
            return True
        except Exception as e:
            logger.error(f"Error writing text to GCS {path}: {str(e)}")
            return False

    def _read_text(self, path: str) -> Optional[str]:
        """Read text from GCS (fresh read, no caching)"""
        try:
            blob = self._get_blob(path)
            # Force fresh read by not using exists() first - just try to download
            try:
                return blob.download_as_text()
            except Exception as download_error:
                if "404" in str(download_error) or "Not Found" in str(download_error):
                    return None
                raise
        except Exception as e:
            logger.error(f"Error reading text from GCS {path}: {str(e)}")
            return None

    def store_analysis_result(self, analysis_id: str, result: Dict) -> bool:
        """Store analysis result to GCS"""
        path = f"{self.analysis_prefix}/{analysis_id}.json"
        success = self._write_json(path, result)
        if success:
            logger.info(f"Stored analysis result to GCS: {analysis_id}")
        return success

    def retrieve_analysis_result(self, analysis_id: str) -> Optional[Dict]:
        """Retrieve analysis result from GCS"""
        path = f"{self.analysis_prefix}/{analysis_id}.json"
        result = self._read_json(path)
        if result:
            return result

        # Fallback: search for analysis by scenario_id field
        # This handles legacy analyses stored only by analysis_id (UUID)
        return self._find_analysis_by_scenario_id(analysis_id)

    def _find_analysis_by_scenario_id(self, scenario_id: str) -> Optional[Dict]:
        """Search through analyses to find one matching the given scenario_id"""
        try:
            blobs = list(self.bucket.list_blobs(prefix=f"{self.analysis_prefix}/"))
            for blob in blobs:
                if not blob.name.endswith('.json'):
                    continue
                try:
                    content = blob.download_as_text()
                    data = json.loads(content)
                    if data.get('scenario_id') == scenario_id:
                        logger.info(f"Found analysis by scenario_id search: {scenario_id}")
                        # Cache it under scenario_id for future lookups
                        self.store_analysis_result(scenario_id, data)
                        return data
                except Exception:
                    continue
            return None
        except Exception as e:
            logger.error(f"Error searching analyses by scenario_id: {e}")
            return None

    def store_scenario_config(self, scenario_id: str, config: Dict) -> bool:
        """Store scenario configuration to GCS"""
        path = f"{self.scenario_prefix}/{scenario_id}.json"
        success = self._write_json(path, config)
        if success:
            logger.info(f"Stored scenario config to GCS: {scenario_id}")
        return success

    def retrieve_scenario_config(self, scenario_id: str) -> Optional[Dict]:
        """Retrieve scenario configuration from GCS"""
        path = f"{self.scenario_prefix}/{scenario_id}.json"
        return self._read_json(path)

    def store_analysis_request(self, analysis_id: str, request: Dict) -> bool:
        """Store analysis request metadata to GCS"""
        path = f"{self.status_prefix}/{analysis_id}_request.json"
        return self._write_json(path, request)

    def update_analysis_status(self, analysis_id: str, status: str) -> bool:
        """Update analysis status in GCS"""
        path = f"{self.status_prefix}/{analysis_id}_status.txt"
        content = f"{status}\n{datetime.utcnow().isoformat()}"
        success = self._write_text(path, content)
        if success:
            logger.info(f"Updated analysis status in GCS: {analysis_id} -> {status}")
        else:
            logger.error(f"FAILED to update analysis status in GCS: {analysis_id} -> {status}")
        return success

    def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis status from GCS with staleness detection.

        Returns a dict with:
        - analysis_id: The analysis ID
        - status: Current status string
        - timestamp: ISO timestamp of last update
        - is_stale: True if status hasn't been updated in 5+ minutes while still processing
        """
        path = f"{self.status_prefix}/{analysis_id}_status.txt"
        content = self._read_text(path)
        if not content:
            return None

        lines = content.strip().split('\n')
        status = lines[0]
        timestamp = lines[1] if len(lines) > 1 else None

        # Detect staleness: if processing and not updated in 5+ minutes
        # Also check progress log - if there are recent log entries, backend is working
        is_stale = False
        if timestamp and status.startswith('processing'):
            try:
                updated = datetime.fromisoformat(timestamp)
                status_age_seconds = (datetime.utcnow() - updated).total_seconds()

                if status_age_seconds > 300:  # Status is old, check progress log
                    # Check if progress log has recent entries
                    progress_log = self.get_progress_log(analysis_id)
                    if progress_log:
                        last_log = progress_log[-1]
                        last_log_time = datetime.fromisoformat(last_log.get('timestamp', ''))
                        log_age_seconds = (datetime.utcnow() - last_log_time).total_seconds()
                        is_stale = log_age_seconds > 300  # Only stale if log is also old
                    else:
                        is_stale = True  # No progress log, use status staleness
            except ValueError:
                pass  # Invalid timestamp, can't determine staleness

        return {
            "analysis_id": analysis_id,
            "status": status,
            "timestamp": timestamp,
            "is_stale": is_stale
        }

    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios from GCS with summary information"""
        try:
            # List all scenario blobs
            blobs = list(self.bucket.list_blobs(prefix=f"{self.scenario_prefix}/"))

            # Filter to only .json files and sort by updated time (newest first)
            json_blobs = [b for b in blobs if b.name.endswith('.json')]
            json_blobs.sort(key=lambda b: b.updated or datetime.min, reverse=True)

            # Apply pagination
            json_blobs = json_blobs[offset:offset+limit]

            scenarios = []
            for blob in json_blobs:
                try:
                    content = blob.download_as_text()
                    data = json.loads(content)

                    # Handle two formats (same logic as FileStorageBackend)
                    if 'scenario_config' in data:
                        config = data.get('scenario_config', {})
                        metadata = config.get('scenario_metadata', {})
                        narrative = config.get('scenario_narrative', {})
                        wrapper_id = data.get('scenario_id')
                        creator = data.get('creator', '')
                    else:
                        config = data
                        metadata = config.get('scenario_metadata', {})
                        narrative = config.get('scenario_narrative', {})
                        wrapper_id = None
                        creator = metadata.get('creator', '')

                    # Extract scenario_id from blob name if not in data
                    blob_id = blob.name.split('/')[-1].replace('.json', '')

                    # Get title from multiple possible locations
                    title = (
                        narrative.get('research_question') or
                        narrative.get('title') or
                        metadata.get('title') or
                        config.get('proposition') or
                        f"Analysis {metadata.get('scenario_id', blob_id)}"
                    )

                    scenario_id = wrapper_id or metadata.get('scenario_id') or config.get('scenario_id') or blob_id

                    # Get topic from domain or extract from title
                    topic = metadata.get('topic') or metadata.get('domain', 'general')

                    # Get model from config or metadata
                    model = (
                        data.get('model') or
                        config.get('reasoning_model') or
                        metadata.get('model') or
                        ''
                    )

                    summary = {
                        'scenario_id': scenario_id,
                        'title': title,
                        'domain': metadata.get('domain', 'general'),
                        'topic': topic,
                        'difficulty_level': metadata.get('difficulty_level', 'medium'),
                        'created_date': metadata.get('created_date', ''),
                        'creator': creator or metadata.get('creator', 'anonymous'),
                        'model': model,
                        'updated': blob.updated.isoformat() if blob.updated else '',
                    }
                    scenarios.append(summary)
                except Exception as e:
                    logger.error(f"Error parsing scenario blob {blob.name}: {str(e)}")
                    continue

            return scenarios
        except Exception as e:
            logger.error(f"Error listing scenarios from GCS: {str(e)}")
            return []

    def store_visualization(self, scenario_id: str, png_content: bytes) -> Optional[str]:
        """
        Store PNG visualization to GCS and return public URL.

        Args:
            scenario_id: The scenario/analysis ID
            png_content: The PNG file content (binary)

        Returns:
            Public URL to the PNG file, or None on failure
        """
        try:
            path = f"{self.prefix}/visualizations/{scenario_id}-evidence-flow.png"
            logger.info(f"Uploading visualization to GCS path: {path}")

            blob = self._get_blob(path)
            blob.upload_from_string(png_content, content_type='image/png')
            logger.info(f"Upload complete, attempting to make public...")

            # Try to make the blob publicly accessible
            try:
                blob.make_public()
                logger.info("Made blob public successfully")
            except Exception as pub_err:
                logger.warning(f"Could not make blob public (may need bucket-level IAM): {pub_err}")
                # Continue anyway - the URL might still work if bucket has public access

            # Construct URL manually as fallback
            public_url = f"https://storage.googleapis.com/{self.bucket.name}/{path}"
            logger.info(f"Stored visualization to GCS: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Error storing visualization to GCS: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def cancel_analysis(self, analysis_id: str) -> bool:
        """Mark an analysis as cancelled."""
        path = f"{self.status_prefix}/{analysis_id}_cancelled.txt"
        return self._write_text(path, datetime.utcnow().isoformat())

    def is_analysis_cancelled(self, analysis_id: str) -> bool:
        """Check if an analysis has been cancelled."""
        path = f"{self.status_prefix}/{analysis_id}_cancelled.txt"
        blob = self._get_blob(path)
        return blob.exists()

    def _get_append_lock(self, analysis_id: str) -> threading.Lock:
        """Get or create a lock for the given analysis_id (thread-safe)."""
        with self._locks_lock:
            if analysis_id not in self._append_locks:
                self._append_locks[analysis_id] = threading.Lock()
            return self._append_locks[analysis_id]

    def append_progress_log(self, analysis_id: str, message: str) -> bool:
        """Append a progress message to the analysis log. Keeps last 20 messages.

        Thread-safe: Uses a per-analysis lock to prevent race conditions
        when multiple callbacks try to append concurrently.
        """
        lock = self._get_append_lock(analysis_id)

        with lock:
            try:
                path = f"{self.status_prefix}/{analysis_id}_progress.json"
                logger.info(f"GCS append_progress_log: reading {path}")
                messages = self._read_json(path) or []
                logger.info(f"GCS append_progress_log: read {len(messages)} existing messages")

                messages.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": message
                })
                # Keep only last 20 messages
                messages = messages[-20:]

                logger.info(f"GCS append_progress_log: writing {len(messages)} messages to {path}")
                result = self._write_json(path, messages)
                logger.info(f"GCS append_progress_log: write result = {result}")
                return result
            except Exception as e:
                logger.error(f"Error appending progress log to GCS: {str(e)}")
                return False

    def get_progress_log(self, analysis_id: str) -> List[Dict]:
        """Get the progress log messages for an analysis."""
        path = f"{self.status_prefix}/{analysis_id}_progress.json"
        return self._read_json(path) or []


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
    
    def update_analysis_status(self, analysis_id: str, status: str, max_retries: int = 3) -> bool:
        """Update analysis status with retry logic for reliability.

        Args:
            analysis_id: The analysis ID
            status: The status string to set
            max_retries: Number of retry attempts (default 3)

        Returns:
            True if status was updated successfully, False otherwise
        """
        import time

        for attempt in range(max_retries):
            if self.backend.update_analysis_status(analysis_id, status):
                return True
            if attempt < max_retries - 1:
                wait_time = 0.5 * (attempt + 1)  # Exponential backoff: 0.5s, 1.0s, 1.5s
                logger.warning(f"Status update failed for {analysis_id}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)

        logger.error(f"Failed to update status after {max_retries} attempts: {analysis_id} -> {status}")
        return False
    
    def get_analysis_status(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis status"""
        return self.backend.get_analysis_status(analysis_id)
    
    def list_scenarios(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all stored scenarios"""
        return self.backend.list_scenarios(limit, offset)

    def store_visualization(self, scenario_id: str, png_content: bytes) -> Optional[str]:
        """Store PNG visualization and return URL/path"""
        return self.backend.store_visualization(scenario_id, png_content)

    def cancel_analysis(self, analysis_id: str) -> bool:
        """Mark an analysis as cancelled. Returns True if successful."""
        return self.backend.cancel_analysis(analysis_id)

    def is_analysis_cancelled(self, analysis_id: str) -> bool:
        """Check if an analysis has been cancelled."""
        return self.backend.is_analysis_cancelled(analysis_id)

    def append_progress_log(self, analysis_id: str, message: str) -> bool:
        """Append a progress message to the analysis log."""
        return self.backend.append_progress_log(analysis_id, message)

    def get_progress_log(self, analysis_id: str) -> List[Dict]:
        """Get the progress log messages for an analysis."""
        return self.backend.get_progress_log(analysis_id)


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
