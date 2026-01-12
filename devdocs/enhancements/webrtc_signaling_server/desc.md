# WebRTC Signaling Server

## Overview

Infrastructure component that enables browser-based voice applications to connect to chatforge. Handles the WebRTC handshake process so that `WebRTCCaptureAdapter` can receive audio from web clients.

## Why WebRTC?

### The Browser Audio Problem

Browsers cannot directly send microphone audio to a Python backend via raw sockets. They require:

1. **HTTPS** - Microphone access requires secure context
2. **MediaStream API** - Browser's audio capture interface
3. **WebRTC or WebSocket** - Transport protocol

### Options Comparison

| Approach | Latency | Quality | Complexity | Browser Support |
|----------|---------|---------|------------|-----------------|
| WebSocket + PCM | Medium | Good | Low | Universal |
| WebRTC | Low | Excellent | High | Universal |
| WebTransport | Very Low | Excellent | Medium | Chrome/Edge only |

**WebRTC wins for voice** because:
- Built-in echo cancellation, noise suppression, auto gain
- Adaptive bitrate based on network conditions
- Sub-100ms latency (vs 200-500ms for WebSocket)
- Opus codec optimized for speech

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ getUserMedia │───▶│ RTCPeerConn  │───▶│  Audio Track │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                              │                    │              │
│                              │ Signaling          │ Media        │
│                              ▼                    ▼              │
└──────────────────────────────┼────────────────────┼──────────────┘
                               │                    │
                     WebSocket │                    │ SRTP/UDP
                               │                    │
┌──────────────────────────────┼────────────────────┼──────────────┐
│                         Server                    │              │
│  ┌──────────────────────┐    │    ┌──────────────┴───────────┐  │
│  │ WebRTCSignalingServer│◀───┘    │    WebRTC Media Server   │  │
│  │   (Infrastructure)   │         │      (e.g., aiortc)      │  │
│  └──────────────────────┘         └──────────────────────────┘  │
│           │                                    │                 │
│           │ session_id                         │ audio frames    │
│           ▼                                    ▼                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              WebRTCCaptureAdapter                         │   │
│  │              (implements AudioCapturePort)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ asyncio.Queue[bytes]              │
│                              ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    VAD / AI Pipeline                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Signaling Protocol

WebRTC requires out-of-band signaling to exchange connection parameters. The signaling server handles this via WebSocket.

### Message Types

```python
# Client → Server
{
    "type": "offer",
    "session_id": "abc123",
    "sdp": "v=0\r\no=- 123456789..."  # Session Description Protocol
}

{
    "type": "ice_candidate",
    "session_id": "abc123",
    "candidate": {
        "candidate": "candidate:1 1 UDP 2130706431...",
        "sdpMid": "audio",
        "sdpMLineIndex": 0
    }
}

# Server → Client
{
    "type": "answer",
    "session_id": "abc123",
    "sdp": "v=0\r\no=- 987654321..."
}

{
    "type": "ice_candidate",
    "session_id": "abc123",
    "candidate": { ... }
}

{
    "type": "error",
    "session_id": "abc123",
    "code": "session_limit_exceeded",
    "message": "Maximum concurrent sessions reached"
}
```

### Connection Flow

```
Browser                    SignalingServer              MediaServer
   │                              │                          │
   │──── connect(ws) ────────────▶│                          │
   │                              │                          │
   │──── offer(sdp) ─────────────▶│                          │
   │                              │──── create_session() ───▶│
   │                              │◀─── session_id ──────────│
   │                              │                          │
   │◀─── answer(sdp) ─────────────│◀─── answer_sdp ──────────│
   │                              │                          │
   │──── ice_candidate ──────────▶│──── add_ice_candidate ──▶│
   │◀─── ice_candidate ───────────│◀─── ice_candidate ───────│
   │           ...                │           ...            │
   │                              │                          │
   │═══════════════ DTLS/SRTP Media Channel ═════════════════│
   │                              │                          │
   │                              │    audio frames          │
   │                              │◀─────────────────────────│
   │                              │                          │
   │──── disconnect ─────────────▶│──── close_session() ────▶│
   │                              │                          │
```

## Infrastructure Components

### 1. WebRTCSignalingServer

Handles WebSocket connections and message routing.

```python
class WebRTCSignalingServer:
    """WebSocket server for WebRTC signaling."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        max_sessions: int = 100,
        stun_servers: list[str] = None,
        turn_servers: list[TURNConfig] = None,
    ):
        ...

    async def start(self) -> None:
        """Start the signaling server."""
        ...

    async def stop(self) -> None:
        """Stop the signaling server and close all sessions."""
        ...

    def on_session_created(
        self,
        callback: Callable[[str, RTCPeerConnection], Awaitable[None]]
    ) -> None:
        """Register callback for new sessions."""
        ...
```

### 2. SessionManager

Tracks active WebRTC sessions.

```python
class WebRTCSession:
    """Represents a single WebRTC session."""

    session_id: str
    peer_connection: RTCPeerConnection
    audio_track: MediaStreamTrack
    created_at: datetime
    client_info: dict  # User-agent, IP, etc.
    state: SessionState  # CONNECTING, CONNECTED, CLOSED
```

### 3. ICE Configuration

```python
@dataclass
class ICEConfig:
    """ICE server configuration."""

    stun_servers: list[str] = field(default_factory=lambda: [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
    ])

    turn_servers: list[TURNServer] = field(default_factory=list)

    ice_transport_policy: str = "all"  # "all" or "relay"

@dataclass
class TURNServer:
    """TURN server credentials."""

    urls: list[str]  # ["turn:turn.example.com:3478"]
    username: str
    credential: str
    credential_type: str = "password"
```

## Integration with AudioCapturePort

