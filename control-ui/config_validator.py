"""
Configuration Validator

Validates load generator configuration and tests Matomo connectivity.
"""
import re
import aiohttp
import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from pydantic import BaseModel, Field, field_validator, model_validator

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - fallback for older Python versions
    ZoneInfo = None


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
    ecommerce_currency: str = Field("SEK", min_length=3, max_length=3)
    
    # Timezone
    timezone: str = Field("CET")

    # Backfill (historical replay)
    backfill_enabled: bool = Field(False)
    backfill_start_date: Optional[str] = None
    backfill_end_date: Optional[str] = None
    backfill_days_back: Optional[int] = Field(None, ge=1, le=365)
    backfill_duration_days: Optional[int] = Field(None, ge=1, le=365)
    backfill_max_visits_per_day: Optional[int] = Field(2000, ge=1, le=10000)
    backfill_max_visits_total: Optional[int] = Field(200000, ge=1, le=10000000)
    backfill_rps_limit: Optional[float] = Field(None, gt=0, le=500)
    backfill_seed: Optional[int] = Field(None, ge=0, le=2**31 - 1)

    # Derived/normalized values (excluded from output)
    backfill_window_days: Optional[int] = Field(default=None, exclude=True)
    
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
            raise ValueError("Currency code must be uppercase (e.g., SEK, EUR, GBP)")
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError("Currency code must be 3 uppercase letters")
        return v

    @staticmethod
    def _parse_date(value: str, field: str) -> date:
        """Parse ISO date strings"""
        try:
            return date.fromisoformat(value)
        except Exception:
            raise ValueError(f"{field} must be in YYYY-MM-DD format")

    @staticmethod
    def _get_timezone(tz_name: str):
        """Resolve timezone name to tzinfo"""
        if ZoneInfo:
            try:
                return ZoneInfo(tz_name)
            except Exception:
                pass
        # Fallback to UTC when unknown
        return timezone.utc
    
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

        # Backfill validation
        if self.backfill_enabled:
            tzinfo = self._get_timezone(self.timezone)
            today = datetime.now(tzinfo).date()

            start_date: Optional[date] = None
            end_date: Optional[date] = None

            has_absolute = self.backfill_start_date or self.backfill_end_date
            has_relative = self.backfill_days_back or self.backfill_duration_days

            if has_absolute and has_relative:
                raise ValueError("Provide either start/end dates or days_back + duration, not both")

            if has_absolute:
                if not (self.backfill_start_date and self.backfill_end_date):
                    raise ValueError("Both backfill_start_date and backfill_end_date are required when using date range")
                start_date = self._parse_date(self.backfill_start_date, "backfill_start_date")
                end_date = self._parse_date(self.backfill_end_date, "backfill_end_date")
            elif has_relative:
                if not (self.backfill_days_back and self.backfill_duration_days):
                    raise ValueError("backfill_days_back and backfill_duration_days must both be set when using relative window")
                # backfill_days_back of 1 = yesterday
                start_date = today - timedelta(days=self.backfill_days_back)
                end_date = start_date + timedelta(days=self.backfill_duration_days - 1)
            else:
                raise ValueError("Backfill window required: provide start/end dates or days_back + duration")

            if start_date > end_date:
                raise ValueError("Backfill start date must be on or before end date")
            if end_date > today:
                raise ValueError("Backfill end date cannot be in the future")

            window_days = (end_date - start_date).days + 1
            if window_days > 180:
                raise ValueError("Backfill window cannot exceed 180 days")

            if self.backfill_max_visits_total and self.backfill_max_visits_per_day:
                if self.backfill_max_visits_total < self.backfill_max_visits_per_day:
                    raise ValueError("BACKFILL_MAX_VISITS_TOTAL must be >= BACKFILL_MAX_VISITS_PER_DAY")

            self.backfill_window_days = window_days
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
            # Use Pydantic model for validation
            validated_config = LoadGeneratorConfig(**config)
            
            # Additional business rule validations
            
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

            # Backfill guardrails and advisories
            if validated_config.backfill_enabled:
                window_days = validated_config.backfill_window_days or 0
                if window_days > 90:
                    warnings.append(ConfigValidationError(
                        field="backfill_window",
                        message=f"Long backfill window ({window_days} days). Consider smaller batches (<=90 days) to reduce load and error risk.",
                        severity="warning"
                    ))

                if validated_config.backfill_max_visits_per_day and validated_config.backfill_max_visits_per_day > 8000:
                    warnings.append(ConfigValidationError(
                        field="backfill_max_visits_per_day",
                        message=f"High per-day backfill cap ({validated_config.backfill_max_visits_per_day:,}). Monitor Matomo for rate limiting.",
                        severity="warning"
                    ))

                if validated_config.backfill_rps_limit and validated_config.backfill_rps_limit > 100:
                    warnings.append(ConfigValidationError(
                        field="backfill_rps_limit",
                        message=f"High backfill RPS limit ({validated_config.backfill_rps_limit}). Consider lowering to avoid HTTP 429/5xx.",
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
        site_id: int = 1,
        token_auth: str | None = None,
        timeout: float = 10.0
    ) -> MatomoConnectionResult:
        """
        Test connectivity to Matomo server
        
        Args:
            matomo_url: Matomo tracking endpoint URL
            site_id: Matomo site ID to test against
            token_auth: Optional Matomo token_auth for secured endpoints
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
                'idsite': site_id,
                'rec': 1,
                'action_name': 'Connection Test',
                'url': 'http://test.local/connection-test',
                '_id': 'test1234567890ab',
                'rand': int(asyncio.get_event_loop().time() * 1000)
            }
            if token_auth:
                params['token_auth'] = token_auth
            
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
