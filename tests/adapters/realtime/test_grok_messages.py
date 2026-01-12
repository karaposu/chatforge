"""Unit tests for Grok messages module."""

import base64
import json
import pytest

from chatforge.adapters.realtime.grok import messages
from chatforge.ports.realtime_voice import VoiceSessionConfig, ToolDefinition


class TestVoiceMapping:
    """Tests for voice name mapping."""

    def test_grok_voices_capitalized(self):
        """Test Grok native voices are capitalized correctly."""
        assert messages._map_voice("ara") == "Ara"
        assert messages._map_voice("rex") == "Rex"
        assert messages._map_voice("sal") == "Sal"
        assert messages._map_voice("eve") == "Eve"
        assert messages._map_voice("leo") == "Leo"

    def test_already_capitalized_voices(self):
        """Test already capitalized voices work."""
        assert messages._map_voice("Ara") == "Ara"
        assert messages._map_voice("REX") == "Rex"

    def test_default_voice(self):
        """Test default maps to Ara."""
        assert messages._map_voice("default") == "Ara"

    def test_unknown_voice_falls_back_to_ara(self, caplog):
        """Test unknown voice falls back to Ara with warning."""
        result = messages._map_voice("unknown_voice")
        assert result == "Ara"
        assert "Unknown voice" in caplog.text

    def test_openai_voice_falls_back(self, caplog):
        """Test OpenAI voice names fall back to Ara."""
        result = messages._map_voice("alloy")
        assert result == "Ara"
        assert "Unknown voice" in caplog.text


class TestAudioFormatMapping:
    """Tests for audio format mapping."""

    def test_pcm16_format(self):
        """Test pcm16 maps to audio/pcm."""
        result = messages._map_audio_format("pcm16", 24000)
        assert result == {"type": "audio/pcm", "rate": 24000}

    def test_pcm_format(self):
        """Test pcm maps to audio/pcm."""
        result = messages._map_audio_format("pcm", 16000)
        assert result == {"type": "audio/pcm", "rate": 16000}

    def test_g711_ulaw_format(self):
        """Test g711_ulaw maps to audio/pcmu."""
        result = messages._map_audio_format("g711_ulaw", 8000)
        assert result == {"type": "audio/pcmu"}

    def test_g711_alaw_format(self):
        """Test g711_alaw maps to audio/pcma."""
        result = messages._map_audio_format("g711_alaw", 8000)
        assert result == {"type": "audio/pcma"}

    def test_unknown_format_defaults_to_pcm(self):
        """Test unknown format defaults to audio/pcm."""
        result = messages._map_audio_format("unknown", 24000)
        assert result == {"type": "audio/pcm", "rate": 24000}


class TestSampleRateValidation:
    """Tests for sample rate validation."""

    @pytest.mark.parametrize("rate", [8000, 16000, 21050, 24000, 32000, 44100, 48000])
    def test_valid_sample_rates(self, rate):
        """Test all valid sample rates are accepted."""
        result = messages._map_audio_format("pcm16", rate)
        assert result["rate"] == rate

    def test_invalid_sample_rate_corrected(self, caplog):
        """Test invalid sample rate is corrected to closest valid."""
        # 22000 should be corrected to 21050 (closest)
        result = messages._map_audio_format("pcm16", 22000)
        assert result["rate"] == 21050
        assert "Invalid sample rate" in caplog.text

    def test_g711_ignores_sample_rate(self, caplog):
        """Test G.711 formats ignore non-8kHz sample rate with warning."""
        result = messages._map_audio_format("g711_ulaw", 24000)
        assert "rate" not in result  # G.711 doesn't include rate
        assert "G.711 format always uses 8kHz" in caplog.text


