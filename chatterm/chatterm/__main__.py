"""
ChatTerm CLI Entry Point

Usage:
    python -m chatterm
    python -m chatterm --mode agent --model gpt-4o
    python -m chatterm --debug
"""

import argparse
import asyncio
import sys
from typing import Optional


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        prog="chatterm",
        description="ChatTerm - Text-based CLI for testing Chatforge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chatterm                         Start in simple LLM mode
  chatterm --mode agent            Start in agent mode
  chatterm --model gpt-4o          Use GPT-4o model
  chatterm --debug                 Enable debug output
  chatterm --provider anthropic    Use Anthropic provider
        """,
    )

    # Mode
    parser.add_argument(
        "--mode",
        "-m",
        choices=["simple", "agent"],
        default="simple",
        help="Chat mode: simple (direct LLM) or agent (with tools)",
    )

    # LLM settings
    parser.add_argument(
        "--provider",
        "-p",
        default="openai",
        help="LLM provider (openai, anthropic, etc.)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name",
    )
    parser.add_argument(
        "--temperature",
        "-t",
        type=float,
        default=0.7,
        help="Temperature (0.0-2.0)",
    )
    parser.add_argument(
        "--system-prompt",
        "-s",
        help="System prompt for the LLM",
    )

    # Display settings
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Disable markdown rendering",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Disable timestamps in output",
    )

    # Debug settings
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--show-tokens",
        action="store_true",
        help="Show token count in responses",
    )
    parser.add_argument(
        "--show-latency",
        action="store_true",
        help="Show latency in responses",
    )

    # Logging
    parser.add_argument(
        "--log-file",
        help="Log session to file",
    )

    # Middleware
    parser.add_argument(
        "--middleware",
        nargs="+",
        default=[],
        help="Enable middleware (pii, safety, injection)",
    )

    # Version
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point"""
    args = parse_args()

    # Import here to avoid slow startup for --help
    from .settings import ChatTermSettings, ChatMode

    # Build settings from args
    settings = ChatTermSettings()

    # Mode
    settings.mode = ChatMode.SIMPLE if args.mode == "simple" else ChatMode.AGENT

    # LLM settings
    settings.llm.provider = args.provider
    settings.llm.model = args.model
    settings.llm.temperature = args.temperature
    settings.llm.system_prompt = args.system_prompt

    # Display settings
    settings.display.color_output = not args.no_color
    settings.display.markdown_rendering = not args.no_markdown
    settings.display.show_timestamp = not args.no_timestamps
    settings.display.show_token_count = args.show_tokens
    settings.display.show_latency = args.show_latency

    # Debug settings
    settings.behavior.debug_mode = args.debug

    # Logging
    if args.log_file:
        settings.log_to_file = True
        settings.log_file_path = args.log_file

    # Middleware
    settings.middleware.enabled = args.middleware

    # Create and run app
    from .app import ChatTermApp

    app = ChatTermApp(settings=settings)

    try:
        asyncio.run(app.run())
        return 0
    except KeyboardInterrupt:
        print("\nGoodbye!")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
