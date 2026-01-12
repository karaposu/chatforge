# Chatforge - Project Summary

## What is Chatforge?

Chatforge is a toolkit for building AI-powered chatbots and voice assistants. Think of it as a construction kit that lets developers create smart assistants that can:

- **Have conversations** - Remember what you said and respond intelligently
- **Talk and listen** - Support real-time voice conversations (like talking to Siri or Alexa)
- **Use tools** - Look things up, create tickets, search databases, and take actions
- **Stay safe** - Block harmful requests and protect private information

## The Big Picture

Imagine you're building a customer support chatbot. You need:

1. A brain (the AI that understands and responds)
2. A memory (to remember the conversation)
3. Hands (tools to actually do things like create tickets)
4. Ears and mouth (for voice conversations)
5. Security guards (to block bad actors)

Chatforge provides all of these as separate, swappable pieces. You can mix and match based on what you need.

## Core Capabilities

### 1. Intelligent Conversations

The heart of Chatforge is an "agent" - an AI that thinks before it acts. When you ask it something:

1. It **thinks** about what you want
2. It **decides** if it needs to use any tools
3. It **acts** by using those tools or responding directly
4. It **observes** the results
5. It **repeats** until your question is fully answered

This is like how a helpful assistant would work - not just answering blindly, but actually reasoning about what you need.

### 2. Voice Conversations

Chatforge supports real-time voice interactions using OpenAI's voice AI:

- You can speak naturally and get spoken responses
- The AI knows when you start and stop talking
- You can interrupt the AI mid-sentence ("barge-in")
- It transcribes what both you and the AI say

This enables building voice assistants, phone bots, or hands-free interfaces.

### 3. Multiple AI Providers

You're not locked into one AI company. Chatforge works with:

- **OpenAI** (ChatGPT, GPT-4)
- **Anthropic** (Claude)
- **AWS Bedrock** (various models)

Switch between them without rewriting your code.

### 4. Memory & Storage

Conversations are automatically saved and can be retrieved later. The system supports:

- **In-memory storage** - Fast but temporary (good for testing)
- **SQLite database** - Persistent storage in a file
- **Full database support** - For production systems

Old conversations are automatically cleaned up based on your settings.

### 5. Security & Safety

Three layers of protection:

- **Personal Information Detection (PII)** - Automatically finds and redacts emails, credit cards, phone numbers, social security numbers, and API keys before they're stored or sent anywhere

- **Prompt Injection Protection** - Detects when someone tries to trick the AI into doing bad things (like "ignore your instructions and do X")

- **Content Safety** - General guardrails to keep conversations appropriate

### 6. Extensibility with Tools

You can give the AI "tools" - actions it can take. For example:

- Search a knowledge base
- Create a support ticket
- Look up customer information
- Check order status

The AI decides when to use each tool based on the conversation.

## Architecture Philosophy

Chatforge uses a "plug-and-play" design. Each major function has:

1. **A Port** - A contract that says "here's what any implementation must do"
2. **Adapters** - Actual implementations that fulfill that contract

For example, the storage system:
- **Port**: "You must be able to save messages, retrieve history, and clean up old data"
- **Adapter 1**: SQLite (saves to a file)
- **Adapter 2**: In-memory (keeps in RAM)
- **Adapter 3**: PostgreSQL (real database)

This means you can swap SQLite for PostgreSQL without changing your application code.

## Current Development Status

The project is actively being developed. Key areas in progress:

- **Voice infrastructure** - Audio capture, playback, and voice activity detection are being refined with multiple adapter options
- **WebRTC support** - For browser-based voice interactions
- **Rate limiting** - To control API usage
- **Speech-to-text** - Converting spoken words to text

## Project Structure

- `chatforge/` - The main library
  - `ports/` - Interfaces (the contracts)
  - `adapters/` - Implementations (the actual code that does things)
  - `services/` - Business logic (the agent, LLM handling)
  - `middleware/` - Security features
  - `config/` - Settings management

- `chatterm/` - A terminal-based chat interface for testing
- `examples/` - Working examples you can run
- `tests/` - Automated tests

## Who Would Use This?

- **Developers building chatbots** - Customer support, internal tools, virtual assistants
- **Teams needing voice AI** - Call centers, voice interfaces, accessibility features
- **Organizations wanting control** - Those who need to swap providers, add security, or customize behavior

## Summary

Chatforge is a flexible, secure, and extensible framework for building conversational AI applications. It handles the complex plumbing (AI integration, storage, security, voice) so developers can focus on building features their users actually need.
