"""
ChatTerm Menu System - Handle menu flow and navigation
Adapted from VoxTerm - simplified for text-only chat.
"""

import asyncio
from typing import Optional, Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .settings import ChatTermSettings, ChatMode, LogLevel
from .logger import logger, setup_logging, patch_print, restore_print


class MenuState(Enum):
    """Menu states"""
    MAIN = "main"
    SETTINGS = "settings"
    MODE_SELECT = "mode_select"
    MODEL_SELECT = "model_select"
    CHATTING = "chatting"
    EXITING = "exiting"


@dataclass
class MenuItem:
    """A menu item"""
    key: str
    label: str
    action: Optional[Callable] = None
    next_state: Optional[MenuState] = None


class ChatTermMenu:
    """Menu system for ChatTerm"""

    def __init__(self, app: Any, settings: Optional[ChatTermSettings] = None):
        self.app = app
        self.settings = settings or ChatTermSettings()
        self.current_state = MenuState.MAIN
        self.running = True

        # Menu definitions
        self.menus = self._create_menus()

    def _create_menus(self) -> Dict[MenuState, Dict[str, MenuItem]]:
        """Create all menu definitions"""
        return {
            MenuState.MAIN: {
                'c': MenuItem('c', 'Start Chat', action=self._start_chat),
                'm': MenuItem('m', 'Mode', next_state=MenuState.MODE_SELECT),
                'o': MenuItem('o', 'Model', next_state=MenuState.MODEL_SELECT),
                's': MenuItem('s', 'Settings', next_state=MenuState.SETTINGS),
                'q': MenuItem('q', 'Quit', action=self._quit),
            },

            MenuState.SETTINGS: {
                'd': MenuItem('d', self._get_debug_label(), action=self._toggle_debug),
                'l': MenuItem('l', self._get_logging_label(), action=self._toggle_logging),
                't': MenuItem('t', self._get_timestamps_label(), action=self._toggle_timestamps),
                'c': MenuItem('c', self._get_color_label(), action=self._toggle_color),
                'i': MenuItem('i', 'Info', action=self._show_info),
                'b': MenuItem('b', 'Back', action=self._go_back),
            },

            MenuState.MODE_SELECT: {
                '1': MenuItem('1', 'Simple (Direct LLM)', action=lambda: self._set_mode(ChatMode.SIMPLE)),
                '2': MenuItem('2', 'Agent (With Tools)', action=lambda: self._set_mode(ChatMode.AGENT)),
                'b': MenuItem('b', 'Back', action=self._go_back),
            },

            MenuState.MODEL_SELECT: {
                '1': MenuItem('1', 'gpt-4o-mini (Fast)', action=lambda: self._set_model('gpt-4o-mini')),
                '2': MenuItem('2', 'gpt-4o (Smart)', action=lambda: self._set_model('gpt-4o')),
                '3': MenuItem('3', 'gpt-4-turbo', action=lambda: self._set_model('gpt-4-turbo')),
                '4': MenuItem('4', 'claude-3-5-sonnet', action=lambda: self._set_model('claude-3-5-sonnet-20241022', 'anthropic')),
                'b': MenuItem('b', 'Back', action=self._go_back),
            },
        }

    def _get_debug_label(self) -> str:
        status = "ON" if self.settings.behavior.debug_mode else "OFF"
        return f'Debug Mode: {status}'

    def _get_logging_label(self) -> str:
        status = "ON" if self.settings.log_to_file else "OFF"
        return f'Log to File: {status}'

    def _get_timestamps_label(self) -> str:
        status = "ON" if self.settings.display.show_timestamp else "OFF"
        return f'Timestamps: {status}'

    def _get_color_label(self) -> str:
        status = "ON" if self.settings.display.color_output else "OFF"
        return f'Color Output: {status}'

    def _update_settings_labels(self):
        """Update dynamic labels in settings menu"""
        settings_menu = self.menus[MenuState.SETTINGS]
        settings_menu['d'].label = self._get_debug_label()
        settings_menu['l'].label = self._get_logging_label()
        settings_menu['t'].label = self._get_timestamps_label()
        settings_menu['c'].label = self._get_color_label()

    def _clear_screen(self):
        """Clear the terminal screen"""
        print("\033[2J\033[H", end="")

    def _show_header(self):
        """Show ChatTerm header"""
        print("+" + "=" * 41 + "+")
        print("|           ChatTerm for Chatforge        |")
        print("+" + "=" * 41 + "+")
        print()

    def _show_current_state(self):
        """Show current state/settings"""
        mode_str = "Simple LLM" if self.settings.mode == ChatMode.SIMPLE else "Agent"
        print(f"Mode: {mode_str} | Model: {self.settings.llm.model}")
        print(f"Provider: {self.settings.llm.provider} | Debug: {'ON' if self.settings.behavior.debug_mode else 'OFF'}")
        print()

    def _show_menu(self):
        """Show current menu"""
        menu = self.menus.get(self.current_state, {})

        # Menu titles
        titles = {
            MenuState.MAIN: "Main Menu",
            MenuState.SETTINGS: "Settings",
            MenuState.MODE_SELECT: "Select Mode",
            MenuState.MODEL_SELECT: "Select Model",
        }

        if self.current_state in titles:
            print(f"{titles[self.current_state]}:")
            print()

        # Show menu items
        for key, item in menu.items():
            print(f"  [{key}] {item.label}")

        print()

    async def run(self):
        """Run the menu system"""
        self._clear_screen()

        # Setup logging based on current settings
        if self.settings.log_to_file:
            setup_logging(self.settings)
            patch_print()
            logger.log_event("SESSION", "ChatTerm menu started")

        while self.running:
            try:
                # Update dynamic labels
                self._update_settings_labels()

                # Show interface
                self._show_header()
                self._show_current_state()
                self._show_menu()

                # Get input
                choice = await self._get_input()

                # Process choice
                await self._process_choice(choice)

                # Clear for next iteration
                if self.running and self.current_state != MenuState.CHATTING:
                    self._clear_screen()

            except KeyboardInterrupt:
                print("\n\nForce quit")
                self.running = False
                break
            except Exception as e:
                print(f"\nError: {e}")
                await asyncio.sleep(2)

    async def _get_input(self) -> str:
        """Get user input"""
        loop = asyncio.get_event_loop()
        choice = await loop.run_in_executor(None, input, "> ")
        return choice.lower().strip()

    async def _process_choice(self, choice: str):
        """Process menu choice"""
        menu = self.menus.get(self.current_state, {})

        if choice not in menu:
            print("Invalid choice")
            await asyncio.sleep(1)
            return

        item = menu[choice]

        # Execute action if any
        if item.action:
            result = await self._execute_action(item.action)
            if result is False:
                return

        # Change state if specified
        if item.next_state:
            self.current_state = item.next_state

    async def _execute_action(self, action: Callable) -> Any:
        """Execute an action"""
        if asyncio.iscoroutinefunction(action):
            return await action()
        else:
            return action()

    # Actions
    async def _start_chat(self):
        """Start a chat session"""
        self._clear_screen()

        if self.settings.log_to_file:
            logger.log_event("SESSION", f"Starting chat - Mode: {self.settings.mode.value}, Model: {self.settings.llm.model}")

        # Run the chat loop from app
        try:
            await self.app._run_chat_loop()
        except Exception as e:
            print(f"\nChat error: {e}")
            if self.settings.behavior.debug_mode:
                import traceback
                traceback.print_exc()

        print("\n[Press ENTER to return to menu]")
        await asyncio.get_event_loop().run_in_executor(None, input, "")

        # Return to main menu
        self.current_state = MenuState.MAIN
        self._clear_screen()

    def _set_mode(self, mode: ChatMode):
        """Set the chat mode"""
        self.settings.mode = mode
        # Also update app settings
        self.app.settings.mode = mode
        mode_str = "Simple LLM" if mode == ChatMode.SIMPLE else "Agent"
        print(f"Mode changed to: {mode_str}")

    def _set_model(self, model: str, provider: str = "openai"):
        """Set the model"""
        self.settings.llm.model = model
        self.settings.llm.provider = provider
        # Also update app settings
        self.app.settings.llm.model = model
        self.app.settings.llm.provider = provider
        # Reset LLM so it gets recreated with new model
        self.app._llm = None
        print(f"Model changed to: {model} ({provider})")

    def _toggle_debug(self):
        """Toggle debug mode"""
        self.settings.behavior.debug_mode = not self.settings.behavior.debug_mode
        self.app.settings.behavior.debug_mode = self.settings.behavior.debug_mode
        status = "ON" if self.settings.behavior.debug_mode else "OFF"
        print(f"Debug mode: {status}")

    def _toggle_logging(self):
        """Toggle file logging"""
        self.settings.log_to_file = not self.settings.log_to_file

        if self.settings.log_to_file:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.settings.log_file_path = f"chatterm_log_{timestamp}.txt"
            print(f"Logging enabled: {self.settings.log_file_path}")

            setup_logging(self.settings)
            patch_print()
            logger.log_event("SESSION", "Logging enabled from settings menu")
        else:
            print("Logging disabled")
            if logger.enabled:
                logger.log_event("SESSION", "Logging disabled from settings menu")
                restore_print()
                logger.disable()
            self.settings.log_file_path = None

    def _toggle_timestamps(self):
        """Toggle timestamps"""
        self.settings.display.show_timestamp = not self.settings.display.show_timestamp
        self.app.settings.display.show_timestamp = self.settings.display.show_timestamp
        # Recreate display with new settings
        from .display import Display
        self.app.display = Display(self.app.settings.display)
        status = "ON" if self.settings.display.show_timestamp else "OFF"
        print(f"Timestamps: {status}")

    def _toggle_color(self):
        """Toggle color output"""
        self.settings.display.color_output = not self.settings.display.color_output
        self.app.settings.display.color_output = self.settings.display.color_output
        # Recreate display with new settings
        from .display import Display
        self.app.display = Display(self.app.settings.display)
        status = "ON" if self.settings.display.color_output else "OFF"
        print(f"Color output: {status}")

    def _show_info(self):
        """Show info about ChatTerm"""
        print("\n" + "-" * 50)
        print("About ChatTerm")
        print("-" * 50)
        print("\nChatTerm is a text-based CLI for testing Chatforge.")
        print("It supports both simple LLM mode and agent mode with tools.")
        print("\nModes:")
        print("  Simple - Direct LLM calls, good for prompt testing")
        print("  Agent  - ReActAgent with tool support")
        print("\n" + "-" * 50)
        print("\nPress ENTER to continue...")
        input()

    def _go_back(self):
        """Go back to main menu"""
        self.current_state = MenuState.MAIN

    def _quit(self):
        """Quit the application"""
        print("\nGoodbye!")
        if self.settings.log_to_file:
            logger.log_event("SESSION", "User quit from menu")
        self.running = False

        # Clean up logging if enabled
        if logger.enabled:
            restore_print()
            logger.disable()
