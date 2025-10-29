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

from docker_client import DockerClient
from container_manager import ContainerManager
from models import (
    StatusResponse,
    StartRequest,
    StartResponse,
    StopResponse,
    RestartResponse,
    LogsResponse,
    URLContentRequest,
)
from config_validator import (
    ConfigValidator,
    ConfigValidationResult,
    MatomoConnectionResult,
)
from auth import verify_api_key, is_auth_enabled

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Docker client and container manager
docker_client = DockerClient()
container_manager = ContainerManager(docker_client)


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
    config: Dict[str, Any] = Body(...),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
