# Grok Adapter Implementation Critic

A critical analysis of the `step_by_step_grok_rt_adapter.md` implementation guide, identifying errors, mismatches, and potential issues.

---

## Critical Errors (Must Fix)

### 1. Audio Commit Message Ambiguity

**Location:** `messages.py` - `input_audio_buffer_commit()`

**Issue:** The guide uses `conversation.item.commit` but the Grok documentation shows TWO different commit mechanisms:

```python
# From Grok docs - Client Events table:
"conversation.item.commit"  # General commit

# From Grok docs - Input audio buffer messages section:
"input_audio_buffer.commit"  # "Only available when turn_detection is type: null"
```

**Problem:** The guide assumes `conversation.item.commit` is the universal commit, but `input_audio_buffer.commit` exists specifically for manual VAD mode.

**Fix Required:**
```python
def input_audio_buffer_commit(vad_mode: str = "server") -> dict:
    """Create commit message - different for manual vs server VAD."""
    if vad_mode in ("client", "none"):
        # Manual VAD mode uses input_audio_buffer.commit
        return {"type": "input_audio_buffer.commit"}
    else:
        # Server VAD uses conversation.item.commit
        return {"type": "conversation.item.commit"}
```

**Impact:** HIGH - Audio commit may fail in manual VAD mode

---

### 2. Transcript Event Type Inconsistency

**Location:** `translator.py` - transcript event handling

**Issue:** Inconsistent mapping of transcript events:
```python
# Current (WRONG):
"response.output_audio_transcript.delta" → VoiceEventType.TRANSCRIPT (is_delta: True)
"response.output_audio_transcript.done"  → VoiceEventType.TEXT_DONE  # WRONG!

# Should be (CONSISTENT):
"response.output_audio_transcript.delta" → VoiceEventType.TRANSCRIPT (is_delta: True)
"response.output_audio_transcript.done"  → VoiceEventType.TRANSCRIPT (is_delta: False)
```

**Problem:** OpenAI adapter maps both to `TRANSCRIPT` with different `is_delta` values. The guide incorrectly maps `.done` to `TEXT_DONE`, which is semantically different (text output vs voice transcript).

**Fix Required:**
```python
if event_type == "response.output_audio_transcript.done":
    return VoiceEvent(
        type=VoiceEventType.TRANSCRIPT,  # Not TEXT_DONE!
        data=raw.get("transcript", ""),
        metadata={
            "response_id": raw.get("response_id"),
            "item_id": raw.get("item_id"),
            "is_delta": False,  # Final transcript
        },
        raw_event=raw,
    )
```

**Impact:** HIGH - Consumers expecting consistent transcript events will break

---

### 3. is_error Parameter Silently Ignored

**Location:** `messages.py` - `conversation_item_create_tool_result()`

**Issue:** The function accepts `is_error: bool = False` but never uses it:
```python
def conversation_item_create_tool_result(
    call_id: str,
    output: str,
    is_error: bool = False  # UNUSED!
) -> dict:
    return {
        "type": "conversation.item.create",
        "item": {
            "type": "function_call_output",
            "call_id": call_id,
            "output": output,
            # Missing error indication!
        },
    }
```

**Problem:** When a tool fails, the AI should know about it to respond appropriately.

**Fix Required:** Either remove the parameter or include error info:
```python
def conversation_item_create_tool_result(
    call_id: str,
    output: str,
    is_error: bool = False
) -> dict:
    item = {
        "type": "function_call_output",
        "call_id": call_id,
        "output": output if not is_error else json.dumps({"error": output}),
    }
    return {"type": "conversation.item.create", "item": item}
```

**Impact:** MEDIUM - Tool errors won't be communicated properly to AI

---

## Significant Issues (Should Fix)

### 4. Missing provider_options Support

**Location:** `messages.py` - `session_update()`

**Issue:** `VoiceSessionConfig.provider_options` exists for provider-specific settings but is completely ignored:
```python
@dataclass
class VoiceSessionConfig:
    # ...
    provider_options: dict | None = None  # Escape hatch for future parameters
```

**Problem:** Users cannot pass Grok-specific options.

**Fix Required:**
```python
def session_update(config: VoiceSessionConfig) -> dict:
    session = { ... }

    # Apply provider-specific options last (can override defaults)
    if config.provider_options:
        session.update(config.provider_options)

    return {"type": "session.update", "session": session}
```

**Impact:** MEDIUM - Limits extensibility

---

### 5. Built-in Tools Not Supported

**Location:** `messages.py` - `_tool_to_grok()`

**Issue:** Grok has built-in tools (`web_search`, `x_search`, `file_search`) that use different formats than custom functions:

