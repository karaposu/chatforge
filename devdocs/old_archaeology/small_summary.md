# Chatforge: A Plain English Summary

## What Is This Project?

Chatforge is a **toolkit for building AI chat assistants**. Think of it like a construction kit that lets you build smart chatbots that can:

- Have conversations with people
- Answer questions
- Perform tasks using "tools" (like searching a knowledge base or creating tickets)
- Work on different messaging platforms (Slack, Microsoft Teams, Discord, etc.)

The project is currently in active development - some parts work, others are still being built.

---

## The Big Idea: "Build Once, Run Anywhere"

The most important concept in Chatforge is **separation of concerns**. Instead of building a chatbot that only works with one specific AI service, one specific database, and one specific messaging platform, Chatforge separates these pieces:

1. **The Brain**: The core chatbot logic that decides what to do
2. **The AI Provider**: Which AI service powers the thinking (OpenAI, Anthropic Claude, or Amazon Bedrock)
3. **The Memory**: Where conversations are stored (in-memory, SQLite file, PostgreSQL database, etc.)
4. **The Platform**: Where the chatbot lives (Slack, Teams, a website, an API, etc.)

This means you can swap out any piece without rewriting everything else. Want to switch from OpenAI to Anthropic? Change one setting. Want to move from a simple file database to PostgreSQL? Change one adapter.

---

## What Can Chatforge Do?

### 1. Hold Intelligent Conversations

The chatbot uses a pattern called **ReACT** (Reason, Act, Observe):
- **Reason**: Think about what the user wants
- **Act**: Take action (like searching for information or creating a ticket)
- **Observe**: Look at the results
- **Repeat** until the task is done

This makes the chatbot smarter than simple keyword matching - it actually thinks through problems.

### 2. Use Tools

Chatbots built with Chatforge can use "tools" to do things:
- Search a knowledge base for answers
- Create support tickets in systems like Jira
- Look at images and describe what's in them
- Any custom tool you create

### 3. Remember Conversations

The chatbot stores conversation history so it remembers what you talked about. This history can be stored:
- In memory (temporary, for testing)
- In a SQLite file (simple, local storage)
- In a full database like PostgreSQL (for production use)

### 4. Protect User Privacy

Chatforge has built-in security features:

- **PII Detection**: Automatically finds and hides personal information like email addresses, phone numbers, credit card numbers, and social security numbers
- **Prompt Injection Protection**: Detects when users try to trick the AI into behaving badly
- **Safety Guardrails**: Checks AI responses to make sure they're appropriate

### 5. Analyze Images

The chatbot can look at images (screenshots, photos, documents) and describe what it sees. Useful for:
- Understanding error screenshots
- Describing uploaded images
- Analyzing visual content

### 6. Work with External Systems

Chatforge can connect to:
- **Knowledge Bases**: Like Notion or Confluence, to find answers to questions
- **Ticketing Systems**: Like Jira or ServiceNow, to create and manage support tickets
- **Messaging Platforms**: Like Slack or Discord, to have conversations where your users already are

---

## Who Would Use This?

Chatforge is designed for teams building:

- **Customer support bots** that can answer questions and create tickets
- **Internal IT help desks** that assist employees
- **Knowledge assistants** that help people find information
- **Any AI-powered chat application** that needs to be reliable and flexible

---

## The Building Blocks

### Ports (The Interfaces)

Think of ports as "socket shapes" - they define what a connection should look like:
- **Storage Port**: How to save and retrieve conversations
- **Messaging Port**: How to talk to chat platforms
- **Knowledge Port**: How to search for information
- **Ticketing Port**: How to create and manage tickets

### Adapters (The Implementations)

Adapters are the actual plugs that fit into the ports:
- **In-Memory Adapter**: Stores conversations in computer memory (temporary)
- **SQLite Adapter**: Stores conversations in a file
- **SQLAlchemy Adapter**: Stores conversations in any database

### Services (The Workers)

Services do the actual work:
- **Agent Service**: The brain that processes messages and decides what to do
- **LLM Service**: Connects to AI providers (OpenAI, Anthropic, Bedrock)
- **Vision Service**: Analyzes images
- **Cleanup Service**: Removes old data to save space

### Middleware (The Security Guards)

Middleware sits between the user and the AI, checking everything:
- **PII Detector**: Finds and hides personal information
- **Injection Guard**: Blocks attempts to manipulate the AI
- **Safety Guardrail**: Ensures responses are appropriate

---

## Current State

The project is under heavy development. Based on the code:

- Core agent functionality works
- Multiple storage options are implemented
- Security middleware is in place
- FastAPI REST endpoints are ready
- Vision/image analysis is functional
- The framework is designed for extensibility

What's likely still in progress:
- Real-time streaming responses (partially implemented)
- Platform-specific adapters (Slack, Teams, Discord)
- Knowledge base and ticketing integrations (interfaces exist, implementations may vary)
- Production hardening and testing

---

## In One Sentence

Chatforge is a modular toolkit for building AI chat assistants that can be deployed anywhere, connect to any AI provider, store data in any database, and includes security features out of the box.
