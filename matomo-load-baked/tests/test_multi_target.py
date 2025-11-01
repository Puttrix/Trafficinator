"""
Tests for multi-target routing functionality (P-008)
"""
import pytest
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import target_router
sys.path.insert(0, str(Path(__file__).parent.parent))

from target_router import Target, TargetRouter, TargetMetrics, parse_targets_from_env, get_distribution_strategy


class TestTarget:
    """Test Target dataclass"""
    
    def test_target_creation(self):
        """Test creating a basic target"""
        target = Target(
            name="Test Target",
            url="https://matomo.example.com",
            site_id=1
        )
        assert target.name == "Test Target"
        assert target.url == "https://matomo.example.com"
        assert target.site_id == 1
        assert target.token_auth is None
        assert target.weight == 1
        assert target.enabled is True
    
    def test_target_with_all_fields(self):
        """Test target with all optional fields"""
        target = Target(
            name="EU Prod",
            url="https://eu.matomo.com",
            site_id=2,
            token_auth="abc123",
            weight=70,
            enabled=False
        )
        assert target.token_auth == "abc123"
        assert target.weight == 70
        assert target.enabled is False


class TestTargetMetrics:
    """Test TargetMetrics tracking"""
    
    def test_initial_metrics(self):
        """Test newly created metrics"""
        metrics = TargetMetrics(target_name="Test")
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.avg_latency_ms is None
        assert metrics.success_rate == 0.0
        assert metrics.status == "unknown"
    
    def test_record_success(self):
        """Test recording successful requests"""
        metrics = TargetMetrics(target_name="Test")
        metrics.record_success(100.5)
        metrics.record_success(200.3)
        
        assert metrics.total_requests == 2
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 0
        assert metrics.avg_latency_ms == pytest.approx(150.4, rel=0.01)
        assert metrics.success_rate == 1.0
        assert metrics.status == "healthy"
        assert metrics.last_success is not None
    
    def test_record_failure(self):
        """Test recording failed requests"""
        metrics = TargetMetrics(target_name="Test")
        metrics.record_failure("Connection timeout")
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.last_error == "Connection timeout"
        assert metrics.success_rate == 0.0
        assert metrics.status == "failed"
        assert metrics.last_failure is not None
    
    def test_status_thresholds(self):
        """Test health status thresholds"""
        metrics = TargetMetrics(target_name="Test")
        
        # 95%+ success = healthy
        for _ in range(19):
            metrics.record_success(100.0)
        metrics.record_failure("error")
        assert metrics.status == "healthy"  # 95% success
        
        # 70-94% success = degraded
        for _ in range(5):
            metrics.record_failure("error")
        assert metrics.status == "degraded"  # 76% success
        
        # <70% success = failed
        for _ in range(10):
            metrics.record_failure("error")
        assert metrics.status == "failed"  # 54% success


