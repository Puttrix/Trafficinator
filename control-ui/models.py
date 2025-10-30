"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List


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
