from pathlib import Path
import numpy as np
from scipy.signal import convolve2d
from scipy.io import wavfile

# --- АВТОМАТИЧЕСКАЯ НАСТРОЙКА ПУТЕЙ ---
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"

# =============================================================
# 1. СТРОГИЙ ТАЙМИНГ MANIM (РОВНО 16.0 СЕКУНД)
# =============================================================
SAMPLE_RATE = 44100
STEPS = 120

INTRO_DELAY = 1.5         # 1.0s FadeIn + 0.5s Wait
SIMULATION_TIME = 12.0    # run_time=12.0
STEP_TIME = SIMULATION_TIME / STEPS  # 0.1 секунды на шаг
OUTRO_DELAY = 2.5         # 1.5s Wait + 1.0s FadeOut

TOTAL_DURATION = INTRO_DELAY + SIMULATION_TIME + OUTRO_DELAY # = 16.0
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# --- МАТРИЦА ПУШКИ ГОСПЕРА (Точно как в видео) ---
ROWS, COLS = 72, 40
grid = np.zeros((ROWS, COLS), dtype=np.uint8)

gun_pattern = [
    (5, 1), (5, 2), (6, 1), (6, 2),
    (5, 11), (6, 11), (7, 11), (4, 12), (8, 12), (3, 13), (9, 13), (3, 14), (9, 14), (6, 15), (4, 16), (8, 16), (5, 17), (6, 17), (7, 17), (6, 18),
    (3, 21), (4, 21), (5, 21), (3, 22), (4, 22), (5, 22), (2, 23), (6, 23), (1, 25), (2, 25), (6, 25), (7, 25),
    (3, 35), (4, 35), (3, 36), (4, 36)
]

r_shift, c_shift = 3, 1
for r, c in gun_pattern:
    if r + r_shift < ROWS and c + c_shift < COLS:
        grid[r + r_shift, c + c_shift] = 1

kernel = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1]
], dtype=np.uint8)

def step_life_fast(g):
    neighbors = convolve2d(g, kernel, mode='same', boundary='fill', fillvalue=0)
    return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(np.uint8)

# =============================================================
# 2. ФОНОВЫЙ ГУЛ (Точная синхронизация затуханий)
# =============================================================
t_full = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False)

drone_vol = np.ones_like(t_full)
drone_vol[t_full < INTRO_DELAY] = 0.3  # Тихо в интро
drone_vol[t_full > (INTRO_DELAY + SIMULATION_TIME)] = np.exp(-(t_full[t_full > (INTRO_DELAY + SIMULATION_TIME)] - (INTRO_DELAY + SIMULATION_TIME)) * 2) # Плавное затухание в конце

base_hum = np.sin(2 * np.pi * 55 * t_full) * 0.08
sub_drone = np.sin(2 * np.pi * 110 * t_full) * 0.05
audio_data[:, 0] += (base_hum + sub_drone) * drone_vol
audio_data[:, 1] += (base_hum + sub_drone) * drone_vol

# =============================================================
# 3. СИНХРОННЫЕ ЩЕЛЧКИ КЛЕТОК (Ровно с 1.5 секунды)
# =============================================================
print(f"Синтез аудио для Пушки Госпера (Длительность {TOTAL_DURATION}с)...")

current_grid = grid
for s in range(STEPS):
    next_grid = step_life_fast(current_grid)
    
    # Строгое вычисление старта каждого кадра
    t_start = INTRO_DELAY + (s * STEP_TIME)
    start_sample = int(t_start * SAMPLE_RATE)

    born = np.argwhere((next_grid == 1) & (current_grid == 0))
    
    if len(born) > 0 and start_sample < TOTAL_SAMPLES:
        # У пушки Госпера период = 30 шагов. Акцентируем выстрел!
        is_shot = ((s - 14) % 30 == 0)
        dur = 0.25 if is_shot else 0.08
        n_samples = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n_samples, endpoint=False)

        freq = 440.0 if is_shot else (1200 + (s % 10) * 150)
        env = np.exp(-t * (15.0 if is_shot else 60.0))
        
        snd = np.sin(2 * np.pi * freq * t) * env * (0.6 if is_shot else 0.15)
        
        # Стерео-эффект: звук распределяется по ширине экрана
        for r, c in born[:15]:
            pan_x = (c - COLS/2) / (COLS/2)
            l_gain = np.sqrt(0.5 * (1 - pan_x))
            r_gain = np.sqrt(0.5 * (1 + pan_x))
            
            end_sample = min(start_sample + n_samples, TOTAL_SAMPLES)
            length = end_sample - start_sample
            if length > 0:
                audio_data[start_sample:end_sample, 0] += snd[:length] * l_gain
                audio_data[start_sample:end_sample, 1] += snd[:length] * r_gain

    current_grid = next_grid

# Пиковая нормализация
peak = np.max(np.abs(audio_data))
if peak > 0:
    audio_data /= peak

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print(f"Аудиофайл готов и синхронизирован: {OUTPUT_FILE}")