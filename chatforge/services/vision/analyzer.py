"""
Image Analyzer Service - Vision LLM integration for image analysis.

This service handles image analysis using vision-capable LLMs.
It provides a generic interface that can be used with any image source.

Features:
- Supports multiple vision LLMs (OpenAI GPT-4o, Anthropic Claude)
- Configurable analysis prompts
- Batch analysis with optional parallelism
- Pluggable caching via callable

Usage:
    from chatforge.services.vision import ImageAnalyzer, ImageInfo

    analyzer = ImageAnalyzer(
        llm=get_vision_llm(),
        system_prompt="Analyze this image...",
    )

    result = await analyzer.analyze_image(
        ImageInfo(
            file_id="123",
            filename="screenshot.png",
            data_uri="data:image/png;base64,...",
        )
    )
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Protocol

from langchain_core.messages import HumanMessage, SystemMessage


if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel


logger = logging.getLogger(__name__)


# Default system prompt for image analysis
DEFAULT_ANALYSIS_PROMPT = """You are an AI assistant analyzing an image.

Describe what you see in the image, including:
1. Main subject or content
2. Any visible text or error messages
3. UI elements and their state (if applicable)
4. Any notable details that might be relevant

Be concise but thorough. Focus on factual observations."""


@dataclass
class ImageInfo:
    """
    Information about an image to analyze.

    Attributes:
        file_id: Unique identifier for the image
        filename: Original filename
        data_uri: Base64 data URI (data:image/png;base64,...)
                  OR a URL accessible by the vision LLM
        mimetype: MIME type (e.g., image/png, image/jpeg)
        metadata: Optional additional metadata
    """

    file_id: str
    filename: str
    data_uri: str
    mimetype: str = "image/png"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_base64(self) -> bool:
        """Check if data_uri is a base64 data URI."""
        return self.data_uri.startswith("data:")


@dataclass
class AnalysisResult:
    """
    Result of an image analysis.

    Attributes:
        file_id: Image file ID
        filename: Original filename
        analysis: Analysis text from vision LLM
        from_cache: Whether this result came from cache
        error: Error message if analysis failed
        metadata: Additional result metadata
    """

    file_id: str
    filename: str
    analysis: str
    from_cache: bool = False
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if analysis was successful."""
        return self.error is None and bool(self.analysis)


class CacheProtocol(Protocol):
    """Protocol for cache implementations."""

    def get(self, key: str) -> str | None:
        """Get cached analysis by key."""
        ...

    def set(self, key: str, value: str) -> None:
        """Store analysis in cache."""
        ...


