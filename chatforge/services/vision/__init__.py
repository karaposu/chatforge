"""
Chatforge Vision Services - Image analysis with vision LLMs.

Provides image analysis capabilities using vision-capable LLMs
like GPT-4o and Claude 3.5 Sonnet.

Usage:
    from chatforge.services.vision import ImageAnalyzer, ImageInfo
    from chatforge.services.llm import get_vision_llm

    # Create analyzer
    analyzer = ImageAnalyzer(
        llm=get_vision_llm(),
        system_prompt="Describe any errors in this screenshot.",
    )

    # Analyze single image
    result = await analyzer.analyze_image(
        ImageInfo(
            file_id="123",
            filename="screenshot.png",
            data_uri="data:image/png;base64,...",
        )
    )

    # Batch analysis with parallelism
    results = await analyzer.analyze_batch(
        images=[img1, img2, img3],
        parallel=True,
        max_concurrent=3,
    )
"""

from chatforge.services.vision.analyzer import (
    AnalysisResult,
    CacheProtocol,
    DEFAULT_ANALYSIS_PROMPT,
    ImageAnalyzer,
    ImageInfo,
    format_analysis_results,
)

__all__ = [
    "ImageAnalyzer",
    "ImageInfo",
    "AnalysisResult",
    "CacheProtocol",
    "DEFAULT_ANALYSIS_PROMPT",
    "format_analysis_results",
]
