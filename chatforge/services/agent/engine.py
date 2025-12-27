"""
ReACT Agent Engine for Chatforge using LangGraph.

This module provides a generic intelligent agent that:
1. Takes user input
2. Reasons about what action to take
3. Acts by using tools
4. Observes the results
5. Repeats until the task is complete

Uses LangChain's create_agent for robust, LLM-driven decision making.

Architecture:
- Follows Hexagonal Architecture (Ports & Adapters)
- Uses dependency injection for ports
- Supports MessagingPlatformIntegrationPort for platform-agnostic I/O
- Platform and domain agnostic core logic

Usage:
    from chatforge.services.agent import ReActAgent

    # With tools and system prompt
    agent = ReActAgent(
        tools=[my_search_tool, my_action_tool],
        system_prompt="You are a helpful assistant...",
    )

    # Process a message
    response, trace_id = agent.process_message(
        "Hello",
        conversation_history=[],
    )
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from chatforge.services.llm.factory import get_llm


if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool

    from chatforge.ports.messaging_platform_integration import ConversationContext, MessagingPlatformIntegrationPort
    from chatforge.ports.tracing import TracingPort


logger = logging.getLogger(__name__)


# Default system prompt - applications should provide their own
DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant.

Your capabilities:
- Answer questions accurately and helpfully
- Use available tools when needed to accomplish tasks
- Maintain a professional and friendly tone

When you don't know something, say so honestly rather than making up information."""


