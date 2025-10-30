"""
Trafficinator Control UI - FastAPI Application

Main application entry point for the web-based control interface.
"""
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
    URLContentRequest,
    PresetListResponse,
    PresetDetail,
    PresetCreateRequest,
    PresetUpdateRequest,
    PresetDeleteResponse,
)
from config_validator import (
    ConfigValidator,
    ConfigValidationResult,
    MatomoConnectionResult,
)
from auth import verify_api_key, is_auth_enabled
from db import Database

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Docker client and container manager
docker_client = DockerClient()
container_manager = ContainerManager(docker_client)
config_database = Database(os.getenv("CONFIG_DB_PATH", "/app/data/presets.db"))


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
