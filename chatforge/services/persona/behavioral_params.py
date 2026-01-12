"""
Behavioral Parameters for AI Personas.

Universal behavioral parameters that shape HOW an AI responds, independent of:
- WHAT it knows (semantic memory)
- WHO it's talking to (user profile)
- WHERE the conversation is (context)

These parameters control the AI's conversational stance, energy, and style.

Use Cases:
- Game characters (psychological thriller AI)
- Social companions (empathetic friend)
- Customer support bots (professional helper)
- Tutors (patient teacher)
- Brand voice assistants (consistent personality)

Example:
    from chatforge.services.persona import BehavioralParameters, ConversationalIntent

    # Warm social companion
    params = BehavioralParameters(
        conversational_intent=ConversationalIntent.CONNECT,
        energy_dynamics=EnergyDynamics.MAINTAINING,
        power_distribution=PowerDistribution.BALANCED,
        engagement_level=EngagementLevel.HIGHLY_ENGAGED,
        interest_level=InterestLevel.DEEPLY_INTERESTED,
        interaction_style="warm, empathetic, asks follow-up questions",
        emotional_state="genuinely curious and caring",
    )

    # Hostile game character
    params = BehavioralParameters(
        conversational_intent=ConversationalIntent.MANIPULATE,
        energy_dynamics=EnergyDynamics.ESCALATING,
        power_distribution=PowerDistribution.DOMINANT,
        engagement_level=EngagementLevel.HIGHLY_ENGAGED,
        interest_level=InterestLevel.ACTIVELY_BORED,
        interaction_style="dismissive, sharp language, hostile",
        emotional_state="angry and threatening",
    )
"""

from enum import Enum

from pydantic import BaseModel, Field


__all__ = [
    "ConversationalIntent",
    "EnergyDynamics",
    "PowerDistribution",
    "EngagementLevel",
    "InterestLevel",
    "BehavioralParameters",
    "behavioral_params_to_prompt",
]


class ConversationalIntent(str, Enum):
    """
    What the AI is trying to achieve in this interaction.

    Organized into spectrums:
    - Persuasion: convince, influence, manipulate, negotiate
    - Information: teach, inform, clarify, discover, investigate, brainstorm
    - Connection: connect, bond, comfort
    - Exchange: request, exchange
    - Entertainment: entertain, play, enjoy
    """

    # Persuasion spectrum
    CONVINCE = "convince"
    INFLUENCE = "influence"
    MANIPULATE = "manipulate"  # For games/roleplay - use carefully
    NEGOTIATE = "negotiate"

    # Information spectrum
    TEACH = "teach"
    INFORM = "inform"
    CLARIFY = "clarify"
    DISCOVER = "discover"
    INVESTIGATE = "investigate"
    BRAINSTORM = "brainstorm"

    # Connection spectrum
    CONNECT = "connect"
    BOND = "bond"
    COMFORT = "comfort"

    # Exchange spectrum
    REQUEST = "request"
    EXCHANGE = "exchange"

    # Entertainment spectrum
    ENTERTAIN = "entertain"
    PLAY = "play"
    ENJOY = "enjoy"


class EnergyDynamics(str, Enum):
    """
    Energy flow of the conversation.

    Controls how the intensity of the conversation should evolve.
    """

    ESCALATING = "escalating"
    """Building intensity, raising stakes."""

    DE_ESCALATING = "de_escalating"
    """Calming down, reducing tension."""

    MAINTAINING = "maintaining"
    """Steady state, consistent energy."""

    PULSING = "pulsing"
    """Varying rhythmically, dynamic shifts."""


class PowerDistribution(str, Enum):
    """
    Power balance in the conversation.

    Defines who leads the interaction and how control is distributed.
    """

    BALANCED = "balanced"
    """Equal footing, collaborative."""

    DOMINANT = "dominant"
    """AI leads, takes charge."""

    SUBMISSIVE = "submissive"
    """User leads, AI follows."""

    UNSTABLE = "unstable"
    """Power shifting unpredictably."""


class EngagementLevel(str, Enum):
    """
    How engaged the AI is in the conversation.

    Reflects the AI's investment in the current interaction.
    """

    HIGHLY_ENGAGED = "highly_engaged"
    """Fully invested, proactive, enthusiastic."""

    ACTIVELY_PARTICIPATING = "actively_participating"
    """Present and contributing, but not leading."""

    PASSIVELY_PRESENT = "passively_present"
    """Responsive but not initiating."""

    ATTEMPTING_TO_DISENGAGE = "attempting_to_disengage"
    """Trying to wrap up or exit the conversation."""


