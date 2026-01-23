"""
Perception Service

Analyzes visual images using Vision LLM and extracts semantic understanding.
"""

import base64
import json
import re
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from chatforge.services.perception.models import AnalysisResult, Issue, Reference


class PerceptionService:
    """
    Service for analyzing images using Vision LLM.

    Takes target images and optional reference images, sends them to a
    vision-capable LLM with an analysis prompt, and returns structured feedback.
    """

    def __init__(self, vision_llm: BaseChatModel):
        """
        Initialize the service.

        Args:
            vision_llm: A vision-capable LangChain chat model
        """
        self._llm = vision_llm

    def analyze(
        self,
        images: list[bytes],
        prompt: str,
        references: Optional[list[Reference]] = None,
    ) -> AnalysisResult:
        """
        Analyze images using Vision LLM.

        Args:
            images: Target images to analyze (as bytes)
            prompt: What to look for / analyze
            references: Optional reference images to compare against,
                        each with optional description text

        Returns:
            Structured analysis result with issues and satisfaction status
        """
        # Build the message content
        content = self._build_message_content(images, prompt, references)

        # Create messages
        system_message = SystemMessage(content=self._get_system_prompt())
        human_message = HumanMessage(content=content)

        # Invoke LLM
        response = self._llm.invoke([system_message, human_message])
        raw_response = response.content

        # Parse response
        return self._parse_response(raw_response)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for analysis."""
        return """You are a visual analysis expert. Your job is to analyze images and identify issues based on the given criteria.

When analyzing, you must respond in the following JSON format:
{
    "satisfied": true/false,
    "summary": "Brief overall assessment",
    "issues": [
        {
            "location": "Where the issue is (e.g., 'slide 0', 'top-left region', 'shape at center')",
            "description": "What the issue is",
            "severity": "low/medium/high",
            "suggestion": "How to fix it (optional)"
        }
    ]
}

If there are no issues and everything looks good, set "satisfied" to true and leave "issues" as an empty array.
Always respond with valid JSON only, no additional text."""

    def _build_message_content(
        self,
        images: list[bytes],
        prompt: str,
        references: Optional[list[Reference]] = None,
    ) -> list[dict]:
        """Build the message content with images and text."""
        content = []

        # Add reference images first (if any)
        if references:
            content.append({
                "type": "text",
                "text": "=== REFERENCE IMAGES ===\nUse these as reference for comparison:"
            })
            for i, ref in enumerate(references):
                # Add reference image
                content.append(self._image_to_content(ref.image))
                # Add reference description
                ref_text = ref.text or f"Reference image {i + 1}"
                content.append({
                    "type": "text",
                    "text": f"[Reference {i + 1}]: {ref_text}"
                })

        # Add target images
        content.append({
            "type": "text",
            "text": "=== TARGET IMAGES TO ANALYZE ===" if references else "=== IMAGES TO ANALYZE ==="
        })
        for i, image in enumerate(images):
            content.append(self._image_to_content(image))
            content.append({
                "type": "text",
                "text": f"[Image {i + 1}]"
            })

        # Add the analysis prompt
        content.append({
            "type": "text",
            "text": f"\n=== ANALYSIS TASK ===\n{prompt}"
        })

        return content

    def _image_to_content(self, image_bytes: bytes) -> dict:
        """Convert image bytes to LangChain message content format."""
        # Detect image type from magic bytes
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            media_type = "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            media_type = "image/jpeg"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            media_type = "image/gif"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            media_type = "image/webp"
        else:
            media_type = "image/png"  # Default to PNG

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{media_type};base64,{b64_image}"
            }
        }

    def _parse_response(self, raw_response: str) -> AnalysisResult:
        """Parse LLM response into AnalysisResult."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(raw_response)

            issues = [
                Issue(
                    location=issue.get("location", "unknown"),
                    description=issue.get("description", ""),
                    severity=issue.get("severity", "medium"),
                    suggestion=issue.get("suggestion"),
                )
                for issue in data.get("issues", [])
            ]

            return AnalysisResult(
                satisfied=data.get("satisfied", len(issues) == 0),
                issues=issues,
                summary=data.get("summary", ""),
                raw_response=raw_response,
            )

        except (json.JSONDecodeError, KeyError) as e:
            # If parsing fails, create a result indicating failure
            return AnalysisResult(
                satisfied=False,
                issues=[
                    Issue(
                        location="response",
                        description=f"Failed to parse LLM response: {e}",
                        severity="high",
                    )
                ],
                summary="Analysis failed due to response parsing error",
                raw_response=raw_response,
            )