class TestTargetRouter:
    """Test TargetRouter distribution logic"""
    
    def test_router_initialization(self):
        """Test router creation"""
        targets = [
            Target("EU", "https://eu.matomo.com", 1),
            Target("US", "https://us.matomo.com", 1),
        ]
        router = TargetRouter(targets, "round-robin")
        
        assert len(router.all_targets) == 2
        assert len(router.enabled_targets) == 2
        assert router.strategy == "round-robin"
        assert len(router.metrics) == 2
    
    def test_router_filters_disabled_targets(self):
        """Test that disabled targets are excluded"""
        targets = [
            Target("EU", "https://eu.matomo.com", 1, enabled=True),
            Target("US", "https://us.matomo.com", 1, enabled=False),
            Target("ASIA", "https://asia.matomo.com", 1, enabled=True),
        ]
        router = TargetRouter(targets, "round-robin")
        
        assert len(router.all_targets) == 3
        assert len(router.enabled_targets) == 2
        assert router.enabled_targets[0].name == "EU"
        assert router.enabled_targets[1].name == "ASIA"
    
    def test_router_requires_enabled_target(self):
        """Test that at least one enabled target is required"""
        targets = [
            Target("EU", "https://eu.matomo.com", 1, enabled=False),
        ]
        with pytest.raises(ValueError, match="At least one target must be enabled"):
            TargetRouter(targets, "round-robin")
    
    def test_round_robin_distribution(self):
        """Test round-robin distribution cycles through targets"""
        targets = [
            Target("T1", "https://t1.com", 1),
            Target("T2", "https://t2.com", 1),
            Target("T3", "https://t3.com", 1),
        ]
        router = TargetRouter(targets, "round-robin")
        
        # Should cycle: T1, T2, T3, T1, T2, T3, ...
        sequence = [router.next_target().name for _ in range(9)]
        assert sequence == ["T1", "T2", "T3", "T1", "T2", "T3", "T1", "T2", "T3"]
    
    def test_weighted_distribution(self):
        """Test weighted distribution respects weights"""
        targets = [
            Target("Heavy", "https://heavy.com", 1, weight=90),
            Target("Light", "https://light.com", 1, weight=10),
        ]
        router = TargetRouter(targets, "weighted")
        
        # Sample 1000 selections
        counts = {"Heavy": 0, "Light": 0}
        for _ in range(1000):
            target = router.next_target()
            counts[target.name] += 1
        
        # Heavy should be selected ~90% of the time (allow some variance)
        assert 850 <= counts["Heavy"] <= 950
        assert 50 <= counts["Light"] <= 150
    
    def test_random_distribution(self):
        """Test random distribution is reasonably uniform"""
        targets = [
            Target("T1", "https://t1.com", 1),
            Target("T2", "https://t2.com", 1),
            Target("T3", "https://t3.com", 1),
        ]
        router = TargetRouter(targets, "random")
        
        # Sample 1500 selections
        counts = {"T1": 0, "T2": 0, "T3": 0}
        for _ in range(1500):
            target = router.next_target()
            counts[target.name] += 1
        
        # Each should be selected ~500 times (allow 30% variance)
        for count in counts.values():
            assert 350 <= count <= 650
    
    def test_weighted_validates_weights(self):
        """Test weighted strategy requires positive weights"""
        targets = [
            Target("T1", "https://t1.com", 1, weight=0),
            Target("T2", "https://t2.com", 1, weight=10),
        ]
        with pytest.raises(ValueError, match="weight >= 1"):
            TargetRouter(targets, "weighted")
    
    def test_get_metrics(self):
        """Test retrieving metrics"""
        targets = [
            Target("EU", "https://eu.matomo.com", 1),
            Target("US", "https://us.matomo.com", 1),
        ]
        router = TargetRouter(targets, "round-robin")
        
        # Record some metrics
        router.metrics["EU"].record_success(100.0)
        router.metrics["US"].record_failure("timeout")
        
        # Get all metrics
        all_metrics = router.get_metrics()
        assert len(all_metrics) == 2
        assert all_metrics["EU"].successful_requests == 1
        assert all_metrics["US"].failed_requests == 1
        
        # Get specific target metrics
        eu_metrics = router.get_metrics("EU")
        assert "EU" in eu_metrics
        assert eu_metrics["EU"].successful_requests == 1
    
    def test_get_summary(self):
        """Test overall summary statistics"""
        targets = [
            Target("EU", "https://eu.matomo.com", 1),
            Target("US", "https://us.matomo.com", 1, enabled=False),
        ]
        router = TargetRouter(targets, "round-robin")
        
        router.metrics["EU"].record_success(100.0)
        router.metrics["EU"].record_success(150.0)
        router.metrics["EU"].record_failure("error")
        
        summary = router.get_summary()
        assert summary["total_targets"] == 2
        assert summary["enabled_targets"] == 1
        assert summary["strategy"] == "round-robin"
        assert summary["total_requests"] == 3
        assert summary["total_successes"] == 2
        assert summary["total_failures"] == 1
        assert summary["overall_success_rate"] == pytest.approx(0.666, rel=0.01)
        assert "EU" in summary["per_target_metrics"]


class TestEnvironmentParsing:
    """Test parsing configuration from environment variables"""
    
    def test_parse_targets_from_env_with_config(self, monkeypatch):
        """Test parsing valid multi-target config"""
        config = {
            "targets": [
                {
                    "name": "EU Prod",
                    "url": "https://eu.matomo.com/",
                    "site_id": 1,
                    "token_auth": "abc123",
                    "weight": 70,
                    "enabled": True
                },
                {
                    "name": "US Prod",
                    "url": "https://us.matomo.com",
                    "site_id": 2,
                    "weight": 30
                }
            ]
        }
        monkeypatch.setenv("MULTI_TARGET_CONFIG", json.dumps(config))
        
        targets = parse_targets_from_env()
        assert targets is not None
        assert len(targets) == 2
        
        assert targets[0].name == "EU Prod"
        assert targets[0].url == "https://eu.matomo.com"  # Trailing slash removed
        assert targets[0].site_id == 1
        assert targets[0].token_auth == "abc123"
        assert targets[0].weight == 70
        assert targets[0].enabled is True
        
        assert targets[1].name == "US Prod"
        assert targets[1].site_id == 2
        assert targets[1].token_auth is None
        assert targets[1].weight == 30
    
    def test_parse_targets_from_env_no_config(self, monkeypatch):
        """Test when no multi-target config is set"""
        monkeypatch.delenv("MULTI_TARGET_CONFIG", raising=False)
        targets = parse_targets_from_env()
        assert targets is None
    
    def test_parse_targets_from_env_invalid_json(self, monkeypatch):
        """Test handling of invalid JSON"""
        monkeypatch.setenv("MULTI_TARGET_CONFIG", "not valid json{}")
        targets = parse_targets_from_env()
        assert targets is None  # Should return None and log warning
    
    def test_get_distribution_strategy_from_env(self, monkeypatch):
        """Test extracting distribution strategy"""
        config = {
            "targets": [{"name": "T1", "url": "https://t1.com", "site_id": 1}],
            "distribution_strategy": "weighted"
        }
        monkeypatch.setenv("MULTI_TARGET_CONFIG", json.dumps(config))
        
        strategy = get_distribution_strategy()
        assert strategy == "weighted"
    
    def test_get_distribution_strategy_default(self, monkeypatch):
        """Test default strategy when not specified"""
        monkeypatch.delenv("MULTI_TARGET_CONFIG", raising=False)
        strategy = get_distribution_strategy()
        assert strategy == "round-robin"
