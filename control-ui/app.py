"""
Trafficinator Control UI - FastAPI Application

Main application entry point for the web-based control interface.
"""
import json
import logging
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Body, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlite3 import IntegrityError

from docker_client import DockerClient
from container_manager import ContainerManager
from models import (
    StatusResponse,
    StartRequest,
    StartResponse,
    StopResponse,
    RestartResponse,
    LogsResponse,
    ApplyConfigResponse,
    BackfillRunRequest,
    BackfillRunResponse,
    BackfillStatusResponse,
    BackfillCleanupResponse,
    BackfillLastResponse,
    BackfillCancelResponse,
    URLContentRequest,
    PresetListResponse,
    PresetDetail,
    PresetCreateRequest,
    PresetUpdateRequest,
    PresetDeleteResponse,
    FunnelListResponse,
    FunnelResponse,
    FunnelCreateRequest,
    FunnelUpdateRequest,
    FunnelDeleteResponse,
    FunnelConfig,
)
from config_validator import (
    ConfigValidator,
    ConfigValidationResult,
    MatomoConnectionResult,
)
from auth import verify_api_key, is_auth_enabled
from db import Database

logger = logging.getLogger("trafficinator.control_ui")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Docker client and container manager
docker_client = DockerClient()
container_manager = ContainerManager(docker_client)
config_database = Database(os.getenv("CONFIG_DB_PATH"))
FUNNEL_CONFIG_PATH = Path(os.getenv("FUNNEL_CONFIG_PATH", "/app/data/funnels.json"))
BACKFILL_HISTORY_PATH = Path(os.getenv("BACKFILL_HISTORY_PATH", "/app/data/backfill_history.json"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Trafficinator Control UI")
    try:
        docker_client.connect()
        print("✅ Connected to Docker daemon")
    except Exception as e:
        print(f"⚠️  Warning: Could not connect to Docker: {e}")
    
    # Log authentication status
    if is_auth_enabled():
        print("🔒 API authentication: ENABLED")
    else:
        print("⚠️  API authentication: DISABLED (set CONTROL_UI_API_KEY to enable)")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Trafficinator Control UI")
    docker_client.disconnect()


# Initialize FastAPI app
app = FastAPI(
    title="Trafficinator Control UI",
    description="Web-based control interface for Trafficinator load generator",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    # Allow all origins
    allow_origins = ["*"]
else:
    # Parse comma-separated list
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Mount static files for web UI
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    print(f"📁 Static files mounted from: {STATIC_DIR}")
else:
    print(f"⚠️  Warning: Static directory not found: {STATIC_DIR}")


@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Health check endpoint
    
    Returns:
        dict: Service health status
    """
    docker_status = "connected" if docker_client.is_connected() else "disconnected"
    container_exists = docker_client.container_exists() if docker_client.is_connected() else False
    
    return {
        "status": "healthy",
        "service": "trafficinator-control-ui",
        "version": "1.0.0",
        "docker": docker_status,
        "container_found": container_exists,
        "auth_enabled": is_auth_enabled(),
    }


@app.get("/")
async def root():
    """
    Serve the web UI or API information based on Accept header
    
    Returns:
        FileResponse: Web UI HTML page for browsers
        dict: API information for API clients
    """
    return {
        "name": "Trafficinator Control UI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/ui")
async def serve_ui():
    """
    Serve the web UI
    
    Returns:
        FileResponse: Web UI HTML page
    """
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Web UI not found")
    return FileResponse(index_path)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/status", response_model=StatusResponse)
@limiter.limit("60/minute")
async def get_status(request: Request, authenticated: bool = Depends(verify_api_key)):
    """
    Get container status, configuration, and runtime statistics
    
    Returns:
        StatusResponse: Container state, config, and stats
    
    Raises:
        HTTPException: If Docker is not connected
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        status = container_manager.get_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting status: {str(e)}"
        )


@app.post("/api/backfill/run", response_model=BackfillRunResponse)
@limiter.limit("10/minute")
async def run_backfill(
    request: Request,
    backfill_request: BackfillRunRequest,
    authenticated: bool = Depends(verify_api_key),
):
    """
    Launch a one-off backfill run in an ephemeral container without mutating the main loadgen config.
    """
    if not docker_client.is_connected():
        raise HTTPException(status_code=503, detail="Docker daemon not connected")

    current_env = container_manager.get_current_env()
    if current_env is None:
        return BackfillRunResponse(success=False, message="Primary container not found", error="container_not_found")

    env = current_env.copy()
    env.update({
        "BACKFILL_ENABLED": "true",
        "BACKFILL_RUN_ONCE": "true" if backfill_request.BACKFILL_RUN_ONCE else "false",
        "AUTO_START": "true",
    })

    for field in [
        "BACKFILL_START_DATE",
        "BACKFILL_END_DATE",
        "BACKFILL_DAYS_BACK",
        "BACKFILL_DURATION_DAYS",
        "BACKFILL_MAX_VISITS_PER_DAY",
        "BACKFILL_MAX_VISITS_TOTAL",
        "BACKFILL_RPS_LIMIT",
        "BACKFILL_SEED",
    ]:
        value = getattr(backfill_request, field)
        if value is not None:
            env[field] = str(value)

    validator = ConfigValidator()
    try:
        validator.validate_config(env)
    except Exception as e:
        return BackfillRunResponse(success=False, message="Validation failed", error=str(e))

    result = container_manager.spawn_backfill_job(env_vars=env, name=backfill_request.name)
    if result.get("success"):
        # Persist last run payload/result for UI reference
        try:
            BACKFILL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            history = {
                "payload": env,
                "result": result,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            BACKFILL_HISTORY_PATH.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write backfill history: {e}")
        return BackfillRunResponse(
            success=True,
            message="Backfill job started",
            container_name=result.get("container_name"),
            container_id=result.get("container_id"),
        )
    return BackfillRunResponse(
        success=False,
        message="Failed to start backfill job",
        error=result.get("error"),
    )


@app.get("/api/backfill/status", response_model=BackfillStatusResponse)
@limiter.limit("30/minute")
async def backfill_status(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Return list of backfill runs (ephemeral containers)."""
    if not docker_client.is_connected():
        raise HTTPException(status_code=503, detail="Docker daemon not connected")

    runs = container_manager.list_backfill_runs()
    formatted = []
    for r in runs:
        formatted.append({
            "container_name": r.get("name"),
            "container_id": r.get("id"),
            "state": r.get("status"),
            "started_at": r.get("started_at"),
            "finished_at": r.get("finished_at"),
            "exit_code": r.get("exit_code"),
            "error": None,
        })

    return BackfillStatusResponse(success=True, message="ok", runs=formatted)


@app.post("/api/backfill/cleanup", response_model=BackfillCleanupResponse)
@limiter.limit("10/minute")
async def backfill_cleanup(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Remove exited backfill containers."""
    if not docker_client.is_connected():
        raise HTTPException(status_code=503, detail="Docker daemon not connected")

    result = container_manager.cleanup_backfill_runs()
    success = len(result.get("errors", [])) == 0
    message = "Cleanup complete" if success else "Cleanup completed with errors"
    return BackfillCleanupResponse(
        success=success,
        message=message,
        removed=result.get("removed", []),
        errors=result.get("errors", []),
    )


@app.get("/api/backfill/last", response_model=BackfillLastResponse)
@limiter.limit("30/minute")
async def backfill_last(request: Request, authenticated: bool = Depends(verify_api_key)):
    """Return last backfill payload/result if available."""
    if not BACKFILL_HISTORY_PATH.exists():
        return BackfillLastResponse(success=True, message="No backfill history", payload=None, result=None, timestamp=None)
    try:
        data = json.loads(BACKFILL_HISTORY_PATH.read_text(encoding="utf-8"))
        return BackfillLastResponse(
            success=True,
            message="ok",
            payload=data.get("payload"),
            result=data.get("result"),
            timestamp=data.get("timestamp"),
        )
    except Exception as e:
        return BackfillLastResponse(success=False, message="Failed to read backfill history", payload=None, result=None, timestamp=None)


@app.post("/api/backfill/cancel", response_model=BackfillCancelResponse)
@limiter.limit("10/minute")
async def backfill_cancel(container_name: str = Body(..., embed=True), authenticated: bool = Depends(verify_api_key)):
    """Stop a running backfill container."""
    if not docker_client.is_connected():
        raise HTTPException(status_code=503, detail="Docker daemon not connected")

    result = container_manager.cancel_backfill(container_name)
    if result.get("success"):
        return BackfillCancelResponse(success=True, message="Backfill container stopped")
    return BackfillCancelResponse(success=False, message="Failed to stop backfill container", error=result.get("error"))


@app.post("/api/start", response_model=StartResponse)
@limiter.limit("10/minute")
async def start_container(
    request: Request,
    start_request: Optional[StartRequest] = None,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Start the load generator container
    
    Args:
        start_request: Optional start request with config
    
    Returns:
        StartResponse: Start operation result
    
    Raises:
        HTTPException: If Docker is not connected or start fails
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        # Get current state
        current_state = docker_client.get_container_state()
        
        # Handle restart_if_running
        if start_request and start_request.restart_if_running and current_state == "running":
            result = container_manager.restart_container()
            return StartResponse(**result)
        
        # Pass config if provided (note: not yet implemented fully)
        config = start_request.config if start_request else None
        result = container_manager.start_container(config=config)
        
        return StartResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting container: {str(e)}"
        )


@app.post("/api/stop", response_model=StopResponse)
@limiter.limit("10/minute")
async def stop_container(
    request: Request,
    timeout: int = Query(10, ge=1, le=60, description="Timeout in seconds"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Stop the load generator container gracefully
    
    Args:
        timeout: Seconds to wait before forcing stop (1-60)
    
    Returns:
        StopResponse: Stop operation result
    
    Raises:
        HTTPException: If Docker is not connected or stop fails
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        result = container_manager.stop_container(timeout=timeout)
        return StopResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping container: {str(e)}"
        )


@app.post("/api/restart", response_model=RestartResponse)
@limiter.limit("10/minute")
async def restart_container(
    request: Request,
    timeout: int = Query(10, ge=1, le=60, description="Timeout in seconds"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Restart the load generator container
    
    Args:
        timeout: Seconds to wait before forcing stop (1-60)
    
    Returns:
        RestartResponse: Restart operation result
    
    Raises:
        HTTPException: If Docker is not connected or restart fails
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        result = container_manager.restart_container(timeout=timeout)
        return RestartResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error restarting container: {str(e)}"
        )


@app.get("/api/logs", response_model=LogsResponse)
@limiter.limit("30/minute")
async def get_logs(
    request: Request,
    lines: int = Query(100, ge=10, le=10000, description="Number of log lines to retrieve"),
    filter: Optional[str] = Query(None, description="Filter logs by text (case-insensitive)"),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get container logs
    
    Args:
        lines: Number of log lines to retrieve (10-10000)
        filter: Optional text to filter logs by (case-insensitive)
    
    Returns:
        LogsResponse: Container logs and metadata
    
    Raises:
        HTTPException: If Docker is not connected or log retrieval fails
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        result = container_manager.get_logs(lines=lines, filter_text=filter)
        return LogsResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving logs: {str(e)}"
        )


@app.post("/api/validate", response_model=ConfigValidationResult)
@limiter.limit("30/minute")
async def validate_config(
    request: Request,
    config: Dict[str, Any] = Body(..., embed=True),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Validate load generator configuration
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        ConfigValidationResult: Validation result with errors and warnings
    """
    try:
        result = ConfigValidator.validate_config(config)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating configuration: {str(e)}"
        )


@app.post("/api/test-connection", response_model=MatomoConnectionResult)
@limiter.limit("20/minute")
async def test_connection(
    request: Request,
    matomo_url: str = Body(..., embed=True),
    timeout: float = Body(10.0, ge=1, le=60, embed=True),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Test connectivity to Matomo server
    
    Args:
        matomo_url: Matomo tracking endpoint URL
        timeout: Request timeout in seconds (1-60)
    
    Returns:
        MatomoConnectionResult: Connection test result
    """
    try:
        result = await ConfigValidator.test_matomo_connection(matomo_url, timeout)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing connection: {str(e)}"
        )


@app.post("/api/config/apply", response_model=ApplyConfigResponse)
@limiter.limit("10/minute")
async def apply_config(
    request: Request,
    config: Dict[str, Any] = Body(..., embed=True),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Apply new configuration to the load generator container
    
    This validates the configuration, updates the container's environment variables,
    and restarts the container to apply the changes.
    
    Args:
        config: Configuration dictionary to apply
    
    Returns:
        ApplyConfigResponse: Result of applying the configuration
    
    Raises:
        HTTPException: If validation fails or Docker operation fails
    """
    if not docker_client.is_connected():
        raise HTTPException(
            status_code=503,
            detail="Docker daemon not connected"
        )
    
    try:
        # First validate the configuration
        validation_result = ConfigValidator.validate_config(config)
        
        if not validation_result.valid:
            error_messages = [f"{err.field}: {err.message}" for err in validation_result.errors]
            raise HTTPException(
                status_code=400,
                detail=f"Configuration validation failed: {'; '.join(error_messages)}"
            )
        
        # Convert config dict to environment variables
        env_vars = container_manager.config_to_env_vars(config)
        
        # Update container with new environment variables
        result = container_manager.update_and_restart(env_vars)
        
        return ApplyConfigResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error applying configuration: {str(e)}"
        )


# ============================================================================
# Configuration Presets
# ============================================================================

@app.get("/api/presets", response_model=PresetListResponse)
@limiter.limit("30/minute")
async def list_presets(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    List saved configuration presets (metadata only)
    """
    try:
        presets = config_database.list_presets()
        return PresetListResponse(presets=presets)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing presets: {str(e)}"
        )


@app.post("/api/presets", response_model=PresetDetail, status_code=201)
@limiter.limit("10/minute")
async def create_preset(
    request: Request,
    preset: PresetCreateRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Create a new configuration preset
    """
    try:
        created = config_database.create_preset(
            name=preset.name,
            config=preset.config,
            description=preset.description,
        )
        return PresetDetail(**created)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Preset name already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating preset: {str(e)}"
        )


@app.get("/api/presets/{preset_id}", response_model=PresetDetail)
@limiter.limit("30/minute")
async def get_preset(
    request: Request,
    preset_id: int,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Retrieve a configuration preset by ID
    """
    try:
        preset = config_database.get_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset not found")
        return PresetDetail(**preset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving preset: {str(e)}"
        )


@app.put("/api/presets/{preset_id}", response_model=PresetDetail)
@limiter.limit("10/minute")
async def update_preset(
    request: Request,
    preset_id: int,
    preset: PresetUpdateRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Update an existing configuration preset
    """
    try:
        updated = config_database.update_preset(
            preset_id,
            name=preset.name,
            config=preset.config,
            description=preset.description,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Preset not found")
        return PresetDetail(**updated)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Preset name already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating preset: {str(e)}"
        )


@app.delete("/api/presets/{preset_id}", response_model=PresetDeleteResponse)
@limiter.limit("10/minute")
async def delete_preset(
    request: Request,
    preset_id: int,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Delete a configuration preset
    """
    try:
        deleted = config_database.delete_preset(preset_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Preset not found")
        return PresetDeleteResponse(
            success=True,
            deleted_id=preset_id,
            message="Preset deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting preset: {str(e)}"
        )


# ============================================================================
# Funnel Management
# ============================================================================


def serialize_funnel_record(record: Dict[str, Any]) -> FunnelResponse:
    """Convert database funnel record into FunnelResponse."""
    config = FunnelConfig(**record["config"])
    return FunnelResponse(
        id=record["id"],
        name=record["name"],
        description=record.get("description"),
        config=config,
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def export_enabled_funnels() -> Dict[str, Any]:
    """
    Serialize enabled funnels to the shared JSON file for the loader.

    Returns:
        Dict containing the export path and funnel count.

    Raises:
        RuntimeError: If writing the export file fails.
    """
    try:
        funnels = config_database.get_funnels_for_export(only_enabled=True)
        FUNNEL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with FUNNEL_CONFIG_PATH.open("w", encoding="utf-8") as handle:
            json.dump(funnels, handle, indent=2)
        logger.info(
            "Exported %d funnel(s) to %s",
            len(funnels),
            FUNNEL_CONFIG_PATH,
        )
        return {"path": str(FUNNEL_CONFIG_PATH), "count": len(funnels)}
    except Exception as exc:
        raise RuntimeError(f"Failed to export funnels: {exc}") from exc


@app.get("/api/funnels", response_model=FunnelListResponse)
@limiter.limit("30/minute")
async def list_funnels(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    List funnel definitions (metadata only).
    """
    try:
        funnels = config_database.list_funnels()
        return FunnelListResponse(funnels=funnels)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing funnels: {str(e)}"
        )


@app.post("/api/funnels", response_model=FunnelResponse, status_code=201)
@limiter.limit("10/minute")
async def create_funnel(
    request: Request,
    funnel: FunnelCreateRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Create a new funnel definition.
    """
    try:
        config = FunnelConfig(
            probability=funnel.probability,
            priority=funnel.priority,
            enabled=funnel.enabled,
            exit_after_completion=funnel.exit_after_completion,
            steps=funnel.steps,
        )

        created = config_database.create_funnel(
            name=funnel.name,
            description=funnel.description,
            config=config.model_dump(),
            probability=config.probability,
            priority=config.priority,
            enabled=config.enabled,
        )
        export_enabled_funnels()
        return serialize_funnel_record(created)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Funnel name already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating funnel: {str(e)}"
        )


@app.get("/api/funnels/{funnel_id}", response_model=FunnelResponse)
@limiter.limit("30/minute")
async def get_funnel(
    request: Request,
    funnel_id: int,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Retrieve a funnel definition.
    """
    try:
        funnel = config_database.get_funnel(funnel_id)
        if not funnel:
            raise HTTPException(status_code=404, detail="Funnel not found")
        return serialize_funnel_record(funnel)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving funnel: {str(e)}"
        )


@app.put("/api/funnels/{funnel_id}", response_model=FunnelResponse)
@limiter.limit("10/minute")
async def update_funnel(
    request: Request,
    funnel_id: int,
    funnel: FunnelUpdateRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Update an existing funnel definition.
    """
    try:
        existing = config_database.get_funnel(funnel_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Funnel not found")

        existing_config = FunnelConfig(**existing["config"])
        config_dict = existing_config.model_dump()

        if funnel.steps is not None:
            config_dict["steps"] = [step.model_dump() for step in funnel.steps]
        if funnel.exit_after_completion is not None:
            config_dict["exit_after_completion"] = funnel.exit_after_completion
        if funnel.priority is not None:
            config_dict["priority"] = funnel.priority
        if funnel.probability is not None:
            config_dict["probability"] = funnel.probability
        if funnel.enabled is not None:
            config_dict["enabled"] = funnel.enabled

        config_payload = None
        if (
            funnel.steps is not None
            or funnel.exit_after_completion is not None
            or funnel.priority is not None
            or funnel.probability is not None
            or funnel.enabled is not None
        ):
            config_payload = FunnelConfig(**config_dict)

        updated = config_database.update_funnel(
            funnel_id=funnel_id,
            name=funnel.name,
            description=funnel.description,
            config=config_payload.model_dump() if config_payload else None,
            probability=funnel.probability,
            priority=funnel.priority,
            enabled=funnel.enabled,
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Funnel not found")

        export_enabled_funnels()
        return serialize_funnel_record(updated)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Funnel name already exists"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating funnel: {str(e)}"
        )


@app.delete("/api/funnels/{funnel_id}", response_model=FunnelDeleteResponse)
@limiter.limit("10/minute")
async def delete_funnel(
    request: Request,
    funnel_id: int,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Delete a funnel definition.
    """
    try:
        deleted = config_database.delete_funnel(funnel_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Funnel not found")
        export_enabled_funnels()
        return FunnelDeleteResponse(
            success=True,
            deleted_id=funnel_id,
            message="Funnel deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting funnel: {str(e)}"
        )
# =============================================================================
# URL Management Endpoints
# =============================================================================

@app.get("/api/urls")
@limiter.limit("20/minute")
async def get_urls(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get current URL list from the load generator container
    
    Returns:
        Dict with urls content and metadata
    """
    try:
        from url_validator import validate_urls, parse_url_structure
        
        # Try to read URLs from mounted volume or container
        urls_path = Path("/app/data/urls.txt")
        default_urls_path = Path("/config/urls.txt")
        
        # Check if custom URLs exist
        if urls_path.exists():
            content = urls_path.read_text()
            source = "custom"
        elif default_urls_path.exists():
            content = default_urls_path.read_text()
            source = "default"
        else:
            # Fallback: try to read from matomo-loadgen container
            if docker_client.is_connected():
                container = docker_client.get_container()
                if container:
                    try:
                        exit_code, output = container.exec_run(
                            "cat /config/urls.txt",
                            demux=False
                        )
                        if exit_code == 0:
                            content = output.decode('utf-8')
                            source = "container"
                        else:
                            raise HTTPException(status_code=404, detail="URLs file not found")
                    except Exception as e:
                        raise HTTPException(status_code=500, detail=f"Error reading URLs from container: {str(e)}")
                else:
                    raise HTTPException(status_code=404, detail="Container not found")
            else:
                raise HTTPException(status_code=503, detail="Docker not connected")
        
        # Validate and parse
        validation = validate_urls(content)
        structure = parse_url_structure(validation['urls']) if validation['valid'] else {}
        
        return {
            "content": content,
            "source": source,
            "validation": validation,
            "structure": structure,
            "line_count": len(content.split('\n')),
            "editable": True  # URLs can always be uploaded/edited
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving URLs: {str(e)}"
        )


@app.post("/api/urls")
@limiter.limit("10/minute")
async def upload_urls(
    request: Request,
    body: URLContentRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Upload custom URL list
    
    Note: Requires container restart to take effect
    
    Args:
        body: URLContentRequest with content field
    
    Returns:
        Dict with validation results and save status
    """
    try:
        from url_validator import validate_urls, parse_url_structure
        
        # Validate URLs
        validation = validate_urls(body.content)
        
        if not validation['valid']:
            return {
                "success": False,
                "message": "URL validation failed",
                "validation": validation
            }
        
        # Save to persistent location
        urls_path = Path("/app/data/urls.txt")
        urls_path.parent.mkdir(parents=True, exist_ok=True)
        urls_path.write_text(body.content)
        
        structure = parse_url_structure(validation['urls'])
        
        return {
            "success": True,
            "message": f"Successfully uploaded {validation['url_count']} URLs. Restart container to apply changes.",
            "validation": validation,
            "structure": structure,
            "restart_required": True
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading URLs: {str(e)}"
        )


@app.post("/api/urls/validate")
@limiter.limit("20/minute")
async def validate_urls_endpoint(
    request: Request,
    body: URLContentRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Validate URL list without saving
    
    Args:
        body: URLContentRequest with content field
    
    Returns:
        Dict with validation results and URL structure
    """
    try:
        from url_validator import validate_urls, parse_url_structure
        
        # Validate URLs
        validation = validate_urls(body.content)
        
        # Get structure if valid
        structure = None
        if validation['valid']:
            structure = parse_url_structure(validation['urls'])
        
        return {
            "valid": validation['valid'],
            "url_count": validation['url_count'],
            "errors": validation['errors'],
            "warnings": validation['warnings'],
            "structure": structure
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating URLs: {str(e)}"
        )


@app.delete("/api/urls")
@limiter.limit("10/minute")
async def reset_urls(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Reset URLs to default (embedded in image)
    
    Note: Requires container restart to take effect
    
    Returns:
        Dict with reset status
    """
    try:
        # Remove custom URLs file
        urls_path = Path("/app/data/urls.txt")
        if urls_path.exists():
            urls_path.unlink()
            return {
                "success": True,
                "message": "URLs reset to defaults. Restart container to apply changes.",
                "restart_required": True
            }
        else:
            return {
                "success": True,
                "message": "Already using default URLs",
                "restart_required": False
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting URLs: {str(e)}"
        )


@app.get("/api/events")
@limiter.limit("20/minute")
async def get_events(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get current event configuration
    
    Checks three locations in priority order:
    1. /app/data/events.json - Custom events (uploaded via UI)
    2. loader.py - Embedded default events
    
    Returns:
        Dict with event configuration, source, and statistics
    """
    try:
        from event_validator import validate_events_config, parse_events_from_loader
        import json
        
        # Check for custom events file
        events_path = Path("/app/data/events.json")
        source = "default"
        config = None
        
        if events_path.exists():
            # Load custom events
            try:
                config = json.loads(events_path.read_text())
                source = "custom"
            except json.JSONDecodeError:
                # Fall back to default if custom file is invalid
                pass
        
        # If no custom events, use default hardcoded events
        if config is None:
            # Use default event configuration from loader.py
            config = {
                'click_events_probability': 0.25,
                'random_events_probability': 0.12,
                'click_events': [
                    {'category': 'Navigation', 'action': 'Menu Click', 'name': 'Main Menu', 'value': None},
                    {'category': 'Navigation', 'action': 'Button Click', 'name': 'Get Started', 'value': None},
                    {'category': 'Navigation', 'action': 'Link Click', 'name': 'Learn More', 'value': None},
                    {'category': 'UI', 'action': 'Tab Click', 'name': 'Product Features', 'value': None},
                    {'category': 'UI', 'action': 'Accordion Click', 'name': 'FAQ Section', 'value': None},
                    {'category': 'UI', 'action': 'Modal Open', 'name': 'Contact Form', 'value': None},
                    {'category': 'UI', 'action': 'Image Click', 'name': 'Product Gallery', 'value': None},
                    {'category': 'Social', 'action': 'Share Click', 'name': 'Twitter Share', 'value': None},
                    {'category': 'Social', 'action': 'Share Click', 'name': 'Facebook Share', 'value': None},
                    {'category': 'Social', 'action': 'Like Click', 'name': 'Article Like', 'value': None},
                    {'category': 'Form', 'action': 'Submit', 'name': 'Newsletter Signup', 'value': None},
                    {'category': 'Form', 'action': 'Focus', 'name': 'Search Input', 'value': None},
                    {'category': 'Video', 'action': 'Play', 'name': 'Tutorial Video', 'value': None},
                    {'category': 'Video', 'action': 'Pause', 'name': 'Product Demo', 'value': None},
                    {'category': 'CTA', 'action': 'Click', 'name': 'Free Trial', 'value': None},
                    {'category': 'CTA', 'action': 'Click', 'name': 'Request Quote', 'value': None},
                ],
                'random_events': [
                    {'category': 'Engagement', 'action': 'Scroll', 'name': 'Page Bottom', 'value': 100},
                    {'category': 'Engagement', 'action': 'Time on Page', 'name': 'Long Read', 'value': 300},
                    {'category': 'Performance', 'action': 'Load Time', 'name': 'Page Load', 'value': 1200},
                    {'category': 'Error', 'action': '404 Error', 'name': 'Broken Link', 'value': None},
                    {'category': 'Error', 'action': 'Form Error', 'name': 'Validation Failed', 'value': None},
                    {'category': 'Feature', 'action': 'Tool Usage', 'name': 'Calculator', 'value': 1},
                    {'category': 'Feature', 'action': 'Filter Applied', 'name': 'Product Filter', 'value': None},
                    {'category': 'Feature', 'action': 'Sort Applied', 'name': 'Price Sort', 'value': None},
                    {'category': 'Content', 'action': 'Print', 'name': 'Article Print', 'value': None},
                    {'category': 'Content', 'action': 'Bookmark', 'name': 'Page Bookmark', 'value': None},
                    {'category': 'Mobile', 'action': 'Swipe', 'name': 'Image Gallery', 'value': None},
                    {'category': 'Mobile', 'action': 'Tap', 'name': 'Phone Number', 'value': None},
                    {'category': 'Analytics', 'action': 'Conversion', 'name': 'Goal Complete', 'value': 50},
                    {'category': 'Analytics', 'action': 'Exit Intent', 'name': 'Modal Trigger', 'value': None},
                    {'category': 'User', 'action': 'Login', 'name': 'User Login', 'value': None},
                    {'category': 'User', 'action': 'Logout', 'name': 'User Logout', 'value': None},
                ]
            }
            source = "default"
        
        # Validate configuration
        validation = validate_events_config(config)
        
        return {
            "config": config,
            "source": source,
            "validation": validation
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving events: {str(e)}"
        )


@app.post("/api/events")
@limiter.limit("10/minute")
async def upload_events(
    request: Request,
    body: URLContentRequest,  # Reuse same model since it's just content
    authenticated: bool = Depends(verify_api_key)
):
    """
    Upload custom event configuration
    
    Note: Requires container restart to take effect
    
    Args:
        body: URLContentRequest with JSON content
    
    Returns:
        Dict with validation results and save status
    """
    try:
        from event_validator import validate_events_config
        import json
        
        # Parse JSON
        try:
            config = json.loads(body.content)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON: {str(e)}"
            )
        
        # Validate events
        validation = validate_events_config(config)
        
        if not validation['valid']:
            return {
                "success": False,
                "message": f"Validation failed: {len(validation['errors'])} errors found",
                "validation": validation,
                "restart_required": False
            }
        
        # Save to persistent location
        events_path = Path("/app/data/events.json")
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(json.dumps(config, indent=2))
        
        return {
            "success": True,
            "message": f"Successfully uploaded {validation['stats']['click_events_count']} click events and {validation['stats']['random_events_count']} random events. Restart container to apply changes.",
            "validation": validation,
            "restart_required": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading events: {str(e)}"
        )


@app.post("/api/events/validate")
@limiter.limit("20/minute")
async def validate_events_endpoint(
    request: Request,
    body: URLContentRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Validate event configuration without saving
    
    Args:
        body: URLContentRequest with JSON content
    
    Returns:
        Validation results
    """
    try:
        from event_validator import validate_events_config
        import json
        
        # Parse JSON
        try:
            config = json.loads(body.content)
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f"Invalid JSON: {str(e)}"],
                "warnings": [],
                "stats": {}
            }
        
        # Validate events
        validation = validate_events_config(config)
        
        return validation
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating events: {str(e)}"
        )


@app.delete("/api/events")
@limiter.limit("10/minute")
async def reset_events(
    request: Request,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Reset events to default (embedded in loader.py)
    
    Note: Requires container restart to take effect
    
    Returns:
        Dict with reset status
    """
    try:
        # Remove custom events file
        events_path = Path("/app/data/events.json")
        if events_path.exists():
            events_path.unlink()
            return {
                "success": True,
                "message": "Events reset to defaults. Restart container to apply changes.",
                "restart_required": True
            }
        else:
            return {
                "success": True,
                "message": "Already using default events",
                "restart_required": False
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting events: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
