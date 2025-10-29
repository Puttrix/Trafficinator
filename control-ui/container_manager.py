"""
Container management operations

Provides high-level operations for managing the load generator container.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from docker_client import DockerClient


class ContainerManager:
    """High-level container management"""
    
    def __init__(self, docker_client: DockerClient):
        self.docker = docker_client
    
    def parse_env_list(self, env_list: list) -> Dict[str, str]:
        """
        Parse Docker environment variable list into dict
        
        Args:
            env_list: List of "KEY=VALUE" strings
        
        Returns:
            Dict of environment variables
        """
        env_dict = {}
        for item in env_list:
            if '=' in item:
                key, value = item.split('=', 1)
                env_dict[key] = value
        return env_dict
    
    def mask_sensitive_values(self, env_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Mask sensitive environment variables
        
        Args:
            env_dict: Environment variables
        
        Returns:
            Dict with sensitive values masked
        """
        masked = env_dict.copy()
        sensitive_keys = ['MATOMO_TOKEN_AUTH', 'TOKEN', 'PASSWORD', 'SECRET', 'KEY']
        
        for key in masked:
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                if masked[key]:
                    masked[key] = '***MASKED***'
        
        return masked
    
    def calculate_uptime(self, started_at: Optional[str]) -> Optional[str]:
        """
        Calculate container uptime from start time
        
        Args:
            started_at: ISO 8601 timestamp string
        
        Returns:
            Human-readable uptime string (e.g., "2h 15m")
        """
        if not started_at or started_at == "0001-01-01T00:00:00Z":
            return None
        
        try:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            delta = now - start_time
            
            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            parts = []
            if days > 0:
                parts.append(f"{days}d")
            if hours > 0:
                parts.append(f"{hours}h")
            if minutes > 0:
                parts.append(f"{minutes}m")
            if not parts and seconds > 0:
                parts.append(f"{seconds}s")
            
            return " ".join(parts) if parts else "0s"
        except Exception as e:
            print(f"Error calculating uptime: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive container status
        
        Returns:
            Dict with container state, config, and stats
        """
        state = self.docker.get_container_state()
        info = self.docker.get_container_info()
        
        result = {
            "container": {
                "state": state,
                "name": "matomo-loadgen",
                "id": None,
                "uptime": None,
                "created": None,
                "started_at": None,
            },
            "config": None,
            "stats": None,
        }
        
        if info:
            result["container"]["id"] = info.get("id")
            result["container"]["created"] = info.get("created")
            result["container"]["started_at"] = info.get("started_at")
            result["container"]["uptime"] = self.calculate_uptime(info.get("started_at"))
            
            # Parse and mask environment variables
            env_list = info.get("config", {}).get("env", [])
            env_dict = self.parse_env_list(env_list)
            result["config"] = self.mask_sensitive_values(env_dict)
            
            # Calculate stats if running
            if state == "running":
                result["stats"] = {
                    "uptime": result["container"]["uptime"],
                    "visits_generated": None,  # TODO: Parse from logs in future
                    "current_rate": None,      # TODO: Calculate from TARGET_VISITS_PER_DAY
                }
                
                # Calculate expected rate
                target_visits = env_dict.get("TARGET_VISITS_PER_DAY")
                if target_visits:
                    try:
                        visits_per_day = float(target_visits)
                        visits_per_second = visits_per_day / 86400
                        result["stats"]["current_rate"] = f"{visits_per_second:.2f}/sec"
                    except (ValueError, TypeError):
                        pass
        
        return result
    
    def start_container(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start the container
        
        Args:
            config: Optional new configuration (not yet implemented - needs docker-compose)
        
        Returns:
            Result dict with success status
        """
        # Note: Updating environment variables requires stopping, updating compose, and restarting
        # For now, we just start with existing config
        if config:
            # TODO: Implement config update via docker-compose
            return {
                "success": False,
                "error": "Config updates not yet implemented. Use docker-compose to change config.",
                "state": self.docker.get_container_state(),
            }
        
        result = self.docker.start_container()
        result["state"] = self.docker.get_container_state()
        return result
    
    def stop_container(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Stop the container gracefully
        
        Args:
            timeout: Seconds to wait before forcing stop
        
        Returns:
            Result dict with success status
        """
        result = self.docker.stop_container(timeout=timeout)
        result["state"] = self.docker.get_container_state()
        return result
    
    def restart_container(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Restart the container
        
        Args:
            timeout: Seconds to wait before forcing stop
        
        Returns:
            Result dict with success status
        """
        result = self.docker.restart_container(timeout=timeout)
        result["state"] = self.docker.get_container_state()
        return result
    
    def get_logs(self, lines: int = 100, filter_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Get container logs
        
        Args:
            lines: Number of lines to retrieve
            filter_text: Optional text to filter logs by
        
        Returns:
            Dict with logs and metadata
        """
        logs = self.docker.get_container_logs(lines=lines, tail=True)
        
        # Apply text filter if provided
        if filter_text and logs:
            log_lines = logs.split('\n')
            filtered_lines = [line for line in log_lines if filter_text.lower() in line.lower()]
            logs = '\n'.join(filtered_lines)
            lines_returned = len(filtered_lines)
        else:
            lines_returned = len(logs.split('\n')) if logs else 0
        
        return {
            "logs": logs,
            "lines_returned": lines_returned,
            "container_state": self.docker.get_container_state(),
        }