The signaling server creates sessions; the adapter captures audio:

```python
# Infrastructure setup
signaling_server = WebRTCSignalingServer(port=8765)

# Adapter creation on new session
async def on_session(session_id: str, peer_connection: RTCPeerConnection):
    # Create adapter for this session's audio track
    audio_track = get_audio_track(peer_connection)

    capture = WebRTCCaptureAdapter(
        audio_track=audio_track,
        session_id=session_id,
        config=AudioCaptureConfig(sample_rate=48000),  # Opus default
    )

    # Start capture - returns standard Queue[bytes]
    audio_queue = await capture.start()

    # Feed into VAD/AI pipeline
    vad = EnergyVADAdapter()
    async for chunk in queue_to_iterator(audio_queue):
        result = vad.process_chunk(chunk)
        if result.is_speaking:
            await send_to_ai(chunk)

signaling_server.on_session_created(on_session)
await signaling_server.start()
```

## Dependencies

| Library | Purpose | Notes |
|---------|---------|-------|
| `aiortc` | WebRTC for Python | Uses libsrtp, libvpx |
| `aiohttp` or `websockets` | WebSocket server | Signaling transport |
| `cryptography` | DTLS handshake | Required by aiortc |

```bash
pip install aiortc websockets
```

## Security Considerations

### 1. Authentication

Signaling connection should be authenticated:

```python
async def authenticate_connection(websocket, path):
    """Verify client before allowing signaling."""
    token = websocket.request_headers.get("Authorization")
    if not await verify_token(token):
        await websocket.close(4001, "Unauthorized")
        return None
    return extract_user_id(token)
```

### 2. Session Limits

Prevent resource exhaustion:

```python
class SessionManager:
    def __init__(self, max_sessions: int = 100, max_per_user: int = 3):
        self.max_sessions = max_sessions
        self.max_per_user = max_per_user

    async def create_session(self, user_id: str) -> str:
        if len(self.sessions) >= self.max_sessions:
            raise SessionLimitError("Server at capacity")

        user_sessions = self.get_user_sessions(user_id)
        if len(user_sessions) >= self.max_per_user:
            raise SessionLimitError("Too many sessions for user")

        return await self._create_session(user_id)
```

### 3. Media Encryption

WebRTC uses DTLS-SRTP - media is encrypted by default. No additional configuration needed.

### 4. CORS/Origin Validation

```python
ALLOWED_ORIGINS = ["https://app.example.com", "https://staging.example.com"]

async def validate_origin(websocket):
    origin = websocket.request_headers.get("Origin")
    if origin not in ALLOWED_ORIGINS:
        await websocket.close(4003, "Origin not allowed")
        return False
    return True
```

## Deployment Considerations

### NAT Traversal

Most users are behind NAT. STUN handles simple NAT; TURN handles symmetric NAT:

```
┌─────────────────┐
│ Symmetric NAT   │  ──▶  Requires TURN (relay)
│ (corporate)     │
└─────────────────┘

┌─────────────────┐
│ Full Cone NAT   │  ──▶  STUN sufficient
│ (home router)   │
└─────────────────┘
```

**Recommendation**: Always configure TURN as fallback. ~10-15% of connections require it.

### TURN Server Options

| Option | Cost | Latency | Notes |
|--------|------|---------|-------|
| Self-hosted (coturn) | Low | Best | Requires UDP ports |
| Twilio TURN | Pay-per-GB | Good | Managed, global |
| Cloudflare Calls | Free tier | Good | Limited free tier |
| Xirsys | Pay-per-GB | Varies | Many regions |

### Port Requirements

```
TCP 443  - HTTPS (web app)
TCP 8765 - WebSocket signaling (or behind reverse proxy)
UDP 3478 - STUN
UDP 5349 - TURNS (TURN over TLS)
UDP 49152-65535 - WebRTC media (configurable range)
```

## Alternatives Considered

### WebSocket + Raw Audio

Simpler but worse quality:

```javascript
// Browser
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
recorder.ondataavailable = (e) => ws.send(e.data);
```

**Problems:**
- No adaptive bitrate
- Higher latency (chunked, not streaming)
- No built-in echo cancellation in transport
- Must decode webm/opus on server

### WebTransport

Future option when browser support improves:

```javascript
const transport = new WebTransport("https://server.com/audio");
const stream = await transport.createUnidirectionalStream();
// Send raw audio frames with minimal overhead
```

**Problems:**
- Chrome/Edge only (2024)
- No Safari/Firefox support
- Still need getUserMedia + processing

## Implementation Phases

### Phase 1: Basic Signaling
- WebSocket server for offer/answer exchange
- Single STUN server (Google's public)
- Single concurrent session

### Phase 2: Production Ready
- Session management with limits
- TURN server integration
- Authentication
- Graceful reconnection

### Phase 3: Scaling
- Multiple signaling server instances (Redis pubsub)
- Session affinity
- Metrics and monitoring
- Geographic TURN distribution

## File Structure

```
chatforge/
├── infrastructure/
│   └── webrtc/
│       ├── __init__.py
│       ├── signaling_server.py    # WebSocket signaling
│       ├── session_manager.py     # Session lifecycle
│       ├── ice_config.py          # STUN/TURN configuration
│       └── types.py               # Protocol message types
│
├── adapters/
│   └── audio_capture/
│       ├── ...
│       └── webrtc_adapter.py      # Implements AudioCapturePort
│
└── ports/
    └── audio_capture.py           # AudioCapturePort interface
```

## Related Documents

- `devdocs/enhancements/audiocaptureport/` - AudioCapturePort interface
- `devdocs/enhancements/vadport/` - VAD integration
- `devdocs/verdict_about_streaming_ports.md` - Overall streaming architecture