```python
# Grok built-in tools (NOT function type):
{"type": "web_search"}
{"type": "x_search", "allowed_x_handles": ["elonmusk"]}
{"type": "file_search", "vector_store_ids": ["id"], "max_num_results": 10}

# Custom functions:
{"type": "function", "name": "...", "parameters": {...}}
```

**Problem:** `ToolDefinition` assumes all tools are functions. Built-in tools will fail.

**Fix Required:** Either extend `ToolDefinition` or add special handling:
```python
def _tool_to_grok(tool: ToolDefinition) -> dict:
    # Check for built-in tool types
    if tool.name in ("web_search", "x_search", "file_search"):
        result = {"type": tool.name}
        # Add tool-specific parameters from tool.parameters
        if tool.name == "x_search" and "allowed_x_handles" in tool.parameters:
            result["allowed_x_handles"] = tool.parameters["allowed_x_handles"]
        elif tool.name == "file_search":
            if "vector_store_ids" in tool.parameters:
                result["vector_store_ids"] = tool.parameters["vector_store_ids"]
            if "max_num_results" in tool.parameters:
                result["max_num_results"] = tool.parameters["max_num_results"]
        return result

    # Regular function tool
    return {
        "type": "function",
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters,
    }
```

**Impact:** MEDIUM - Built-in tools unusable

---

### 6. Sample Rate Validation Missing

**Location:** `messages.py` - `_map_audio_format()`

**Issue:** Grok only supports specific sample rates: `8000, 16000, 21050, 24000, 32000, 44100, 48000`

The code passes any sample rate without validation:
```python
def _map_audio_format(format_str: str, sample_rate: int) -> dict:
    result = {"type": audio_type}
    if audio_type == "audio/pcm":
        result["rate"] = sample_rate  # No validation!
    return result
```

**Problem:** Invalid sample rates will cause API errors.

**Fix Required:**
```python
VALID_SAMPLE_RATES = {8000, 16000, 21050, 24000, 32000, 44100, 48000}

def _map_audio_format(format_str: str, sample_rate: int) -> dict:
    audio_type = type_map.get(format_str, "audio/pcm")
    result = {"type": audio_type}

    if audio_type == "audio/pcm":
        if sample_rate not in VALID_SAMPLE_RATES:
            logger.warning(
                "Invalid sample rate %d, using closest valid rate",
                sample_rate
            )
            # Find closest valid rate
            sample_rate = min(VALID_SAMPLE_RATES, key=lambda x: abs(x - sample_rate))
        result["rate"] = sample_rate

    return result
```

**Impact:** MEDIUM - Invalid sample rates cause cryptic errors

---

### 7. Session Ready Race Condition

**Location:** `adapter.py` - `connect()`

**Issue:** The event sequence may be:
1. Connect to WebSocket
2. Receive `conversation.created` (immediately)
3. Send `session.update`
4. Receive `session.updated`

But the code:
```python
# Start receive loop
self._receive_task = asyncio.create_task(self._receive_loop())

# Send session configuration
await self._ws.send_json(messages.session_update(config))

# Wait for session ready
await asyncio.wait_for(self._session_ready.wait(), timeout=10.0)
```

**Problem:** `conversation.created` may arrive and set `_session_ready` BEFORE we send `session.update`. This means we proceed without our configuration being applied!

**Fix Required:**
```python
async def connect(self, config: VoiceSessionConfig) -> None:
    # ...

    # Start receive loop
    self._receive_task = asyncio.create_task(self._receive_loop())

    # Wait for conversation.created (Grok's initial handshake)
    # This is different from SESSION_UPDATED which confirms our config
    self._conversation_created = asyncio.Event()

    try:
        await asyncio.wait_for(self._conversation_created.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        pass  # Proceed anyway, might work

    # NOW send session configuration
    await self._ws.send_json(messages.session_update(config))

    # Wait for session.updated (confirms our config)
    self._session_updated = asyncio.Event()
    try:
        await asyncio.wait_for(self._session_updated.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        await self.disconnect()
        raise RealtimeConnectionError("Session configuration timeout")
```

**Impact:** MEDIUM - Config may not be applied on first connect

---

### 8. Ephemeral Token Support Missing

**Location:** `adapter.py` - constructor and connect

**Issue:** Grok supports ephemeral tokens for client-side authentication:
```python
# From Grok docs:
POST https://api.x.ai/v1/realtime/client_secrets
{"expires_after": {"seconds": 300}}
# Returns: {"value": "ephemeral_token", "expires_at": ...}
```

**Problem:** The adapter only supports direct API key authentication, not ephemeral tokens. This is a security issue for browser-based applications.

