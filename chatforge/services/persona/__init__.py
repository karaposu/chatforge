"""
Persona service for AI character behavior management.

This module provides structures for defining and controlling AI behavioral
parameters - how an AI responds regardless of what it knows or who it's
talking to.

Usage:
    from chatforge.services.persona import BehavioralParameters, ConversationalIntent

    params = BehavioralParameters(
        conversational_intent=ConversationalIntent.CONNECT,
        interaction_style="warm and empathetic",
        emotional_state="genuinely curious",
    )
"""

from chatforge.services.persona.behavioral_params import (
    BehavioralParameters,
    ConversationalIntent,
    EnergyDynamics,
    PowerDistribution,
    EngagementLevel,
    InterestLevel,
    behavioral_params_to_prompt,
)

__all__ = [
    "BehavioralParameters",
    "ConversationalIntent",
    "EnergyDynamics",
    "PowerDistribution",
    "EngagementLevel",
    "InterestLevel",
    "behavioral_params_to_prompt",
]
