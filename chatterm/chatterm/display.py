"""
ChatTerm Display - Output formatting and rendering

Handles all output - supports rich library or plain text fallback.
"""

from datetime import datetime
from typing import Optional, Any

from .settings import DisplaySettings


class Display:
    """Handle all output - supports rich or plain text"""

    def __init__(self, settings: DisplaySettings):
        self.settings = settings
        self.console = None
        self.has_rich = False

        # Try to import rich if color output enabled
        if settings.color_output:
            try:
                from rich.console import Console

                self.console = Console()
                self.has_rich = True
            except ImportError:
                self.console = None
                self.has_rich = False

    def print_welcome(self) -> None:
        """Print welcome banner"""
        banner = """
╔═══════════════════════════════════════╗
║       ChatTerm for Chatforge          ║
║    Type /help for commands            ║
╚═══════════════════════════════════════╝
"""
        if self.has_rich:
            self.console.print(banner, style="bold blue")
        else:
            print(banner)

    def print_prompt(self) -> str:
        """Get the input prompt string"""
        if self.settings.show_timestamp:
            timestamp = datetime.now().strftime(self.settings.timestamp_format)
            return f"[{timestamp}] You: "
        return "You: "

    def print_response(
        self,
        text: str,
        tokens: Optional[int] = None,
        latency_ms: Optional[float] = None,
    ) -> None:
        """Print AI response (with markdown if rich available)"""
        # Build metadata string
        metadata = []
        if self.settings.show_token_count and tokens:
            metadata.append(f"{tokens} tokens")
        if self.settings.show_latency and latency_ms:
            metadata.append(f"{latency_ms:.0f}ms")

        metadata_str = f" ({', '.join(metadata)})" if metadata else ""

        # Print with timestamp if enabled
        if self.settings.show_timestamp:
            timestamp = datetime.now().strftime(self.settings.timestamp_format)
            prefix = f"[{timestamp}] AI{metadata_str}: "
        else:
            prefix = f"AI{metadata_str}: "

        if self.has_rich and self.settings.markdown_rendering:
            from rich.markdown import Markdown

            self.console.print(prefix, end="")
            self.console.print(Markdown(text))
        else:
            print(f"{prefix}{text}")
        print()  # Extra newline for readability

    def print_middleware_action(
        self,
        middleware_name: str,
        action: str,
        details: Optional[dict] = None,
    ) -> None:
        """Print middleware action (debug mode)"""
        if self.has_rich:
            self.console.print(
                f"[dim][{middleware_name}][/dim] {action}", style="yellow"
            )
            if details:
                for key, value in details.items():
                    self.console.print(f"  [dim]{key}:[/dim] {value}")
        else:
            print(f"[{middleware_name}] {action}")
            if details:
                for key, value in details.items():
                    print(f"  {key}: {value}")

    def print_tool_call(
        self,
        tool_name: str,
        args: Optional[dict] = None,
        result: Optional[str] = None,
    ) -> None:
        """Print tool invocation (debug mode)"""
        if self.has_rich:
            self.console.print(f"[bold cyan]Tool:[/bold cyan] {tool_name}")
            if args:
                self.console.print(f"  [dim]Args:[/dim] {args}")
            if result:
                self.console.print(f"  [dim]Result:[/dim] {result[:100]}...")
        else:
            print(f"[Tool: {tool_name}]")
            if args:
                print(f"  Args: {args}")
            if result:
                print(f"  Result: {result[:100]}...")

    def print_trace_info(self, trace_id: str) -> None:
        """Print trace information (debug mode)"""
        if self.has_rich:
            self.console.print(f"[dim]Trace ID: {trace_id}[/dim]")
        else:
            print(f"Trace ID: {trace_id}")

    def print_error(self, error: str, details: Optional[str] = None) -> None:
        """Print error message"""
        if self.has_rich:
            self.console.print(f"[bold red]Error:[/bold red] {error}")
            if details:
                self.console.print(f"[dim]{details}[/dim]")
        else:
            print(f"Error: {error}")
            if details:
                print(f"  {details}")

    def print_info(self, info: str) -> None:
        """Print info message"""
        if self.has_rich:
            self.console.print(f"[blue]Info:[/blue] {info}")
        else:
            print(f"Info: {info}")

    def print_success(self, message: str) -> None:
        """Print success message"""
        if self.has_rich:
            self.console.print(f"[green]OK:[/green] {message}")
        else:
            print(f"OK: {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message"""
        if self.has_rich:
            self.console.print(f"[yellow]Warning:[/yellow] {message}")
        else:
            print(f"Warning: {message}")

    def print_blocked(self, reason: str) -> None:
        """Print blocked message (from middleware)"""
        if self.has_rich:
            self.console.print(f"[bold red]Blocked:[/bold red] {reason}")
        else:
            print(f"Blocked: {reason}")

    def print_config(self, config: dict[str, Any]) -> None:
        """Print current configuration"""
        print("\nCurrent Configuration:")
        print("-" * 40)
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()

    def print_tools(self, tools: list[tuple[str, str]]) -> None:
        """Print available tools list"""
        if not tools:
            self.print_info("No tools configured")
            return

        print("\nAvailable Tools:")
        print("-" * 40)
        for name, description in tools:
            if self.has_rich:
                self.console.print(f"  [bold]{name}[/bold]: {description}")
            else:
                print(f"  {name}: {description}")
        print()

    def print_history(self, messages: list[tuple[str, str]]) -> None:
        """Print conversation history"""
        if not messages:
            self.print_info("No conversation history")
            return

        print("\nConversation History:")
        print("-" * 40)
        for role, content in messages:
            label = "You" if role == "human" else "AI"
            # Truncate long messages
            display_content = content[:100] + "..." if len(content) > 100 else content
            print(f"  [{label}] {display_content}")
        print()

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        import os

        os.system("cls" if os.name == "nt" else "clear")
