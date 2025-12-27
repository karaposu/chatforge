"""
ChatTerm Settings - Configuration for the chat terminal

Simple dataclasses for configuring ChatTerm behavior.
Simplified from VoxTerm - no audio/voice settings.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ChatMode(Enum):
    """Chat processing modes"""
    SIMPLE = "simple"   # Direct LLM calls
    AGENT = "agent"     # ReActAgent with tools


@dataclass
class DisplaySettings:
    """Display configuration"""
    # Timestamps
    show_timestamp: bool = True
    timestamp_format: str = "%H:%M:%S"

    # Output formatting
    color_output: bool = True
    markdown_rendering: bool = True

    # Status display
    show_token_count: bool = False
    show_latency: bool = False


@dataclass
class BehaviorSettings:
    """Behavior configuration"""
    # Debug mode
    debug_mode: bool = False

    # Auto-actions
    auto_clear_on_exit: bool = False

    # Interaction behavior
    confirm_before_quit: bool = False
    show_welcome_message: bool = True

    # Error handling
    show_error_details: bool = True


@dataclass
class MiddlewareSettings:
    """Middleware configuration"""
    # Enabled middleware list
    enabled: list[str] = field(default_factory=list)

    # Show middleware actions in debug mode
    show_actions: bool = True

    # Individual middleware options
    pii_mask_char: str = "*"
    safety_block_message: str = "Content blocked by safety filter"


@dataclass
class LLMSettings:
    """LLM configuration"""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


@dataclass
class AgentSettings:
    """Agent configuration"""
    # Tools to enable (by name)
    tools: list[str] = field(default_factory=list)

    # Agent behavior
    max_iterations: int = 10
    show_tool_calls: bool = True
    show_trace: bool = False


@dataclass
class ChatTermSettings:
    """Complete ChatTerm configuration"""
    # Components
    display: DisplaySettings = field(default_factory=DisplaySettings)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)
    middleware: MiddlewareSettings = field(default_factory=MiddlewareSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)
    agent: AgentSettings = field(default_factory=AgentSettings)

    # Mode
    mode: ChatMode = ChatMode.SIMPLE

    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = False
    log_file_path: Optional[str] = None

    # Interactive mode (menu vs direct)
    interactive: bool = True


# Default settings instance
DEFAULT_SETTINGS = ChatTermSettings()


def create_settings(**kwargs) -> ChatTermSettings:
    """Create settings with overrides"""
    settings = ChatTermSettings()

    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    return settings


def create_debug_settings() -> ChatTermSettings:
    """Create settings for debugging"""
    settings = ChatTermSettings()
    settings.log_level = LogLevel.DEBUG
    settings.behavior.debug_mode = True
    settings.display.show_latency = True
    settings.display.show_token_count = True
    settings.middleware.show_actions = True
    settings.agent.show_tool_calls = True
    settings.agent.show_trace = True
    return settings


def create_minimal_settings() -> ChatTermSettings:
    """Create minimal settings (no visual fluff)"""
    settings = ChatTermSettings()
    settings.display.show_timestamp = False
    settings.display.color_output = False
    settings.display.markdown_rendering = False
    settings.behavior.show_welcome_message = False
    return settings
