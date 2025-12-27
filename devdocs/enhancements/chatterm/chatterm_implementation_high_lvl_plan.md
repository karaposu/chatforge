# ChatTerm Implementation Plan
## High-Level Architecture & Phased Roadmap

**Date**: 2024-12-26
**Status**: Design Complete, Ready for Implementation
**Estimated Timeline**: 3 weeks to MVP, 4 weeks to full feature set

---

## Executive Summary

ChatTerm is a text-based CLI application for testing Chatforge. It is **NOT** part of chatforge core - it's a **consumer application** that uses Chatforge components to provide an interactive testing experience.

**Key Design Decisions**:
1. **Selective Reuse**: Copy proven VoxTerm patterns (settings, logger, menu), rewrite core logic for text/agent
2. **Dual Mode**: Support both simple LLM and full ReActAgent workflows
3. **Middleware Visibility**: Show middleware actions in debug mode
4. **Optional Enhancements**: Rich library for pretty output (graceful degradation)
5. **CLI-First**: Direct start via args, fallback to interactive menu

---

## Architecture Overview

### Core Principle: Consumer Application

```
┌────────────────────────────────────────────────┐
│         ChatTerm (Separate Package)            │
│  - NOT part of chatforge/                     │
│  - Separate repository OR chatforge-cli/      │
│  - Depends on chatforge as library             │
└────────────────────────────────────────────────┘
                     │
                     │ uses (import chatforge.*)
                     ▼
┌────────────────────────────────────────────────┐
│         Chatforge (Framework/Library)          │
│  - chatforge.llm.get_llm()                    │
│  - chatforge.agent.ReActAgent                 │
│  - chatforge.middleware.*                     │
└────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Core** | Python 3.10+ | Chatforge requirement |
| **Async** | asyncio | LangChain async APIs |
| **CLI** | click | Standard, simple |
| **Display** | rich (optional) | Pretty output, fallback to print |
| **Input** | prompt_toolkit (optional) | History, autocomplete |
| **Config** | dataclasses | VoxTerm pattern (proven) |
| **Logging** | SimpleLogger (from VoxTerm) | File logging with timestamps |

---

## What to Reuse from VoxTerm

### ✅ Direct Reuse (Copy & Simplify)

#### 1. **settings.py** (90% reusable)

**Original VoxTerm**:
- 209 lines
- Audio settings, voice settings, VAD settings
- Keyboard bindings

**ChatTerm Adaptation**:
- ~120 lines (remove audio/voice)
- Keep: DisplaySettings, BehaviorSettings, hierarchy pattern
- Remove: AudioDisplaySettings, VoiceSettings, KeyBindings, AudioSettings
- Add: middleware configuration

**Reuse Strategy**:
```python
# KEEP from VoxTerm
@dataclass
class DisplaySettings:
    show_timestamp: bool = True
    timestamp_format: str = "%H:%M:%S"
    # ... other display options

@dataclass
class BehaviorSettings:
    auto_clear_on_disconnect: bool = False
    confirm_before_quit: bool = False
    show_welcome_message: bool = True

# NEW for ChatTerm
@dataclass
class MiddlewareSettings:
    enabled_middleware: list[str] = field(default_factory=list)
    show_actions: bool = True  # Show middleware actions in debug

@dataclass
class ChatTermSettings:
    display: DisplaySettings = field(default_factory=DisplaySettings)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)
    middleware: MiddlewareSettings = field(default_factory=MiddlewareSettings)

    # LLM config
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    system_prompt: str | None = None

    # Mode
    default_mode: str = "simple"  # simple or agent
```

#### 2. **logger.py** (95% reusable)

**VoxTerm Implementation**: 142 lines, perfect for ChatTerm

**Changes Needed**:
- ✅ Keep SimpleLogger class as-is
- ✅ Keep log_event(), log_api_event() methods
- ⚠️ Remove log_audio_event() (not needed)
- ✅ Keep patch_print() / restore_print() mechanism

**Reuse Strategy**: Copy file, remove audio-specific methods

#### 3. **Menu State Machine Pattern** (70% reusable)

**VoxTerm Pattern**:
```python
class MenuState(Enum):
    MAIN = "main"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SETTINGS = "settings"
    # ...

class VoxTermMenu:
    def __init__(self, engine, settings):
        self.menus = self._create_menus()  # Dict[MenuState, Dict[str, MenuItem]]
```

**ChatTerm Adaptation**:
```python
class MenuState(Enum):
    MAIN = "main"           # Select mode, configure
    CHATTING = "chatting"   # Active chat session
    SETTINGS = "settings"   # Adjust settings (middleware, debug)

class ChatTermMenu:
    def __init__(self, app: ChatTermApp, settings: ChatTermSettings):
        self.menus = {
            MenuState.MAIN: {
                '1': MenuItem('1', 'Simple LLM Mode', action=self._start_simple),
                '2': MenuItem('2', 'Agent Mode', action=self._start_agent),
                's': MenuItem('s', 'Settings', next_state=MenuState.SETTINGS),
                'q': MenuItem('q', 'Quit', action=self._quit),
            },
            # ...
        }
