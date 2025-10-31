"""
Pydantic models for request/response validation
"""
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContainerState(BaseModel):
    """Container state information"""
    state: str = Field(..., description="Container state: running, stopped, not_found, error")
    name: str = Field(..., description="Container name")
    id: Optional[str] = Field(None, description="Container ID (short)")
    uptime: Optional[str] = Field(None, description="Container uptime")
    created: Optional[str] = Field(None, description="Container creation time")
    started_at: Optional[str] = Field(None, description="Last start time")


class ContainerStats(BaseModel):
    """Runtime statistics"""
    uptime: Optional[str] = Field(None, description="Container uptime (e.g., '2h 15m')")
    visits_generated: Optional[int] = Field(None, description="Total visits generated (estimate)")
    current_rate: Optional[str] = Field(None, description="Current visit rate (e.g., '0.23/sec')")


class ConfigEnvironment(BaseModel):
    """Configuration environment variables"""
    MATOMO_URL: Optional[str] = None
    MATOMO_SITE_ID: Optional[str] = None
    MATOMO_TOKEN_AUTH: Optional[str] = Field(None, description="Masked for security")
    TARGET_VISITS_PER_DAY: Optional[str] = None
    PAGEVIEWS_MIN: Optional[str] = None
    PAGEVIEWS_MAX: Optional[str] = None
    CONCURRENCY: Optional[str] = None
    PAUSE_BETWEEN_PVS_MIN: Optional[str] = None
    PAUSE_BETWEEN_PVS_MAX: Optional[str] = None
    AUTO_STOP_AFTER_HOURS: Optional[str] = None
    MAX_TOTAL_VISITS: Optional[str] = None
    SITESEARCH_PROBABILITY: Optional[str] = None
    VISIT_DURATION_MIN: Optional[str] = None
    VISIT_DURATION_MAX: Optional[str] = None
    OUTLINKS_PROBABILITY: Optional[str] = None
    DOWNLOADS_PROBABILITY: Optional[str] = None
    CLICK_EVENTS_PROBABILITY: Optional[str] = None
    RANDOM_EVENTS_PROBABILITY: Optional[str] = None
    DIRECT_TRAFFIC_PROBABILITY: Optional[str] = None
    RANDOMIZE_VISITOR_COUNTRIES: Optional[str] = None
    ECOMMERCE_PROBABILITY: Optional[str] = None
    ECOMMERCE_ORDER_VALUE_MIN: Optional[str] = None
    ECOMMERCE_ORDER_VALUE_MAX: Optional[str] = None
    ECOMMERCE_CURRENCY: Optional[str] = None
    TIMEZONE: Optional[str] = None

    model_config = ConfigDict(extra='allow')


class StatusResponse(BaseModel):
    """Response for GET /api/status"""
    container: ContainerState
    config: Optional[ConfigEnvironment] = None
    stats: Optional[ContainerStats] = None


class StartRequest(BaseModel):
    """Request body for POST /api/start"""
    config: Dict[str, Any] = Field(..., description="Environment variables to use")
    restart_if_running: bool = Field(
        default=False,
        description="If true, restart container if already running"
    )


class StartResponse(BaseModel):
    """Response for POST /api/start"""
    success: bool
    message: str
    state: str
    error: Optional[str] = None


class StopResponse(BaseModel):
    """Response for POST /api/stop"""
    success: bool
    message: str
    state: str
    error: Optional[str] = None


class RestartResponse(BaseModel):
    """Response for POST /api/restart"""
    success: bool
    message: str
    state: str
    error: Optional[str] = None


class LogsResponse(BaseModel):
    """Response for GET /api/logs"""
    logs: str = Field(..., description="Container logs")
    lines_returned: int = Field(..., description="Number of log lines returned")
    container_state: str = Field(..., description="Current container state")


class ApplyConfigResponse(BaseModel):
    """Response for POST /api/config/apply"""
    success: bool
    message: str
    container_restarted: bool
    state: str
    error: Optional[str] = None


class URLContentRequest(BaseModel):
    """Request for URL validation/upload"""
    content: str = Field(..., description="URL file content (one URL per line)")


class PresetMetadata(BaseModel):
    """Metadata for a saved configuration preset"""
    id: int
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str


class PresetDetail(PresetMetadata):
    """Detailed preset information with configuration"""
    config: Dict[str, Any]


class PresetListResponse(BaseModel):
    """Response for GET /api/presets"""
    presets: List[PresetMetadata]


class PresetCreateRequest(BaseModel):
    """Request body for creating a preset"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Dict[str, Any]

    model_config = ConfigDict(extra='forbid')


class PresetUpdateRequest(BaseModel):
    """Request body for updating a preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='forbid')


class PresetDeleteResponse(BaseModel):
    """Response for deleting a preset"""
    success: bool
    deleted_id: int
    message: str


# ---------------------------------------------------------------------------
# Funnel models
# ---------------------------------------------------------------------------

