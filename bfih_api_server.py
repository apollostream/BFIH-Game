"""
BFIH Backend: FastAPI Web Service
REST API for AI-Assisted Hypothesis Tournament Game

Endpoints:
- POST /api/bfih-analysis - Submit BFIH analysis request
- GET /api/bfih-analysis/{analysis_id} - Retrieve completed analysis
- GET /api/health - Health check
- POST /api/scenario - Store scenario config
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid
import os

from bfih_orchestrator_fixed import (
    BFIHOrchestrator,
    BFIHAnalysisRequest,
    BFIHAnalysisResult
)
from bfih_storage import StorageManager


# ============================================================================
# CREDENTIAL HELPERS
# ============================================================================

def get_orchestrator_for_request(
    api_key: Optional[str] = None,
    vector_store_id: Optional[str] = None
) -> BFIHOrchestrator:
    """
    Create an orchestrator with user-provided or default credentials.

    For multi-tenant deployment, users provide their own OpenAI API key
    via the User-OpenAI-API-Key header.
    """
    # Use provided credentials or fall back to env vars
    effective_api_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
    effective_vector_store = vector_store_id if vector_store_id else os.getenv("TREATISE_VECTOR_STORE_ID")

    if not effective_api_key:
        raise HTTPException(
            status_code=401,
            detail="OpenAI API key required. Provide via User-OpenAI-API-Key header or configure server environment."
        )

    return BFIHOrchestrator(
        api_key=effective_api_key,
        vector_store_id=effective_vector_store
    )


# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="BFIH Analysis API",
    description="Bayesian Framework for Intellectual Honesty Analysis API",
    version="1.0.0"
)

# Enable CORS for game frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
# Note: orchestrator is now created per-request to support user-provided API keys
# Default orchestrator for backwards compatibility (uses env vars if available)
_default_orchestrator = None
storage = StorageManager()


def get_default_orchestrator() -> Optional[BFIHOrchestrator]:
    """Get or create default orchestrator using env vars (for backwards compat)."""
    global _default_orchestrator
    if _default_orchestrator is None and os.getenv("OPENAI_API_KEY"):
        _default_orchestrator = BFIHOrchestrator()
    return _default_orchestrator


# ============================================================================
# DATA MODELS (Request/Response)
# ============================================================================

class AnalysisRequest(dict):
    """Request to conduct BFIH analysis"""
    def __init__(self, scenario_id: str, proposition: str, scenario_config: Dict, user_id: Optional[str] = None):
        self.scenario_id = scenario_id
        self.proposition = proposition
        self.scenario_config = scenario_config
        self.user_id = user_id


class AnalysisResponse(dict):
    """Response with BFIH analysis result"""
    pass


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BFIH Analysis API",
        "requires_api_key": not bool(os.getenv("OPENAI_API_KEY"))
    }


@app.get("/api/debug/static")
async def debug_static():
    """Debug endpoint to check static file status"""
    static_dir = Path(__file__).parent / "static"
    index_path = static_dir / "index.html"
    assets_dir = static_dir / "assets"

    result = {
        "static_dir": str(static_dir),
        "static_dir_exists": static_dir.exists(),
        "index_html_exists": index_path.exists(),
        "assets_dir_exists": assets_dir.exists(),
        "cwd": os.getcwd(),
        "file_location": str(Path(__file__).parent),
    }

    if static_dir.exists():
        try:
            result["static_contents"] = os.listdir(static_dir)
        except Exception as e:
            result["static_contents_error"] = str(e)

    return result


@app.post("/api/validate-credentials")
async def validate_credentials(
    user_openai_api_key: Optional[str] = Header(None, alias="User-OpenAI-API-Key"),
    user_vector_store_id: Optional[str] = Header(None, alias="User-Vector-Store-ID")
):
    """
    Validate user-provided OpenAI credentials.

    Headers:
        User-OpenAI-API-Key: Your OpenAI API key (required)
        User-Vector-Store-ID: Your vector store ID (optional)

    Returns:
    {
        "valid": true,
        "api_key_valid": true,
        "vector_store_valid": true/false,
        "message": "Credentials validated successfully"
    }
    """
    from openai import OpenAI, AuthenticationError, NotFoundError

    if not user_openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="User-OpenAI-API-Key header is required"
        )

    result = {
        "valid": False,
        "api_key_valid": False,
        "vector_store_valid": None,
        "message": ""
    }

    try:
        # Test API key with a minimal request
        test_client = OpenAI(api_key=user_openai_api_key)
        test_client.models.list()
        result["api_key_valid"] = True

        # Test vector store if provided
        if user_vector_store_id:
            try:
                test_client.vector_stores.retrieve(user_vector_store_id)
                result["vector_store_valid"] = True
            except NotFoundError:
                result["vector_store_valid"] = False
                result["message"] = "API key valid, but vector store not found"
                result["valid"] = True  # API key is still valid
                return result
        else:
            result["vector_store_valid"] = None  # Not provided

        result["valid"] = True
        result["message"] = "Credentials validated successfully"
        return result

    except AuthenticationError:
        result["message"] = "Invalid OpenAI API key"
        raise HTTPException(status_code=401, detail=result)
    except Exception as e:
        result["message"] = f"Validation error: {str(e)}"
        raise HTTPException(status_code=500, detail=result)


class SetupRequest(BaseModel):
    """Request body for user setup"""
    api_key: str


@app.post("/api/setup")
async def setup_user(request: SetupRequest):
    """
    One-time setup for new users.

    Creates a vector store with the BFIH methodology using the user's API key.
    The treatise PDF is bundled with the server deployment.

    Request body:
    {
        "api_key": "sk-proj-..."
    }

    Returns:
    {
        "success": true,
        "vector_store_id": "vs_...",
        "message": "Setup complete! Your vector store has been created."
    }
    """
    from openai import OpenAI, AuthenticationError
    from pathlib import Path
    import time

    api_key = request.api_key.strip()

    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")

    if not api_key.startswith("sk-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid API key format. OpenAI API keys start with 'sk-'"
        )

    # Find the treatise PDF (bundled in Docker image or local development)
    possible_paths = [
        Path("./assets/Intellectual-Honesty_rev-4.pdf"),  # Docker deployment
        Path("./Intellectual-Honesty_rev-4.pdf"),  # Local development
        Path(__file__).parent / "assets" / "Intellectual-Honesty_rev-4.pdf",
        Path(__file__).parent / "Intellectual-Honesty_rev-4.pdf",
    ]

    treatise_path = None
    for path in possible_paths:
        if path.exists():
            treatise_path = path
            break

    if not treatise_path:
        logger.error("Treatise PDF not found in any expected location")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: BFIH treatise not found. Please contact the administrator."
        )

    try:
        # Create OpenAI client with user's API key
        user_client = OpenAI(api_key=api_key)

        # Validate the API key first
        logger.info("Validating user API key...")
        try:
            user_client.models.list()
        except AuthenticationError:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Please check your OpenAI API key and try again."
            )

        # Create vector store
        logger.info("Creating vector store for user...")
        vs = user_client.beta.vector_stores.create(name="BFIH_Methodology")
        vector_store_id = vs.id
        logger.info(f"Vector store created: {vector_store_id}")

        # Upload treatise PDF
        logger.info(f"Uploading treatise from {treatise_path}...")
        with open(treatise_path, "rb") as f:
            file_response = user_client.beta.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file=f
            )
        logger.info(f"Treatise uploaded: {file_response.id}")

        # Wait for processing (with timeout)
        logger.info("Waiting for file processing...")
        for i in range(60):  # Wait up to 60 seconds
            vs_files = user_client.beta.vector_stores.files.list(vector_store_id)
            if vs_files.data:
                status = vs_files.data[0].status
                if status == "completed":
                    logger.info("File processing complete")
                    break
                elif status == "failed":
                    logger.error("File processing failed")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to process the methodology document. Please try again."
                    )
            time.sleep(1)
        else:
            logger.warning("File processing timeout - continuing anyway")

        return {
            "success": True,
            "vector_store_id": vector_store_id,
            "message": "Setup complete! Your vector store has been created with the BFIH methodology."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Setup failed: {str(e)}"
        )


@app.get("/api/reasoning-models")
async def get_reasoning_models():
    """Get available reasoning models for analysis"""
    from bfih_orchestrator_fixed import AVAILABLE_REASONING_MODELS, REASONING_MODEL
    return {
        "models": [
            {"id": "o3-mini", "name": "o3-mini", "description": "Fast, cost-efficient reasoning (default)", "cost": "low"},
            {"id": "o3", "name": "o3", "description": "Full o3 reasoning model", "cost": "medium"},
            {"id": "o4-mini", "name": "o4-mini", "description": "Latest mini reasoning model", "cost": "low"},
            {"id": "gpt-5", "name": "GPT-5", "description": "Full GPT-5 model", "cost": "high"},
            {"id": "gpt-5.2", "name": "GPT-5.2", "description": "Latest GPT-5, most capable", "cost": "high"},
            {"id": "gpt-5-mini", "name": "GPT-5 Mini", "description": "Budget GPT-5 variant", "cost": "low"},
        ],
        "default": REASONING_MODEL
    }


@app.post("/api/bfih-analysis")
async def submit_analysis(
    request: Dict,
    background_tasks: BackgroundTasks,
    user_openai_api_key: Optional[str] = Header(None, alias="User-OpenAI-API-Key"),
    user_vector_store_id: Optional[str] = Header(None, alias="User-Vector-Store-ID")
):
    """
    Submit a BFIH analysis request

    Headers (optional - falls back to server env vars if not provided):
        User-OpenAI-API-Key: Your OpenAI API key
        User-Vector-Store-ID: Your vector store ID for methodology retrieval

    Request body:
    {
        "scenario_id": "s_001_startup_success",
        "proposition": "Why did Startup X succeed?",
        "scenario_config": {...},
        "user_id": "user_123"
    }

    Returns:
    {
        "analysis_id": "uuid",
        "status": "processing",
        "estimated_seconds": 45
    }
    """
    try:
        # Validate credentials are available (either from headers or env)
        effective_api_key = user_openai_api_key or os.getenv("OPENAI_API_KEY")
        if not effective_api_key:
            raise HTTPException(
                status_code=401,
                detail="OpenAI API key required. Provide via User-OpenAI-API-Key header."
            )

        # Validate request
        required_fields = ["scenario_id", "proposition", "scenario_config"]
        if not all(field in request for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {required_fields}"
            )

        # Create analysis request object
        analysis_request = BFIHAnalysisRequest(
            scenario_id=request["scenario_id"],
            proposition=request["proposition"],
            scenario_config=request["scenario_config"],
            user_id=request.get("user_id"),
            reasoning_model=request.get("reasoning_model")  # Optional model override
        )

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        # Store request metadata
        storage.store_analysis_request(
            analysis_id=analysis_id,
            request=analysis_request
        )

        # Run analysis in background with user's credentials
        background_tasks.add_task(
            _run_analysis,
            analysis_id=analysis_id,
            analysis_request=analysis_request,
            api_key=user_openai_api_key,
            vector_store_id=user_vector_store_id
        )

        logger.info(f"Submitted analysis request: {analysis_id}")

        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "estimated_seconds": 45,
            "scenario_id": request["scenario_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bfih-analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """
    Retrieve completed BFIH analysis
    
    Returns:
    {
        "analysis_id": "uuid",
        "scenario_id": "s_001",
        "proposition": "...",
        "status": "completed",
        "report": "markdown report",
        "posteriors": {...},
        "metadata": {...},
        "created_at": "2026-01-06T..."
    }
    """
    try:
        result = storage.retrieve_analysis_result(analysis_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis not found: {analysis_id}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scenario")
async def store_scenario(scenario: Dict):
    """
    Store a scenario configuration for later use
    
    Request body:
    {
        "scenario_id": "s_001_startup_success",
        "title": "Startup Success Analysis",
        "domain": "business",
        "difficulty_level": "medium",
        "scenario_config": {...}
    }
    
    Returns:
    {
        "scenario_id": "s_001_startup_success",
        "status": "stored",
        "created_at": "..."
    }
    """
    try:
        # Validate
        if "scenario_id" not in scenario or "scenario_config" not in scenario:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: scenario_id, scenario_config"
            )
        
        # Store scenario
        storage.store_scenario_config(
            scenario_id=scenario["scenario_id"],
            config=scenario
        )
        
        logger.info(f"Stored scenario: {scenario['scenario_id']}")
        
        return {
            "scenario_id": scenario["scenario_id"],
            "status": "stored",
            "created_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenario/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Retrieve stored scenario configuration"""
    try:
        data = storage.retrieve_scenario_config(scenario_id)

        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario not found: {scenario_id}"
            )

        # Handle wrapper format: unwrap scenario_config if present
        # Old format: {scenario_id, title, scenario_config: {...}}
        # New format: {scenario_metadata, scenario_narrative, paradigms, ...}
        if 'scenario_config' in data:
            scenario = data['scenario_config']
            # Ensure scenario_id is set
            if 'scenario_id' not in scenario and 'scenario_metadata' in scenario:
                scenario['scenario_id'] = scenario['scenario_metadata'].get('scenario_id', scenario_id)
            elif 'scenario_id' not in scenario:
                scenario['scenario_id'] = scenario_id
            return scenario

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scenarios/list")
async def list_scenarios(limit: int = 50, offset: int = 0):
    """List all stored scenarios"""
    try:
        scenarios = storage.list_scenarios(limit=limit, offset=offset)
        return {
            "scenarios": scenarios,
            "count": len(scenarios),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing scenarios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Get status of analysis (processing, completed, failed)"""
    try:
        status = storage.get_analysis_status(analysis_id)

        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis not found: {analysis_id}"
            )

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class SynopsisRequest(BaseModel):
    """Request body for synopsis generation with report content"""
    report: str
    scenario_id: Optional[str] = None


@app.post("/api/generate-synopsis")
async def generate_synopsis_from_report(
    request: SynopsisRequest,
    user_openai_api_key: Optional[str] = Header(None, alias="User-OpenAI-API-Key"),
    user_vector_store_id: Optional[str] = Header(None, alias="User-Vector-Store-ID")
):
    """
    Generate a magazine-style synopsis from a provided BFIH report.

    Headers (optional - falls back to server env vars if not provided):
        User-OpenAI-API-Key: Your OpenAI API key

    This endpoint accepts the report content directly from the frontend,
    avoiding storage lookups. This is the preferred method.

    Returns:
    {
        "scenario_id": "s_001",
        "synopsis": "markdown synopsis content",
        "status": "completed"
    }
    """
    try:
        if not request.report:
            raise HTTPException(
                status_code=400,
                detail="No report content provided"
            )

        scenario_id = request.scenario_id or "synopsis"

        # Create orchestrator with user's credentials
        orchestrator = get_orchestrator_for_request(user_openai_api_key, user_vector_store_id)

        # Generate the synopsis
        logger.info(f"Generating magazine synopsis for scenario: {scenario_id}")
        synopsis = orchestrator.generate_magazine_synopsis(request.report, scenario_id)

        return {
            "scenario_id": scenario_id,
            "synopsis": synopsis,
            "status": "completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating synopsis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-synopsis/{analysis_id}")
async def generate_synopsis(
    analysis_id: str,
    user_openai_api_key: Optional[str] = Header(None, alias="User-OpenAI-API-Key"),
    user_vector_store_id: Optional[str] = Header(None, alias="User-Vector-Store-ID")
):
    """
    Generate a magazine-style synopsis from a completed BFIH analysis.

    DEPRECATED: Use POST /api/generate-synopsis with report content instead.

    Headers (optional - falls back to server env vars if not provided):
        User-OpenAI-API-Key: Your OpenAI API key

    This transforms the technical report into an engaging, Atlantic-style
    magazine article that is accessible to general readers.

    Returns:
    {
        "analysis_id": "uuid",
        "scenario_id": "s_001",
        "synopsis": "markdown synopsis content",
        "status": "completed"
    }
    """
    try:
        # Retrieve the completed analysis
        result = storage.retrieve_analysis_result(analysis_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis not found: {analysis_id}"
            )

        if result.get("status") != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Analysis not yet completed. Status: {result.get('status')}"
            )

        report = result.get("report")
        if not report:
            raise HTTPException(
                status_code=400,
                detail="No report found in analysis result"
            )

        scenario_id = result.get("scenario_id", analysis_id[:8])

        # Create orchestrator with user's credentials
        orchestrator = get_orchestrator_for_request(user_openai_api_key, user_vector_store_id)

        # Generate the synopsis
        logger.info(f"Generating magazine synopsis for analysis: {analysis_id}")
        synopsis = orchestrator.generate_magazine_synopsis(report, scenario_id)

        return {
            "analysis_id": analysis_id,
            "scenario_id": scenario_id,
            "synopsis": synopsis,
            "status": "completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating synopsis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKGROUND TASK
# ============================================================================

async def _run_analysis(
    analysis_id: str,
    analysis_request: BFIHAnalysisRequest,
    api_key: Optional[str] = None,
    vector_store_id: Optional[str] = None
):
    """Background task to run BFIH analysis with user-provided credentials."""
    try:
        logger.info(f"Starting background analysis: {analysis_id}")

        # Update status
        storage.update_analysis_status(analysis_id, "processing")

        # Create orchestrator with user's credentials (or fall back to env vars)
        orchestrator = get_orchestrator_for_request(api_key, vector_store_id)

        # Check if this is autonomous mode (empty or minimal scenario_config)
        scenario_config = analysis_request.scenario_config or {}
        is_autonomous = not scenario_config.get("hypotheses") and not scenario_config.get("paradigms")

        if is_autonomous:
            # Autonomous mode: generate everything from proposition
            logger.info(f"Running autonomous analysis for: {analysis_request.proposition}")
            result = orchestrator.analyze_topic(
                proposition=analysis_request.proposition,
                domain="general",
                reasoning_model=analysis_request.reasoning_model
            )
        else:
            # Standard mode: use provided scenario_config
            result = orchestrator.conduct_analysis(analysis_request)

        # Store result
        storage.store_analysis_result(analysis_id, result)

        # Update status
        storage.update_analysis_status(analysis_id, "completed")

        logger.info(f"Analysis completed: {analysis_id}")

    except Exception as e:
        logger.error(f"Error in background analysis task: {str(e)}")
        storage.update_analysis_status(analysis_id, f"failed: {str(e)}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Catch-all exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("BFIH API Server starting...")

    # Check if default credentials are configured
    has_default_api_key = bool(os.getenv("OPENAI_API_KEY"))
    has_default_vector_store = bool(os.getenv("TREATISE_VECTOR_STORE_ID"))

    if has_default_api_key:
        logger.info("Server mode: Default credentials configured (single-tenant or fallback)")
        default_orch = get_default_orchestrator()
        if default_orch:
            logger.info(f"Default model: {default_orch.model}")
            logger.info(f"Default vector store: {default_orch.vector_store_id}")
    else:
        logger.info("Server mode: Multi-tenant (users must provide their own API keys)")
        logger.info("Clients must include User-OpenAI-API-Key header in requests")

    if not has_default_vector_store:
        logger.info("Note: No default vector store configured. Users can provide via User-Vector-Store-ID header.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("BFIH API Server shutting down...")


# ============================================================================
# STATIC FILE SERVING (Frontend)
# ============================================================================

# Path to built frontend files
FRONTEND_DIR = Path(__file__).parent / "static"

# Mount static assets if they exist
assets_dir = FRONTEND_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")
    logger.info(f"Static assets mounted from {assets_dir}")


# Root handler - explicit to ensure / is captured
@app.get("/")
async def serve_root():
    """Serve the frontend index.html at root."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    # Fallback: return API info if no frontend
    return JSONResponse({
        "name": "BFIH API Server",
        "version": "1.0",
        "docs": "/docs",
        "status": "Frontend not found - API-only mode"
    })


# Catch-all route for SPA - must be AFTER all API routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the frontend SPA for any non-API routes."""
    index_path = FRONTEND_DIR / "index.html"

    # Check if requesting a specific file that exists
    file_path = FRONTEND_DIR / full_path
    if full_path and file_path.exists() and file_path.is_file():
        return FileResponse(file_path)

    # Serve index.html for SPA routing if it exists
    if index_path.exists():
        return FileResponse(index_path)

    # No frontend available
    raise HTTPException(status_code=404, detail="Not found")


# Log frontend status
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
    logger.info(f"Frontend mounted from {FRONTEND_DIR}")
else:
    logger.warning(f"Frontend not found at {FRONTEND_DIR} - API-only mode")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