class ImageAnalyzer:
    """
    Service for analyzing images with vision-capable LLMs.

    This service provides:
    - Single and batch image analysis
    - Configurable system prompt
    - Optional caching via pluggable cache
    - Parallel analysis with configurable concurrency

    Example:
        from chatforge.services.llm import get_vision_llm

        analyzer = ImageAnalyzer(
            llm=get_vision_llm(),
            system_prompt="Describe any errors shown in this screenshot.",
        )

        # Analyze single image
        result = await analyzer.analyze_image(image_info)

        # Batch analysis
        results = await analyzer.analyze_batch(
            images=[img1, img2, img3],
            parallel=True,
            max_concurrent=3,
        )
    """

    def __init__(
        self,
        llm: BaseChatModel,
        system_prompt: str | None = None,
        cache: CacheProtocol | None = None,
        cache_key_fn: Callable[[ImageInfo], str] | None = None,
    ):
        """
        Initialize the image analyzer.

        Args:
            llm: Vision-capable LLM (must support image inputs)
            system_prompt: Custom system prompt for analysis
            cache: Optional cache implementation for storing results
            cache_key_fn: Function to generate cache keys from ImageInfo.
                         Default: uses file_id
        """
        self.llm = llm
        self.system_prompt = system_prompt or DEFAULT_ANALYSIS_PROMPT
        self.cache = cache
        self.cache_key_fn = cache_key_fn or (lambda img: img.file_id)

        logger.debug(
            f"ImageAnalyzer initialized with cache={'enabled' if cache else 'disabled'}"
        )

    async def analyze_image(
        self,
        image: ImageInfo,
        prompt: str | None = None,
        use_cache: bool = True,
    ) -> AnalysisResult:
        """
        Analyze a single image using the vision LLM.

        Args:
            image: ImageInfo with data_uri or URL
            prompt: Optional custom prompt for this specific analysis
            use_cache: Whether to check/store in cache

        Returns:
            AnalysisResult with analysis or error
        """
        # Check cache first
        if use_cache and self.cache:
            cache_key = self.cache_key_fn(image)
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {image.filename}")
                return AnalysisResult(
                    file_id=image.file_id,
                    filename=image.filename,
                    analysis=cached,
                    from_cache=True,
                )

        try:
            logger.info(f"Analyzing image: {image.filename}")

            # Build messages
            system_msg = SystemMessage(content=self.system_prompt)

            # Build user message with image
            user_content = []
            if prompt:
                user_content.append({"type": "text", "text": prompt})
            else:
                user_content.append(
                    {
                        "type": "text",
                        "text": f"Analyze this image (filename: {image.filename}):",
                    }
                )

            user_content.append(
                {"type": "image_url", "image_url": {"url": image.data_uri}}
            )

            human_msg = HumanMessage(content=user_content)

            # Invoke LLM
            response = await self.llm.ainvoke([system_msg, human_msg])
            analysis = str(response.content)

            logger.info(f"Analysis complete for {image.filename}: {len(analysis)} chars")

            # Store in cache
            if use_cache and self.cache:
                cache_key = self.cache_key_fn(image)
                self.cache.set(cache_key, analysis)

            return AnalysisResult(
                file_id=image.file_id,
                filename=image.filename,
                analysis=analysis,
                from_cache=False,
            )

        except Exception as e:
            logger.error(f"Error analyzing {image.filename}: {e}", exc_info=True)
            return AnalysisResult(
                file_id=image.file_id,
                filename=image.filename,
                analysis="",
                error=str(e),
            )

    async def analyze_batch(
        self,
        images: list[ImageInfo],
        parallel: bool = False,
        max_concurrent: int = 3,
        max_images: int | None = None,
        prompt: str | None = None,
        use_cache: bool = True,
    ) -> list[AnalysisResult]:
        """
        Analyze multiple images.

        Args:
            images: List of images to analyze
            parallel: Whether to analyze in parallel
            max_concurrent: Max concurrent analyses when parallel
            max_images: Optional limit on number of images (takes most recent)
            prompt: Optional custom prompt for all images
            use_cache: Whether to use cache

        Returns:
            List of AnalysisResult in same order as input
        """
        if not images:
            return []

        # Limit images if specified
        if max_images and len(images) > max_images:
            logger.info(
                f"Limiting to {max_images} most recent images (total: {len(images)})"
            )
            images = images[-max_images:]

        if parallel and len(images) > 1:
            return await self._analyze_parallel(
                images, max_concurrent, prompt, use_cache
            )
        else:
            return await self._analyze_sequential(images, prompt, use_cache)

    async def _analyze_sequential(
        self,
        images: list[ImageInfo],
        prompt: str | None,
        use_cache: bool,
    ) -> list[AnalysisResult]:
        """Analyze images one at a time."""
        results = []
        for image in images:
            result = await self.analyze_image(image, prompt, use_cache)
            results.append(result)
        return results

    async def _analyze_parallel(
        self,
        images: list[ImageInfo],
        max_concurrent: int,
        prompt: str | None,
        use_cache: bool,
    ) -> list[AnalysisResult]:
        """Analyze images in parallel with semaphore limiting."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_limit(image: ImageInfo) -> AnalysisResult:
            async with semaphore:
                return await self.analyze_image(image, prompt, use_cache)

        logger.info(
            f"Starting parallel analysis of {len(images)} images "
            f"(max concurrent: {max_concurrent})"
        )

        results = await asyncio.gather(
            *[analyze_with_limit(img) for img in images]
        )

        return list(results)


def format_analysis_results(results: list[AnalysisResult]) -> str:
    """
    Format analysis results as context text.

    Creates a structured text block that can be used as context
    for an AI agent or displayed to users.

    Args:
        results: List of AnalysisResult objects

    Returns:
        Formatted context string

    Example output:
        **IMAGE ANALYSIS:**

        **Image 1: screenshot.png**
        [Analysis text here...]

        **Image 2: error.png**
        [Analysis text here...]
    """
    if not results:
        return ""

    successful = [r for r in results if r.is_success]
    if not successful:
        return ""

    lines = [
        "**IMAGE ANALYSIS:**",
        "",
    ]

    for i, result in enumerate(successful, 1):
        cache_indicator = " (cached)" if result.from_cache else ""
        lines.append(f"**Image {i}: {result.filename}**{cache_indicator}")
        lines.append(result.analysis)
        lines.append("")

    return "\n".join(lines)
