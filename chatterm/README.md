# ChatTerm

Text-based CLI for testing Chatforge.

## Quick Start

```bash
# Install (from chatforge root)
pip install -e ./chatterm

# Or with optional dependencies
pip install -e "./chatterm[full]"

# Run
chatterm
```

## Usage

```bash
# Simple LLM mode (default)
chatterm

# Agent mode with tools
chatterm --mode agent

# Specify model
chatterm --model gpt-4o

# Debug mode
chatterm --debug --show-tokens --show-latency

# Different provider
chatterm --provider anthropic --model claude-3-5-sonnet-20241022
```

## Commands

Inside ChatTerm, use these slash commands:

- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/history` - Show conversation history
- `/debug` - Toggle debug mode
- `/tools` - List available tools (agent mode)
- `/config` - Show current configuration
- `/mode [simple|agent]` - Switch mode
- `/exit` - Exit ChatTerm

## Modes

### Simple Mode
Direct LLM calls without tools. Good for basic testing and prompt experimentation.

### Agent Mode
Uses Chatforge's ReActAgent with tool support. Enables complex multi-step reasoning.

## Optional Dependencies

- `rich` - Pretty colored output and markdown rendering
- `prompt-toolkit` - Enhanced input with history and autocomplete

```bash
pip install -e "./chatterm[rich]"      # Just rich
pip install -e "./chatterm[full]"      # All optional deps
```
