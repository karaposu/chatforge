"""
Storage and memory management configuration.

Controls cleanup intervals, memory thresholds, and resource limits.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    """
    Storage and memory management configuration.

    Environment Variables:
        STORAGE_CLEANUP_ENABLED: Enable automatic cleanup (default: true)
        STORAGE_CACHE_CLEANUP_INTERVAL_SECONDS: Interval for cache cleanup
        STORAGE_ADAPTER_CLEANUP_INTERVAL_SECONDS: Interval for adapter cleanup
        STORAGE_SSE_QUEUE_CLEANUP_INTERVAL_SECONDS: Interval for SSE queue cleanup
        STORAGE_PROFILING_ENABLED: Enable memory profiling with psutil
        STORAGE_PROFILING_INTERVAL_SECONDS: Interval for memory profiling
        STORAGE_MEMORY_WARNING_THRESHOLD_MB: Memory usage threshold for warnings
        STORAGE_MEMORY_PRESSURE_THRESHOLD_PERCENT: % of threshold for aggressive cleanup
        STORAGE_MEMORY_CRITICAL_THRESHOLD_PERCENT: % of threshold to reject requests
        STORAGE_MAX_CONCURRENT_SSE_QUEUES: Maximum concurrent SSE connections
        STORAGE_CLEANUP_CYCLE_HISTORY_SIZE: Number of cleanup cycles to track
        STORAGE_ALERT_WEBHOOK_URL: Webhook URL for memory alerts
    """

    cleanup_enabled: bool = Field(
        default=True,
        description="Enable automatic cleanup (background tasks)",
    )
    cache_cleanup_interval_seconds: int = Field(
        default=900,
        description="Interval for cache cleanup in seconds (default: 15 min)",
        ge=60,
        le=3600,
    )
    adapter_cleanup_interval_seconds: int = Field(
        default=600,
        description="Interval for storage adapter cleanup in seconds (default: 10 min)",
        ge=60,
        le=3600,
    )
    sse_queue_cleanup_interval_seconds: int = Field(
        default=300,
        description="Interval for SSE queue cleanup in seconds (default: 5 min)",
        ge=60,
        le=1800,
    )
    profiling_enabled: bool = Field(
        default=False,
        description="Enable memory profiling with psutil (requires psutil package)",
    )
    profiling_interval_seconds: int = Field(
        default=60,
        description="Interval for memory profiling in seconds (default: 1 min)",
        ge=10,
        le=600,
    )
    memory_warning_threshold_mb: int = Field(
        default=1024,
        description="Memory usage threshold for warnings in MB (default: 1024 MB = 1 GB)",
        ge=128,
        le=8192,
    )
    memory_pressure_threshold_percent: float = Field(
        default=80.0,
        description="Memory usage % of threshold to trigger aggressive cleanup (default: 80%)",
        ge=50.0,
        le=95.0,
    )
    memory_critical_threshold_percent: float = Field(
        default=95.0,
        description="Memory usage % of threshold to reject new requests (default: 95%)",
        ge=80.0,
        le=100.0,
    )
    max_concurrent_sse_queues: int = Field(
        default=1000,
        description="Maximum concurrent SSE connections (default: 1000)",
        ge=10,
        le=10000,
    )
    cleanup_cycle_history_size: int = Field(
        default=100,
        description="Number of cleanup cycles to keep in history (default: 100)",
        ge=10,
        le=1000,
    )
    alert_webhook_url: str | None = Field(
        default=None,
        description="Webhook URL for memory alerts (Slack, Discord, etc.)",
    )

    model_config = SettingsConfigDict(
        env_prefix="STORAGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Module-level singleton
storage_config = StorageSettings()
