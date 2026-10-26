from pathlib import Path
from collections.abc import Sequence

import numpy as np
from scipy.io import wavfile


SAMPLE_RATE = 44100
SOUNDTRACK_PATH = (
    Path(__file__).resolve().parents[2]
    / "media"
    / "sounds"
    / "packing_progression"
    / "packing_progression.wav"
)

CHORDS = (
    (60, 64, 67, 71, 74),
    (57, 60, 64, 67, 71),
    (62, 65, 69, 72, 76),
    (55, 59, 62, 64, 69),
    (53, 57, 60, 64, 67),
    (60, 64, 67, 71, 74),
)
PENTATONIC = (0, 2, 4, 7, 9, 12, 14, 16)


def midi_to_frequency(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def add_pluck(
    audio: np.ndarray,
    start_time: float,
    note: int,
    pan: float,
    amplitude: float,
    total_samples: int,
) -> None:
    duration = 0.42
    start = int(start_time * SAMPLE_RATE)
    end = min(start + int(duration * SAMPLE_RATE), total_samples)
    if start >= total_samples or end <= start:
        return

    time = np.arange(end - start, dtype=np.float64) / SAMPLE_RATE
    frequency = midi_to_frequency(note)
    envelope = (1 - np.exp(-time * 90)) * np.exp(-time * 8.5)
    signal = (
        np.sin(2 * np.pi * frequency * time)
        + 0.24 * np.sin(2 * np.pi * frequency * 2 * time)
        + 0.06 * np.sin(2 * np.pi * frequency * 3.01 * time)
    ) * envelope * amplitude
    pan = float(np.clip(pan, -1, 1))
    left_gain = np.sqrt(0.5 * (1 - pan))
    right_gain = np.sqrt(0.5 * (1 + pan))
    audio[start:end, 0] += signal * left_gain
    audio[start:end, 1] += signal * right_gain


def add_soft_pad(
    audio: np.ndarray,
    start_time: float,
    duration: float,
    chord_index: int,
    total_samples: int,
) -> None:
    start = max(0, int(start_time * SAMPLE_RATE))
    end = min(
        int((start_time + duration) * SAMPLE_RATE),
        total_samples,
    )
    if end <= start:
        return

    time = np.arange(end - start, dtype=np.float64) / SAMPLE_RATE
    fade_in = np.clip(time / 0.8, 0, 1)
    envelope = (0.5 - 0.5 * np.cos(np.pi * fade_in))
    release_start = max(duration - 1.0, 0.0)
    release_progress = np.clip(
        (time - release_start) / max(duration - release_start, 1e-6),
        0,
        1,
    )
    envelope *= 0.5 + 0.5 * np.cos(np.pi * release_progress)

    chord = CHORDS[chord_index]
    for voice_index, note in enumerate(chord):
        frequency = midi_to_frequency(note)
        pan = (voice_index / max(len(chord) - 1, 1) - 0.5) * 0.65
        voice = (
            np.sin(2 * np.pi * frequency * time)
            + 0.12 * np.sin(2 * np.pi * frequency * 2 * time)
        )
        voice *= envelope * 0.018
        audio[start:end, 0] += voice * np.sqrt(0.5 * (1 - pan))
        audio[start:end, 1] += voice * np.sqrt(0.5 * (1 + pan))


def generate_soundtrack(
    shot_events: Sequence[tuple[float, int, float]],
    stage_events: Sequence[tuple[float, float, int]],
    total_duration: float,
) -> Path:
    total_samples = int(np.ceil(total_duration * SAMPLE_RATE))
    audio = np.zeros((total_samples, 2), dtype=np.float64)

    for stage_start, shot_duration, stage_index in stage_events:
        pad_duration = min(
            shot_duration + 3.2,
            total_duration - stage_start,
        )
        add_soft_pad(
            audio,
            stage_start,
            pad_duration,
            stage_index,
            total_samples,
        )
        highlight_start = stage_start + shot_duration
        chord = CHORDS[stage_index]
        for arpeggio_index, note in enumerate(chord):
            add_pluck(
                audio,
                highlight_start + 0.12 * arpeggio_index,
                note + 12,
                pan=(arpeggio_index - 2) * 0.18,
                amplitude=0.11,
                total_samples=total_samples,
            )
        add_pluck(
            audio,
            highlight_start + 1.25,
            chord[0] + 12,
            pan=0,
            amplitude=0.15,
            total_samples=total_samples,
        )

    for start_time, note, pan in shot_events:
        add_pluck(
            audio,
            start_time,
            note,
            pan=pan,
            amplitude=0.09,
            total_samples=total_samples,
        )

    fade_samples = min(SAMPLE_RATE * 2, total_samples)
    if fade_samples:
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)[:, None]

    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio *= 0.92 / peak

    SOUNDTRACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    wavfile.write(
        str(SOUNDTRACK_PATH),
        SAMPLE_RATE,
        np.clip(audio * 32767, -32768, 32767).astype(np.int16),
    )
    return SOUNDTRACK_PATH


def generate_for_packing_progression() -> Path:
    from packing_progression import PackingProgression

    scene = PackingProgression()
    schedule, total_duration = scene.get_stage_schedule()
    shot_events = []
    stage_events = []

    for stage_index, _, seed_data, step_time, start_time in schedule:
        shot_duration = len(seed_data) * step_time
        stage_events.append((start_time, shot_duration, stage_index))
        chord = CHORDS[stage_index]
        for shot_index, (position, _) in enumerate(seed_data):
            event_time = start_time + (shot_index + 0.85) * step_time
            note = chord[shot_index % len(chord)] + 12
            pan = position[0] / scene.field_radius
            shot_events.append((event_time, note, pan))

    return generate_soundtrack(
        shot_events,
        stage_events,
        total_duration,
    )


if __name__ == "__main__":
    output_file = generate_for_packing_progression()
    print(f"Separate soundtrack saved to: {output_file}")
