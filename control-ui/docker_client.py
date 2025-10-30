"""
Docker Client Wrapper

Provides interface for controlling the matomo-loadgen container.
"""
import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional, Dict, Any


class DockerClient:
    """Wrapper for Docker SDK to manage matomo-loadgen container"""
    
    CONTAINER_NAME = "matomo-loadgen"
    
    def __init__(self):
        """Initialize Docker client"""
        self.client: Optional[docker.DockerClient] = None
        self._connected = False
    
    def connect(self):
        """
        Connect to Docker daemon
        
        Raises:
            DockerException: If connection fails
        """
        try:
            # Connect via Unix socket
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self._connected = True
        except Exception as e:
            raise DockerException(f"Failed to connect to Docker daemon: {e}")
    
    def disconnect(self):
        """Disconnect from Docker daemon"""
        if self.client:
            self.client.close()
            self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to Docker daemon"""
        return self._connected and self.client is not None
    
    def get_container(self):
        """
        Get the matomo-loadgen container
        
        Returns:
            Container object or None if not found
        """
        if not self.is_connected():
            raise DockerException("Not connected to Docker daemon")
        
        try:
            return self.client.containers.get(self.CONTAINER_NAME)
        except NotFound:
            return None
        except APIError as e:
            raise DockerException(f"Error accessing container: {e}")
    
    def container_exists(self) -> bool:
        """Check if matomo-loadgen container exists"""
        return self.get_container() is not None
    
    def get_container_state(self) -> str:
        """
        Get current container state
        
        Returns:
            str: 'running', 'stopped', 'not_found', or 'error'
        """
        try:
            container = self.get_container()
            if not container:
                return "not_found"
            
            container.reload()
            status = container.status
            
            # Map Docker statuses to our states
            if status == "running":
                return "running"
            elif status in ["exited", "stopped", "dead"]:
                return "stopped"
            elif status in ["created", "restarting", "paused"]:
                return status
            else:
                return "unknown"
        except Exception as e:
            print(f"Error getting container state: {e}")
            return "error"
    
    def start_container(self) -> Dict[str, Any]:
        """
        Start the matomo-loadgen container
        
        Returns:
            dict: Result with success status and message
        """
        try:
            container = self.get_container()
            if not container:
                return {
                    "success": False,
                    "error": "Container not found. Please create it first with docker-compose.",
                }
            
            current_state = self.get_container_state()
            if current_state == "running":
                return {
                    "success": True,
                    "message": "Container is already running",
                    "state": "running",
                }
            
            container.start()
            return {
                "success": True,
                "message": "Container started successfully",
                "state": "running",
            }
        except APIError as e:
            return {
                "success": False,
                "error": f"Failed to start container: {e}",
            }
    
    def stop_container(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Stop the matomo-loadgen container gracefully
        
        Args:
            timeout: Seconds to wait before forcing stop
        
        Returns:
            dict: Result with success status and message
        """
        try:
            container = self.get_container()
            if not container:
                return {
                    "success": False,
                    "error": "Container not found",
                }
            
            current_state = self.get_container_state()
            if current_state == "stopped":
                return {
                    "success": True,
                    "message": "Container is already stopped",
                    "state": "stopped",
                }
            
            container.stop(timeout=timeout)
            return {
                "success": True,
                "message": "Container stopped successfully",
                "state": "stopped",
            }
        except APIError as e:
            return {
                "success": False,
                "error": f"Failed to stop container: {e}",
            }
    
    def restart_container(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Restart the matomo-loadgen container
        
        Args:
            timeout: Seconds to wait before forcing stop
        
        Returns:
            dict: Result with success status and message
        """
        try:
            container = self.get_container()
            if not container:
                return {
                    "success": False,
                    "error": "Container not found",
                }
            
            container.restart(timeout=timeout)
            return {
                "success": True,
                "message": "Container restarted successfully",
                "state": "running",
            }
        except APIError as e:
            return {
                "success": False,
                "error": f"Failed to restart container: {e}",
            }
    
    def get_container_logs(self, lines: int = 100, tail: bool = True) -> str:
        """
        Get container logs
        
        Args:
            lines: Number of lines to retrieve
            tail: If True, get last N lines. If False, get first N lines.
        
        Returns:
            str: Container logs
        """
        try:
            container = self.get_container()
            if not container:
                return "Container not found"
            
            logs = container.logs(
                tail=lines if tail else None,
                timestamps=True,
            )
            return logs.decode('utf-8')
        except APIError as e:
            return f"Error retrieving logs: {e}"
    
    def get_container_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed container information
        
        Returns:
            dict: Container info including config, state, stats
        """
        try:
            container = self.get_container()
            if not container:
                return None
            
            container.reload()
            attrs = container.attrs
            
            # Extract relevant information
            return {
                "name": attrs.get("Name", "").lstrip("/"),
                "id": attrs.get("Id", "")[:12],
                "status": attrs.get("State", {}).get("Status"),
                "created": attrs.get("Created"),
                "started_at": attrs.get("State", {}).get("StartedAt"),
                "finished_at": attrs.get("State", {}).get("FinishedAt"),
                "config": {
                    "env": attrs.get("Config", {}).get("Env", []),
                    "image": attrs.get("Config", {}).get("Image"),
                },
            }
        except APIError as e:
            print(f"Error getting container info: {e}")
            return None
