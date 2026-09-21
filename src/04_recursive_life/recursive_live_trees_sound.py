from pathlib import Path
import numpy as np
from scipy.io import wavfile
import random

# =============================================================
# 0. НАСТРОЙКА ПУТЕЙ
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
SCRIPT_DIR = SCRIPT_PATH.parent
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"

SAMPLE_RATE = 44100
TOTAL_DURATION = 26.5  
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 1. СИНТЕЗАТОРЫ
# =============================================================
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def synth_juno_chord(chord_freqs, duration=2.5, vel=0.75):
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)
    
    attack = min(int(0.18 * SAMPLE_RATE), n_samples)
    env = np.ones(n_samples)
    env[:attack] = np.linspace(0, 1, attack)
    env[attack:] = np.exp(-t[attack:] * 0.95)
    
    for f in chord_freqs:
        detune = 0.5
        s1 = np.sin(2 * np.pi * (f - detune) * t)
        s2 = np.sin(2 * np.pi * (f + detune) * t)
        saw = 2.0 * (t * f - np.floor(t * f + 0.5)) * 0.28
        
        left += (s1 + saw) * env * 0.22
        right += (s2 + saw) * env * 0.22
        
    sound_l = np.tanh(left) * vel
    sound_r = np.tanh(right) * vel
    return np.column_stack((sound_l, sound_r))

def synth_cosmic_pluck(freq, duration=0.55, vel=0.5, pan=0.0):
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    env = np.exp(-t * 11.0)
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)) * env * vel
    
    pan = np.clip(pan, -1.0, 1.0)
    l = np.sqrt(0.5 * (1.0 - pan)) * s
    r = np.sqrt(0.5 * (1.0 + pan)) * s
    return np.column_stack((l, r))

def add_audio(start_time, sound_data):
    s_idx = int(start_time * SAMPLE_RATE)
    e_idx = min(s_idx + len(sound_data), TOTAL_SAMPLES)
    length = e_idx - s_idx
    if length > 0:
        audio[s_idx:e_idx] += sound_data[:length]

print(f"Синтез гармонически разрешенного саундтрека для {SCRIPT_NAME}...")

# =============================================================
# 2. ЧАСТЬ 1: ОБУЧАЮЩИЙ ПОБЕГ
# =============================================================
t = 0.3
tree_str = "F[+F][-F[-F]F]F[+F][-F]"

intro_chord = [midi_to_freq(m) for m in [50, 57, 62, 65, 69]]
add_audio(0.0, synth_juno_chord(intro_chord, duration=4.2, vel=0.45))

tutorial_pitches = [62, 65, 69, 72, 74, 76, 77, 81]
p_i = 0

for char in tree_str:
    if char == 'F':
        f = midi_to_freq(tutorial_pitches[p_i % len(tutorial_pitches)])
        add_audio(t, synth_cosmic_pluck(f, duration=0.6, vel=0.6, pan=(p_i % 3 - 1) * 0.3))
        p_i += 1
        t += 0.18
    elif char == '[':
        add_audio(t, synth_cosmic_pluck(midi_to_freq(86), duration=0.25, vel=0.45, pan=-0.4))
        t += 0.10
    elif char == ']':
        add_audio(t, synth_cosmic_pluck(midi_to_freq(57), duration=0.35, vel=0.4, pan=0.3))
        t += 0.10
    elif char in ['+', '-']:
        add_audio(t, synth_cosmic_pluck(midi_to_freq(78), duration=0.08, vel=0.2, pan=0.1))
        t += 0.07

t += 0.6 + 0.8 + 0.2

# =============================================================
# 3. ЧАСТЬ 2: ТАЙМЛАПС 7 ДЕРЕВЬЕВ
# =============================================================
FUNK_CHORDS = [
    [midi_to_freq(m) for m in [50, 57, 60, 64, 69]], # 1. a - Dm9
    [midi_to_freq(m) for m in [43, 55, 59, 64, 67]], # 2. b - G13
    [midi_to_freq(m) for m in [48, 55, 59, 64, 71]], # 3. c - Cmaj9
    [midi_to_freq(m) for m in [53, 57, 60, 64, 69]], # 4. d - Fmaj7
    [midi_to_freq(m) for m in [47, 53, 57, 62, 65]], # 5. e - Bm7b5
    [midi_to_freq(m) for m in [52, 56, 58, 62, 68]], # 6. f - E7(#9) [Напряжение]
    # 7. g - ДРЕВО ЖИЗНИ: Am11 [Разрешение в тонику]
    [midi_to_freq(m) for m in [45, 52, 55, 60, 64, 69, 72, 76]] 
]

for i in range(7):
    chord = FUNK_CHORDS[i]
    is_last = (i == 6)
    
    chord_dur = 4.8 if is_last else 2.5
    chord_vel = 0.88 if is_last else 0.72
    add_audio(t, synth_juno_chord(chord, duration=chord_dur, vel=chord_vel))
    
    n_sparks = 28 if is_last else 18
    growth_time = 1.8 if is_last else 1.5
    
    for s in range(n_sparks):
        prog = (s / n_sparks) ** 1.3
        spark_t = t + prog * growth_time
        note_f = random.choice(chord) * (2 ** random.choice([1, 2]))
        pan = (random.random() - 0.5) * 1.3
        vel = 0.45 if is_last else 0.35
        add_audio(spark_t, synth_cosmic_pluck(note_f, duration=0.6, vel=vel, pan=pan))
        
    t += 1.8 if is_last else 1.6
    t += 1.0 if is_last else 0.5
    
    if not is_last:
        t += 0.45 + 0.1
    else:
        t += 1.6 + 1.0

# =============================================================
# 4. ПРОСТРАНСТВО И МАСТЕРИНГ
# =============================================================
delay_time = int(0.27 * SAMPLE_RATE)
audio[delay_time:, 0] += audio[:-delay_time, 1] * 0.25
audio[delay_time:, 1] += audio[:-delay_time, 0] * 0.20

peak = np.max(np.abs(audio))
if peak > 0:
    audio = (audio / peak) * 0.94

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))
print(f"Готово! Финал сохранен в:\n{OUTPUT_FILE}")