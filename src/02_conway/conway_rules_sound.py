from pathlib import Path
import numpy as np
from scipy.io import wavfile

# =============================================================
# 0. НАСТРОЙКА ПУТЕЙ
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"

# =============================================================
# 1. ТОЧНЫЙ ТАЙМИНГ MANIM СЦЕНЫ (18.1 сек)
# =============================================================
SAMPLE_RATE = 44100
TOTAL_DURATION = 18.15
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 2. ЗВУКОВЫЕ ПРИМИТИВЫ (Синтез)
# =============================================================

def add_audio_segment(sound_mono, start_time_sec, pan_x=0.0):
    """Микширует звук в общий мастер-трек со стереопанорамой."""
    start_idx = int(start_time_sec * SAMPLE_RATE)
    n_samples = len(sound_mono)
    end_idx = min(start_idx + n_samples, TOTAL_SAMPLES)
    length = end_idx - start_idx
    
    if length > 0 and start_idx < TOTAL_SAMPLES:
        # Панорама: pan_x от -1.0 (лево) до +1.0 (право)
        l_gain = np.sqrt(0.5 * (1.0 - pan_x))
        r_gain = np.sqrt(0.5 * (1.0 + pan_x))
        audio_data[start_idx:end_idx, 0] += sound_mono[:length] * l_gain
        audio_data[start_idx:end_idx, 1] += sound_mono[:length] * r_gain

def synth_click(dur=0.04, freq=2800.0, volume=0.25):
    """Тактильный щелчок клика мышки по клетке."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.uniform(-0.8, 0.8, n)
    sine = np.sin(2 * np.pi * freq * t) * 0.4
    env = np.exp(-t * 180.0) # Резкая атака
    return (noise * 0.6 + sine) * env * volume

def synth_death(dur=0.25, volume=0.28):
    """Сухой мягкий звук угасания клетки в красный (смерть)."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # Низкий тон + мягкий шум
    sine_low = np.sin(2 * np.pi * 160.0 * t) * 0.5
    noise = np.convolve(np.random.uniform(-0.5, 0.5, n), np.ones(8)/8, mode='same')
    env = np.exp(-t * 22.0)
    return (sine_low + noise) * env * volume

