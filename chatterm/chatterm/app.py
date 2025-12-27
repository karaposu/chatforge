"""
ChatTerm App - Main application for the chat terminal

Coordinates LLM/Agent, middleware, and user interaction.
"""

import asyncio
import time
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .settings import ChatMode, ChatTermSettings, DEFAULT_SETTINGS
from .display import Display
from .commands import CommandHandler
from .logger import logger, setup_logging


class ChatTermApp:
    """Main ChatTerm application - handles both simple and agent modes"""

    def __init__(
        self,
        settings: Optional[ChatTermSettings] = None,
    ):
        self.settings = settings or DEFAULT_SETTINGS

        # Initialize components
        self.display = Display(self.settings.display)
        self.commands = CommandHandler(self)

        # Setup logging
        setup_logging(self.settings)

        # Conversation history (LangChain message format)
        self.messages: list[HumanMessage | AIMessage | SystemMessage] = []

        # LLM and Agent (lazy initialized)
        self._llm = None
        self._agent = None

        # Middleware chain
        self._middleware = []

    @property
    def llm(self):
        """Lazy-initialize LLM"""
        if self._llm is None:
            from chatforge import get_llm

            self._llm = get_llm(
                provider=self.settings.llm.provider,
                model_name=self.settings.llm.model,
                temperature=self.settings.llm.temperature,
            )
        return self._llm

    @property
    def agent(self):
        """Lazy-initialize Agent"""
        if self._agent is None:
            from chatforge import ReActAgent

            # Get tools if configured
            tools = self._load_tools()

            self._agent = ReActAgent(
                llm=self.llm,
                tools=tools,
                system_prompt=self.settings.llm.system_prompt,
                max_iterations=self.settings.agent.max_iterations,
            )
        return self._agent

    def _load_tools(self) -> list:
        """Load configured tools"""
        tools = []
        # TODO: Implement tool loading from settings
        # For now, return empty list - tools can be added programmatically
        return tools

    def _load_middleware(self) -> list:
        """Load configured middleware"""
        middleware = []
        # TODO: Implement middleware loading from settings
        # Example:
        # if "pii" in self.settings.middleware.enabled:
        #     from chatforge.middleware import get_pii_middleware
        #     middleware.append(get_pii_middleware())
        return middleware

    async def run(self) -> None:
        """Main entry point"""
        if self.settings.interactive:
            await self._run_interactive()
        else:
            await self._run_direct()

    async def _run_interactive(self) -> None:
        """Run with interactive menu"""
        # For now, just run direct chat
        # TODO: Implement menu system
        await self._run_direct()

    async def _run_direct(self) -> None:
        """Run direct chat session"""
        # Show welcome
        if self.settings.behavior.show_welcome_message:
            self.display.print_welcome()
            mode_info = f"Mode: {self.settings.mode.value} | Model: {self.settings.llm.model}"
            self.display.print_info(mode_info)
            print()

        # Add system prompt if configured
        if self.settings.llm.system_prompt:
            self.messages.append(SystemMessage(content=self.settings.llm.system_prompt))

        # Main REPL loop
        await self._run_chat_loop()

    async def _run_chat_loop(self) -> None:
        """Main chat REPL loop"""
        while True:
            try:
                # Get user input
                prompt = self.display.print_prompt()
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    should_continue = await self.commands.handle(user_input)
                    if not should_continue:
                        break
                    continue

                # Log user action
                logger.log_user_action(f"Message: {user_input[:50]}...")

                # Process message
                response, tokens, latency = await self._process_message(user_input)

                # Display response
                self.display.print_response(response, tokens=tokens, latency_ms=latency)

            except KeyboardInterrupt:
                print()  # Newline after ^C
                self.display.print_info("Use /exit to quit")
            except EOFError:
                break
            except Exception as e:
                if self.settings.behavior.show_error_details:
                    self.display.print_error(str(e), details=str(type(e).__name__))
                else:
                    self.display.print_error("An error occurred")

    async def _process_message(
        self, text: str
    ) -> tuple[str, Optional[int], Optional[float]]:
        """
        Process user message through middleware -> LLM/Agent -> middleware.

        Returns: (response_text, token_count, latency_ms)
        """
        start_time = time.time()
        processed_text = text
        tokens = None

        # Pre-processing middleware
        for mw in self._middleware:
            result = await mw.process_input(processed_text)
            processed_text = result.modified_text

            if self.settings.behavior.debug_mode and result.action_taken:
                self.display.print_middleware_action(
                    result.middleware_name,
                    result.action_description,
                    result.details,
                )

            if result.blocked:
                self.display.print_blocked(result.block_reason)
                return result.block_reason, None, None

        # Core processing based on mode
        if self.settings.mode == ChatMode.SIMPLE:
            response, tokens = await self._process_with_llm(processed_text)
        else:
            response, tokens = await self._process_with_agent(processed_text)

        # Post-processing middleware
        for mw in self._middleware:
            result = await mw.process_output(response)
            response = result.modified_text

            if self.settings.behavior.debug_mode and result.action_taken:
                self.display.print_middleware_action(
                    result.middleware_name,
                    result.action_description,
                    result.details,
                )

        latency = (time.time() - start_time) * 1000
        return response, tokens, latency

    async def _process_with_llm(self, text: str) -> tuple[str, Optional[int]]:
        """Process with direct LLM call"""
        # Add user message to history
        self.messages.append(HumanMessage(content=text))

        # Invoke LLM
        logger.log_api_event("LLM invoke", self.settings.llm.model)
        result = await self.llm.ainvoke(self.messages)

        # Extract response
        response_text = result.content
        tokens = None

        # Try to get token count
        if hasattr(result, "usage_metadata") and result.usage_metadata:
            tokens = result.usage_metadata.get("total_tokens")

        # Add response to history
        self.messages.append(AIMessage(content=response_text))

        return response_text, tokens

    async def _process_with_agent(self, text: str) -> tuple[str, Optional[int]]:
        """Process with ReActAgent"""
        # Convert messages to conversation history format
        history = self._messages_to_history()

        # Log
        logger.log_api_event("Agent process", self.settings.llm.model)

        # Process through agent (synchronous call)
        response, trace_id = self.agent.process_message(
            text,
            conversation_history=history,
            context={"debug": self.settings.behavior.debug_mode},
        )

        # Show trace in debug mode
        if self.settings.behavior.debug_mode and trace_id:
            self.display.print_trace_info(trace_id)

        # Update history
        self.messages.append(HumanMessage(content=text))
        self.messages.append(AIMessage(content=response))

        return response, None  # Agent doesn't provide token count directly

    def _messages_to_history(self) -> list[dict]:
        """Convert LangChain messages to conversation history format"""
        history = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
            # Skip system messages in history
        return history

    def clear_history(self) -> None:
        """Clear conversation history"""
        # Keep system message if present
        system_msgs = [m for m in self.messages if isinstance(m, SystemMessage)]
        self.messages = system_msgs

    def get_history_display(self) -> list[tuple[str, str]]:
        """Get history in display format"""
        result = []
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                result.append(("human", msg.content))
            elif isinstance(msg, AIMessage):
                result.append(("ai", msg.content))
        return result

    def get_tools_display(self) -> list[tuple[str, str]]:
        """Get tools in display format"""
        if self._agent is None:
            return []
        return [(tool.name, tool.description) for tool in self.agent.tools]

    def add_tool(self, tool) -> None:
        """Add a tool to the agent"""
        if self._agent is not None:
            self._agent.tools.append(tool)
        self.settings.agent.tools.append(tool.name)

    def add_middleware(self, middleware) -> None:
        """Add middleware to the chain"""
        self._middleware.append(middleware)


def create_app(
    mode: str = "simple",
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    debug: bool = False,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> ChatTermApp:
    """Factory function to create ChatTermApp with common settings"""
    from .settings import ChatTermSettings, ChatMode

    settings = ChatTermSettings()
    settings.mode = ChatMode.SIMPLE if mode == "simple" else ChatMode.AGENT
    settings.llm.provider = provider
    settings.llm.model = model
    settings.behavior.debug_mode = debug
    settings.llm.system_prompt = system_prompt

    # Apply any additional kwargs
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    return ChatTermApp(settings=settings)
