"""
Configuration Validator

Validates load generator configuration and tests Matomo connectivity.
"""
import re
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator


class ConfigValidationError(BaseModel):
    """Single validation error"""
    field: str
    message: str
    severity: str = "error"  # error, warning


class ConfigValidationResult(BaseModel):
    """Result of configuration validation"""
    valid: bool
    errors: List[ConfigValidationError] = []
    warnings: List[ConfigValidationError] = []


class MatomoConnectionResult(BaseModel):
    """Result of Matomo connectivity test"""
    success: bool
    reachable: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    message: str


class LoadGeneratorConfig(BaseModel):
    """Load generator configuration model with validation"""
    
    # Required fields
    matomo_url: str = Field(..., description="Matomo tracking endpoint URL")
    matomo_site_id: int = Field(..., ge=1, description="Matomo site ID")
    
    # Optional fields with defaults
    matomo_token_auth: Optional[str] = Field(None, description="Matomo authentication token")
    target_visits_per_day: float = Field(20000, ge=1, le=1000000)
    pageviews_min: int = Field(3, ge=1, le=100)
    pageviews_max: int = Field(6, ge=1, le=100)
    concurrency: int = Field(50, ge=1, le=500)
    pause_between_pvs_min: float = Field(0.5, ge=0.1, le=60)
    pause_between_pvs_max: float = Field(2.0, ge=0.1, le=60)
    
    # Auto-stop controls
    auto_stop_after_hours: float = Field(0, ge=0, le=168)  # 0-168 hours (1 week)
    max_total_visits: int = Field(0, ge=0, le=10000000)
    
    # Probabilities (0.0 - 1.0)
    sitesearch_probability: float = Field(0.15, ge=0, le=1)
    outlinks_probability: float = Field(0.10, ge=0, le=1)
    downloads_probability: float = Field(0.08, ge=0, le=1)
    click_events_probability: float = Field(0.25, ge=0, le=1)
    random_events_probability: float = Field(0.12, ge=0, le=1)
    direct_traffic_probability: float = Field(0.30, ge=0, le=1)
    ecommerce_probability: float = Field(0.05, ge=0, le=1)
    
    # Visit duration (minutes)
    visit_duration_min: float = Field(1.0, ge=0.1, le=120)
    visit_duration_max: float = Field(8.0, ge=0.1, le=120)
    
    # Geolocation
    randomize_visitor_countries: bool = Field(True)
    
    # Ecommerce
    ecommerce_order_value_min: float = Field(15.99, ge=0.01)
    ecommerce_order_value_max: float = Field(299.99, ge=0.01)
    ecommerce_currency: str = Field("USD", min_length=3, max_length=3)
    
    # Timezone
    timezone: str = Field("UTC")
    
    @field_validator("matomo_url")
    @classmethod
    def validate_matomo_url(cls, v: str) -> str:
        """Validate Matomo URL format"""
        if not v:
            raise ValueError("Matomo URL is required")
        
        # Parse URL
        parsed = urlparse(v)
        if not parsed.scheme:
            raise ValueError("Matomo URL must include scheme (http:// or https://)")
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("Matomo URL must use http:// or https://")
        if not parsed.netloc:
            raise ValueError("Matomo URL must include a valid domain")
        
        return v.rstrip("/")
    
    @field_validator("ecommerce_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code"""
        if not v.isupper():
            raise ValueError("Currency code must be uppercase (e.g., USD, EUR, GBP)")
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError("Currency code must be 3 uppercase letters")
        return v
    
    @model_validator(mode='after')
    def validate_ranges(self) -> 'LoadGeneratorConfig':
        """Validate min/max ranges"""
        if self.pageviews_min > self.pageviews_max:
            raise ValueError("pageviews_min cannot be greater than pageviews_max")
        if self.pause_between_pvs_min > self.pause_between_pvs_max:
            raise ValueError("pause_between_pvs_min cannot be greater than pause_between_pvs_max")
        if self.visit_duration_min > self.visit_duration_max:
            raise ValueError("visit_duration_min cannot be greater than visit_duration_max")
        if self.ecommerce_order_value_min > self.ecommerce_order_value_max:
            raise ValueError("ecommerce_order_value_min cannot be greater than ecommerce_order_value_max")
        return self


class ConfigValidator:
    """Validates load generator configuration"""
    
    @staticmethod
    def validate_config(config: Dict) -> ConfigValidationResult:
        """
        Validate configuration
        
        Args:
            config: Configuration dictionary
            
        Returns:
            ConfigValidationResult with validation status and errors
        """
        errors = []
        warnings = []
        
        try:
            # Check if this is a multi-target config (P-008)
            is_multi_target = 'targets' in config and isinstance(config.get('targets'), list)
            
            if is_multi_target:
                # Validate using ConfigEnvironment model for multi-target
                from models import ConfigEnvironment
                validated_env = ConfigEnvironment(**config)
                
                # Get the validated config values for business rules
                # Note: For multi-target, we check each target individually
                if validated_env.targets:
                    for target in validated_env.targets:
                        if not target.token_auth and config.get('randomize_visitor_countries', True):
                            warnings.append(ConfigValidationError(
                                field=f"targets.{target.name}.token_auth",
                                message=f"Token auth recommended for '{target.name}' when randomizing visitor countries",
                                severity="warning"
                            ))
            else:
                # Legacy single-target validation
                validated_config = LoadGeneratorConfig(**config)
                
                # Additional business rule validations for single-target
                
                # Check if token_auth is provided when randomize_visitor_countries is true
                if validated_config.randomize_visitor_countries and not validated_config.matomo_token_auth:
                    warnings.append(ConfigValidationError(
                        field="matomo_token_auth",
                        message="MATOMO_TOKEN_AUTH is recommended when RANDOMIZE_VISITOR_COUNTRIES is enabled for accurate geolocation",
                        severity="warning"
                    ))
                
                # Warn if concurrency is very high
                if validated_config.concurrency > 200:
                    warnings.append(ConfigValidationError(
                        field="concurrency",
                        message=f"High concurrency ({validated_config.concurrency}) may cause performance issues or rate limiting",
                        severity="warning"
                    ))
                
                # Warn if target visits is very high
                if validated_config.target_visits_per_day > 500000:
                    warnings.append(ConfigValidationError(
                        field="target_visits_per_day",
                        message=f"Very high target ({validated_config.target_visits_per_day:,.0f} visits/day) may overwhelm the Matomo server",
                        severity="warning"
                    ))
                
                # Check if auto-stop is configured
                if validated_config.auto_stop_after_hours == 0 and validated_config.max_total_visits == 0:
                    warnings.append(ConfigValidationError(
                        field="auto_stop",
                        message="No auto-stop configured. Load generator will run indefinitely until manually stopped",
                        severity="warning"
                    ))
            
            # Common validations for both modes
            concurrency = config.get('concurrency', 50)
            target_visits = config.get('target_visits_per_day', 20000)
            auto_stop_hours = config.get('auto_stop_after_hours', 0)
            max_visits = config.get('max_total_visits', 0)
            
            # Warn if concurrency is very high
            if concurrency > 200:
                warnings.append(ConfigValidationError(
                    field="concurrency",
                    message=f"High concurrency ({concurrency}) may cause performance issues or rate limiting",
                    severity="warning"
                ))
            
            # Warn if target visits is very high
            if target_visits > 500000:
                warnings.append(ConfigValidationError(
                    field="target_visits_per_day",
                    message=f"Very high target ({target_visits:,.0f} visits/day) may overwhelm the Matomo server",
                    severity="warning"
                ))
            
            # Check if auto-stop is configured
            if auto_stop_hours == 0 and max_visits == 0:
                warnings.append(ConfigValidationError(
                    field="auto_stop",
                    message="No auto-stop configured. Load generator will run indefinitely until manually stopped",
                    severity="warning"
                ))
            
            return ConfigValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            # Convert validation errors to our format
            error_message = str(e)
            
            # Try to parse Pydantic validation errors
            if hasattr(e, 'errors'):
                for err in e.errors():
                    field = '.'.join(str(x) for x in err['loc'])
                    errors.append(ConfigValidationError(
                        field=field,
                        message=err['msg']
                    ))
            else:
                errors.append(ConfigValidationError(
                    field="config",
                    message=error_message
                ))
            
            return ConfigValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings
            )
    
    @staticmethod
    async def test_matomo_connection(
        matomo_url: str,
        timeout: float = 10.0
    ) -> MatomoConnectionResult:
        """
        Test connectivity to Matomo server
        
        Args:
            matomo_url: Matomo tracking endpoint URL
            timeout: Request timeout in seconds
            
        Returns:
            MatomoConnectionResult with connection status
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Parse URL
            parsed = urlparse(matomo_url)
            if not parsed.scheme or not parsed.netloc:
                return MatomoConnectionResult(
                    success=False,
                    reachable=False,
                    error="Invalid URL format",
                    message="Invalid URL format"
                )
            
            # Test connection with minimal valid request
            params = {
                'idsite': 1,
                'rec': 1,
                'action_name': 'Connection Test',
                'url': 'http://test.local/connection-test',
                '_id': 'test1234567890ab',
                'rand': int(asyncio.get_event_loop().time() * 1000)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    matomo_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True
                ) as resp:
                    end_time = asyncio.get_event_loop().time()
                    response_time_ms = (end_time - start_time) * 1000
                    
                    # Matomo typically returns 200 or 204 for tracking requests
                    if resp.status in [200, 204]:
                        return MatomoConnectionResult(
                            success=True,
                            reachable=True,
                            status_code=resp.status,
                            response_time_ms=round(response_time_ms, 2),
                            message=f"Connection successful (HTTP {resp.status}, {response_time_ms:.0f}ms)"
                        )
                    else:
                        return MatomoConnectionResult(
                            success=False,
                            reachable=True,
                            status_code=resp.status,
                            response_time_ms=round(response_time_ms, 2),
                            error=f"Unexpected HTTP status {resp.status}",
                            message=f"Server responded with HTTP {resp.status}"
                        )
        
        except asyncio.TimeoutError:
            return MatomoConnectionResult(
                success=False,
                reachable=False,
                error="Connection timeout",
                message=f"Connection timed out after {timeout}s"
            )
        
        except aiohttp.ClientConnectorError as e:
            return MatomoConnectionResult(
                success=False,
                reachable=False,
                error=f"Connection failed: {str(e)}",
                message="Cannot reach Matomo server (connection refused or DNS error)"
            )
        
        except aiohttp.ClientError as e:
            return MatomoConnectionResult(
                success=False,
                reachable=False,
                error=f"HTTP error: {str(e)}",
                message=f"HTTP request error: {str(e)}"
            )
        
        except Exception as e:
            return MatomoConnectionResult(
                success=False,
                reachable=False,
                error=str(e),
                message=f"Unexpected error: {str(e)}"
            )
