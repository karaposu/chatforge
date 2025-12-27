"""
ChatTerm Launcher - Main entry point with menu flow
Adapted from VoxTerm - uses Chatforge LLM instead of VoiceEngine.
"""

import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from .menu import ChatTermMenu
from .settings import ChatTermSettings, ChatMode
from .app import ChatTermApp


async def launch_chatterm(
    api_key: Optional[str] = None,
    mode: str = "simple",
    model: str = "gpt-4o-mini",
    provider: str = "openai",
    interactive: bool = True,
):
    """Launch ChatTerm with menu interface or direct chat"""

    # Get API key based on provider
    if not api_key:
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
        else:
            api_key = os.getenv("OPENAI_API_KEY")  # Default fallback

    if not api_key:
        print("No API key found!")
        print("\nSet your API key:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("   or create a .env file")
        return

    # Create settings
    settings = ChatTermSettings()
    settings.mode = ChatMode.SIMPLE if mode == "simple" else ChatMode.AGENT
    settings.llm.provider = provider
    settings.llm.model = model
    settings.interactive = interactive

    # Create app
    app = ChatTermApp(settings=settings)

    if interactive:
        # Create and run menu
        menu = ChatTermMenu(app, settings)

        try:
            await menu.run()
        except Exception as e:
            print(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()
    else:
        # Direct chat mode (no menu)
        try:
            await app.run()
        except Exception as e:
            print(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Check for chatforge
    try:
        import chatforge
    except ImportError:
        print("chatforge not found!")
        print("   pip install -e ../chatforge")
        print("   (from the chatterm directory)")
        return

    # Parse simple args (full arg parsing in __main__.py)
    import sys

    interactive = True
    mode = "simple"
    model = "gpt-4o-mini"
    provider = "openai"

    # Simple arg handling for launcher
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-menu":
            interactive = False
        elif arg == "--mode" and i + 1 < len(args):
            mode = args[i + 1]
            i += 1
        elif arg == "--model" and i + 1 < len(args):
            model = args[i + 1]
            i += 1
        elif arg == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 1
        i += 1

    # Run the launcher
    asyncio.run(launch_chatterm(
        mode=mode,
        model=model,
        provider=provider,
        interactive=interactive,
    ))


if __name__ == "__main__":
    main()