class TestSessionUpdate:
    """Tests for session.update message creation."""

    def test_basic_session_update(self):
        """Test basic session update message structure."""
        config = VoiceSessionConfig(voice="Ara")
        msg = messages.session_update(config)

        assert msg["type"] == "session.update"
        assert "session" in msg
        assert msg["session"]["voice"] == "Ara"

    def test_session_update_with_instructions(self):
        """Test session update includes instructions."""
        config = VoiceSessionConfig(system_prompt="You are a helpful assistant.")
        msg = messages.session_update(config)

        assert msg["session"]["instructions"] == "You are a helpful assistant."

    def test_session_update_without_instructions(self):
        """Test session update without instructions."""
        config = VoiceSessionConfig(system_prompt=None)
        msg = messages.session_update(config)

        assert "instructions" not in msg["session"]

    def test_session_update_server_vad(self):
        """Test server VAD configuration."""
        config = VoiceSessionConfig(vad_mode="server")
        msg = messages.session_update(config)

        assert msg["session"]["turn_detection"] == {"type": "server_vad"}

    def test_session_update_client_vad(self):
        """Test client VAD maps to null."""
        config = VoiceSessionConfig(vad_mode="client")
        msg = messages.session_update(config)

        assert msg["session"]["turn_detection"] is None

    def test_session_update_no_vad(self):
        """Test none VAD maps to null."""
        config = VoiceSessionConfig(vad_mode="none")
        msg = messages.session_update(config)

        assert msg["session"]["turn_detection"] is None

    def test_session_update_audio_format(self):
        """Test audio format structure."""
        config = VoiceSessionConfig(
            input_format="pcm16",
            output_format="pcm16",
            sample_rate=24000
        )
        msg = messages.session_update(config)

        assert msg["session"]["audio"]["input"]["format"]["type"] == "audio/pcm"
        assert msg["session"]["audio"]["input"]["format"]["rate"] == 24000
        assert msg["session"]["audio"]["output"]["format"]["type"] == "audio/pcm"
        assert msg["session"]["audio"]["output"]["format"]["rate"] == 24000

    def test_session_update_with_tools(self):
        """Test session update includes tools."""
        config = VoiceSessionConfig(
            tools=[
                ToolDefinition(
                    name="get_weather",
                    description="Get weather",
                    parameters={"type": "object"},
                )
            ]
        )
        msg = messages.session_update(config)

        assert len(msg["session"]["tools"]) == 1
        assert msg["session"]["tools"][0]["name"] == "get_weather"

    def test_session_update_provider_options(self):
        """Test provider_options are applied."""
        config = VoiceSessionConfig(
            provider_options={"custom_option": "custom_value"}
        )
        msg = messages.session_update(config)

        assert msg["session"]["custom_option"] == "custom_value"


class TestIgnoredParameterWarnings:
    """Tests for warnings about ignored parameters."""

    def test_warns_on_temperature(self, caplog):
        """Test warning when temperature is set."""
        config = VoiceSessionConfig(temperature=0.5)
        messages.session_update(config)
        assert "temperature" in caplog.text

    def test_warns_on_max_tokens(self, caplog):
        """Test warning when max_tokens is set."""
        config = VoiceSessionConfig(max_tokens=100)
        messages.session_update(config)
        assert "max_tokens" in caplog.text

    def test_warns_on_tool_choice(self, caplog):
        """Test warning when tool_choice is not auto."""
        config = VoiceSessionConfig(tool_choice="required")
        messages.session_update(config)
        assert "tool_choice" in caplog.text

    def test_warns_on_transcription_disabled(self, caplog):
        """Test warning when transcription is disabled."""
        config = VoiceSessionConfig(transcription_enabled=False)
        messages.session_update(config)
        assert "cannot disable transcription" in caplog.text

    def test_warns_on_vad_threshold(self, caplog):
        """Test warning when VAD threshold is non-default."""
        config = VoiceSessionConfig(vad_threshold=0.7)
        messages.session_update(config)
        assert "VAD threshold" in caplog.text

    def test_no_warning_on_defaults(self, caplog):
        """Test no warnings with default config."""
        config = VoiceSessionConfig()
        messages.session_update(config)
        # Should not have any warnings about ignored parameters
        assert "does not support" not in caplog.text


class TestAudioBufferMessages:
    """Tests for audio buffer messages."""

    def test_append_audio(self):
        """Test input_audio_buffer.append message."""
        audio_bytes = b"\x00\x01\x02\x03"
        msg = messages.input_audio_buffer_append(audio_bytes)

        assert msg["type"] == "input_audio_buffer.append"
        assert msg["audio"] == base64.b64encode(audio_bytes).decode("ascii")

    def test_commit_server_vad(self):
        """Test commit uses conversation.item.commit for server VAD."""
        msg = messages.input_audio_buffer_commit(vad_mode="server")
        assert msg["type"] == "conversation.item.commit"

    def test_commit_client_vad(self):
        """Test commit uses input_audio_buffer.commit for client VAD."""
        msg = messages.input_audio_buffer_commit(vad_mode="client")
        assert msg["type"] == "input_audio_buffer.commit"

    def test_commit_no_vad(self):
        """Test commit uses input_audio_buffer.commit for none VAD."""
        msg = messages.input_audio_buffer_commit(vad_mode="none")
        assert msg["type"] == "input_audio_buffer.commit"

    def test_commit_default_is_server(self):
        """Test commit defaults to server VAD behavior."""
        msg = messages.input_audio_buffer_commit()
        assert msg["type"] == "conversation.item.commit"

    def test_clear_audio(self):
        """Test input_audio_buffer.clear message."""
        msg = messages.input_audio_buffer_clear()
        assert msg["type"] == "input_audio_buffer.clear"


