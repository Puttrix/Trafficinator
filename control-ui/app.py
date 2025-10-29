"""
Trafficinator Control UI - FastAPI Application

Main application entry point for the web-based control interface.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from docker_client import DockerClient

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

# Initialize Docker client
docker_client = DockerClient()


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
    
    return {
        "status": "healthy",
        "service": "trafficinator-control-ui",
        "version": "1.0.0",
        "docker": docker_status,
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
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