**Fix Required:** Add factory method or parameter:
```python
class GrokRealtimeAdapter(RealtimeVoiceAPIPort):
    def __init__(
        self,
        api_key: str | None = None,
        ephemeral_token: str | None = None,  # NEW
        *,
        # ...
    ):
        if not api_key and not ephemeral_token:
            raise ValueError("Either api_key or ephemeral_token required")
        self._auth_token = ephemeral_token or api_key

    @classmethod
    async def create_ephemeral_session(
        cls,
        api_key: str,
        expires_seconds: int = 300,
    ) -> "GrokRealtimeAdapter":
        """Create adapter with ephemeral token (for client-side use)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/realtime/client_secrets",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"expires_after": {"seconds": expires_seconds}},
            )
            data = response.json()
            return cls(ephemeral_token=data["value"])
```

**Impact:** MEDIUM - Security issue for browser apps

---

## Minor Issues (Nice to Fix)

### 9. Silently Ignored Parameters

**Location:** `messages.py` - `session_update()`

**Issue:** Multiple `VoiceSessionConfig` parameters are silently ignored:
- `temperature` - Not supported by Grok
- `max_tokens` - Not supported by Grok
- `tool_choice` - Not supported by Grok
- `transcription_enabled` - Grok always transcribes
- `transcription_model` - Grok has no model selection
- `vad_threshold`, `vad_prefix_ms`, `vad_silence_ms` - Grok has no fine VAD control

**Problem:** Users won't know their settings are being ignored.

**Fix Required:** Log warnings for ignored parameters:
```python
def session_update(config: VoiceSessionConfig) -> dict:
    # Warn about ignored parameters
    if config.temperature != 0.8:  # default
        logger.warning("Grok API does not support temperature parameter, ignoring")
    if config.max_tokens:
        logger.warning("Grok API does not support max_tokens parameter, ignoring")
    if config.tool_choice != "auto":
        logger.warning("Grok API does not support tool_choice parameter, ignoring")
    if not config.transcription_enabled:
        logger.warning("Grok API always transcribes, cannot disable transcription")
    if config.vad_threshold != 0.5:  # default
        logger.warning("Grok API does not support VAD threshold configuration")
    # etc...
```

**Impact:** LOW - Confusing UX but not a bug

---

### 10. Modalities Handling Incorrect

**Location:** `messages.py` - `response_create()`

**Issue:** The guide hardcodes modalities in `response.create`:
```python
def response_create(instructions: str | None = None) -> dict:
    msg: dict = {
        "type": "response.create",
        "response": {
            "modalities": ["text", "audio"],  # Hardcoded!
        },
    }
```

But `VoiceSessionConfig` has a `modalities` field that should be respected:
```python
@dataclass
class VoiceSessionConfig:
    modalities: list[Literal["audio", "text"]] = field(
        default_factory=lambda: ["audio", "text"]
    )
```

**Fix Required:** Pass modalities from config or add parameter:
```python
def response_create(
    instructions: str | None = None,
    modalities: list[str] | None = None
) -> dict:
    msg: dict = {
        "type": "response.create",
        "response": {
            "modalities": modalities or ["text", "audio"],
        },
    }
    if instructions:
        msg["response"]["instructions"] = instructions
    return msg
```

**Impact:** LOW - Text-only mode won't work

---

### 11. Error Event Format Assumed

**Location:** `translator.py` - error handling

**Issue:** The error event format is assumed to match OpenAI's:
```python
if event_type == "error":
    error = raw.get("error", {})
    return VoiceEvent(
        type=VoiceEventType.ERROR,
        data={
            "code": error.get("code"),
            "message": error.get("message"),
            "type": error.get("type"),
        },
        raw_event=raw,
    )
```

**Problem:** Grok's error format is not documented. It might be different.

**Fix Required:** Add defensive handling:
```python
if event_type == "error":
    # Handle both nested and flat error formats
    error = raw.get("error", raw)  # Try nested, fall back to flat
    return VoiceEvent(
        type=VoiceEventType.ERROR,
        data={
            "code": error.get("code") or error.get("error_code"),
            "message": error.get("message") or error.get("error_message") or str(error),
            "type": error.get("type") or error.get("error_type"),
        },
        raw_event=raw,
    )
```

**Impact:** LOW - Errors might show as None

---

### 12. response_cancel Missing response_id

**Location:** `messages.py` - `response_cancel()`

**Issue:** OpenAI's cancel accepts optional `response_id`, but Grok's might too:
```python
def response_cancel() -> dict:
    return {"type": "response.cancel"}  # No response_id
```

**Fix Required:**
```python
def response_cancel(response_id: str | None = None) -> dict:
    msg = {"type": "response.cancel"}
    if response_id:
        msg["response_id"] = response_id
    return msg
```

**Impact:** LOW - Might not cancel specific response

---

### 13. Transcription Cannot Be Disabled

**Location:** N/A

**Issue:** `VoiceSessionConfig.transcription_enabled = False` has no effect because Grok always transcribes. Users expecting to disable transcription for privacy/cost will be surprised.

