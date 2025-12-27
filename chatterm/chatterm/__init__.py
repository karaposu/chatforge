"""
ChatTerm - Text-based CLI for testing Chatforge

A consumer application that uses Chatforge components to provide
an interactive testing experience.
"""

from .settings import (
    ChatTermSettings,
    ChatMode,
    DisplaySettings,
    BehaviorSettings,
    MiddlewareSettings,
    LLMSettings,
    AgentSettings,
    create_settings,
    create_debug_settings,
    create_minimal_settings,
)
from .app import ChatTermApp, create_app
from .display import Display
from .commands import CommandHandler
from .logger import SimpleLogger, logger, setup_logging
from .menu import ChatTermMenu, MenuState, MenuItem
from .launcher import launch_chatterm

__version__ = "0.1.0"
__all__ = [
    # App
    "ChatTermApp",
    "create_app",
    # Settings
    "ChatTermSettings",
    "ChatMode",
    "DisplaySettings",
    "BehaviorSettings",
    "MiddlewareSettings",
    "LLMSettings",
    "AgentSettings",
    "create_settings",
    "create_debug_settings",
    "create_minimal_settings",
    # Display
    "Display",
    # Commands
    "CommandHandler",
    # Logger
    "SimpleLogger",
    "logger",
    "setup_logging",
    # Menu
    "ChatTermMenu",
    "MenuState",
    "MenuItem",
    # Launcher
    "launch_chatterm",
    # Version
    "__version__",
]
