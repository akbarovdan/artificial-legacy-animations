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

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / "golden_ratio_intro"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
# Файл будет сохранен как golden_ratio_intro_sound.wav
OUTPUT_FILE = OUTPUT_DIR / "golden_ratio_intro_sound.wav"

SAMPLE_RATE = 44100
# Хронометраж: 1.0 (пауза) + 3.65 (дерево 1) + 3.65 (дерево 2) + 4.6 (дерево 3) + хвост
TOTAL_DURATION = 16.0  
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 1. ТЕПЛЫЕ АНАЛОГОВЫЕ СИНТЕЗАТОРЫ (БЕЗ ДИСТОРШНА)
# =============================================================
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def synth_juno_chord(chord_freqs, duration=2.5, vel=0.75):
    """Мягкий и глубокий пэд Roland Juno-106 со стерео-хорусом"""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    left = np.zeros(n_samples)
    right = np.zeros(n_samples)
    
    # Очень мягкое нарастание (fade-in), чтобы не было удара
    attack = min(int(0.25 * SAMPLE_RATE), n_samples)
    env = np.ones(n_samples)
    env[:attack] = np.linspace(0, 1, attack)
    # Плавное угасание
    env[attack:] = np.exp(-t[attack:] * 0.85)
    
    for f in chord_freqs:
        detune = 0.45
        s1 = np.sin(2 * np.pi * (f - detune) * t)
        s2 = np.sin(2 * np.pi * (f + detune) * t)
        # Добавляем лишь каплю пилы для теплоты, основа - синусоиды
        saw = 2.0 * (t * f - np.floor(t * f + 0.5)) * 0.15 
        
        left += (s1 + saw) * env * 0.25
        right += (s2 + saw) * env * 0.25
        
    # Мягкое сатурирование (без жесткого клиппинга)
    sound_l = np.tanh(left) * vel
    sound_r = np.tanh(right) * vel
    return np.column_stack((sound_l, sound_r))

def synth_cosmic_pluck(freq, duration=0.6, vel=0.5, pan=0.0):
    """Стеклянные, прозрачные искры для веток (без писка)"""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    env = np.exp(-t * 9.0) # Мягкий хвост
    s = (np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 2 * t)) * env * vel
    
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

print(f"Синтез гармоничного финала для {SCRIPT_NAME}...")

# =============================================================
# 2. МУЗЫКАЛЬНАЯ ПРОГРАММА (3 ИДЕАЛЬНЫХ АККОРДА)
# =============================================================
# Идеальная каденция, которая звучит как единое музыкальное произведение:
FUNK_CHORDS = [
    # 1. Царский Дуб (Широкий, открытый Fmaj7)
    [midi_to_freq(m) for m in [53, 57, 60, 64, 69]], 
    
    # 2. Огненная Лоза (Горячий, напряженный E7#9)
    [midi_to_freq(m) for m in [52, 56, 58, 62, 68]], 
    
    # 3. Сумеречный Папоротник (Разрешение в глубокий, бархатный Am11)
    [midi_to_freq(m) for m in [45, 52, 55, 60, 64, 69, 72, 76]] 
]

t = 1.0 # self.wait(1.0) перед началом роста

for i in range(3):
    chord = FUNK_CHORDS[i]
    is_last = (i == 2)
    
    # Аккорд звучит дольше и полнее на последнем дереве
    chord_dur = 5.5 if is_last else 3.2
    chord_vel = 0.85 if is_last else 0.75
    add_audio(t, synth_juno_chord(chord, duration=chord_dur, vel=chord_vel))
    
    # Россыпь звездных искр по мере роста (run_time=2.1)
    n_sparks = 32 if is_last else 24
    growth_time = 2.1
    
    for s in range(n_sparks):
        # Экспоненциальное распределение: сначала ствол, потом густая крона
        prog = (s / n_sparks) ** 1.5 
        spark_t = t + prog * growth_time
        
        # Выбираем ноту из текущего аккорда, переносим на октаву/две вверх
        note_f = random.choice(chord) * (2 ** random.choice([1, 2]))
        pan = (random.random() - 0.5) * 1.4 # Широкое стерео
        vel = 0.40 if is_last else 0.30
        
        add_audio(spark_t, synth_cosmic_pluck(note_f, duration=0.7, vel=vel, pan=pan))
        
    # Точная синхронизация с таймингами Manim:
    t += 2.1 # run_time роста
    t += 0.7 # self.wait(0.7)
    
    if not is_last:
        t += 0.65 # FadeOut
        t += 0.20 # wait(0.2)
    else:
        # Финальный уход в космос
        t += 1.8 

# =============================================================
# 3. ТЕПЛОЕ ПРОСТРАНСТВО И МАСТЕРИНГ
# =============================================================
# Мягкий аналоговый дилей для глубины космоса
delay_time = int(0.28 * SAMPLE_RATE)
audio[delay_time:, 0] += audio[:-delay_time, 1] * 0.25
audio[delay_time:, 1] += audio[:-delay_time, 0] * 0.22

# Нормализация громкости с идеальным запасом (чтобы звук был бархатным)
peak = np.max(np.abs(audio))
if peak > 0:
    audio = (audio / peak) * 0.90

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))
print(f"Готово! Музыкальная сонификация сохранена в:\n{OUTPUT_FILE}")