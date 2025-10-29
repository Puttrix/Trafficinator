"""
Trafficinator Control UI - FastAPI Application

Main application entry point for the web-based control interface.
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional

from docker_client import DockerClient
from container_manager import ContainerManager
from models import (
    StatusResponse,
    StartRequest,
    StartResponse,
    StopResponse,
    RestartResponse,
    LogsResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="Trafficinator Control UI",
    description="Web-based control interface for Trafficinator load generator",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
    yield
    
    # Shutdown
    print("👋 Shutting down Trafficinator Control UI")
    docker_client.disconnect()


app.router.lifespan_context = lifespan


@app.get("/health")
async def health_check():
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
    }


@app.get("/")
async def root():
    """
    Root endpoint - API information
    
    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "Trafficinator Control UI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "status": "GET /api/status",
            "start": "POST /api/start",
            "stop": "POST /api/stop",
            "restart": "POST /api/restart",
            "logs": "GET /api/logs",
        },
    }


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
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
async def start_container(request: StartRequest = None):
    """
    Start the load generator container
    
    Args:
        request: Optional start request with config
    
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
        if request and request.restart_if_running and current_state == "running":
            result = container_manager.restart_container()
            return StartResponse(**result)
        
        # Pass config if provided (note: not yet implemented fully)
        config = request.config if request else None
        result = container_manager.start_container(config=config)
        
        return StartResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error starting container: {str(e)}"
        )


@app.post("/api/stop", response_model=StopResponse)
async def stop_container(timeout: int = Query(10, ge=1, le=60, description="Timeout in seconds")):
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
async def restart_container(timeout: int = Query(10, ge=1, le=60, description="Timeout in seconds")):
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
async def get_logs(
    lines: int = Query(100, ge=10, le=10000, description="Number of log lines to retrieve"),
    filter: Optional[str] = Query(None, description="Filter logs by text (case-insensitive)")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
