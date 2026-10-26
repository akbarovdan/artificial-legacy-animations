from pathlib import Path
import numpy as np
from scipy.io import wavfile

# =============================================================
# 1. НАСТРОЙКИ ПРОЕКТА
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / "golden_ratio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "spacetime_ambient_pad.wav"

SAMPLE_RATE = 44100
# 3 дерева по ~12.8 секунд + хвост
TOTAL_DURATION = 42.0  
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 2. МЯГКИЙ АТМОСФЕРНЫЙ СИНТЕЗАТОР (AMBIENT PAD)
# =============================================================
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def generate_ambient_pad(chord_midi, duration, vol=0.3):
    """
    Генерирует теплый, медленный аккорд без резких атак.
    Идеален как подложка под звуки растущего льда/кристаллов.
    """
    n_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n_samples, endpoint=False)
    
    pad_l = np.zeros(n_samples)
    pad_r = np.zeros(n_samples)
    
    for midi_note in chord_midi:
        freq = midi_to_freq(midi_note)
        
        # 3 осциллятора на каждую ноту с легким расстроем (Detune) для ширины космоса
        osc1 = np.sin(2 * np.pi * freq * t)
        osc2 = np.sin(2 * np.pi * (freq * 1.004) * t) * 0.6
        osc3 = np.sin(2 * np.pi * (freq * 0.996) * t) * 0.6
        
        # Добавляем крошечную долю треугольной волны для теплоты (тело звука)
        tri = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
        
        # Разводим расстроенные осцилляторы по панораме
        pad_l += (osc1 + osc2 + tri * 0.1)
        pad_r += (osc1 + osc3 + tri * 0.1)

    # ---------------------------------------------------------
    # КОНВЕРТ (Огибающая громкости): Очень плавное всплытие и угасание
    # ---------------------------------------------------------
    attack_time = 3.5  # Секунд на плавное появление
    release_time = 4.0 # Секунд на растворение в конце
    
    attack_samples = int(attack_time * SAMPLE_RATE)
    release_samples = int(release_time * SAMPLE_RATE)
    
    env = np.ones(n_samples)
    # Плавная параболическая атака
    env[:attack_samples] = np.linspace(0, 1, attack_samples) ** 2 
    # Плавное параболическое затухание
    env[-release_samples:] = np.linspace(1, 0, release_samples) ** 2 
    
    pad_l = pad_l * env * vol
    pad_r = pad_r * env * vol
    
    return np.column_stack((pad_l, pad_r))

def mix_audio(start_time, sound_data):
    s_idx = int(start_time * SAMPLE_RATE)
    e_idx = min(s_idx + len(sound_data), TOTAL_SAMPLES)
    length = e_idx - s_idx
    if length > 0:
        audio[s_idx:e_idx] += sound_data[:length]

print("Генерация фоновых эмбиент-аккордов...")

# =============================================================
# 3. ТАЙМИНГИ И АККОРДЫ ДЛЯ ТРЕХ ДЕРЕВЬЕВ
# =============================================================
# Тайминг одного дерева в Manim:
# 0.5s (пауза) + (130 * 0.07 = 9.1s рост) + 1.5s (созерцание) + 1.2s (затухание) + 0.5s (пауза) 
# Итого ~12.8 секунд на одно дерево.

# Дерево 1: Клен (Fmaj9 - Открытый, земной, широкий)
chord_maple = [41, 48, 52, 55, 60] # F2, C3, E3, G3, C4
mix_audio(0.0, generate_ambient_pad(chord_maple, duration=13.0, vol=0.08))

# Дерево 2: Сосна (Em11 - Лесной, высокий, прохладный)
chord_pine = [40, 47, 50, 55, 57] # E2, B2, D3, G3, A3
mix_audio(12.8, generate_ambient_pad(chord_pine, duration=13.0, vol=0.08))

# Дерево 3: Фибоначчи (Cmaj13#11 - Роскошный, "божественный" Лидийский лад)
chord_fibo = [36, 43, 47, 50, 54, 59] # C2, G2, B2, D3, F#3, B3
mix_audio(25.6, generate_ambient_pad(chord_fibo, duration=15.0, vol=0.09)) # Звучит чуть дольше в конце

# =============================================================
# 4. МАСТЕРИНГ И РЕВЕРБЕРАЦИЯ
# =============================================================
# Создаем эффект огромного пустого пространства (Space Reverb / Delay)
delay_samples = int(0.6 * SAMPLE_RATE) # 600ms
audio[delay_samples:, 0] += audio[:-delay_samples, 1] * 0.35 
audio[delay_samples:, 1] += audio[:-delay_samples, 0] * 0.35 

# Мягкий лимитер (чтобы звук не "запирал")
audio = np.tanh(audio)

# Нормализация
peak = np.max(np.abs(audio))
if peak > 0:
    audio = (audio / peak) * 0.85

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))
print(f"Готово! Эмбиент сохранен в: {OUTPUT_FILE}")