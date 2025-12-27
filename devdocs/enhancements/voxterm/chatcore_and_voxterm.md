# Chatforge CLI Architecture: ChatTerm and VoxTerm

*How CLI interfaces fit into Chatforge's hexagonal architecture.*

---

## The Insight

Chatforge is the **core framework** (agents, ports, adapters). CLIs are **presentation layers** that use Chatforge.

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interfaces                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│    ChatTerm     │    VoxTerm      │     Web UI / API            │
│   (text CLI)    │   (voice CLI)   │    (future)                 │
├─────────────────┴─────────────────┴─────────────────────────────┤
│                        Chatforge                                  │
│         (ReActAgent, Ports, Adapters)                           │
└─────────────────────────────────────────────────────────────────┘
```

**ChatTerm** = Text-based CLI using Chatforge
**VoxTerm** = Voice-based CLI using Chatforge + AudioStreamPort + RealtimeVoiceAPIPort

---

## Why Two CLIs?

| CLI | Input | Output | Use Case |
|-----|-------|--------|----------|
| **ChatTerm** | Keyboard typing | Text on screen | Coding, research, quiet environments |
| **VoxTerm** | Voice (microphone) | Voice (speaker) + text | Hands-free, accessibility, conversations |

They're different **modalities** for the same underlying AI capabilities.

---

## Architecture Comparison

### ChatTerm (Text CLI)

```
┌─────────────────────────────────────────────────────────────────┐
│                        ChatTerm                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Terminal UI                             │  │
│  │  - Input prompt (readline/prompt_toolkit)                  │  │
│  │  - Streaming text output                                   │  │
│  │  - Markdown rendering                                      │  │
│  │  - Command history                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Chatforge                               │  │
│  │  - ReActAgent                                              │  │
│  │  - MessagingPort → OpenAI/Anthropic adapter               │  │
│  │  - TicketingPort → Tool execution                            │  │
│  │  - StoragePort → Conversation history                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Ports used**: MessagingPort, TicketingPort, StoragePort, StreamingPort (for token streaming)

### VoxTerm (Voice CLI)

```
┌─────────────────────────────────────────────────────────────────┐
│                        VoxTerm                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Terminal UI                             │  │
│  │  - Audio level meter                                       │  │
│  │  - Transcript display                                      │  │
│  │  - Status indicators (listening/speaking)                  │  │
│  │  - Command input (for /commands)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Chatforge                               │  │
│  │  - VoiceAgent                                              │  │
│  │  - AudioStreamPort → VoxStream adapter                    │  │
│  │  - RealtimeVoiceAPIPort → OpenAI Realtime adapter                 │  │
│  │  - TicketingPort → Tool execution                            │  │
│  │  - StoragePort → Conversation history                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Ports used**: AudioStreamPort, RealtimeVoiceAPIPort, TicketingPort, StoragePort

---

## Should Chatforge Include ChatTerm?

### Option A: ChatTerm Inside Chatforge

```
chatforge/
├── ports/
├── adapters/
├── agent/
└── cli/
    ├── __init__.py
    ├── chatterm.py      # Text CLI
    └── voxterm.py       # Voice CLI (requires voxstream)
```

**Pros**:
- Single package to install
- Tight integration
- Unified versioning

**Cons**:
- CLI dependencies in core library
- VoxTerm needs VoxStream (extra dependency)
- Mixes library with application

### Option B: Separate Packages (RECOMMENDED)

```
chatforge/           # Library only (ports, adapters, agents)
chatterm/           # Text CLI (depends on chatforge)
voxterm/            # Voice CLI (depends on chatforge + voxstream)
```

**Pros**:
- Clean separation
- Install only what you need
- Chatforge stays a pure library
- VoxStream dependency isolated to VoxTerm

**Cons**:
- Multiple packages to maintain
- Version coordination

### Option C: ChatTerm in Chatforge, VoxTerm Separate

```
chatforge/
├── ports/
├── adapters/
├── agent/
└── cli/
    └── chatterm.py      # Basic text CLI included

voxterm/                 # Voice CLI separate
```

**Pros**:
- Basic CLI available immediately
- Voice-specific stuff isolated
- Common use case (text) bundled

**Cons**:
- Asymmetric structure
- Where to draw the line?

---

## Recommendation: Option B (Separate Packages)

Chatforge is a **library**. CLIs are **applications** that use the library.

```
┌─────────────────────────────────────────────────────────────────┐
│                         PACKAGES                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   chatforge   │   │   voxstream  │   │  voxterm     │         │
│  │   (library)  │   │   (library)  │   │  (app)       │         │
│  └──────────────┘   └──────────────┘   └──────────────┘         │
│         │                  │                  │                  │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────────────────────────────────────────────┐        │
│  │                      voxterm                         │        │
│  │            depends on: chatforge, voxstream           │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌──────────────┐                                               │
│  │   chatterm   │   (if we want a text CLI)                     │
│  │   (app)      │   depends on: chatforge                        │
│  └──────────────┘                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Installation Scenarios

