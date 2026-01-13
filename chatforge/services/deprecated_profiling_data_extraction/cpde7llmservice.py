"""
CPDE-7 LLM Service - Extracts profiling data using LLM structured output.

This service connects batch prompts with Pydantic models and the LLM factory
to extract profiling data from batches of messages.

All extraction methods are async for better concurrency and integration
with async web frameworks and the async StoragePort.

Usage:
    from chatforge.services.profiling_data_extraction.cpde7llmservice import CPDE7LLMService

    service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")

    # Extract single dimension
    result = await service.extract_core_identity(messages_text)

    # Extract all dimensions (sequential)
    results = await service.extract_all(messages_text)

    # Extract all dimensions (parallel)
    results = await service.extract_all(messages_text, parallel=True)
"""

import asyncio
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from chatforge.services.llm.factory import get_llm
from chatforge.services.profiling_data_extraction.batch_prompts import (
    CPDE_CORE_IDENTITY_BATCH,
    CPDE_OPINIONS_VIEWS_BATCH,
    CPDE_PREFERENCES_PATTERNS_BATCH,
    CPDE_DESIRES_NEEDS_BATCH,
    CPDE_LIFE_NARRATIVE_BATCH,
    CPDE_EVENTS_BATCH,
    CPDE_ENTITIES_RELATIONSHIPS_BATCH,
    CPDE_ALL_7_BATCH,
)
from chatforge.services.profiling_data_extraction.models import (
    # Batch output models
    BatchCoreIdentityOutput,
    BatchOpinionsOutput,
    BatchPreferencesOutput,
    BatchDesiresOutput,
    BatchNarrativeOutput,
    BatchEventsOutput,
    BatchEntitiesOutput,
    # Combined result
    BatchProfilingDataExtractionResult,
    BatchAll7Output,
)
from chatforge.services.profiling_data_extraction.prompts import (
    build_prompt,
    build_output_model,
    DIMENSION_NAMES,
)


