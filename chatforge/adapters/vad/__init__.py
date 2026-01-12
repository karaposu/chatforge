"""
VAD Adapters - Voice Activity Detection implementations.

Available Adapters:
    EnergyVADAdapter: Simple RMS energy threshold (fast, no dependencies beyond numpy)
    AdaptiveEnergyVADAdapter: Energy-based with adaptive threshold based on ambient noise

Example:
    from chatforge.adapters.vad import EnergyVADAdapter
    from chatforge.ports.vad import VADConfig

    vad = EnergyVADAdapter(VADConfig(energy_threshold=0.02))
    vad.set_callbacks(
        on_speech_start=lambda: print("Speaking"),
        on_speech_end=lambda: print("Done"),
    )

    for chunk in audio_stream:
        result = vad.process_chunk(chunk)
        if result.is_speaking:
            send_to_asr(chunk)
"""

from chatforge.adapters.vad.energy import AdaptiveEnergyVADAdapter, EnergyVADAdapter

__all__ = [
    "EnergyVADAdapter",
    "AdaptiveEnergyVADAdapter",
]