class ReActAgent:
    """
    ReACT agent using LangGraph.

    This agent uses the ReACT (Reason-Act-Observe) pattern:
    1. Reason: LLM decides what to do based on conversation
    2. Act: Execute tools as needed
    3. Observe: See tool results
    4. Repeat: Continue until task is complete

    Architecture:
    - Supports both direct instantiation and factory-based creation
    - Uses ToolNode with error handling for robust tool execution
    - Supports MessagingPlatformIntegrationPort injection for platform-agnostic I/O
    - Supports TracingPort injection for observability

    Benefits:
    - LLM-driven decisions (not keyword matching)
    - Multi-step reasoning capability
    - Easily extensible with new tools
    - Industry-standard pattern

    Example:
        # Direct instantiation
        agent = ReActAgent(
            tools=[search_tool, action_tool],
            system_prompt="You are a customer support assistant...",
        )

        # With pre-built LangGraph agent
        agent = ReActAgent(agent=my_langgraph_agent, tools=tools)

        # With messaging port for async I/O
        agent = ReActAgent(
            tools=tools,
            system_prompt=my_prompt,
            messaging_port=my_messaging_adapter,
        )
    """

    def __init__(
        self,
        agent=None,
        tools: list[BaseTool] | None = None,
        system_prompt: str | None = None,
        messaging_port: MessagingPlatformIntegrationPort | None = None,
        tracing: TracingPort | None = None,
        llm: BaseChatModel | None = None,
        temperature: float = 0.0,
    ):
        """
        Initialize ReACT agent.

        There are two ways to create a ReActAgent:

        1. **With pre-built agent** (from factory):
           ```python
           react = ReActAgent(agent=langgraph_agent, tools=tools_list)
           ```

        2. **With tools** (creates agent internally):
           ```python
           react = ReActAgent(
               tools=[search_tool, ticket_tool],
               system_prompt="You are..."
           )
           ```

        Args:
            agent: Optional pre-built LangGraph agent. If provided, uses directly.
            tools: List of tools. Required if agent is not provided.
            system_prompt: System prompt for the agent. Uses default if not provided.
            messaging_port: Optional MessagingPlatformIntegrationPort for platform-agnostic I/O.
            tracing: TracingPort for observability.
            llm: Optional pre-configured LLM (overrides default).
            temperature: LLM temperature if using default LLM (default: 0.0).

        Raises:
            ValueError: If neither agent nor tools are provided.
        """
        self.messaging_port = messaging_port
        self.tracing = tracing
        self._system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

        # Case 1: Pre-built agent provided
        if agent is not None:
            self.agent = agent
            self.tools = tools or []
            self.llm = llm
            logger.info(
                f"ReActAgent initialized with pre-built agent "
                f"(messaging={'enabled' if messaging_port else 'disabled'}, "
                f"tracing={'enabled' if tracing and tracing.enabled else 'disabled'})"
            )
            return

        # Case 2: Need to build agent - tools are required
        if tools is None:
            raise ValueError(
                "ReActAgent requires either:\n"
                "  1. A pre-built agent: ReActAgent(agent=my_agent)\n"
                "  2. A list of tools: ReActAgent(tools=[...])"
            )

        self.tools = tools

        # Get LLM for agent
        self.llm = llm or get_llm(streaming=False, temperature=temperature)

        # Create LangGraph ReACT agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=self._system_prompt,
        )

        tool_names = [t.name for t in self.tools]
        logger.info(
            f"ReActAgent initialized with tools: {tool_names} "
            f"(messaging={'enabled' if messaging_port else 'disabled'}, "
            f"tracing={'enabled' if tracing and tracing.enabled else 'disabled'})"
        )

    @property
    def system_prompt(self) -> str:
        """Get the system prompt used by this agent."""
        return self._system_prompt

    def process_message(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
        context: dict[str, Any] | None = None,
        return_metadata: bool = False,
    ) -> tuple[str, str | None] | tuple[str, str | None, dict[str, Any]]:
        """
        Process a user message using ReACT pattern.

        The agent will:
        1. Convert conversation to LangChain message format
        2. Let LangGraph's ReACT agent reason about next steps
        3. Agent may use tools as needed
        4. Agent may ask clarifying questions
        5. Return final response with trace_id for feedback linking

        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            context: Optional context dict containing:
                - user_id: User identifier for tracing
                - session_id: Session/conversation identifier
                - Any additional metadata for tools/tracing
            return_metadata: If True, return execution metadata as third element

        Returns:
            If return_metadata=False:
                Tuple of (agent_response, trace_id)
                - agent_response: The agent's text response
                - trace_id: Trace ID for feedback linking (None if tracing disabled)

            If return_metadata=True:
                Tuple of (agent_response, trace_id, metadata)
                - metadata: Dict with execution details (tool_calls, message_count, etc.)
        """
        trace_id = None
        metadata: dict[str, Any] = {
            "tool_calls": [],
            "tool_call_count": 0,
            "message_count": 0,
        }

        try:
            # Convert to LangChain message format
            messages = self._convert_to_messages(conversation_history, user_message)

            logger.info(f"Processing message with {len(messages)} messages in context")
            logger.debug(f"User message: {user_message[:100]}...")

            # Invoke ReACT agent with context for tracing
            logger.debug("Invoking ReACT agent...")
            result, trace_id = self._invoke_with_context(messages, context)

            # Log execution details
            logger.info(
                f"Agent execution completed. Total messages in result: {len(result['messages'])}"
            )

            metadata["message_count"] = len(result["messages"])

            # Track tool invocations
            tool_calls_count = 0
            tool_calls_list = []

            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls_count += len(msg.tool_calls)
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = tool_call.get("args", {})
                        tool_calls_list.append({
                            "name": tool_name,
                            "args": tool_args,
                            "id": tool_call.get("id"),
                        })
                        logger.info(f"Tool invoked: {tool_name} with args: {tool_args}")
                elif hasattr(msg, "tool_call_id") and msg.tool_call_id:
                    logger.debug(f"Tool result received: {str(msg.content)[:200]}...")

            if tool_calls_count > 0:
                logger.info(f"Total tool invocations: {tool_calls_count}")

            metadata["tool_call_count"] = tool_calls_count
            metadata["tool_calls"] = tool_calls_list

            # Extract final response
            final_message = result["messages"][-1]

            if isinstance(final_message, AIMessage):
                response = final_message.content
            else:
                response = str(final_message.content)

            logger.info(f"Agent final response: {str(response)[:200]}...")

            if return_metadata:
                return response, trace_id, metadata
            else:
                return response, trace_id

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_response = (
                "I apologize, but I encountered an error processing your request. "
                "Please try again.",
                trace_id,
            )
            if return_metadata:
                return error_response[0], error_response[1], metadata
            else:
                return error_response

    def _convert_to_messages(
        self, conversation_history: list[dict[str, str]], user_message: str
    ) -> list:
        """
        Convert conversation history to LangChain message format.

        IMPORTANT: External messaging platforms (via MessagingPlatformIntegrationPort) only store
        final human-readable messages, not intermediate tool calls/responses.
        OpenAI requires that every assistant message with tool_calls must be
        immediately followed by tool response messages. Since reconstructed
        history doesn't include these, we create clean AIMessage objects
        without tool_calls to prevent "tool_calls must be followed by tool
        messages" errors (HTTP 400).

        Args:
            conversation_history: List of dicts with 'role' and 'content'
            user_message: Current user message to add

        Returns:
            List of LangChain message objects
        """
        messages = []

        # Add conversation history
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                # Create AIMessage WITHOUT tool_calls - reconstructed history
                # from external platforms doesn't include tool responses
                messages.append(AIMessage(content=content, tool_calls=[]))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        return messages

    def _invoke_with_context(
        self,
        messages: list,
        context: dict[str, Any] | None,
    ) -> tuple[dict, str | None]:
        """
        Invoke the agent with runtime configuration and tracing.

        Args:
            messages: LangChain message objects
            context: Optional context dict with user_id, session_id, etc.

        Returns:
            Tuple of (agent_result, trace_id)
            - agent_result: The agent invocation result dict
            - trace_id: Trace ID (None if tracing disabled)
        """
        config: dict[str, Any] = {}
        tracing = self.tracing

        if not tracing or not tracing.enabled:
            # No tracing - invoke directly
            agent_result = self.agent.invoke({"messages": messages}, config=config)
            return agent_result, None

        # Create parent span for agent execution
        with tracing.span("chatforge_agent") as span:
            # Get trace_id from active context
            trace_id = tracing.get_active_trace_id()

            # Set user/session metadata on the trace
            if context:
                user_id = context.get("user_id", "")
                session_id = context.get("session_id", "")

                metadata = {}
                if user_id:
                    metadata["user_id"] = user_id
                if session_id:
                    metadata["session_id"] = session_id

                if metadata:
                    tracing.set_trace_metadata(metadata)
                    logger.debug(f"Set trace metadata: user={user_id}, session={session_id}")

            # Set inputs on the span
            if span and messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "content"):
                    span.set_inputs({"user_message": str(last_msg.content)})

            # Invoke the agent within the trace context
            agent_result = self.agent.invoke({"messages": messages}, config=config)

            # Set outputs on the span
            if span and agent_result.get("messages"):
                final_msg = agent_result["messages"][-1]
                if hasattr(final_msg, "content"):
                    span.set_outputs({"response": str(final_msg.content)})

            logger.debug(f"Agent execution traced with ID: {trace_id}")

        return agent_result, trace_id

    # =========================================================================
    # MessagingPlatformIntegrationPort Integration (async methods)
    # =========================================================================

    async def get_conversation_history_async(
        self, context: ConversationContext
    ) -> list[dict[str, str]]:
        """
        Get conversation history via MessagingPlatformIntegrationPort.

        Args:
            context: Conversation context with platform-specific identifiers.

        Returns:
            List of message dicts with 'role' and 'content' keys.

        Raises:
            RuntimeError: If no messaging port is configured.
        """
        if not self.messaging_port:
            raise RuntimeError(
                "No messaging port configured. Initialize ReActAgent with messaging_port parameter."
            )

        messages = await self.messaging_port.get_conversation_history(context)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def send_response_async(self, context: ConversationContext, message: str) -> None:
        """
        Send a response via MessagingPlatformIntegrationPort.

        Args:
            context: Conversation context identifying where to send.
            message: Text content to send.

        Raises:
            RuntimeError: If no messaging port is configured.
        """
        if not self.messaging_port:
            raise RuntimeError(
                "No messaging port configured. Initialize ReActAgent with messaging_port parameter."
            )

        await self.messaging_port.send_message(context, message)
        logger.debug(f"Sent response via messaging port: {message[:100]}...")

    async def send_typing_indicator_async(self, context: ConversationContext) -> None:
        """
        Show typing indicator via MessagingPlatformIntegrationPort.

        Args:
            context: Conversation context.

        Raises:
            RuntimeError: If no messaging port is configured.
        """
        if not self.messaging_port:
            raise RuntimeError(
                "No messaging port configured. Initialize ReActAgent with messaging_port parameter."
            )

        await self.messaging_port.send_typing_indicator(context)

    async def get_user_email_async(self, user_id: str) -> str | None:
        """
        Resolve user email via MessagingPlatformIntegrationPort.

        Args:
            user_id: Platform-specific user identifier.

        Returns:
            User email or None if not found.

        Raises:
            RuntimeError: If no messaging port is configured.
        """
        if not self.messaging_port:
            raise RuntimeError(
                "No messaging port configured. Initialize ReActAgent with messaging_port parameter."
            )

        return await self.messaging_port.get_user_email(user_id)

    def has_messaging_port(self) -> bool:
        """Check if a messaging port is configured."""
        return self.messaging_port is not None

    def process_message_with_timeout(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]],
        timeout_seconds: float = 25.0,
        context: dict[str, Any] | None = None,
    ) -> tuple[str | None, bool, str | None]:
        """
        Process message with timeout.

        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            timeout_seconds: Maximum time to wait for response
            context: Optional context dict (see process_message for details)

        Returns:
            tuple: (response, timed_out, trace_id)
            - response: Agent response or None if timed out
            - timed_out: True if operation timed out
            - trace_id: Trace ID (None if timed out or tracing disabled)
        """
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.process_message,
                user_message,
                conversation_history,
                context,
            )
            try:
                response, trace_id = future.result(timeout=timeout_seconds)
                return response, False, trace_id
            except FuturesTimeoutError:
                logger.warning(f"Agent timed out after {timeout_seconds}s")
                return None, True, None