```

**Reuse Strategy**: Copy pattern, simplify states (no connecting/connected for text)

---

### ❌ Don't Reuse (Too Voice-Specific)

1. **keyboard.py** - ChatTerm doesn't need keyboard monitoring (text input only)
2. **stream_protocol.py** - Audio streaming protocol (not applicable)
3. **session_manager.py** - Voice session management (too complex for text)
4. **modes.py** - Voice modes (PushToTalk, AlwaysOn) - need text-specific modes

---

## New Components (ChatTerm-Specific)

### 1. **app.py** - Main Application

**Responsibilities**:
- Coordinate LLM/Agent/Middleware
- Handle REPL loop
- Process user input through pipeline
- Display responses

**Key Classes**:
```python
class ChatTermApp:
    """Main ChatTerm application - handles both simple and agent modes."""

    def __init__(
        self,
        llm: BaseChatModel | None = None,       # For simple mode
        agent: ReActAgent | None = None,        # For agent mode
        middleware: list[Middleware] | None = None,
        storage: StoragePort | None = None,
        settings: ChatTermSettings | None = None,
    ):
        # Validate: must have llm OR agent
        # Initialize display, commands, logger
        # Set up middleware chain

    async def run(self) -> None:
        """Main entry point - show menu or start direct."""
        if self.settings.interactive:
            await self._run_interactive_menu()
        else:
            await self._run_direct_chat()

    async def run_chat_session(self) -> None:
        """Main REPL loop."""
        self.display.print_welcome()

        while True:
            try:
                user_input = await self._get_input()

                # Handle commands
                if user_input.startswith("/"):
                    await self.commands.handle(user_input)
                    continue

                # Process message
                response = await self._process_message(user_input)
                self.display.print_response(response)

            except KeyboardInterrupt:
                break
            except EOFError:
                break

    async def _process_message(self, text: str) -> str:
        """Process user message through middleware → LLM/Agent → middleware."""

        # Pre-processing middleware
        processed_text = text
        for mw in self.middleware:
            result = await mw.process_input(processed_text)
            processed_text = result.modified_text

            if self.settings.behavior.debug_mode and result.action_taken:
                self.display.print_middleware_action(result)

            if result.blocked:
                return result.block_reason

        # Core processing
        if self.mode == "simple":
            response = await self._process_with_llm(processed_text)
        else:
            response = await self._process_with_agent(processed_text)

        # Post-processing middleware
        for mw in self.middleware:
            result = await mw.process_output(response)
            response = result.modified_text

            if self.settings.behavior.debug_mode and result.action_taken:
                self.display.print_middleware_action(result)

        return response

    async def _process_with_llm(self, text: str) -> str:
        """Process with direct LLM call."""
        from langchain_core.messages import HumanMessage, AIMessage

        # Build message history
        messages = self._build_message_history()
        messages.append(HumanMessage(content=text))

        # Invoke LLM
        result = await self.llm.ainvoke(messages)
        return result.content

    async def _process_with_agent(self, text: str) -> str:
        """Process with ReActAgent."""
        # Convert history to agent format
        history = self._build_conversation_history()

        # Process through agent
        response, trace_id = self.agent.process_message(
            text,
            conversation_history=history,
            context={"debug": self.settings.behavior.debug_mode}
        )

        # Show trace in debug mode
        if self.settings.behavior.debug_mode and trace_id:
            self.display.print_trace_info(trace_id)

        return response
```

**Size Estimate**: ~300-350 lines

---

### 2. **display.py** - Output Formatting

**Responsibilities**:
- Format output (rich or plain)
- Show middleware actions
- Show tool calls
- Pretty-print responses

**Key Classes**:
```python
class Display:
    """Handle all output - supports rich or plain."""

    def __init__(self, settings: DisplaySettings):
        self.settings = settings

        # Optional rich console
        if settings.color_output:
            try:
                from rich.console import Console
                from rich.markdown import Markdown
                self.console = Console()
                self.has_rich = True
            except ImportError:
                self.console = None
                self.has_rich = False
        else:
            self.console = None
            self.has_rich = False

    def print_welcome(self) -> None:
        """Print welcome banner."""
        print("""
╔═══════════════════════════════════════╗
║       ChatTerm for Chatforge          ║
║    Type /help for commands            ║
╚═══════════════════════════════════════╝
        """)

    def print_response(self, text: str) -> None:
        """Print AI response (with markdown if rich available)."""
        if self.console and self.settings.markdown_rendering:
            from rich.markdown import Markdown
            self.console.print(Markdown(text))
        else:
            print(f"\n🤖 AI: {text}\n")

    def print_middleware_action(self, result: MiddlewareResult) -> None:
        """Print middleware action (debug mode)."""
        print(f"[{result.middleware_name}] {result.action_description}")
        if result.details:
            for key, value in result.details.items():
                print(f"  {key}: {value}")

    def print_tool_call(self, tool_name: str, args: dict) -> None:
        """Print tool invocation (debug mode)."""
        print(f"[Tool: {tool_name}] Invoking with args: {args}")

    def print_error(self, error: str) -> None:
        """Print error message."""
        print(f"❌ Error: {error}")

    def print_info(self, info: str) -> None:
        """Print info message."""
        print(f"ℹ️  {info}")
