"""
Test script to verify VoxStream VAD pre-buffer behavior.

Questions to answer:
1. How does `get_pre_buffer()` work?
2. When should we call it - during on_speech_end callback or after?
3. What format is the pre-buffer data?
4. Does calling get_pre_buffer() clear the buffer?

Run with: python -m pytest devdocs/enhancements/audiostreamingport/gaps_to_fill/tests/test_vad_prebuffer.py -v
Or standalone: python devdocs/enhancements/audiostreamingport/gaps_to_fill/tests/test_vad_prebuffer.py
"""

import asyncio
import sys
from pathlib import Path

# Add voxstream to path if needed
voxstream_path = Path("/Users/ns/Desktop/projects/voxstream")
if voxstream_path.exists():
    sys.path.insert(0, str(voxstream_path))

try:
    from voxstream import VoxStream
    from voxstream.config.types import StreamConfig, VADConfig, ProcessingMode
    from voxstream.voice.vad import VADetector
    VOXSTREAM_AVAILABLE = True
except ImportError:
    VOXSTREAM_AVAILABLE = False
    print("VoxStream not available - running mock tests only")


class VADTestResults:
    """Collect test results"""
    def __init__(self):
        self.speech_start_count = 0
        self.speech_end_count = 0
        self.pre_buffer_on_end = None
        self.pre_buffer_on_start = None


def test_vad_prebuffer_retrieval():
    """
    Test 1: Verify pre-buffer can be retrieved in on_speech_end callback

    Expected behavior (needs verification):
    - Pre-buffer accumulates audio before speech detection
    - get_pre_buffer() returns the buffered audio
    - We should call get_pre_buffer() when on_speech_end fires
    """
    if not VOXSTREAM_AVAILABLE:
        print("SKIP: VoxStream not available")
        return

    results = VADTestResults()

    def on_speech_start():
        results.speech_start_count += 1
        print(f"[VAD] Speech started (count: {results.speech_start_count})")

    def on_speech_end():
        results.speech_end_count += 1
        # KEY QUESTION: Can we access the VAD's pre-buffer here?
        # The callback has no arguments, so we need a reference to the VAD
        print(f"[VAD] Speech ended (count: {results.speech_end_count})")

    # Create VAD with pre-buffer enabled
    config = VADConfig(
        pre_buffer_ms=300,  # 300ms of audio before speech
        speech_start_ms=100,
        speech_end_ms=500
    )

    vad = VADetector(
        config=config,
        on_speech_start=on_speech_start,
        on_speech_end=on_speech_end
    )

    # Check if get_pre_buffer exists and what it returns
    if hasattr(vad, 'get_pre_buffer'):
        pre_buffer = vad.get_pre_buffer()
        print(f"[TEST] get_pre_buffer() exists, returns: {type(pre_buffer)}")
        if pre_buffer is not None:
            print(f"[TEST] Pre-buffer length: {len(pre_buffer) if hasattr(pre_buffer, '__len__') else 'N/A'}")
    else:
        print("[TEST] WARNING: get_pre_buffer() method not found!")

    # Check pre_buffer attribute directly
    if hasattr(vad, 'pre_buffer'):
        print(f"[TEST] vad.pre_buffer exists, type: {type(vad.pre_buffer)}")

    print("\n[TEST] VAD pre-buffer test completed")
    return results


def test_vad_with_simulated_audio():
    """
    Test 2: Feed simulated audio to VAD and check pre-buffer behavior
    """
    if not VOXSTREAM_AVAILABLE:
        print("SKIP: VoxStream not available")
        return

    import numpy as np

    results = VADTestResults()
    vad_ref = None  # We'll capture the VAD reference

    def on_speech_start():
        results.speech_start_count += 1
        if vad_ref and hasattr(vad_ref, 'get_pre_buffer'):
            results.pre_buffer_on_start = vad_ref.get_pre_buffer()
            print(f"[VAD] Speech started - pre-buffer captured: {len(results.pre_buffer_on_start) if results.pre_buffer_on_start else 0} bytes")

    def on_speech_end():
        results.speech_end_count += 1
        if vad_ref and hasattr(vad_ref, 'get_pre_buffer'):
            results.pre_buffer_on_end = vad_ref.get_pre_buffer()
            print(f"[VAD] Speech ended - pre-buffer: {len(results.pre_buffer_on_end) if results.pre_buffer_on_end else 0} bytes")

    config = VADConfig(
        pre_buffer_ms=300,
        speech_start_ms=50,  # Faster detection for testing
        speech_end_ms=200
    )

    audio_config = StreamConfig(
        sample_rate=24000,
        channels=1,
        bit_depth=16
    )

    vad = VADetector(
        config=config,
        audio_config=audio_config,
        on_speech_start=on_speech_start,
        on_speech_end=on_speech_end
    )
    vad_ref = vad  # Capture reference for callbacks

    # Generate test audio: silence -> speech -> silence
    sample_rate = 24000
    chunk_duration_ms = 20
    samples_per_chunk = int(sample_rate * chunk_duration_ms / 1000)

    # Silence chunks (low amplitude noise)
    silence_chunks = 20  # 400ms of silence
    for i in range(silence_chunks):
        noise = np.random.randn(samples_per_chunk) * 100  # Low amplitude
        audio_bytes = noise.astype(np.int16).tobytes()
        vad.process_chunk(audio_bytes)

    print(f"[TEST] Fed {silence_chunks} silence chunks")

    # Speech chunks (higher amplitude)
    speech_chunks = 20  # 400ms of "speech"
    for i in range(speech_chunks):
        # Generate louder audio to trigger speech detection
        tone = np.sin(2 * np.pi * 440 * np.arange(samples_per_chunk) / sample_rate)
        audio = (tone * 10000).astype(np.int16)
        audio_bytes = audio.tobytes()
        vad.process_chunk(audio_bytes)

    print(f"[TEST] Fed {speech_chunks} speech chunks")

    # More silence to trigger speech end
    for i in range(30):  # 600ms of silence
        noise = np.random.randn(samples_per_chunk) * 100
        audio_bytes = noise.astype(np.int16).tobytes()
        vad.process_chunk(audio_bytes)

    print(f"[TEST] Fed 30 silence chunks")

    # Report results
    print(f"\n[RESULTS]")
    print(f"  Speech start events: {results.speech_start_count}")
    print(f"  Speech end events: {results.speech_end_count}")
    print(f"  Pre-buffer on start: {len(results.pre_buffer_on_start) if results.pre_buffer_on_start else 'None'}")
    print(f"  Pre-buffer on end: {len(results.pre_buffer_on_end) if results.pre_buffer_on_end else 'None'}")

    return results