**Fix Required:** Document limitation and log warning:
```python
# In adapter.py connect():
if not config.transcription_enabled:
    logger.warning(
        "Grok API does not support disabling transcription. "
        "All audio will be transcribed."
    )
```

**Impact:** LOW - Privacy/cost concerns

---

### 14. G.711 Sample Rate Not Enforced

**Location:** `messages.py` - `_map_audio_format()`

**Issue:** G.711 (pcmu/pcma) is always 8kHz, but the code doesn't enforce this:
```python
if audio_type == "audio/pcm":
    result["rate"] = sample_rate
# G.711 types get no rate (correct) but should warn if rate != 8000
```

**Fix Required:**
```python
def _map_audio_format(format_str: str, sample_rate: int) -> dict:
    audio_type = type_map.get(format_str, "audio/pcm")
    result = {"type": audio_type}

    if audio_type == "audio/pcm":
        result["rate"] = sample_rate
    elif audio_type in ("audio/pcmu", "audio/pcma"):
        if sample_rate != 8000:
            logger.warning(
                "G.711 format always uses 8kHz sample rate, ignoring %d",
                sample_rate
            )

    return result
```

**Impact:** LOW - Documentation issue

---

## Conceptual Mismatches

### 15. "Model" Concept Doesn't Apply

**Issue:** `VoiceSessionConfig.model` and `get_capabilities().available_models` assume multiple models exist, but Grok has a single realtime model.

**Current:**
```python
available_models=["grok-realtime"],  # Single model
```

**Problem:** The model abstraction doesn't fit. Should either:
1. Return empty list and document that model selection isn't supported
2. Return the implicit model name and ignore the config value

**Recommendation:** Keep as-is but add comment explaining Grok has single model.

---

### 16. VAD Mode "client" vs "none" Ambiguity

**Location:** `messages.py` - `session_update()`

**Issue:** `VoiceSessionConfig` has three VAD modes:
- `"server"` - Server handles VAD
- `"client"` - Client handles VAD
- `"none"` - No VAD, manual commit

But Grok only has:
- `"server_vad"` - Server handles
- `null` - Manual/no VAD

**Current mapping:**
```python
if config.vad_mode == "server":
    session["turn_detection"] = {"type": "server_vad"}
else:  # "client" or "none" both map to null
    session["turn_detection"] = None
```

**Problem:** "client" implies the client will handle VAD and call `commit_audio()`. "none" implies the user manually commits. Both map to the same thing in Grok, but have different semantic meanings.

**Recommendation:** Document that both "client" and "none" result in manual mode.

---

### 17. Voice Abstraction Leaks

**Issue:** The voice mapping tries to map OpenAI voices to Grok voices, but this creates a leaky abstraction:

```python
VOICE_MAP = {
    "alloy": "Ara",      # Warm, friendly
    "echo": "Rex",       # Confident, clear
    # ...
}
```

**Problems:**
1. Users might expect "alloy" to sound like OpenAI's alloy
2. New voices added to either platform require code changes
3. The subjective mapping (alloy→Ara "because both are warm") is debatable

**Recommendation:**
1. Support Grok voices directly (Ara, Rex, etc.)
2. Map "default" to "Ara"
3. For unknown voices, either fail fast or default with warning
4. Don't try to map OpenAI voices - let users choose explicitly

```python
GROK_VOICES = {"ara", "rex", "sal", "eve", "leo"}

def _map_voice(voice: str) -> str:
    normalized = voice.lower()
    if normalized in GROK_VOICES:
        return voice.capitalize()
    if normalized == "default":
        return "Ara"
    logger.warning("Unknown voice '%s', using default 'Ara'", voice)
    return "Ara"
```

---

## Summary

### By Severity

| Severity | Count | Issues |
|----------|-------|--------|
| **Critical** | 3 | Audio commit, transcript type, is_error unused |
| **Significant** | 5 | provider_options, built-in tools, sample rate, race condition, ephemeral tokens |
| **Minor** | 6 | Ignored params, modalities, error format, response_id, transcription, G.711 |
| **Conceptual** | 3 | Model concept, VAD modes, voice abstraction |

### Recommended Priority

1. **Fix transcript event mapping** (5 min) - Clear bug
2. **Fix audio commit for VAD modes** (15 min) - Will break manual VAD
3. **Add sample rate validation** (15 min) - Prevents confusing errors
4. **Use is_error parameter** (5 min) - Currently misleading API
5. **Add provider_options support** (10 min) - Extensibility
6. **Document/warn ignored parameters** (20 min) - UX improvement
7. **Built-in tools support** (30 min) - Feature completeness
8. **Session ready sequence fix** (30 min) - Potential race condition
9. **Ephemeral tokens** (1 hour) - Security for browsers

### Total Additional Effort

Fixing all issues: ~3-4 additional hours on top of original estimate.

**Revised total estimate: 10-15 hours**