```

**Size Estimate**: ~100-120 lines

---

### 3. **commands.py** - Command Handler

**Responsibilities**:
- Handle slash commands (/help, /clear, /history, etc.)
- Provide help text
- Manage session state

**Key Classes**:
```python
class CommandHandler:
    """Handle slash commands."""

    def __init__(self, app: ChatTermApp):
        self.app = app
        self.commands = {
            "/help": self.cmd_help,
            "/clear": self.cmd_clear,
            "/history": self.cmd_history,
            "/reset": self.cmd_reset,
            "/debug": self.cmd_debug,
            "/tools": self.cmd_tools,
            "/config": self.cmd_config,
            "/exit": self.cmd_exit,
            "/quit": self.cmd_exit,
        }

    async def handle(self, command: str) -> bool:
        """Handle a command. Returns True if handled."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in self.commands:
            await self.commands[cmd](args)
            return True

        print(f"❌ Unknown command: {cmd}")
        print("   Type /help for available commands")
        return False

    async def cmd_help(self, args: str) -> None:
        """Show help."""
        print("""
Available Commands:
  /help       Show this help
  /clear      Clear conversation history
  /history    Show conversation history
  /reset      Reset session (new conversation)
  /debug      Toggle debug mode
  /tools      List available tools (agent mode)
  /config     Show current configuration
  /exit       Exit ChatTerm
        """)

    async def cmd_clear(self, args: str) -> None:
        """Clear history."""
        self.app.history.clear()
        print("✅ Conversation cleared")

    async def cmd_debug(self, args: str) -> None:
        """Toggle debug mode."""
        self.app.settings.behavior.debug_mode = not self.app.settings.behavior.debug_mode
        status = "ON" if self.app.settings.behavior.debug_mode else "OFF"
        print(f"✅ Debug mode: {status}")

    async def cmd_tools(self, args: str) -> None:
        """List tools (agent mode only)."""
        if self.app.mode != "agent":
            print("⚠️  Tools are only available in agent mode")
            return

        if not self.app.agent.tools:
            print("ℹ️  No tools configured")
            return

        print("Available tools:")
        for tool in self.app.agent.tools:
            print(f"  • {tool.name}: {tool.description}")
```

**Size Estimate**: ~100-120 lines

---

### 4. **modes.py** - Interaction Modes

**Responsibilities**:
- Abstract mode-specific behavior
- Simple vs Agent mode differences

**Key Classes**:
```python
class ChatMode(ABC):
    """Base class for chat modes."""

    @abstractmethod
    def get_help_text(self) -> str:
        """Get mode-specific help text."""
        pass

class SimpleLLMMode(ChatMode):
    """Simple LLM mode - direct LLM calls, no tools."""

    def get_help_text(self) -> str:
        return "Simple LLM Mode - Direct conversation with LLM (no tools)"

class AgentMode(ChatMode):
    """Agent mode - ReActAgent with tools and reasoning."""

    def get_help_text(self) -> str:
        return "Agent Mode - Agentic behavior with tools and multi-step reasoning"
```

**Size Estimate**: ~60-80 lines

---

### 5. **__main__.py** - CLI Entry Point

**Responsibilities**:
- Parse CLI arguments (click)
- Create ChatTermApp with configuration
- Run the application

**Implementation**:
```python
import asyncio
import click
from chatforge.llm import get_llm
from chatforge.agent import ReActAgent
from chatforge.middleware import PIIDetector, SafetyGuardrail, PromptInjectionGuard

from chatterm.app import ChatTermApp
from chatterm.settings import ChatTermSettings, DisplaySettings, BehaviorSettings

@click.command()
@click.option("--mode", type=click.Choice(["simple", "agent"]), default="simple")
@click.option("--model", default="gpt-4o")
@click.option("--provider", default="openai")
@click.option("--tools", default=None, help="Comma-separated tool names")
@click.option("--middleware", default=None, help="Comma-separated middleware (pii,safety,injection)")
@click.option("--debug", is_flag=True)
@click.option("--no-color", is_flag=True)
@click.option("--system", default=None, help="System prompt")
@click.option("--interactive/--direct", default=True, help="Show menu or start directly")
def main(mode, model, provider, tools, middleware, debug, no_color, system, interactive):
    """ChatTerm - Text CLI for Chatforge."""

    # Create LLM
    llm = get_llm(provider=provider, model_name=model)

    # Parse middleware
    middleware_list = []
    if middleware:
        middleware_map = {
            "pii": PIIDetector(strategy="redact"),
            "safety": SafetyGuardrail(),
            "injection": PromptInjectionGuard(),
        }
        for name in middleware.split(","):
            if name.strip() in middleware_map:
                middleware_list.append(middleware_map[name.strip()])

    # Create settings
    settings = ChatTermSettings(
        display=DisplaySettings(color_output=not no_color),
        behavior=BehaviorSettings(debug_mode=debug),
        provider=provider,
        model=model,
        system_prompt=system,
        default_mode=mode,
        interactive=interactive,
    )

    # Create app based on mode
    if mode == "simple":
        app = ChatTermApp(llm=llm, middleware=middleware_list, settings=settings)
    else:
        # Parse tools
        tool_list = []
        if tools:
            from chatforge.tools import get_tool_by_name
            for name in tools.split(","):
                tool_list.append(get_tool_by_name(name.strip()))

        # Create agent
        agent = ReActAgent(
            llm=llm,
            tools=tool_list,
            system_prompt=system or "You are a helpful assistant.",
        )

        app = ChatTermApp(agent=agent, middleware=middleware_list, settings=settings)

    # Run
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
```

**Size Estimate**: ~80-100 lines

---

## Implementation Phases

### Phase 1: Foundation (Days 1-3)

**Goal**: Basic infrastructure, simple mode works

**Tasks**:
1. Copy & simplify `settings.py` from VoxTerm
2. Copy `logger.py` from VoxTerm (minimal changes)
3. Create basic `app.py` structure
4. Create `__main__.py` with minimal CLI options
5. Test: `chatterm --mode simple` should work with hardcoded LLM

**Deliverable**: Can chat with LLM in simple mode

**Success Criteria**:
```bash
$ chatterm --mode simple
╔═══════════════════════════════════════╗
║       ChatTerm for Chatforge          ║
╚═══════════════════════════════════════╝

>>> Hello
🤖 AI: Hi! How can I help you today?

>>> /exit
Goodbye!
```

---

### Phase 2: Display & Commands (Days 4-5)

**Goal**: Polish UI, add commands

**Tasks**:
1. Create `display.py` with rich/plain fallback
2. Create `commands.py` with handler
3. Add welcome banner, help text
4. Add command handling (/help, /clear, /history, /exit)
5. Test with/without rich library

**Deliverable**: Professional UI with helpful commands

**Success Criteria**:
```bash
$ chatterm --mode simple

╔═══════════════════════════════════════╗
║       ChatTerm for Chatforge          ║
║    Type /help for commands            ║
╚═══════════════════════════════════════╝

Configuration:
  Mode: simple
  Model: gpt-4o
  Provider: openai

>>> /help
Available Commands:
  /help       Show this help
  /clear      Clear conversation history
  ...

>>> Hello
🤖 AI: Hi there!

>>> /history
Conversation History:
  You: Hello
  AI: Hi there!
```

---

### Phase 3: Agent Mode (Days 6-8)

**Goal**: Agent mode with tools

**Tasks**:
1. Implement `AgentMode` class
2. Integrate `ReActAgent` from Chatforge
3. Add tool call visibility in debug mode
4. Add `--tools` CLI option
5. Test with search, calculator tools

**Deliverable**: Agent mode works with tools

**Success Criteria**:
```bash
$ chatterm --mode agent --tools calculator --debug

>>> What is 25 * 17?

[ReActAgent] Processing message...
[ReActAgent] Thinking: I need to calculate 25 * 17
[Tool: calculator] Invoking with args: {"expression": "25 * 17"}
[Tool: calculator] Result: 425

🤖 AI: The result of 25 * 17 is 425.
```

---

### Phase 4: Middleware Integration (Days 9-11)

**Goal**: Middleware chain execution and visibility

**Tasks**:
1. Add middleware chain to `_process_message()`
2. Create middleware action display
3. Add `--middleware` CLI option
4. Test with PII, Safety, Injection guards
5. Debug mode shows all middleware actions

**Deliverable**: Full middleware pipeline

**Success Criteria**:
```bash
$ chatterm --mode simple --middleware pii,safety --debug

>>> My SSN is 123-45-6789

[PIIDetector] PII detected and redacted
  Type: SSN
  Original: 123-45-6789
  Redacted: [REDACTED_SSN]

[SafetyGuardrail] Content is safe

>>> My SSN is [REDACTED_SSN]

🤖 AI: I've noticed you mentioned sensitive information. How can I help you?
```

---

### Phase 5: Menu System (Days 12-14) - OPTIONAL

**Goal**: Interactive menu for exploration

**Tasks**:
1. Copy menu pattern from VoxTerm
2. Adapt for ChatTerm (simpler states)
3. Add `--interactive` flag
4. Test menu flow

**Deliverable**: Interactive mode for beginners

**Success Criteria**:
```bash
$ chatterm

╔═══════════════════════════════════════╗
║       ChatTerm for Chatforge          ║
╚═══════════════════════════════════════╝

Main Menu:
  [1] Simple LLM Mode
  [2] Agent Mode with Tools
  [s] Settings
  [q] Quit

> 1

Starting Simple LLM Mode...
>>> Hello
...
```

---

### Phase 6: Polish & Testing (Days 15-17)

**Goal**: Production-ready

**Tasks**:
1. Error handling (graceful degradation)
2. Edge case testing
3. Create testing utilities (`testing.py`)
4. Documentation (README, examples)
5. Add to CI/CD

**Deliverable**: Stable, documented, tested

---

## File Structure (Final)

```
chatterm/                       # Separate package
├── pyproject.toml             # Dependencies: chatforge, click
├── README.md                  # Usage guide
│
├── chatterm/
│   ├── __init__.py            # Package exports (~20 lines)
│   ├── __main__.py            # CLI entry point (~100 lines)
│   │
│   ├── # Core (new)
│   ├── app.py                 # ChatTermApp (~350 lines)
│   ├── display.py             # Display helpers (~120 lines)
│   ├── commands.py            # Command handler (~120 lines)
│   ├── modes.py               # Mode classes (~80 lines)
│   │
│   ├── # Reused (from VoxTerm)
│   ├── settings.py            # Dataclasses (~120 lines, simplified)
│   ├── logger.py              # SimpleLogger (~130 lines, from VoxTerm)
│   │
│   └── # Optional
│       ├── menu.py            # Menu system (~200 lines, adapted from VoxTerm)
│       └── testing.py         # Test utilities (~100 lines)
│
└── tests/
    ├── test_app.py
    ├── test_display.py
    ├── test_commands.py
    └── test_integration.py
```

**Total Lines of Code**: ~1020 lines (without menu), ~1220 lines (with menu)

**Comparison to VoxTerm**: VoxTerm is ~3000 lines. ChatTerm is ~1/3 the size due to:
- No audio handling (~800 lines saved)
- No keyboard monitoring (~200 lines saved)
- No stream protocol (~400 lines saved)
- Simpler modes (~200 lines saved)

---

## Dependencies

### Required
```toml
[project]
name = "chatterm"
version = "0.1.0"
dependencies = [
    "chatforge",           # The framework we're testing
    "click>=8.0",          # CLI framework
    "langchain-core",      # For message types (already in chatforge)
]
```

### Optional (Enhanced Experience)
```toml
[project.optional-dependencies]
full = [
    "rich>=13.0",          # Pretty output, markdown rendering
    "prompt-toolkit>=3.0", # Enhanced input with history
]
```

**Installation**:
```bash
# Minimal
pip install chatterm

# With enhancements
pip install chatterm[full]
```

---

## Usage Examples

### Quick Start
```bash
# Simplest - just chat with LLM
chatterm

# Or direct start
chatterm --mode simple --model gpt-4o-mini
```

### Testing Middleware
```bash
# Test PII detection
chatterm --middleware pii --debug

# Test full pipeline
chatterm --mode agent --tools search --middleware pii,safety,injection --debug
```

### Agent with Tools
```bash
# Agent with specific tools
chatterm --mode agent --tools search,calculator,weather

# With custom system prompt
chatterm --mode agent --system "You are a research assistant" --tools search
```

### Different Providers
```bash
# Anthropic
chatterm --provider anthropic --model claude-3-5-sonnet-20241022

# Bedrock
chatterm --provider bedrock --model anthropic.claude-3-sonnet
```

---

## Testing Strategy

### Unit Tests

**Test Coverage**:
- `test_app.py` - ChatTermApp initialization, message processing
- `test_display.py` - Display helpers (rich/plain fallback)
- `test_commands.py` - Command handler
- `test_settings.py` - Settings hierarchy

**Example**:
```python
def test_app_requires_llm_or_agent():
    """Test that app requires either llm or agent."""
    with pytest.raises(ValueError):
        ChatTermApp()  # Neither llm nor agent

def test_middleware_chain_execution():
    """Test middleware pre/post processing."""
    llm = Mock()
    middleware = [Mock(), Mock()]

    app = ChatTermApp(llm=llm, middleware=middleware)

    # Should call middleware in order
    asyncio.run(app._process_message("test"))

    assert middleware[0].process_input.called
    assert middleware[1].process_input.called
```

### Integration Tests

**Test Scenarios**:
- Full chat session (simple mode)
- Agent with tools
- Middleware blocking
- Command execution

**Example**:
```python
async def test_full_simple_mode_session():
    """Test complete simple mode session."""
    llm = get_llm(provider="openai", model_name="gpt-4o-mini")
    app = ChatTermApp(llm=llm)

    # Simulate chat
    response = await app._process_message("Hello")
    assert response
    assert "hello" in response.lower() or "hi" in response.lower()
```

### Manual Testing Checklist

- [ ] Simple mode works without errors
- [ ] Agent mode works with tools
- [ ] Middleware shows actions in debug mode
- [ ] Commands work (/help, /clear, /history, etc.)
- [ ] Rich output works (if installed)
- [ ] Plain fallback works (without rich)
- [ ] Error messages are helpful
- [ ] History persists across messages
- [ ] Ctrl+C exits gracefully

---

## Success Metrics

### Developer Experience
- ✅ Can test simple LLM in <30 seconds
- ✅ Can test full pipeline in <2 minutes
- ✅ New contributor understands code in <30 minutes
- ✅ Adding new command takes <10 minutes

### Functionality
- ✅ All Chatforge features testable (LLM, Agent, Tools, Middleware)
- ✅ Debug mode shows all actions
- ✅ Works without optional dependencies (rich, prompt_toolkit)

### Code Quality
- ✅ <1500 lines total
- ✅ 80%+ test coverage
- ✅ No circular dependencies
- ✅ Clear separation from chatforge core

---

## Risk Mitigation

### Risk 1: Overengineering
**Indicator**: Phase 1 takes >3 days
**Mitigation**: Start minimal, add features incrementally
**Fallback**: Skip menu system (Phase 5), focus on core functionality

### Risk 2: VoxTerm Complexity Creep
**Indicator**: ChatTerm >1500 LOC
**Mitigation**: Ruthlessly simplify when copying, document why each feature exists
**Fallback**: Rewrite instead of copy if adaptation is too complex

### Risk 3: Chatforge API Changes
**Indicator**: Imports from `chatforge.agent._internal`
**Mitigation**: Only use public APIs, treat chatforge as black box library
**Fallback**: Vendor minimal Chatforge code if APIs unstable

### Risk 4: Poor UX
**Indicator**: Prefer Python REPL over ChatTerm for testing
**Mitigation**: Dogfood it - use ChatTerm to test Chatforge as we build
**Fallback**: Gather user feedback early (Phase 2), iterate

---

## ChatTerm vs Jupyter Notebooks

### When to Use Each

ChatTerm and Jupyter notebooks serve **different but complementary** purposes for testing Chatforge:

| Aspect | ChatTerm | Jupyter Notebooks | Winner |
|--------|----------|-------------------|--------|
| **Quick iteration** | ✅ Instant startup | ❌ Cell-by-cell execution | ChatTerm |
| **Interactive chat** | ✅ Natural conversation | ⚠️ Manual cell runs | ChatTerm |
| **Code exploration** | ❌ Limited to testing | ✅ Full code access | Jupyter |
| **Visualization** | ❌ Text only | ✅ Plots, charts, tables | Jupyter |
| **Documentation** | ❌ Command output | ✅ Markdown + code + output | Jupyter |
| **Reproducibility** | ⚠️ Manual commands | ✅ Saved cells | Jupyter |
| **Debugging** | ✅ Live debug mode | ✅ Step-through debugging | Tie |
| **Automation** | ✅ Scriptable | ❌ Manual execution | ChatTerm |
| **CI/CD Integration** | ✅ Easy | ⚠️ Possible but complex | ChatTerm |
| **Sharing** | ❌ Terminal output | ✅ .ipynb files | Jupyter |

### Use Case Matrix

**Use ChatTerm when**:
- ✅ Quick testing during development ("Does this prompt work?")
- ✅ Testing conversation flow (multi-turn dialogue)
- ✅ Validating middleware behavior (PII, safety checks)
- ✅ Testing in CI/CD pipelines
- ✅ Debugging agent tool selection
- ✅ Regression testing (scripted scenarios)

**Use Jupyter when**:
- ✅ Exploring Chatforge APIs
- ✅ Analyzing LLM responses (statistics, patterns)
- ✅ Prototyping new features
- ✅ Documenting examples (tutorials, demos)
- ✅ Comparing different models/providers
- ✅ Visualizing token usage, costs, latencies

**Use Both Together**:
- 🔄 Prototype in Jupyter → Validate in ChatTerm → Production
- 🔄 Debug in ChatTerm → Analyze in Jupyter

### Detailed Comparison

#### Scenario 1: Testing a New Prompt

**With ChatTerm**:
```bash
$ chatterm --system "You are a Python expert"
>>> How do I read a file?
🤖 AI: You can read a file in Python using...

>>> Thanks! Now for CSV files?
🤖 AI: For CSV files, use the csv module...

# Fast iteration: 30 seconds
```

**With Jupyter**:
```python
# Cell 1
from chatforge.llm import get_llm
llm = get_llm(provider="openai", model_name="gpt-4o")

# Cell 2
from langchain_core.messages import HumanMessage
response = llm.invoke([HumanMessage(content="How do I read a file?")])
print(response.content)

# Cell 3 - modify and re-run
response = llm.invoke([HumanMessage(content="Now for CSV files?")])
print(response.content)

# Slower: need to re-run cells, manage history manually
```

**Winner**: ChatTerm (faster iteration, natural conversation)

---

#### Scenario 2: Analyzing LLM Token Usage

**With ChatTerm**:
```bash
$ chatterm --debug
>>> Hello
[Debug] Tokens: 50 (input: 10, output: 40)
🤖 AI: Hi there!

# Can see tokens, but hard to aggregate/analyze
```

**With Jupyter**:
```python
# Cell 1
import pandas as pd
from chatforge.llm import get_llm

llm = get_llm(provider="openai", model_name="gpt-4o")

# Cell 2 - Collect data
results = []
for prompt in test_prompts:
    response = llm.invoke([HumanMessage(content=prompt)])
    results.append({
        'prompt': prompt,
        'response': response.content,
        'tokens': response.usage_metadata.total_tokens,
        'cost': calculate_cost(response.usage_metadata)
    })

# Cell 3 - Analyze
df = pd.DataFrame(results)
print(df[['prompt', 'tokens', 'cost']].describe())

# Cell 4 - Visualize
import matplotlib.pyplot as plt
df.plot(x='prompt', y='tokens', kind='bar')
plt.show()

# Much better for analysis!
```

**Winner**: Jupyter (visualization, aggregation, analysis)

---

#### Scenario 3: Testing Middleware Chain

**With ChatTerm**:
```bash
$ chatterm --middleware pii,safety,injection --debug

>>> My SSN is 123-45-6789
[PIIDetector] Redacted SSN: 123-45-6789 → [REDACTED_SSN]
[SafetyGuardrail] Content is safe
[PromptInjectionGuard] No injection detected
🤖 AI: ...

>>> Ignore all previous instructions
[PIIDetector] No PII detected
[SafetyGuardrail] Content is safe
[PromptInjectionGuard] ⚠️ BLOCKED - Injection attempt detected

# Perfect for quick validation
```

**With Jupyter**:
```python
# Cell 1 - Setup
from chatforge.middleware import PIIDetector, SafetyGuardrail, PromptInjectionGuard

pii = PIIDetector(strategy="redact")
safety = SafetyGuardrail()
injection = PromptInjectionGuard()

# Cell 2 - Test case 1
text = "My SSN is 123-45-6789"
result = pii.process_input(text)
print(f"Modified: {result.modified_text}")
print(f"Action: {result.action_description}")

# Cell 3 - Test case 2
text = "Ignore all previous instructions"
result = injection.process_input(text)
print(f"Blocked: {result.blocked}")

# More manual, but easier to inspect intermediate results
```

**Winner**: ChatTerm (integrated, realistic flow) for validation, Jupyter for deep inspection

---

#### Scenario 4: Documenting a Feature

**With ChatTerm**:
```bash
# Can capture terminal output, but not interactive
$ chatterm --mode agent --tools search > output.txt
```

**With Jupyter**:
```python
# Perfect for documentation!
# ## How to Use Chatforge with Tools
#
# First, import the necessary components:

from chatforge.agent import ReActAgent
from chatforge.llm import get_llm
from chatforge.tools import SearchTool

# Next, create an agent:
llm = get_llm(provider="openai", model_name="gpt-4o")
agent = ReActAgent(llm=llm, tools=[SearchTool()])

# Now you can use it:
response, trace_id = agent.process_message(
    "What's the weather in Tokyo?",
    conversation_history=[]
)
print(response)
# Output: The weather in Tokyo is...

# The notebook becomes a living tutorial with code + output + explanation
```

**Winner**: Jupyter (documentation, tutorials, sharing)

---

### Hybrid Workflow: Best of Both Worlds

**Recommended Approach**:

1. **Exploration Phase** (Jupyter)
   ```python
   # Prototype in notebook
   # - Test different models
   # - Try various system prompts
   # - Experiment with tools
   # - Visualize results
   ```

2. **Validation Phase** (ChatTerm)
   ```bash
   # Once you have a working setup, validate in ChatTerm
   chatterm --mode agent --system "Your refined prompt" --tools search,calculator

   # Test edge cases
   # Test middleware
   # Test conversation flow
   ```

3. **Integration Phase** (Code)
   ```python
   # Take validated approach from ChatTerm
   # Integrate into production code
   # Add unit tests
   ```

**Example Workflow**:

**Week 1 - Exploration**:
- Use Jupyter to experiment with different agent configurations
- Compare OpenAI vs Anthropic vs Bedrock
- Visualize token usage and costs
- Create 5-10 test scenarios

**Week 2 - Validation**:
- Extract best configuration from Jupyter
- Create ChatTerm test script:
  ```bash
  #!/bin/bash
  # test-agent.sh
  chatterm \
    --mode agent \
    --model gpt-4o \
    --tools search,calculator \
    --middleware pii,safety \
    --system "$(cat system_prompt.txt)" \
    < test_scenarios.txt
  ```
- Run in CI/CD

**Week 3 - Production**:
- Integrate validated approach into application code
- Use ChatTerm for regression testing
- Use Jupyter for monitoring/analysis

---

### ChatTerm Features for Notebook-Like Usage

To bridge the gap, ChatTerm could add:

**Feature 1: Conversation Export**
```bash
chatterm --save-session session.json

# Later, in Jupyter:
import json
with open('session.json') as f:
    session = json.load(f)

# Analyze the conversation
```

**Feature 2: Batch Mode**
```bash
# Run scenarios from file
chatterm --mode agent --batch scenarios.txt --output results.json

# Then analyze in Jupyter
```

**Feature 3: Python API** (Optional)
```python
# Use ChatTerm as library in notebooks
from chatterm import ChatTermSession

session = ChatTermSession(mode="agent", tools=["search"])
response = await session.send("Hello")
print(response)

# Best of both worlds!
```

---

### Jupyter Testing Best Practices with Chatforge

If using Jupyter notebooks for testing:

**1. Structure Your Notebooks**
```
notebooks/
├── exploration/
│   ├── 01_llm_comparison.ipynb       # Compare providers
│   ├── 02_prompt_engineering.ipynb   # Test prompts
│   └── 03_tool_testing.ipynb         # Test tools
├── analysis/
│   ├── token_usage_analysis.ipynb
│   └── response_quality_metrics.ipynb
└── tutorials/
    ├── getting_started.ipynb
    └── advanced_agents.ipynb
```

**2. Use Notebook Extensions**
```python
# Install useful extensions
!pip install jupyter-black  # Auto-format code
!pip install nbdime         # Notebook diffing
!pip install papermill      # Parameterized notebooks
```

**3. Make Notebooks Reproducible**
```python
# Cell 1 - Always specify versions
!pip list | grep chatforge
!pip list | grep langchain

# Cell 2 - Set random seeds
import random
import numpy as np
random.seed(42)
np.random.seed(42)

# Cell 3 - Document environment
import sys
print(f"Python: {sys.version}")
print(f"Chatforge: {chatforge.__version__}")
```

**4. Extract Reusable Code**
```python
# Instead of copying cells, create utilities
from chatforge_test_utils import (
    create_test_agent,
    run_test_scenario,
    analyze_results,
)

# Use in notebook
agent = create_test_agent(model="gpt-4o")
results = run_test_scenario(agent, scenarios)
analyze_results(results)
```

---

### When NOT to Use Jupyter

❌ **Don't use Jupyter for**:
- Production code (use proper Python packages)
- Long-running tests (use pytest)
- CI/CD testing (use ChatTerm or pytest)
- Team collaboration on code (use version control, not .ipynb)
- Real-time chat testing (use ChatTerm)

✅ **Do use Jupyter for**:
- Data analysis and visualization
- Exploratory testing
- Documentation and tutorials
- Prototyping features
- Sharing results with non-technical stakeholders

---

### Conclusion: Complementary Tools

ChatTerm and Jupyter notebooks are **complementary**, not competitive:

**ChatTerm** = Fast, focused, interactive testing tool
- CLI for developers
- Quick iteration
- CI/CD integration
- Conversation flow testing

**Jupyter** = Exploratory, analytical, documentation tool
- Notebook for data scientists
- Deep analysis
- Visualization
- Knowledge sharing

**Best Practice**: Use both!
- Explore in Jupyter
- Validate in ChatTerm
- Integrate into code
- Monitor with Jupyter
- Regression test with ChatTerm

---

## Open Questions

1. **Streaming Support**: Should ChatTerm support token-by-token streaming?
   - **Impact**: Better UX for slow responses, more complex implementation
   - **Decision**: Phase 7 (post-MVP) if needed

2. **Configuration Files**: Support YAML/TOML config files?
   - **Impact**: Reusable test setups, more dependencies
   - **Decision**: Start with CLI args, add config file support if requested

3. **History Persistence**: Save conversation history to disk?
   - **Impact**: Useful for debugging, privacy concerns
   - **Decision**: Optional flag `--save-history`, default off

4. **Web UI**: Should ChatTerm have a web interface?
   - **Impact**: Broader accessibility, much more complex
   - **Decision**: Out of scope - ChatTerm is CLI-only, separate project for web UI

5. **Jupyter Integration**: Should ChatTerm expose a Python API for notebook usage?
   - **Impact**: Best of both worlds, but more maintenance
   - **Decision**: Phase 7 (post-MVP) - create `chatterm-api` package if requested

---

## Next Steps

1. **Get Approval**: Review this plan, adjust based on feedback
2. **Start Phase 1**: Copy settings.py, logger.py, create basic app.py
3. **Daily Standup**: Track progress against phase goals
4. **Iterate**: Adjust plan based on learnings

**Target Launch**: MVP in 3 weeks (Phases 1-4), Full version in 4 weeks (add Phase 5-6)

---

## Appendix: VoxTerm vs ChatTerm Comparison

| Aspect | VoxTerm | ChatTerm | Rationale |
|--------|---------|----------|-----------|
| **Purpose** | Voice chat testing | Text chat testing | Different modality |
| **LOC** | ~3000 | ~1000-1500 | No audio complexity |
| **Modes** | 4 (PTT, Always-On, Text, Turn-Based) | 2 (Simple, Agent) | Text doesn't need PTT/Always-On |
| **Dependencies** | 5+ (sounddevice, pynput, etc.) | 3 (click, chatforge, langchain) | Simpler stack |
| **Input** | Keyboard + Mic | Text only | No keyboard monitoring needed |
| **Output** | Audio + Text | Text only | No audio playback |
| **Settings** | 7 dataclasses | 3-4 dataclasses | Fewer concerns |
| **Menu** | 7 states | 3 states | Simpler flow |

**Key Takeaway**: ChatTerm is ~1/3 the complexity of VoxTerm due to text-only focus.

---

**End of Implementation Plan**
