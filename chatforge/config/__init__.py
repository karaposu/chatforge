"""
Chatforge Configuration - Settings for LLM, agent, guardrails, and storage.

All configuration is loaded from environment variables with sensible defaults.
Each module provides both a Settings class (for custom instances) and a
pre-configured singleton (for convenience).
"""

from chatforge.config.agent import AgentSettings, agent_config
from chatforge.config.guardrails import GuardrailsSettings, guardrails_config
from chatforge.config.llm import LLMSettings, llm_config
from chatforge.config.storage import StorageSettings, storage_config

__all__ = [
    # LLM
    "LLMSettings",
    "llm_config",
    # Agent
    "AgentSettings",
    "agent_config",
    # Guardrails
    "GuardrailsSettings",
    "guardrails_config",
    # Storage
    "StorageSettings",
    "storage_config",
]
