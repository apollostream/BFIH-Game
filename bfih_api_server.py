"""
BFIH Backend: FastAPI Web Service
REST API for AI-Assisted Hypothesis Tournament Game

Endpoints:
- POST /api/bfih-analysis - Submit BFIH analysis request
- GET /api/bfih-analysis/{analysis_id} - Retrieve completed analysis
- GET /api/health - Health check
- POST /api/scenario - Store scenario config
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from bfih_orchestrator_fixed import (
    BFIHOrchestrator,
    BFIHAnalysisRequest,
    BFIHAnalysisResult
)
from bfih_storage import StorageManager


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
orchestrator = BFIHOrchestrator()
storage = StorageManager()


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
        "service": "BFIH Analysis API"
    }


@app.post("/api/bfih-analysis")
async def submit_analysis(request: Dict, background_tasks: BackgroundTasks):
    """
    Submit a BFIH analysis request
    
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
            user_id=request.get("user_id")
        )
        
        # Generate analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Store request metadata
        storage.store_analysis_request(
            analysis_id=analysis_id,
            request=analysis_request
        )
        
        # Run analysis in background
        background_tasks.add_task(
            _run_analysis,
            analysis_id=analysis_id,
            analysis_request=analysis_request
        )
        
        logger.info(f"Submitted analysis request: {analysis_id}")
        
        return {
            "analysis_id": analysis_id,
            "status": "processing",
            "estimated_seconds": 45,
            "scenario_id": request["scenario_id"]
        }
        
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
        scenario = storage.retrieve_scenario_config(scenario_id)
        
        if not scenario:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario not found: {scenario_id}"
            )
        
        return scenario
        
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


# ============================================================================
# BACKGROUND TASK
# ============================================================================

async def _run_analysis(analysis_id: str, analysis_request: BFIHAnalysisRequest):
    """Background task to run BFIH analysis"""
    try:
        logger.info(f"Starting background analysis: {analysis_id}")

        # Update status
        storage.update_analysis_status(analysis_id, "processing")

        # Check if this is autonomous mode (empty or minimal scenario_config)
        scenario_config = analysis_request.scenario_config or {}
        is_autonomous = not scenario_config.get("hypotheses") and not scenario_config.get("paradigms")

        if is_autonomous:
            # Autonomous mode: generate everything from proposition
            logger.info(f"Running autonomous analysis for: {analysis_request.proposition}")
            result = orchestrator.analyze_topic(
                proposition=analysis_request.proposition,
                domain="general"
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
    logger.info(f"Using model: {orchestrator.model}")
    logger.info(f"Vector store ID: {orchestrator.vector_store_id}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("BFIH API Server shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