class FunnelStep(BaseModel):
    """Single step in a funnel definition"""

    type: Literal["pageview", "event", "site_search", "outlink", "download", "ecommerce"]
    title: Optional[str] = Field(None, max_length=120, description="Human-friendly step label")
    url: Optional[str] = Field(
        None,
        description="Page URL for pageview steps (also used as context url for other step types)",
    )
    action_name: Optional[str] = Field(
        None, description="Custom action name override for pageview or event tracking"
    )

    # Event payload
    event_category: Optional[str] = Field(
        None, description="Matomo event category (required for event steps)"
    )
    event_action: Optional[str] = Field(
        None, description="Matomo event action (required for event steps)"
    )
    event_name: Optional[str] = Field(
        None, description="Matomo event name (required for event steps)"
    )
    event_value: Optional[float] = Field(
        None, description="Matomo event value (optional for event steps)"
    )

    # Search payload
    search_keyword: Optional[str] = Field(
        None, description="Keyword used for site-search steps"
    )
    search_category: Optional[str] = Field(
        None, description="Site-search category (optional)"
    )
    search_results: Optional[int] = Field(
        None, ge=0, description="Number of results returned for site-search steps"
    )

    # Outlink / download target
    target_url: Optional[str] = Field(
        None,
        description="Target URL for outlink/download steps",
    )

    # Ecommerce metadata
    ecommerce_revenue: Optional[float] = Field(
        None, ge=0, description="Optional override for ecommerce revenue"
    )
    ecommerce_items: Optional[int] = Field(
        None, ge=1, description="Optional override for number of ecommerce items"
    )
    ecommerce_subtotal: Optional[float] = Field(
        None, ge=0, description="Optional override for ecommerce subtotal"
    )
    ecommerce_tax: Optional[float] = Field(
        None, ge=0, description="Optional override for ecommerce tax"
    )
    ecommerce_shipping: Optional[float] = Field(
        None, ge=0, description="Optional override for ecommerce shipping"
    )
    ecommerce_currency: Optional[str] = Field(
        None, min_length=3, max_length=3, description="Currency override for ecommerce step"
    )

    # Timing controls
    delay_seconds_min: float = Field(
        0.0,
        ge=0.0,
        le=3600.0,
        description="Minimum delay after this step before the next one begins (seconds)",
    )
    delay_seconds_max: float = Field(
        0.0,
        ge=0.0,
        le=3600.0,
        description="Maximum delay after this step before the next one begins (seconds)",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_step(self):
        if self.delay_seconds_max < self.delay_seconds_min:
            raise ValueError("delay_seconds_max cannot be less than delay_seconds_min")

        if self.type == "pageview" and not self.url:
            raise ValueError("Pageview steps require a 'url' value")

        if self.type == "event":
            missing = [
                field
                for field in ("event_category", "event_action", "event_name")
                if getattr(self, field) in (None, "")
            ]
            if missing:
                raise ValueError(
                    f"Event steps require event_category, event_action, event_name (missing: {', '.join(missing)})"
                )

        if self.type == "site_search" and not self.search_keyword:
            raise ValueError("Site-search steps require a search_keyword value")

        if self.type in ("outlink", "download") and not self.target_url:
            raise ValueError(f"{self.type.title()} steps require a target_url value")

        return self


class FunnelConfig(BaseModel):
    """Reusable funnel configuration payload"""

    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Probability that a visit will execute this funnel (0-1)",
    )
    priority: int = Field(
        0,
        ge=0,
        description="Execution priority (lower values evaluated first)",
    )
    enabled: bool = Field(
        True,
        description="Whether the funnel is active",
    )
    exit_after_completion: bool = Field(
        True,
        description="Whether the visitor should return to random browsing after the funnel finishes",
    )
    steps: List[FunnelStep] = Field(
        ...,
        min_length=1,
        description="Ordered steps that define the funnel",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_config(self):
        if not self.steps:
            raise ValueError("Funnel must include at least one step")
        if self.steps[0].type != "pageview":
            raise ValueError("First funnel step must be a pageview")
        return self


class FunnelCreateRequest(FunnelConfig):
    """Request body for creating a funnel"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class FunnelUpdateRequest(BaseModel):
    """Request body for updating a funnel"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    priority: Optional[int] = Field(None, ge=0)
    enabled: Optional[bool] = None
    exit_after_completion: Optional[bool] = None
    steps: Optional[List[FunnelStep]] = Field(
        None, min_length=1, description="Replacement steps for the funnel"
    )

    model_config = ConfigDict(extra="forbid")


class FunnelSummary(BaseModel):
    """Summary entry for funnel listings"""

    id: int
    name: str
    description: Optional[str] = None
    probability: float
    priority: int
    enabled: bool
    step_count: int
    created_at: str
    updated_at: str


class FunnelListResponse(BaseModel):
    """Response for GET /api/funnels (summary list)"""

    funnels: List[FunnelSummary]


class FunnelResponse(BaseModel):
    """Detailed funnel response"""

    id: int
    name: str
    description: Optional[str] = None
    config: FunnelConfig
    created_at: str
    updated_at: str


class FunnelDeleteResponse(BaseModel):
    """Response for deleting a funnel"""

    success: bool
    deleted_id: int
    message: str