def synth_birth(dur=0.35, volume=0.35):
    """Яркий хрустальный мятно-зеленый звон рождения новой клетки."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq1 = 659.25  # E5
    freq2 = 1318.5  # E6
    sine = (np.sin(2 * np.pi * freq1 * t) + 0.3 * np.sin(2 * np.pi * freq2 * t))
    env = np.minimum(t / 0.003, 1.0) * np.exp(-t * 12.0)
    return sine * env * volume

def synth_blinker_tick(dur=0.15, high=True, volume=0.22):
    """Ритмичный мягкий тик-так осциллятора (мигалки)."""
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = 523.25 if high else 392.00 # C5 vs G4
    sine = np.sin(2 * np.pi * freq * t)
    env = np.exp(-t * 35.0)
    return sine * env * volume

# =============================================================
# 3. ПОСТРОЕНИЕ ДОРОЖКИ СТРОГО ПО КАДРАМ MANIM
# =============================================================
print(f"Синтез аудио по кадрам для '{SCRIPT_NAME}'...")

# -------------------------------------------------------------
# ЭТАП 1: ТРИ ПРАВИЛА (0.0с - 8.2с)
# -------------------------------------------------------------
# 1. Underpopulation: клетка краснеет на 0.8с
add_audio_segment(synth_death(), start_time_sec=0.8, pan_x=-0.2)

# 2. Overcrowding: клетка краснеет на 3.0с (на 2.2с + 0.8с)
add_audio_segment(synth_death(), start_time_sec=3.0, pan_x=0.0)

# 3. Reproduction: зеленая вспышка рождения на 5.2с (4.4с + 0.8с)
add_audio_segment(synth_birth(), start_time_sec=5.2, pan_x=0.2)

# -------------------------------------------------------------
# ЭТАП 2: ФОНОВЫЙ ГУЛ ТЕМНОЙ СЕТКИ (9.3с - 18.1с)
# -------------------------------------------------------------
t_full = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False)
ambient_drone = np.zeros_like(t_full)

# Гул включается на 9.3с при появлении сетки и плавно гаснет в конце
mask_drone = (t_full >= 9.3)
t_drone = t_full[mask_drone] - 9.3
drone_sub = np.sin(2 * np.pi * 55.0 * t_drone) * 0.06
drone_env = np.minimum(t_drone / 1.0, 1.0) * np.exp(-np.maximum(0, t_drone - 7.0) * 1.5)
ambient_drone[mask_drone] = drone_sub * drone_env

audio_data[:, 0] += ambient_drone
audio_data[:, 1] += ambient_drone

# -------------------------------------------------------------
# ЭТАП 3: СЦЕНА 1 — ВЫМИРАНИЕ ПО ДИАГОНАЛИ (10.2с - 13.15с)
# -------------------------------------------------------------
# 5 щелчков прокликивания по диагонали (по 0.15с каждый)
t_extinct_clicks = 10.2
for i in range(5):
    t_c = t_extinct_clicks + (i * 0.15)
    pan = (i - 2) / 2.0 * 0.7  # панорама слева направо
    pitch = 2400 + i * 200     # легкое повышение тона
    add_audio_segment(synth_click(freq=pitch), start_time_sec=t_c, pan_x=pan)

# Симуляция вымирания за 3 шага:
# Шаг 1: крайние гибнут на 11.35с
add_audio_segment(synth_death(dur=0.18, volume=0.22), start_time_sec=11.35, pan_x=-0.6)
add_audio_segment(synth_death(dur=0.18, volume=0.22), start_time_sec=11.35, pan_x=0.6)

# Шаг 2: следующие две гибнут на 11.95с (11.35 + 0.25 + 0.35)
add_audio_segment(synth_death(dur=0.18, volume=0.24), start_time_sec=11.95, pan_x=-0.3)
add_audio_segment(synth_death(dur=0.18, volume=0.24), start_time_sec=11.95, pan_x=0.3)

# Шаг 3: последняя центральная клетка гаснет на 12.55с (11.95 + 0.25 + 0.35)
add_audio_segment(synth_death(dur=0.22, volume=0.28), start_time_sec=12.55, pan_x=0.0)

# (13.15с - 13.65с: 0.5 секунды абсолютной тишины на щелчки!)

# -------------------------------------------------------------
# ЭТАП 4: СЦЕНА 2 — МИГАЛКА И ВЕЧНЫЙ БЛОК (13.65с - 18.1с)
# -------------------------------------------------------------
# 6 щелчков прокликивания (по 0.15с каждый)
t_loop_clicks = 13.65
for i in range(6):
    t_c = t_loop_clicks + (i * 0.15)
    pan = -0.5 if i < 3 else 0.5  # первые 3 слева (мигалка), следующие 3 справа (блок)
    pitch = 2200 + (i % 3) * 300
    add_audio_segment(synth_click(freq=pitch), start_time_sec=t_c, pan_x=pan)

# Эволюция 1 на 14.95с (13.65 + 6*0.15 + 0.4):
# Мигалка стала вертикальной + 4-я клетка блока родилась зеленым!
add_audio_segment(synth_blinker_tick(high=True), start_time_sec=14.95, pan_x=-0.5)
add_audio_segment(synth_birth(dur=0.3, volume=0.32), start_time_sec=14.95, pan_x=0.5)

# Эволюция 2 на 15.35с (14.95 + 0.4):
# Мигалка горизонтальная + блок застыл
add_audio_segment(synth_blinker_tick(high=False), start_time_sec=15.35, pan_x=-0.5)

# Эволюция 3 на 15.75с (15.35 + 0.4):
add_audio_segment(synth_blinker_tick(high=True), start_time_sec=15.75, pan_x=-0.5)

# Эволюция 4 на 16.15с (15.75 + 0.4):
add_audio_segment(synth_blinker_tick(high=False), start_time_sec=16.15, pan_x=-0.5)

# Пиковая нормализация мастера
peak = np.max(np.abs(audio_data))
if peak > 0:
    audio_data /= peak

# Экспорт
wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print(f"Готово! Синхронный файл сохранен в:\n{OUTPUT_FILE}")