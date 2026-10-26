from pathlib import Path
import numpy as np
from scipy.io import wavfile
import random

# =============================================================
# 1. НАСТРОЙКИ ФАЙЛА И ПРОЕКТА
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / "golden_ratio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "achillea_growth_sound.wav"

SAMPLE_RATE = 44100
TOTAL_DURATION = 14.0  # Длина аудио с запасом на затухание
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 2. МЯГКИЙ АКУСТИЧЕСКИЙ СИНТЕЗАТОР (ЭФФЕКТ АРФЫ/КОЛОКОЛЬЧИКА)
# =============================================================
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def synth_crystal_harp(freq, duration=2.0, vel=0.5, pan=0.0):
    """Поверхностная гармония: чистые синусоиды с мягким затуханием струны"""
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    # Мягкая атака (чтобы не щелкало) и долгое воздушное затухание
    attack = int(0.02 * SAMPLE_RATE)
    env = np.ones(n_samples)
    env[:attack] = np.linspace(0, 1, attack)
    env[attack:] = np.exp(-t[attack:] * 3.5) # Экспоненциальное угасание
    
    # Фундаментальная частота + очень тихие гармоники для "стеклянного" окраса
    s = (np.sin(2 * np.pi * freq * t) + 
         0.25 * np.sin(2 * np.pi * (freq * 2) * t) + 
         0.10 * np.sin(2 * np.pi * (freq * 3) * t)) * env * vel
    
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

# =============================================================
# 3. ТОЧНЫЕ ТАЙМИНГИ ИЗ MANIM И ЛОГИКА ОЗВУЧКИ
# =============================================================
# Я высчитал точные миллисекунды из вашего кода `achillea_ptarmica.py`
# Время, когда вызывается self.play(Create(branches), run_time=0.6)
growth_times = [1.57, 2.94, 4.68, 6.04, 7.64, 9.60]

# Количество веток на каждом ярусе
branch_counts = [1, 2, 3, 5, 8, 13]

# Эфирная (магическая) гамма: До-мажор с добавленной 9-й и 11-й (Лидийский лад)
# Она звучит как природа, космос и гармония
scale_midi = [60, 62, 64, 67, 71, 72, 74, 76, 79, 83, 84, 86, 88, 91, 95]

print("Генерация гармонии роста Птармики...")

for tier_idx in range(6):
    start_t = growth_times[tier_idx]
    num_branches = branch_counts[tier_idx]
    
    # Все ветки одного яруса рисуются за 0.6 секунды
    duration_of_growth = 0.6 
    
    for b in range(num_branches):
        # Распределяем ноты равномерно по времени роста яруса
        # Для 13 веток ноты будут сыпаться очень быстро (как водопад), для 2-х - медленно.
        note_t = start_t + (b / num_branches) * (duration_of_growth * 0.9)
        
        # Чем выше ярус, тем шире и выше гармония
        note_idx = (tier_idx * 2 + b) % len(scale_midi)
        midi_note = scale_midi[note_idx]
        
        freq = midi_to_freq(midi_note)
        
        # Раскидываем звуки по стереобазе влево-вправо для объема
        pan = np.random.uniform(-0.6, 0.6)
        
        # Чем больше веток, тем тише каждая отдельная нота (чтобы звук оставался легким)
        vel = 0.4 / np.sqrt(num_branches)
        
        add_audio(note_t, synth_crystal_harp(freq, duration=2.5, vel=vel, pan=pan))

# =============================================================
# 4. МАСТЕРИНГ (ЭХО КОСМОСА)
# =============================================================
# Добавляем легкое обволакивающее стерео-эхо (Delay)
delay_samples = int(0.35 * SAMPLE_RATE) # Задержка 350 мс
audio[delay_samples:, 0] += audio[:-delay_samples, 1] * 0.25 # Левое ухо слышит правое эхо
audio[delay_samples:, 1] += audio[:-delay_samples, 0] * 0.25 # Правое ухо слышит левое эхо

# Нормализация (защита от перегруза)
peak = np.max(np.abs(audio))
if peak > 0:
    audio = (audio / peak) * 0.85

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))
print(f"Готово! Сохранено в: {OUTPUT_FILE}")