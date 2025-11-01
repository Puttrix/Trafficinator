"""
Target Router for multi-target load distribution (P-008)

Handles routing and distribution of tracking requests across multiple Matomo instances.
Supports round-robin, weighted, and random distribution strategies.
"""
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
from datetime import datetime


@dataclass
class Target:
    """Single Matomo tracking target"""
    name: str
    url: str
    site_id: int
    token_auth: Optional[str] = None
    weight: int = 1
    enabled: bool = True


@dataclass
class TargetMetrics:
    """Runtime metrics for a single target"""
    target_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_error: Optional[str] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    
    @property
    def avg_latency_ms(self) -> Optional[float]:
        """Calculate average latency"""
        if self.successful_requests > 0:
            return self.total_latency_ms / self.successful_requests
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)"""
        if self.total_requests > 0:
            return self.successful_requests / self.total_requests
        return 0.0
    
    @property
    def status(self) -> Literal["healthy", "degraded", "failed", "unknown"]:
        """Determine target health status"""
        if self.total_requests == 0:
            return "unknown"
        elif self.success_rate >= 0.95:
            return "healthy"
        elif self.success_rate >= 0.70:
            return "degraded"
        else:
            return "failed"
    
    def record_success(self, latency_ms: float):
        """Record a successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_latency_ms += latency_ms
        self.last_success = datetime.utcnow()
    
    def record_failure(self, error: str):
        """Record a failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_error = error
        self.last_failure = datetime.utcnow()


class TargetRouter:
    """
    Routes tracking requests across multiple Matomo targets.
    
    Supports three distribution strategies:
    - round-robin: Cycle through targets sequentially (ignores weights)
    - weighted: Probability proportional to target weights
    - random: Uniform random selection across enabled targets
    """
    
    def __init__(
        self,
        targets: List[Target],
        strategy: Literal["round-robin", "weighted", "random"] = "round-robin"
    ):
        self.all_targets = targets
        self.enabled_targets = [t for t in targets if t.enabled]
        self.strategy = strategy
        self._index = 0  # For round-robin
        
        # Initialize metrics for all targets
        self.metrics: Dict[str, TargetMetrics] = {
            t.name: TargetMetrics(target_name=t.name) for t in targets
        }
        
        if not self.enabled_targets:
            raise ValueError("At least one target must be enabled")
        
        # Validate weighted strategy
        if strategy == "weighted":
            if any(t.weight < 1 for t in self.enabled_targets):
                raise ValueError("All enabled targets must have weight >= 1 for weighted distribution")
    
    def next_target(self) -> Target:
        """
        Select the next target according to the configured strategy.
        
        Returns:
            Target instance to send the next request to
        """
        if self.strategy == "round-robin":
            return self._next_round_robin()
        elif self.strategy == "weighted":
            return self._next_weighted()
        else:  # random
            return self._next_random()
    
    def _next_round_robin(self) -> Target:
        """Round-robin: cycle through targets sequentially"""
        target = self.enabled_targets[self._index % len(self.enabled_targets)]
        self._index += 1
        return target
    
    def _next_weighted(self) -> Target:
        """Weighted: select based on weight probabilities"""
        weights = [t.weight for t in self.enabled_targets]
        return random.choices(self.enabled_targets, weights=weights, k=1)[0]
    
    def _next_random(self) -> Target:
        """Random: uniform random selection"""
        return random.choice(self.enabled_targets)
    
    def get_metrics(self, target_name: Optional[str] = None) -> Dict[str, TargetMetrics]:
        """
        Get metrics for specific target or all targets.
        
        Args:
            target_name: Optional target name to filter by
            
        Returns:
            Dictionary of target metrics
        """
        if target_name:
            return {target_name: self.metrics.get(target_name)}
        return self.metrics
    
    def get_summary(self) -> Dict[str, any]:
        """Get overall summary statistics"""
        total_requests = sum(m.total_requests for m in self.metrics.values())
        total_successes = sum(m.successful_requests for m in self.metrics.values())
        total_failures = sum(m.failed_requests for m in self.metrics.values())
        
        return {
            "total_targets": len(self.all_targets),
            "enabled_targets": len(self.enabled_targets),
            "strategy": self.strategy,
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_failures": total_failures,
            "overall_success_rate": total_successes / total_requests if total_requests > 0 else 0.0,
            "per_target_metrics": {
                name: {
                    "requests": m.total_requests,
                    "successes": m.successful_requests,
                    "failures": m.failed_requests,
                    "success_rate": m.success_rate,
                    "avg_latency_ms": m.avg_latency_ms,
                    "status": m.status
                }
                for name, m in self.metrics.items()
            }
        }


def parse_targets_from_env() -> Optional[List[Target]]:
    """
    Parse multi-target configuration from environment variable.
    
    Expected format (JSON):
    {
        "targets": [
            {
                "name": "EU Production",
                "url": "https://eu.matomo.com",
                "site_id": 1,
                "token_auth": "abc123",
                "weight": 70,
                "enabled": true
            },
            ...
        ],
        "distribution_strategy": "weighted"
    }
    
    Returns:
        List of Target objects if multi-target config exists, None otherwise
    """
    import os
    import json
    
    multi_target_config = os.environ.get("MULTI_TARGET_CONFIG")
    if not multi_target_config:
        return None
    
    try:
        config = json.loads(multi_target_config)
        targets_data = config.get("targets", [])
        
        if not targets_data:
            return None
        
        targets = []
        for t in targets_data:
            targets.append(Target(
                name=t["name"],
                url=t["url"].rstrip("/"),
                site_id=int(t["site_id"]),
                token_auth=t.get("token_auth"),
                weight=int(t.get("weight", 1)),
                enabled=bool(t.get("enabled", True))
            ))
        
        return targets
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        import logging
        logging.warning(f"Failed to parse MULTI_TARGET_CONFIG: {e}")
        return None


def get_distribution_strategy() -> str:
    """Get distribution strategy from environment or default to round-robin"""
    import os
    import json
    
    multi_target_config = os.environ.get("MULTI_TARGET_CONFIG")
    if multi_target_config:
        try:
            config = json.loads(multi_target_config)
            return config.get("distribution_strategy", "round-robin")
        except json.JSONDecodeError:
            pass
    
    return "round-robin"