```bash
# Just the library (for building apps)
pip install chatforge

# Text CLI
pip install chatterm  # pulls in chatforge

# Voice CLI
pip install voxterm   # pulls in chatforge + voxstream

# Everything
pip install chatforge voxstream chatterm voxterm
```

---

## ChatTerm Design

### Core Features

```python
# chatterm/main.py

import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown

from chatforge.agent import ReActAgent
from chatforge.adapters.messaging import OpenAIAdapter
from chatforge.adapters.storage import SQLiteAdapter


class ChatTerm:
    """Text-based CLI for Chatforge."""

    def __init__(
        self,
        agent: ReActAgent,
        console: Console | None = None,
    ):
        self.agent = agent
        self.console = console or Console()
        self.session = PromptSession(
            history=FileHistory(".chatterm_history"),
        )

    async def run(self) -> None:
        """Main REPL loop."""
        self.console.print("[bold]ChatTerm[/bold] - Type /help for commands\n")

        while True:
            try:
                user_input = await self.session.prompt_async("You: ")

                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                # Stream response
                self.console.print("\n[bold]Assistant:[/bold]")
                async for chunk in self.agent.stream_response(user_input):
                    self.console.print(chunk, end="")
                self.console.print("\n")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    async def _handle_command(self, command: str) -> None:
        match command.split()[0]:
            case "/help":
                self._show_help()
            case "/clear":
                self.agent.clear_history()
            case "/history":
                self._show_history()
            case "/exit" | "/quit":
                raise EOFError
            case _:
                self.console.print(f"Unknown command: {command}")

    def _show_help(self) -> None:
        self.console.print("""
Commands:
  /help     - Show this help
  /clear    - Clear conversation history
  /history  - Show conversation history
  /exit     - Exit ChatTerm
        """)
```

### Entry Point

```python
# chatterm/__main__.py

import asyncio
import click
from chatforge.agent import ReActAgent
from chatforge.adapters.messaging import OpenAIAdapter
from .main import ChatTerm


@click.command()
@click.option("--model", default="gpt-4o", help="Model to use")
@click.option("--system", default=None, help="System prompt")
def main(model: str, system: str | None):
    """ChatTerm - Text CLI for Chatforge."""
    agent = ReActAgent(
        messaging=OpenAIAdapter(model=model),
        system_prompt=system,
    )

    term = ChatTerm(agent)
    asyncio.run(term.run())


if __name__ == "__main__":
    main()
```

---

## VoxTerm Design

### Core Features

```python
# voxterm/main.py

import asyncio
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from chatforge.agent.voice import VoiceAgent
from chatforge.ports.realtime import VoiceEventType
from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.adapters.audio import VoxStreamAdapter


class VoxTerm:
    """Voice-based CLI for Chatforge."""

    def __init__(
        self,
        agent: VoiceAgent,
        console: Console | None = None,
    ):
        self.agent = agent
        self.console = console or Console()
        self._transcript = ""
        self._status = "idle"

    async def run(self) -> None:
        """Main voice loop."""
        self.console.print("[bold]VoxTerm[/bold] - Voice CLI")
        self.console.print("Press Ctrl+C to exit\n")

        # Start voice agent
        await self.agent.start()

        # Display loop
        with Live(self._render_ui(), refresh_per_second=10) as live:
            async for event in self.agent.events():
                self._handle_event(event)
                live.update(self._render_ui())

    def _handle_event(self, event) -> None:
        match event.type:
            case VoiceEventType.SPEECH_STARTED:
                self._status = "listening"
            case VoiceEventType.SPEECH_ENDED:
                self._status = "processing"
            case VoiceEventType.TRANSCRIPT:
                self._transcript = f"You: {event.data}"
            case VoiceEventType.RESPONSE_STARTED:
                self._status = "speaking"
            case VoiceEventType.RESPONSE_DONE:
                self._status = "idle"
            case VoiceEventType.TEXT_CHUNK:
                self._transcript += event.data

    def _render_ui(self) -> Panel:
        status_icon = {
            "idle": "[dim]Ready[/dim]",
            "listening": "[green]Listening...[/green]",
            "processing": "[yellow]Processing...[/yellow]",
            "speaking": "[blue]Speaking...[/blue]",
        }.get(self._status, self._status)

        return Panel(
            f"{status_icon}\n\n{self._transcript}",
            title="VoxTerm",
            border_style="blue",
        )
```

### Entry Point

