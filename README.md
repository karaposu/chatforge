# Chatforge

Building blocks for AI & chat applications at 3 levels of abstraction.


### Services: For Rapid Development
### Ports: For Flexibility and Testing
### Adapters: For Full Control


which

Decouple your chat application from infrastructure.

  Whether it's:
  - A simple LLM chat
  - A complex agent with tools
  - A customer support bot
  - A game NPC

  Doesn't matter. Your application logic - whatever it is - stays clean. Everything external (database, chat platform, voice, ticketing, knowledge base, tracing) connects through ports.

## What You Get

**A complete skeleton for chat applications.** Storage, agents, middleware, platform integrations - all abstracted behind clean interfaces. Pick your tech stack, implement the adapters, ship.

**Production security out of the box.** PII detection, prompt injection guards, content safety filters - already built, just enable them.

**Voice-ready architecture.** Start with text, switch to voice AI later. Same agent logic, same tools, same storage - just swap the I/O layer.

## How It Works

Chatforge uses ports (interfaces) and adapters (implementations). Your domain logic depends on ports. You provide adapters for your specific stack.

```
Your Bot Logic
     │
     ▼
┌─────────────────────────────────────────────┐
│  PORTS (what you need)                      │
│  Storage, Messaging, Tracing, Knowledge...  │
└─────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────┐
│  ADAPTERS (your tech choices)               │
│  Postgres, Telegram, Datadog, Pinecone...   │
└─────────────────────────────────────────────┘
```

Need Telegram? Implement `MessagingPlatformIntegrationPort`.
Need MongoDB? Implement `StoragePort`.
Need voice? Swap text I/O for Realtime API.

Your agent code never changes.

## Built-in Ports

| Port | Purpose | Example Adapters |
|------|---------|------------------|
| `StoragePort` | Conversations, history | SQLite, Postgres, Redis, your DB |
| `MessagingPlatformIntegrationPort` | Chat platforms | Slack, Discord, Telegram, Teams |
| `TicketingPort` | Workflow systems | Jira, Zendesk, ServiceNow |
| `KnowledgePort` | RAG, search | Pinecone, Notion, Confluence |
| `TracingPort` | Observability | MLflow, LangSmith, Datadog |

## Built-in Security

```python
from chatforge.middleware import PIIDetector, PromptInjectionGuard, SafetyGuardrail

# PII detection - no external API needed
pii = PIIDetector()
result = pii.scan(user_input)  # emails, SSNs, credit cards, API keys

# Prompt injection detection
guard = PromptInjectionGuard(llm)
if guard.check(user_input).is_injection:
    block()

# Response safety evaluation
safety = SafetyGuardrail(context="support agent", forbidden=["bypass security"])
if not safety.check(response).is_safe:
    use_fallback()
```

## Text to Voice in One Swap

```python
# Text chatbot
from chatforge import ReActAgent
agent = ReActAgent(llm=llm, tools=tools)
response = agent.process_message(text_input)

# Voice chatbot - same agent, same tools
from realtimevoiceapi import VoiceEngine
engine = VoiceEngine(agent=agent)  # Your agent logic unchanged
await engine.start()
```

## Install

```bash
pip install -e .
```

## Quick Start

```python
from chatforge import get_llm, ReActAgent
from chatforge.adapters.storage import SQLiteStorageAdapter

# Pick your LLM
llm = get_llm(provider="openai", model_name="gpt-4o-mini")

# Pick your storage
storage = SQLiteStorageAdapter("./conversations.db")

# Build your agent
agent = ReActAgent(llm=llm, tools=[your_tools])

# Your platform adapter handles the I/O
# (Telegram, Slack, Discord, or your custom integration)
```


## Port List (Not all implemented)

TicketingPort
Storage
Tracing
KnowledgeRetrievalPort
Audio
AudioStreamPort
Text2SpeechPort
Text2SpeechStreamingPort 
Speech2TextPort
Speech2TextStreamingPort
MessagingPlatformIntegrationPort
RealtimeVoiceAPIPort


## Adapters (Not all implemented)

## For AudioStreamPort and AudioPort

VoxStreamAdapter (local voice usage)
WebAudioAdapter
MobileAudioAdapter
FileAudioAdapter


## For TTS and STT

elevenlabs
openai whisper
local (for models like chatterbox)

## for TicketingPort

Jira


## MessagingPlatformIntegrationPort

telegram
slack
discord
whatsapp



## for KnowledgeRetrievalPort

chroma db 
notion retrivial


## for Storage

sqlite, postgresql, bigquery, mongodb


## for Tracing

Mlflow




