from pathlib import Path

import numpy as np
from scipy.io import wavfile

from layered_packing import LayeredPacking, PATTERNS


SAMPLE_RATE = 44100
TRACK_DURATION = 41.2
BOUNDARY_DURATION = 0.9
INTRO_DURATION = 0.8
STAGE_TRANSITION_DURATION = 0.7
SEED_GROWTH_DURATION = 3.5
HIGHLIGHT_DURATION = 1.3
METRIC_HOLD_DURATION = 1.0
STAGE_DURATION = (
    SEED_GROWTH_DURATION
    + HIGHLIGHT_DURATION
    + METRIC_HOLD_DURATION
    + STAGE_TRANSITION_DURATION
)
SEED_LAG_RATIO = 0.012
OUTPUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "media"
    / "sounds"
    / "layered_packing"
)
BACKGROUND_PATH = OUTPUT_DIR / "layered_packing_background.wav"
MIXED_PATH = OUTPUT_DIR / "layered_packing_with_bubbles.wav"

STAGE_CHORDS = (
    (53, 57, 60, 64, 67, 72),
    (45, 52, 55, 60, 64, 69),
    (50, 57, 60, 62, 64, 69),
    (43, 50, 55, 59, 64, 69),
    (52, 55, 59, 64, 67, 71),
    (48, 55, 59, 60, 64, 67, 69, 74),
)
SEED_NOTE_SETS = (
    (60, 64, 67, 69, 72),
    (57, 60, 64, 67, 69, 72),
    (57, 60, 62, 64, 69, 74),
    (55, 59, 62, 64, 67, 69, 74),
    (55, 59, 64, 67, 71, 74),
    (60, 62, 64, 67, 69, 72, 76),
)


def midi_to_frequency(note: int) -> float:
    return 440.0 * 2 ** ((note - 69) / 12)


def get_stage_start(stage_index: int) -> float:
    return (
        BOUNDARY_DURATION
        + INTRO_DURATION
        + stage_index * STAGE_DURATION
    )


def add_background_pad(
    audio: np.ndarray,
    start_time: float,
    end_time: float,
    chord: tuple[int, ...],
) -> None:
    start = max(0, int(start_time * SAMPLE_RATE))
    end = min(int(end_time * SAMPLE_RATE), len(audio))
    if end <= start:
        return

    time = np.arange(end - start, dtype=np.float64) / SAMPLE_RATE
    duration = (end - start) / SAMPLE_RATE
    fade_in = np.clip(time / 1.15, 0.0, 1.0)
    fade_out = np.clip((duration - time) / 1.0, 0.0, 1.0)
    envelope = (0.5 - 0.5 * np.cos(np.pi * fade_in)) * fade_out
    drift = 1.0 + 0.012 * np.sin(2 * np.pi * 0.09 * time)

    for voice_index, note in enumerate(chord):
        frequency = midi_to_frequency(note)
        pan = (voice_index / max(len(chord) - 1, 1) - 0.5) * 0.6
        left = np.sin(2 * np.pi * (frequency - 0.07) * time)
        right = np.sin(2 * np.pi * (frequency + 0.07) * time)
        left += 0.12 * np.sin(2 * np.pi * frequency * 2 * time)
        right += 0.12 * np.sin(2 * np.pi * frequency * 2 * time)
        left *= envelope * drift * 0.014
        right *= envelope * drift * 0.014
        audio[start:end, 0] += left * np.sqrt(0.5 * (1 - pan))
        audio[start:end, 1] += right * np.sqrt(0.5 * (1 + pan))


def make_background() -> np.ndarray:
    total_samples = int(round(TRACK_DURATION * SAMPLE_RATE))
    audio = np.zeros((total_samples, 2), dtype=np.float64)

    for stage_index, chord in enumerate(STAGE_CHORDS):
        stage_start = get_stage_start(stage_index)
        next_stage_start = (
            get_stage_start(stage_index + 1)
            if stage_index + 1 < len(STAGE_CHORDS)
            else TRACK_DURATION
        )
        add_background_pad(
            audio,
            stage_start,
            min(next_stage_start + 0.9, TRACK_DURATION),
            chord,
        )

    fade_samples = int(1.5 * SAMPLE_RATE)
    audio[-fade_samples:] *= np.linspace(1.0, 0.0, fade_samples)[:, None]
    return audio


def add_seed_chime(
    audio: np.ndarray,
    start_time: float,
    note: int,
    pan: float,
) -> None:
    duration = 0.32
    start = int(start_time * SAMPLE_RATE)
    end = min(start + int(duration * SAMPLE_RATE), len(audio))
    if start >= len(audio) or end <= start:
        return

    time = np.arange(end - start, dtype=np.float64) / SAMPLE_RATE
    frequency = midi_to_frequency(note)
    envelope = (1 - np.exp(-time * 115)) * np.exp(-time * 10)
    signal = (
        np.sin(2 * np.pi * frequency * time)
        + 0.2 * np.sin(2 * np.pi * frequency * 2.01 * time)
        + 0.07 * np.sin(2 * np.pi * frequency * 3.98 * time)
    )
    signal *= envelope * 0.045
    pan = float(np.clip(pan, -1.0, 1.0))
    audio[start:end, 0] += signal * np.sqrt(0.5 * (1 - pan))
    audio[start:end, 1] += signal * np.sqrt(0.5 * (1 + pan))


def add_seed_events(audio: np.ndarray) -> None:
    scene = LayeredPacking()
    for stage_index, pattern in enumerate(PATTERNS):
        seeds = scene.get_pattern_seeds(pattern)
        group_duration = 1 + SEED_LAG_RATIO * max(len(seeds) - 1, 0)
        time_scale = SEED_GROWTH_DURATION / group_duration
        stage_start = get_stage_start(stage_index)
        notes = SEED_NOTE_SETS[stage_index]

        for seed_index, (position, _) in enumerate(seeds):
            start_time = (
                stage_start + seed_index * SEED_LAG_RATIO * time_scale
            )
            note = notes[(seed_index * 3 + stage_index) % len(notes)]
            pan = float(position[0] / scene.field_radius)
            add_seed_chime(audio, start_time, note, pan)


def write_wav(path: Path, audio: np.ndarray) -> None:
    peak = float(np.max(np.abs(audio)))
    if peak > 0.92:
        audio = audio * (0.92 / peak)
    pcm = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    wavfile.write(str(path), SAMPLE_RATE, pcm)


def generate_soundtracks() -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    background = make_background()
    write_wav(BACKGROUND_PATH, background.copy())

    with_bubbles = background.copy()
    add_seed_events(with_bubbles)
    write_wav(MIXED_PATH, with_bubbles)
    return MIXED_PATH, BACKGROUND_PATH


if __name__ == "__main__":
    mixed_path, background_path = generate_soundtracks()
    print(f"Background + harmonic seed sounds: {mixed_path}")
    print(f"Background only: {background_path}")
