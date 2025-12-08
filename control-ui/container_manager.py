"""
Container management operations

Provides high-level operations for managing the load generator container.
"""
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from docker_client import DockerClient


class ContainerManager:
    """High-level container management"""
    
    def __init__(self, docker_client: DockerClient):
        self.docker = docker_client
        self.start_signal_file = os.environ.get("START_SIGNAL_FILE", "/app/data/loadgen.start")
        self.backfill_container_prefix = os.environ.get("BACKFILL_CONTAINER_PREFIX", "matomo-loadgen-backfill")
    
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

    def get_current_env(self) -> Optional[Dict[str, str]]:
        """Return current container env as a dict."""
        info = self.docker.get_container_info()
        if not info:
            return None
        env_list = info.get("config", {}).get("env", [])
        return self.parse_env_list(env_list)
    
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

    def send_start_signal(self) -> bool:
        """
        Touch the start signal file used to allow the load generator to begin when AUTO_START is disabled.
        Returns True if the signal was written successfully.
        """
        try:
            os.makedirs(os.path.dirname(self.start_signal_file), exist_ok=True)
            with open(self.start_signal_file, "w", encoding="utf-8") as fh:
                fh.write(datetime.utcnow().isoformat())
            return True
        except Exception as e:
            print(f"Error writing start signal: {e}")
            return False

    def spawn_backfill_job(self, env_vars: Dict[str, str], name: Optional[str] = None) -> Dict[str, Any]:
        """
        Launch a one-off backfill container using the current container as a template.
        Does not mutate the primary matomo-loadgen container.
        """
        try:
            container = self.docker.get_container()
            if not container:
                return {"success": False, "error": "Primary container not found", "container_name": None, "container_id": None}

            # Extract template info
            attrs = container.attrs
            config = attrs.get("Config", {})
            host_config = attrs.get("HostConfig", {})
            image = config.get("Image")
            volumes = host_config.get("Binds", [])
            network_mode = host_config.get("NetworkMode", "bridge")

            # Prepare env (disable restart loops and force backfill run)
            env = self.parse_env_list(config.get("Env", []))
            env.update(env_vars)
            env.setdefault("BACKFILL_ENABLED", "true")
            env.setdefault("BACKFILL_RUN_ONCE", "true")
            env.setdefault("AUTO_START", "true")

            env_list = [f"{k}={v}" for k, v in env.items()]

            job_name = name or f"{self.backfill_container_prefix}-{int(time.time())}"
            new_container = self.docker.client.containers.run(
                image=image,
                name=job_name,
                environment=env_list,
                volumes=volumes,
                network_mode=network_mode,
                restart_policy={"Name": "no"},
                detach=True,
            )

            return {
                "success": True,
                "error": None,
                "container_name": new_container.name,
                "container_id": new_container.short_id,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "container_name": None, "container_id": None}
    
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

        signal_written = self.send_start_signal()
        result = self.docker.start_container()
        result["state"] = self.docker.get_container_state()
        if result.get("success") and signal_written:
            # Encourage loader with AUTO_START=false to begin
            message = result.get("message", "Container started successfully")
            result["message"] = f"{message}; start signal sent"
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
        signal_written = self.send_start_signal()
        result = self.docker.restart_container(timeout=timeout)
        result["state"] = self.docker.get_container_state()
        if result.get("success") and signal_written:
            message = result.get("message", "Container restarted successfully")
            result["message"] = f"{message}; start signal sent"
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
    
    def config_to_env_vars(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        Convert configuration dictionary to environment variables
        
        Args:
            config: Configuration dictionary with snake_case keys
        
        Returns:
            Dict of environment variables with UPPER_CASE keys
        """
        env_vars = {}
        
        # Map config keys to environment variable names
        key_mapping = {
            'matomo_url': 'MATOMO_URL',
            'matomo_site_id': 'MATOMO_SITE_ID',
            'matomo_token_auth': 'MATOMO_TOKEN_AUTH',
            'target_visits_per_day': 'TARGET_VISITS_PER_DAY',
            'pageviews_min': 'PAGEVIEWS_MIN',
            'pageviews_max': 'PAGEVIEWS_MAX',
            'concurrency': 'CONCURRENCY',
            'pause_between_pvs_min': 'PAUSE_BETWEEN_PVS_MIN',
            'pause_between_pvs_max': 'PAUSE_BETWEEN_PVS_MAX',
            'auto_stop_after_hours': 'AUTO_STOP_AFTER_HOURS',
            'max_total_visits': 'MAX_TOTAL_VISITS',
            'sitesearch_probability': 'SITESEARCH_PROBABILITY',
            'outlinks_probability': 'OUTLINKS_PROBABILITY',
            'downloads_probability': 'DOWNLOADS_PROBABILITY',
            'click_events_probability': 'CLICK_EVENTS_PROBABILITY',
            'random_events_probability': 'RANDOM_EVENTS_PROBABILITY',
            'direct_traffic_probability': 'DIRECT_TRAFFIC_PROBABILITY',
            'ecommerce_probability': 'ECOMMERCE_PROBABILITY',
            'visit_duration_min': 'VISIT_DURATION_MIN',
            'visit_duration_max': 'VISIT_DURATION_MAX',
            'randomize_visitor_countries': 'RANDOMIZE_VISITOR_COUNTRIES',
            'ecommerce_order_value_min': 'ECOMMERCE_ORDER_VALUE_MIN',
            'ecommerce_order_value_max': 'ECOMMERCE_ORDER_VALUE_MAX',
            'ecommerce_currency': 'ECOMMERCE_CURRENCY',
            'timezone': 'TIMEZONE',
            'backfill_enabled': 'BACKFILL_ENABLED',
            'backfill_start_date': 'BACKFILL_START_DATE',
            'backfill_end_date': 'BACKFILL_END_DATE',
            'backfill_days_back': 'BACKFILL_DAYS_BACK',
            'backfill_duration_days': 'BACKFILL_DURATION_DAYS',
            'backfill_max_visits_per_day': 'BACKFILL_MAX_VISITS_PER_DAY',
            'backfill_max_visits_total': 'BACKFILL_MAX_VISITS_TOTAL',
            'backfill_rps_limit': 'BACKFILL_RPS_LIMIT',
            'backfill_seed': 'BACKFILL_SEED',
        }
        
        for config_key, env_key in key_mapping.items():
            if config_key in config:
                value = config[config_key]
                # Convert boolean to string
                if isinstance(value, bool):
                    env_vars[env_key] = 'true' if value else 'false'
                else:
                    env_vars[env_key] = str(value)
        
        return env_vars
    
    def update_and_restart(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """
        Update container environment variables and restart
        
        This recreates the container with new environment variables using Docker SDK.
        
        Args:
            env_vars: Dictionary of environment variables to set
        
        Returns:
            Dict with success status and message
        """
        try:
            import time
            
            current_state = self.docker.get_container_state()
            
            # Get current container to preserve settings
            container = self.docker.get_container()
            if not container:
                return {
                    "success": False,
                    "message": "Container not found",
                    "container_restarted": False,
                    "state": "not_found",
                    "error": "Container does not exist"
                }
            
            # Get container configuration
            config = container.attrs['Config']
            host_config = container.attrs['HostConfig']
            
            # Merge new env vars with existing ones (prioritize new)
            existing_env = {e.split('=', 1)[0]: e.split('=', 1)[1] for e in config.get('Env', []) if '=' in e}
            existing_env.update(env_vars)
            new_env = [f"{k}={v}" for k, v in existing_env.items()]
            
            # Store container settings
            image = config['Image']
            name = container.name
            volumes = host_config.get('Binds', [])
            network_mode = host_config.get('NetworkMode', 'bridge')
            restart_policy = host_config.get('RestartPolicy', {})
            
            # Stop and remove the old container
            was_running = current_state == "running"
            if was_running:
                self.docker.stop_container(timeout=10)
            
            # Remove container using Docker SDK
            container.remove(force=True)
            
            # Create new container with updated environment
            new_container = self.docker.client.containers.create(
                image=image,
                name=name,
                environment=new_env,
                volumes=volumes,
                network_mode=network_mode,
                restart_policy=restart_policy,
                detach=True
            )
            
            # Start the new container if it was running before
            if was_running:
                new_container.start()
                time.sleep(2)  # Give it time to start
            
            new_state = self.docker.get_container_state()
            
            return {
                "success": True,
                "message": "Configuration applied successfully. Container recreated and restarted." if was_running else "Configuration applied successfully. Container recreated (stopped).",
                "container_restarted": was_running,
                "state": new_state,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error applying configuration: {str(e)}",
                "container_restarted": False,
                "state": self.docker.get_container_state(),
                "error": str(e)
            }