class TestConversationItemMessages:
    """Tests for conversation item messages."""

    def test_create_text_message(self):
        """Test conversation.item.create for text."""
        msg = messages.conversation_item_create_message("Hello, world!")

        assert msg["type"] == "conversation.item.create"
        assert msg["item"]["type"] == "message"
        assert msg["item"]["role"] == "user"
        assert msg["item"]["content"][0]["type"] == "input_text"
        assert msg["item"]["content"][0]["text"] == "Hello, world!"

    def test_create_tool_result_success(self):
        """Test tool result without error."""
        msg = messages.conversation_item_create_tool_result(
            call_id="call_123",
            output='{"result": "sunny"}',
            is_error=False,
        )

        assert msg["type"] == "conversation.item.create"
        assert msg["item"]["type"] == "function_call_output"
        assert msg["item"]["call_id"] == "call_123"
        assert msg["item"]["output"] == '{"result": "sunny"}'

    def test_create_tool_result_error(self):
        """Test tool result with error wraps in JSON."""
        msg = messages.conversation_item_create_tool_result(
            call_id="call_123",
            output="Connection failed",
            is_error=True,
        )

        assert msg["type"] == "conversation.item.create"
        # Error should be wrapped in JSON
        output = json.loads(msg["item"]["output"])
        assert output == {"error": "Connection failed"}


class TestResponseMessages:
    """Tests for response control messages."""

    def test_response_create_basic(self):
        """Test basic response.create message."""
        msg = messages.response_create()

        assert msg["type"] == "response.create"
        assert msg["response"]["modalities"] == ["text", "audio"]

    def test_response_create_with_instructions(self):
        """Test response.create with instructions."""
        msg = messages.response_create(instructions="Be brief.")

        assert msg["response"]["instructions"] == "Be brief."

    def test_response_create_with_modalities(self):
        """Test response.create with custom modalities."""
        msg = messages.response_create(modalities=["text"])

        assert msg["response"]["modalities"] == ["text"]

    def test_response_cancel_basic(self):
        """Test basic response.cancel message."""
        msg = messages.response_cancel()

        assert msg["type"] == "response.cancel"
        assert "response_id" not in msg

    def test_response_cancel_with_id(self):
        """Test response.cancel with response_id."""
        msg = messages.response_cancel(response_id="resp_123")

        assert msg["type"] == "response.cancel"
        assert msg["response_id"] == "resp_123"


class TestToolConversion:
    """Tests for tool definition conversion."""

    def test_function_tool(self):
        """Test regular function tool conversion."""
        tool = ToolDefinition(
            name="get_weather",
            description="Get current weather for a city",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        )
        result = messages._tool_to_grok(tool)

        assert result["type"] == "function"
        assert result["name"] == "get_weather"
        assert result["description"] == "Get current weather for a city"
        assert result["parameters"]["type"] == "object"

    def test_builtin_web_search(self):
        """Test built-in web_search tool."""
        tool = ToolDefinition(
            name="web_search",
            description="Search the web",
            parameters={},
        )
        result = messages._tool_to_grok(tool)

        assert result == {"type": "web_search"}

    def test_builtin_x_search(self):
        """Test built-in x_search tool."""
        tool = ToolDefinition(
            name="x_search",
            description="Search X",
            parameters={},
        )
        result = messages._tool_to_grok(tool)

        assert result == {"type": "x_search"}

    def test_builtin_x_search_with_handles(self):
        """Test x_search with allowed handles."""
        tool = ToolDefinition(
            name="x_search",
            description="Search X",
            parameters={"allowed_x_handles": ["@user1", "@user2"]},
        )
        result = messages._tool_to_grok(tool)

        assert result["type"] == "x_search"
        assert result["allowed_x_handles"] == ["@user1", "@user2"]

    def test_builtin_file_search(self):
        """Test built-in file_search tool."""
        tool = ToolDefinition(
            name="file_search",
            description="Search files",
            parameters={
                "vector_store_ids": ["vs_123"],
                "max_num_results": 10,
            },
        )
        result = messages._tool_to_grok(tool)

        assert result["type"] == "file_search"
        assert result["vector_store_ids"] == ["vs_123"]
        assert result["max_num_results"] == 10