```python
# voxterm/__main__.py

import asyncio
import click
from chatforge.agent.voice import VoiceAgent, VoiceAgentConfig
from chatforge.adapters.realtime import OpenAIRealtimeAdapter
from chatforge.adapters.audio import VoxStreamAdapter
from .main import VoxTerm


@click.command()
@click.option("--voice", default="alloy", help="AI voice")
@click.option("--system", default=None, help="System prompt")
def main(voice: str, system: str | None):
    """VoxTerm - Voice CLI for Chatforge."""
    config = VoiceAgentConfig(
        voice=voice,
        system_prompt=system,
    )

    agent = VoiceAgent(
        audio=VoxStreamAdapter(),
        realtime=OpenAIRealtimeAdapter(),
        config=config,
    )

    term = VoxTerm(agent)
    asyncio.run(term.run())


if __name__ == "__main__":
    main()
```

---

## Hybrid Mode: Voice + Text in VoxTerm

VoxTerm could support both voice AND text input:

```python
class VoxTerm:
    async def run(self) -> None:
        # Start voice in background
        voice_task = asyncio.create_task(self._voice_loop())

        # Also accept keyboard input
        keyboard_task = asyncio.create_task(self._keyboard_loop())

        await asyncio.gather(voice_task, keyboard_task)

    async def _keyboard_loop(self) -> None:
        """Handle slash commands and text input."""
        while True:
            line = await aioconsole.ainput()
            if line.startswith("/"):
                await self._handle_command(line)
            else:
                # Send text to voice agent (it can handle text too)
                await self.agent.send_text(line)
```

This way VoxTerm handles:
- `/help`, `/exit`, `/mute`, `/unmute` commands via keyboard
- Voice input via microphone
- Optional text input for quiet environments

---

## Package Structure

### chatforge (Library)

```
chatforge/
├── __init__.py
├── ports/
│   ├── messaging.py
│   ├── storage.py
│   ├── action.py
│   ├── audio_stream.py
│   └── realtime.py
├── adapters/
│   ├── messaging/
│   ├── storage/
│   ├── audio/
│   └── realtime/
└── agent/
    ├── engine.py      # ReActAgent
    └── voice.py       # VoiceAgent
```

### chatterm (Text CLI App)

```
chatterm/
├── __init__.py
├── __main__.py
├── main.py
├── ui/
│   ├── prompt.py
│   └── output.py
└── commands/
    ├── help.py
    └── history.py
```

**Dependencies**: `chatforge`, `prompt-toolkit`, `rich`, `click`

### voxterm (Voice CLI App)

```
voxterm/
├── __init__.py
├── __main__.py
├── main.py
├── ui/
│   ├── display.py
│   └── meters.py
└── commands/
    ├── help.py
    ├── mute.py
    └── voice.py
```

**Dependencies**: `chatforge`, `voxstream`, `rich`, `click`

---

## Naming Consideration

| Option | Text CLI | Voice CLI | Notes |
|--------|----------|-----------|-------|
| A | chatterm | voxterm | Current naming |
| B | chatcli | voicecli | More descriptive |
| C | ct | vt | Short aliases |
| D | chat | vox | Shortest |

Recommendation: Keep **chatterm** and **voxterm**. Clear, memorable, parallel structure.

---

## Comparison with Claude Code

| Feature | Claude Code | ChatTerm | VoxTerm |
|---------|-------------|----------|---------|
| Text input | Yes | Yes | Yes (keyboard commands) |
| Voice input | No | No | Yes |
| Voice output | No | No | Yes |
| Tool execution | Yes | Yes | Yes |
| Streaming | Yes | Yes | Yes (audio) |
| IDE integration | Yes | Future | Future |

ChatTerm and VoxTerm together provide similar capabilities to Claude Code, but with voice as a first-class citizen.

---

## Summary

### The Model

```
                    ┌─────────────────┐
                    │   chatforge      │  ← Library (pure)
                    │ (agents, ports) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │ chatterm │   │ voxterm  │   │ your-app │
       │(text CLI)│   │(voice CLI│   │ (custom) │
       └──────────┘   └──────────┘   └──────────┘
```

### Key Points

1. **Chatforge is a library**, not an application
2. **ChatTerm** = text CLI, depends only on Chatforge
3. **VoxTerm** = voice CLI, depends on Chatforge + VoxStream
4. **Separate packages** keep dependencies clean
5. **VoxTerm can be hybrid** (voice + keyboard commands)

### Why This Makes Sense

- **Hexagonal architecture**: CLI is just another adapter/interface
- **Single responsibility**: Chatforge does AI, CLIs do UI
- **Flexibility**: Use text, voice, or build your own interface
- **Testability**: Test Chatforge without CLI dependencies

---

## Related Documents

| Document | Topic |
|----------|-------|
| `chatforge_should_implement.md` | Chatforge enhancements |
| `how_can_chatforge_should_implement_voice_connection.md` | RealtimeVoiceAPIPort design |
| `chatforge_voxstream_high_level.md` | AudioStreamPort design |
