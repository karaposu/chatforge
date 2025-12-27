"""
Simple LLM Call Test

This script tests the most basic functionality of ChatForge:
making a simple LLM call without any storage, tracing, or middleware.

Setup:
1. Create a .env file in the project root with:
   OPENAI_API_KEY=your_key_here
   LLM_PROVIDER=openai
   LLM_MODEL_NAME=gpt-4o-mini
   LLM_TEMPERATURE=0.0

2. Install the package in development mode (from project root):
   pip install -e .

   Or install with OpenAI dependencies:
   pip install -e ".[openai]"

3. Run from project root:
   python -m chatforge.test_simple_llm_call
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root (parent directory)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("ChatForge - Simple LLM Call Test")
print("=" * 60)

# Import directly (we're running from src/ directory)
try:
    from chatforge.services.llm import get_llm
    from chatforge.config import llm_config
    print("✓ Successfully imported modules")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    print("\nMake sure you have installed the required dependencies:")
    print("  pip install langchain-core langchain-openai pydantic pydantic-settings")
    sys.exit(1)

# Display configuration
print("\n" + "-" * 60)
print("Configuration:")
print("-" * 60)
print(f"Provider: {llm_config.provider}")
print(f"Model: {llm_config.model_name}")
print(f"Temperature: {llm_config.temperature}")
print(f"API Key configured: {'Yes' if llm_config.openai_api_key else 'No'}")
print("-" * 60)

# Validate configuration
if not llm_config.openai_api_key:
    print("\n✗ ERROR: OPENAI_API_KEY not found in environment")
    print("\nPlease create a .env file with:")
    print("  OPENAI_API_KEY=your_key_here")
    sys.exit(1)

# Create LLM instance
print("\n[1/3] Creating LLM instance...")
try:
    llm = get_llm()
    print("✓ LLM instance created successfully")
except Exception as e:
    print(f"✗ Failed to create LLM instance: {e}")
    sys.exit(1)

# Test simple message
print("\n[2/3] Sending test message to LLM...")
test_message = "Hello! Please respond with a simple greeting."
print(f"Message: \"{test_message}\"")

try:
    response = llm.invoke(test_message)
    print("✓ Received response from LLM")
except Exception as e:
    print(f"✗ Failed to get response: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Display response
print("\n[3/3] Response:")
print("-" * 60)
print(response.content)
print("-" * 60)

# Test with a list of messages (conversation format)
print("\n[Bonus] Testing conversation format...")
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is 2+2?"),
]

try:
    response = llm.invoke(messages)
    print("✓ Conversation format works")
    print(f"Response: {response.content}")
except Exception as e:
    print(f"✗ Conversation format failed: {e}")

print("\n" + "=" * 60)
print("Test completed successfully! ✓")
print("=" * 60)
print("\nNext steps:")
print("- Test with streaming: get_streaming_llm()")
print("- Test with vision: get_vision_llm()")
print("- Test the ReActAgent")
print("=" * 60)