class CPDE7LLMService:
    """
    Service for extracting CPDE-7 profiling data using LLM structured output.

    Each extraction method:
    1. Formats the prompt with the provided messages
    2. Calls the LLM with structured output (async)
    3. Returns a typed Pydantic model

    Args:
        provider: LLM provider ('openai', 'anthropic', 'bedrock')
        model_name: Model to use (e.g., 'gpt-4o-mini', 'claude-3-5-sonnet-latest')
        temperature: LLM temperature (default 0 for deterministic extraction)

    Example:
        service = CPDE7LLMService(provider="openai", model_name="gpt-4o-mini")

        messages = '''
        Message ID: msg_001
        Content: I'm a 34-year-old software engineer.
        '''

        result = await service.extract_core_identity(messages)
        # result.core_identity.has_content == True
        # result.core_identity.items[0].aspect == "age"
    """

    def __init__(
        self,
        provider: str = "openai",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0,
    ):
        self._provider = provider
        self._model_name = model_name
        self._temperature = temperature
        self._llm: BaseChatModel | None = None

    def _get_llm(self) -> BaseChatModel:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = get_llm(
                provider=self._provider,
                model_name=self._model_name,
                temperature=self._temperature,
            )
        return self._llm

    @property
    def model_info(self) -> str:
        """Return model identifier for logging/tracking."""
        return f"{self._provider}/{self._model_name}"

    # =========================================================================
    # Individual Dimension Extraction Methods (Async)
    # =========================================================================

    async def extract_core_identity(self, messages: str) -> BatchCoreIdentityOutput:
        """
        Extract core identity facts from messages.

        Core identity includes: age, profession, location, physical attributes,
        roles, affiliations, conditions, personality traits.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchCoreIdentityOutput with core_identity.items
        """
        prompt = CPDE_CORE_IDENTITY_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchCoreIdentityOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_opinions_views(self, messages: str) -> BatchOpinionsOutput:
        """
        Extract non-ephemeral opinions and views from messages.

        Opinions include: beliefs, worldviews, values, persistent stances.
        Excludes: momentary reactions, preferences, desires.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchOpinionsOutput with opinions_views.items
        """
        prompt = CPDE_OPINIONS_VIEWS_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchOpinionsOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_preferences_patterns(self, messages: str) -> BatchPreferencesOutput:
        """
        Extract stable preferences and behavioral patterns from messages.

        Preferences include: work habits, communication styles, routines,
        recurring choices, behavioral tendencies.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchPreferencesOutput with preferences_patterns.items
        """
        prompt = CPDE_PREFERENCES_PATTERNS_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchPreferencesOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_desires_needs(self, messages: str) -> BatchDesiresOutput:
        """
        Extract desires, wishes, hopes, and needs from messages.

        Includes: wants, goals, aspirations, motivations, needs.
        Tracks: type (need/want/wish/hope), intensity, temporal aspects.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchDesiresOutput with desires_needs.items
        """
        prompt = CPDE_DESIRES_NEEDS_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchDesiresOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_life_narrative(self, messages: str) -> BatchNarrativeOutput:
        """
        Extract life narrative elements from messages.

        Narrative includes: biographical facts, formative experiences,
        life transitions, personal history.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchNarrativeOutput with life_narrative.items
        """
        prompt = CPDE_LIFE_NARRATIVE_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchNarrativeOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_events(self, messages: str) -> BatchEventsOutput:
        """
        Extract significant events and involvements from messages.

        Events include: current activities, upcoming events, ongoing situations,
        recent occurrences. Tracks involvement and people involved.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchEventsOutput with events.items
        """
        prompt = CPDE_EVENTS_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchEventsOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_entities_relationships(self, messages: str) -> BatchEntitiesOutput:
        """
        Extract entities and relationships from messages.

        Entities include: people, organizations, places, products, pets.
        Tracks: relationship indicators, interaction metadata.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchEntitiesOutput with entities_relationships.items
        """
        prompt = CPDE_ENTITIES_RELATIONSHIPS_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchEntitiesOutput)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    # =========================================================================
    # Combined Extraction
    # =========================================================================

    async def extract_all_7(self, messages: str) -> BatchAll7Output:
        """
        Extract all 7 dimensions in a single LLM call.

        This method uses a single prompt to extract all dimensions at once,
        which is more efficient than calling each dimension separately but
        may be less accurate for complex messages.

        Args:
            messages: Formatted message text with Message ID and Content

        Returns:
            BatchAll7Output with all 7 dimensions populated.
            Empty dimensions will have has_content=false and items=[].

        Example:
            result = await service.extract_all_7(messages)
            print(result.core_identity.items)
            print(result.events.items)
        """
        prompt = CPDE_ALL_7_BATCH.format(messages=messages)
        structured_llm = self._get_llm().with_structured_output(BatchAll7Output)
        return await structured_llm.ainvoke([HumanMessage(content=prompt)])

    async def extract_all(
        self,
        messages: str,
        dimensions: list[str] | None = None,
        parallel: bool = False,
    ) -> BatchProfilingDataExtractionResult:
        """
        Extract all (or selected) dimensions from messages.

        Args:
            messages: Formatted message text with Message ID and Content
            dimensions: Optional list of dimensions to extract. If None, extracts all.
                       Valid values: core_identity, opinions_views, preferences_patterns,
                       desires_needs, life_narrative, events, entities_relationships
            parallel: If True, extract all dimensions concurrently using asyncio.gather().
                     If False (default), extract sequentially.

        Returns:
            BatchProfilingDataExtractionResult with all extracted dimensions
        """
        all_dimensions = [
            "core_identity",
            "opinions_views",
            "preferences_patterns",
            "desires_needs",
            "life_narrative",
            "events",
            "entities_relationships",
        ]

        if dimensions is None:
            dimensions = all_dimensions

        result = BatchProfilingDataExtractionResult()

        if parallel:
            # Run all extractions concurrently
            tasks = []
            task_dims = []

            if "core_identity" in dimensions:
                tasks.append(self.extract_core_identity(messages))
                task_dims.append("core_identity")
            if "opinions_views" in dimensions:
                tasks.append(self.extract_opinions_views(messages))
                task_dims.append("opinions_views")
            if "preferences_patterns" in dimensions:
                tasks.append(self.extract_preferences_patterns(messages))
                task_dims.append("preferences_patterns")
            if "desires_needs" in dimensions:
                tasks.append(self.extract_desires_needs(messages))
                task_dims.append("desires_needs")
            if "life_narrative" in dimensions:
                tasks.append(self.extract_life_narrative(messages))
                task_dims.append("life_narrative")
            if "events" in dimensions:
                tasks.append(self.extract_events(messages))
                task_dims.append("events")
            if "entities_relationships" in dimensions:
                tasks.append(self.extract_entities_relationships(messages))
                task_dims.append("entities_relationships")

            # Execute all tasks concurrently
            outputs = await asyncio.gather(*tasks)

            # Map outputs to result
            for dim, output in zip(task_dims, outputs):
                if dim == "core_identity":
                    result.core_identity = output.core_identity
                elif dim == "opinions_views":
                    result.opinions_views = output.opinions_views
                elif dim == "preferences_patterns":
                    result.preferences_patterns = output.preferences_patterns
                elif dim == "desires_needs":
                    result.desires_needs = output.desires_needs
                elif dim == "life_narrative":
                    result.life_narrative = output.life_narrative
                elif dim == "events":
                    result.events = output.events
                elif dim == "entities_relationships":
                    result.entities_relationships = output.entities_relationships
        else:
            # Sequential extraction
            if "core_identity" in dimensions:
                output = await self.extract_core_identity(messages)
                result.core_identity = output.core_identity

            if "opinions_views" in dimensions:
                output = await self.extract_opinions_views(messages)
                result.opinions_views = output.opinions_views

            if "preferences_patterns" in dimensions:
                output = await self.extract_preferences_patterns(messages)
                result.preferences_patterns = output.preferences_patterns

            if "desires_needs" in dimensions:
                output = await self.extract_desires_needs(messages)
                result.desires_needs = output.desires_needs

            if "life_narrative" in dimensions:
                output = await self.extract_life_narrative(messages)
                result.life_narrative = output.life_narrative

            if "events" in dimensions:
                output = await self.extract_events(messages)
                result.events = output.events

            if "entities_relationships" in dimensions:
                output = await self.extract_entities_relationships(messages)
                result.entities_relationships = output.entities_relationships

        return result

    # =========================================================================
    # Extraction by Dimension Name
    # =========================================================================

    async def extract_dimension(
        self,
        messages: str,
        dimension: str,
    ) -> (
        BatchCoreIdentityOutput |
        BatchOpinionsOutput |
        BatchPreferencesOutput |
        BatchDesiresOutput |
        BatchNarrativeOutput |
        BatchEventsOutput |
        BatchEntitiesOutput
    ):
        """
        Extract a single dimension by name.

        Args:
            messages: Formatted message text
            dimension: Dimension name (e.g., 'core_identity', 'events')

        Returns:
            The appropriate BatchOutput model for that dimension

        Raises:
            ValueError: If dimension name is invalid
        """
        extractors = {
            "core_identity": self.extract_core_identity,
            "opinions_views": self.extract_opinions_views,
            "preferences_patterns": self.extract_preferences_patterns,
            "desires_needs": self.extract_desires_needs,
            "life_narrative": self.extract_life_narrative,
            "events": self.extract_events,
            "entities_relationships": self.extract_entities_relationships,
        }

        if dimension not in extractors:
            raise ValueError(
                f"Invalid dimension: {dimension}. "
                f"Valid dimensions: {list(extractors.keys())}"
            )

        return await extractors[dimension](messages)

    # =========================================================================
    # Configurable Dimension Extraction
    # =========================================================================

    async def _extract_per_dimension(
        self,
        messages: str,
        dimensions: list[str],
        parallel: bool = False
    ) -> BatchProfilingDataExtractionResult:
        """
        Extract dimensions with separate LLM call per dimension.

        Args:
            messages: Formatted message text
            dimensions: List of dimensions to extract
            parallel: Run calls in parallel if True

        Returns:
            BatchProfilingDataExtractionResult with requested dimensions populated
        """
        pde_result = BatchProfilingDataExtractionResult()

        if parallel:
            tasks = [self.extract_dimension(messages, dim) for dim in dimensions]
            outputs = await asyncio.gather(*tasks)
            for dim, output in zip(dimensions, outputs):
                inner = getattr(output, dim)
                setattr(pde_result, dim, inner)
        else:
            for dim in dimensions:
                output = await self.extract_dimension(messages, dim)
                inner = getattr(output, dim)
                setattr(pde_result, dim, inner)

        return pde_result

    async def _extract_combined(
        self,
        messages: str,
        dimensions: list[str]
    ) -> BatchProfilingDataExtractionResult:
        """
        Extract dimensions with single LLM call using combined prompt.

        Uses Proteas to build a prompt with only the requested dimensions.

        Args:
            messages: Formatted message text
            dimensions: List of dimensions to extract

        Returns:
            BatchProfilingDataExtractionResult with requested dimensions populated
        """
        # Build prompt with Proteas
        prompt = build_prompt(dimensions=dimensions, messages=messages)

        # Create dynamic model for LLM response
        output_model = build_output_model(dimensions)

        # Single LLM call
        structured_llm = self._get_llm().with_structured_output(output_model)
        llm_response = await structured_llm.ainvoke([HumanMessage(content=prompt)])

        # Map to BatchProfilingDataExtractionResult
        pde_result = BatchProfilingDataExtractionResult()
        for dim in dimensions:
            setattr(pde_result, dim, getattr(llm_response, dim))

        return pde_result

    async def extract_dimensions(
        self,
        messages: str,
        dimensions: list[str],
        strategy: Literal["per_dimension", "combined"] = "combined",
        parallel: bool = False
    ) -> BatchProfilingDataExtractionResult:
        """
        Extract selected dimensions using specified strategy.

        Args:
            messages: Formatted message text with Message ID and Content
            dimensions: List of dimensions to extract (at least one required)
            strategy:
                - "per_dimension": Separate LLM call per dimension
                - "combined": Single LLM call with combined prompt (uses Proteas)
            parallel: Run per-dimension calls in parallel (only for "per_dimension")

        Returns:
            BatchProfilingDataExtractionResult with requested dimensions populated,
            non-requested dimensions are None.

        Raises:
            ValueError: If dimensions is empty or contains invalid dimension names.

        Example:
            pde_result = await service.extract_dimensions(
                messages=messages,
                dimensions=["core_identity", "events"],
                strategy="combined"
            )

            if pde_result.core_identity is not None:
                print(pde_result.core_identity.items)
        """
        # Validate dimensions not empty
        if not dimensions:
            raise ValueError("At least one dimension must be specified")

        # Validate dimension names
        for dim in dimensions:
            if dim not in DIMENSION_NAMES:
                raise ValueError(f"Invalid dimension: {dim}. Valid: {DIMENSION_NAMES}")

        # Special case: all 7 dimensions with combined strategy
        # Use existing optimized extract_all_7()
        if strategy == "combined" and set(dimensions) == set(DIMENSION_NAMES):
            all_7_result = await self.extract_all_7(messages)
            # Convert BatchAll7Output to BatchProfilingDataExtractionResult
            pde_result = BatchProfilingDataExtractionResult(
                core_identity=all_7_result.core_identity,
                opinions_views=all_7_result.opinions_views,
                preferences_patterns=all_7_result.preferences_patterns,
                desires_needs=all_7_result.desires_needs,
                life_narrative=all_7_result.life_narrative,
                events=all_7_result.events,
                entities_relationships=all_7_result.entities_relationships,
            )
            return pde_result

        # Route to appropriate strategy
        if strategy == "per_dimension":
            return await self._extract_per_dimension(messages, dimensions, parallel)
        else:
            return await self._extract_combined(messages, dimensions)
