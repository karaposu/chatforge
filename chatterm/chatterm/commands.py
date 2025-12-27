"""
ChatTerm Commands - Slash command handler

Handles /help, /clear, /debug, /tools, etc.
"""

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .app import ChatTermApp


class CommandHandler:
    """Handle slash commands"""

    def __init__(self, app: "ChatTermApp"):
        self.app = app
        self.commands: dict[str, Callable] = {
            "/help": self.cmd_help,
            "/h": self.cmd_help,
            "/clear": self.cmd_clear,
            "/c": self.cmd_clear,
            "/history": self.cmd_history,
            "/reset": self.cmd_reset,
            "/debug": self.cmd_debug,
            "/d": self.cmd_debug,
            "/tools": self.cmd_tools,
            "/config": self.cmd_config,
            "/mode": self.cmd_mode,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit,
            "/q": self.cmd_exit,
        }

    async def handle(self, command: str) -> bool:
        """Handle a command. Returns True if handled, False if should exit."""
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in self.commands:
            result = await self.commands[cmd](args)
            # Return False if command signals exit
            return result if result is not None else True

        self.app.display.print_error(f"Unknown command: {cmd}")
        print("   Type /help for available commands")
        return True

    async def cmd_help(self, args: str) -> None:
        """Show help"""
        help_text = """
Available Commands:
  /help, /h       Show this help
  /clear, /c      Clear conversation history
  /history        Show conversation history
  /reset          Reset session (new conversation)
  /debug, /d      Toggle debug mode
  /tools          List available tools (agent mode)
  /config         Show current configuration
  /mode [simple|agent]  Switch or show current mode
  /exit, /quit, /q      Exit ChatTerm
"""
        print(help_text)

    async def cmd_clear(self, args: str) -> None:
        """Clear conversation history"""
        self.app.clear_history()
        self.app.display.print_success("Conversation cleared")

    async def cmd_history(self, args: str) -> None:
        """Show conversation history"""
        history = self.app.get_history_display()
        self.app.display.print_history(history)

    async def cmd_reset(self, args: str) -> None:
        """Reset session completely"""
        self.app.clear_history()
        self.app.display.clear_screen()
        self.app.display.print_success("Session reset")
        if self.app.settings.behavior.show_welcome_message:
            self.app.display.print_welcome()

    async def cmd_debug(self, args: str) -> None:
        """Toggle debug mode"""
        self.app.settings.behavior.debug_mode = (
            not self.app.settings.behavior.debug_mode
        )
        status = "ON" if self.app.settings.behavior.debug_mode else "OFF"
        self.app.display.print_success(f"Debug mode: {status}")

    async def cmd_tools(self, args: str) -> None:
        """List tools (agent mode only)"""
        from .settings import ChatMode

        if self.app.settings.mode != ChatMode.AGENT:
            self.app.display.print_warning("Tools are only available in agent mode")
            return

        tools = self.app.get_tools_display()
        self.app.display.print_tools(tools)

    async def cmd_config(self, args: str) -> None:
        """Show current configuration"""
        config = {
            "Mode": self.app.settings.mode.value,
            "Provider": self.app.settings.llm.provider,
            "Model": self.app.settings.llm.model,
            "Temperature": self.app.settings.llm.temperature,
            "Debug": self.app.settings.behavior.debug_mode,
            "Middleware": ", ".join(self.app.settings.middleware.enabled) or "None",
            "Color Output": self.app.settings.display.color_output,
            "Markdown": self.app.settings.display.markdown_rendering,
        }
        self.app.display.print_config(config)

    async def cmd_mode(self, args: str) -> None:
        """Switch or show current mode"""
        from .settings import ChatMode

        if not args:
            self.app.display.print_info(f"Current mode: {self.app.settings.mode.value}")
            return

        mode_str = args.lower().strip()
        if mode_str == "simple":
            self.app.settings.mode = ChatMode.SIMPLE
            self.app.display.print_success("Switched to simple LLM mode")
        elif mode_str == "agent":
            self.app.settings.mode = ChatMode.AGENT
            self.app.display.print_success("Switched to agent mode")
        else:
            self.app.display.print_error(f"Unknown mode: {mode_str}")
            print("   Available modes: simple, agent")

    async def cmd_exit(self, args: str) -> bool:
        """Exit ChatTerm"""
        if self.app.settings.behavior.confirm_before_quit:
            try:
                confirm = input("Are you sure you want to exit? (y/n): ")
                if confirm.lower() != "y":
                    return True
            except (EOFError, KeyboardInterrupt):
                pass

        self.app.display.print_info("Goodbye!")
        return False  # Signal exit