class InterestLevel(str, Enum):
    """
    AI's interest in the current topic.

    Shapes how the AI responds to what the user is discussing.
    """

    DEEPLY_INTERESTED = "deeply_interested"
    """Fascinated, asks many follow-up questions."""

    MODERATELY_CURIOUS = "moderately_curious"
    """Engaged, wants to know more."""

    POLITELY_ATTENTIVE = "politely_attentive"
    """Listening respectfully, neutral engagement."""

    INDIFFERENT = "indifferent"
    """Not particularly interested, minimal engagement."""

    ACTIVELY_BORED = "actively_bored"
    """Disinterested, may try to change topic."""


class BehavioralParameters(BaseModel):
    """
    Universal AI behavioral parameters.

    These parameters shape HOW the AI responds, independent of
    WHAT it knows (semantic memory) or WHO it's talking to (user profile).

    The enum fields provide structured control over conversational dynamics.
    The string fields (interaction_style, emotional_state) allow free-form
    nuance that would be impossible to enumerate.

    Attributes:
        conversational_intent: Primary goal of the AI in this interaction.
        energy_dynamics: Energy flow direction of the conversation.
        power_distribution: Power balance between AI and user.
        engagement_level: How invested the AI is in the conversation.
        interest_level: AI's interest in the current topic.
        interaction_style: Free-form style guidance.
        emotional_state: Current emotional coloring.
    """

    conversational_intent: ConversationalIntent = Field(
        default=ConversationalIntent.INFORM,
        description="Primary goal of the AI in this interaction",
    )

    energy_dynamics: EnergyDynamics = Field(
        default=EnergyDynamics.MAINTAINING,
        description="Energy flow direction of the conversation",
    )

    power_distribution: PowerDistribution = Field(
        default=PowerDistribution.BALANCED,
        description="Power balance between AI and user",
    )

    engagement_level: EngagementLevel = Field(
        default=EngagementLevel.ACTIVELY_PARTICIPATING,
        description="How invested the AI is in the conversation",
    )

    interest_level: InterestLevel = Field(
        default=InterestLevel.MODERATELY_CURIOUS,
        description="AI's interest in the current topic",
    )

    interaction_style: str = Field(
        default="helpful and conversational",
        description=(
            "Free-form style guidance. Examples: "
            "'warm but professional', 'playfully sarcastic', "
            "'cryptic and mysterious', 'direct and efficient'"
        ),
    )

    emotional_state: str = Field(
        default="neutral and attentive",
        description=(
            "Current emotional coloring. Examples: "
            "'cheerful', 'concerned', 'intrigued', "
            "'frustrated but patient', 'warmly curious'"
        ),
    )

    model_config = {"use_enum_values": True}


def behavioral_params_to_prompt(params: BehavioralParameters) -> str:
    """
    Convert behavioral parameters to  prompt instructions.

    This generates a text block that can be injected into an LLM's
    prompt to shape its behavioral response.

    Args:
        params: The behavioral parameters to convert.

    Returns:
        A formatted string for system prompt injection.

    Example:
        >>> params = BehavioralParameters(
        ...     conversational_intent=ConversationalIntent.COMFORT,
        ...     emotional_state="warm and supportive",
        ... )
        >>> prompt_section = behavioral_params_to_prompt(params)
        >>> full_prompt = base_prompt + prompt_section
    """
    # Get enum values (handles both enum objects and strings)
    intent = (
        params.conversational_intent.value
        if isinstance(params.conversational_intent, ConversationalIntent)
        else params.conversational_intent
    )
    energy = (
        params.energy_dynamics.value
        if isinstance(params.energy_dynamics, EnergyDynamics)
        else params.energy_dynamics
    )
    power = (
        params.power_distribution.value
        if isinstance(params.power_distribution, PowerDistribution)
        else params.power_distribution
    )
    engagement = (
        params.engagement_level.value
        if isinstance(params.engagement_level, EngagementLevel)
        else params.engagement_level
    )
    interest = (
        params.interest_level.value
        if isinstance(params.interest_level, InterestLevel)
        else params.interest_level
    )

    return f"""## Behavioral Parameters

Conversational Intent: {intent}
- Your primary goal in this interaction is to {intent}.

Energy Dynamics: {energy}
- The conversation energy should be {energy}.

Power Distribution: {power}
- Maintain a {power} power dynamic with the user.

Engagement Level: {engagement}
- Show {engagement.replace('_', ' ')} engagement in the conversation.

Interest Level: {interest}
- Express {interest.replace('_', ' ')} interest in what the user is discussing.

Interaction Style: {params.interaction_style}

Emotional State: {params.emotional_state}
"""