def test_prebuffer_clears_after_retrieval():
    """
    Test 3: Check if get_pre_buffer() clears the buffer
    """
    if not VOXSTREAM_AVAILABLE:
        print("SKIP: VoxStream not available")
        return

    config = VADConfig(pre_buffer_ms=300)
    vad = VADetector(config=config)

    if not hasattr(vad, 'get_pre_buffer'):
        print("[TEST] SKIP: get_pre_buffer() not available")
        return

    # Get pre-buffer twice
    first_call = vad.get_pre_buffer()
    second_call = vad.get_pre_buffer()

    print(f"[TEST] First call result: {type(first_call)}, {len(first_call) if first_call else 'None'}")
    print(f"[TEST] Second call result: {type(second_call)}, {len(second_call) if second_call else 'None'}")

    # Check if they're the same (buffer not cleared) or different (buffer cleared)
    if first_call == second_call:
        print("[FINDING] Pre-buffer is NOT cleared after retrieval")
    else:
        print("[FINDING] Pre-buffer IS cleared after retrieval")


async def test_live_capture_with_vad():
    """
    Test 4: Live audio capture with VAD (requires microphone)
    Run this interactively to test real VAD behavior.
    """
    if not VOXSTREAM_AVAILABLE:
        print("SKIP: VoxStream not available")
        return

    print("\n" + "="*60)
    print("LIVE VAD TEST - Speak into microphone for 5 seconds")
    print("="*60 + "\n")

    results = VADTestResults()
    vs = None

    def on_speech_start():
        results.speech_start_count += 1
        print(f"🎤 Speech STARTED (count: {results.speech_start_count})")

    def on_speech_end():
        results.speech_end_count += 1
        print(f"🔇 Speech ENDED (count: {results.speech_end_count})")

    try:
        vs = VoxStream(mode=ProcessingMode.REALTIME)
        vs.configure_vad(VADConfig(
            pre_buffer_ms=300,
            speech_start_ms=100,
            speech_end_ms=500
        ))

        # Note: Need to figure out how to register callbacks with VoxStream
        # This may require different approach than direct VADetector

        queue = await vs.start_capture_stream()

        # Capture for 5 seconds
        import time
        start_time = time.time()
        chunk_count = 0

        while time.time() - start_time < 5:
            try:
                chunk = await asyncio.wait_for(queue.get(), timeout=0.1)
                chunk_count += 1
                if chunk_count % 50 == 0:
                    print(f"  Captured {chunk_count} chunks...")
            except asyncio.TimeoutError:
                continue

        print(f"\n[TEST] Captured {chunk_count} chunks in 5 seconds")
        print(f"[TEST] Speech starts: {results.speech_start_count}")
        print(f"[TEST] Speech ends: {results.speech_end_count}")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        if vs:
            await vs.cleanup_async()


if __name__ == "__main__":
    print("="*60)
    print("VoxStream VAD Pre-buffer Tests")
    print("="*60)

    print("\n--- Test 1: Basic pre-buffer retrieval ---")
    test_vad_prebuffer_retrieval()

    print("\n--- Test 2: Simulated audio with VAD ---")
    test_vad_with_simulated_audio()

    print("\n--- Test 3: Pre-buffer clearing behavior ---")
    test_prebuffer_clears_after_retrieval()

    # Uncomment to run live test
    # print("\n--- Test 4: Live capture (requires microphone) ---")
    # asyncio.run(test_live_capture_with_vad())

    print("\n" + "="*60)
    print("Tests completed. Review output for findings.")
    print("="*60)
