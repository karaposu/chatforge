"""
Knowledge Port - Abstract interface for knowledge bases.

This port defines the contract for knowledge base integrations.
Implementations can include Notion, Confluence, SharePoint, or custom systems.

The core agent logic depends only on this interface, enabling:
- Easy swapping of knowledge bases
- RAG (Retrieval Augmented Generation) injection
- Mock implementations for testing
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypedDict


class KnowledgeMetadata(TypedDict, total=False):
    """
    Type-safe metadata for knowledge base results.

    All fields are optional (total=False) to maintain flexibility.

    Attributes:
        page_id: Unique identifier of the source page.
        database_id: ID of the database containing the page.
        last_edited: ISO timestamp of last modification.
        created_by: User who created the document.
        tags: Classification tags.
        category: Document category.
    """

    page_id: str
    database_id: str
    last_edited: str
    created_by: str
    tags: list[str]
    category: str


@dataclass
class KnowledgeResult:
    """
    Search result from knowledge base.

    Attributes:
        title: Title of the document/page.
        content: Relevant content snippet or full text.
        url: URL to the source document (if available).
        relevance_score: Score indicating relevance (0.0 to 1.0).
        source: Source identifier (e.g., "notion", "confluence").
        metadata: Additional metadata (page ID, last updated, etc.).
    """

    title: str
    content: str
    url: str | None = None
    relevance_score: float = 0.0
    source: str = "unknown"
    metadata: KnowledgeMetadata | None = None

    def format_for_display(self) -> str:
        """Format result for user-friendly display."""
        if self.url:
            return f"**{self.title}**\n{self.content}\n[View more]({self.url})"
        return f"**{self.title}**\n{self.content}"

    def format_for_rag(self) -> str:
        """Format result for RAG injection into prompts."""
        return f"### {self.title}\n{self.content}"


class KnowledgePort(ABC):
    """
    Abstract port for knowledge bases.

    This interface defines the contract that all knowledge base adapters
    must implement. Used for:

    1. **Search**: Find relevant documentation for user queries
    2. **RAG**: Inject relevant context into agent prompts
    """

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[KnowledgeResult]:
        """
        Search knowledge base for relevant documents.

        Args:
            query: Search query (keywords or natural language).
            limit: Maximum number of results to return.

        Returns:
            List of KnowledgeResult objects sorted by relevance.
        """

    @abstractmethod
    def get_context_for_rag(self, query: str, max_tokens: int = 1000) -> str:
        """
        Get formatted context for RAG injection into prompts.

        This method searches the knowledge base and formats the results
        into a string suitable for including in the system prompt.

        Args:
            query: Query to search for relevant context.
            max_tokens: Approximate maximum length of returned context.

        Returns:
            Formatted string with relevant documentation, or empty string
            if no relevant results found.
        """

    @abstractmethod
    def get_page_content(self, page_id: str) -> str | None:
        """
        Get full content of a specific page.

        Args:
            page_id: Identifier of the page to retrieve.

        Returns:
            Page content as string, or None if not found.
        """

    def format_search_results(self, results: list[KnowledgeResult]) -> str:
        """
        Format search results for user display.

        This is a default implementation that can be overridden.

        Args:
            results: List of search results.

        Returns:
            Formatted string for display to user.
        """
        if not results:
            return "No relevant documentation found."

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result.format_for_display()}")

        return "\n\n".join(formatted)

    def format_results_for_rag(self, results: list[KnowledgeResult]) -> str:
        """
        Format search results for RAG injection.

        This is a default implementation that can be overridden.

        Args:
            results: List of search results.

        Returns:
            Formatted string for prompt injection.
        """
        if not results:
            return ""

        formatted = [r.format_for_rag() for r in results]
        return "\n\n---\n\n".join(formatted)
