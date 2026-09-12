from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import convolve2d
from scipy.io import wavfile

# =============================================================
# 0. АВТОМАТИЧЕСКАЯ НАСТРОЙКА ПУТЕЙ
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
SCRIPT_DIR = SCRIPT_PATH.parent
PROJECT_ROOT = SCRIPT_PATH.parents[2]

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"

# =============================================================
# 1. ТОЧНЫЙ ХРОНОМЕТРАЖ MANIM (18.8 сек)
# =============================================================
SAMPLE_RATE = 44100

INTRO_DELAY = 2.5         # 1.0с (FadeIn) + 1.5с (Wait портрета)
SIMULATION_TIME = 15.0    # run_time эволюции с наездом камеры
OUTRO_TIME = 1.3          # 0.8с (FadeOut) + 0.5с (финальная темнота)

TOTAL_DURATION = INTRO_DELAY + SIMULATION_TIME + OUTRO_TIME  # Ровно 18.8 с.
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# Мягкая гармоническая пентатоника
PENTATONIC_SCALE = np.array([
    130.81, 146.83, 164.81, 196.00, 220.00,  # C3, D3, E3, G3, A3
    261.63, 293.66, 329.63, 392.00, 440.00,  # C4, D4, E4, G4, A4
    523.25, 587.33, 659.25, 783.99, 880.00,  # C5, D5, E5, G5, A5
    1046.50, 1174.66, 1318.51, 1567.98       # C6, D6, E6, G6
])

# =============================================================
# 2. МАТРИЦА ЛИЦА КОНВЕЯ (270 x 480)
# =============================================================
GRID_W = 270
GRID_H = 480
grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)

img_path = SCRIPT_DIR / "conway.png"
FACE_SIZE = 180

if img_path.exists():
    raw_img = Image.open(img_path).convert("L").resize((FACE_SIZE, FACE_SIZE), Image.Resampling.LANCZOS)
    face_bin = (np.array(raw_img) > 105).astype(np.uint8)
    r_start = (GRID_H - FACE_SIZE) // 2
    c_start = (GRID_W - FACE_SIZE) // 2
    grid[r_start:r_start+FACE_SIZE, c_start:c_start+FACE_SIZE] = face_bin
else:
    # Резервная генерация
    grid[150:330, 45:225] = np.random.choice([0, 1], size=(180, 180), p=[0.75, 0.25]).astype(np.uint8)

kernel = np.array([
    [1, 1, 1],
    [1, 0, 1],
    [1, 1, 1]
], dtype=np.uint8)

def step_life_fast(g):
    neighbors = convolve2d(g, kernel, mode='same', boundary='fill', fillvalue=0)
    return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(np.uint8)

# =============================================================
# 3. СИНТЕЗ ГЛУБОКОГО АНАЛОГОВОГО ГУЛА
# =============================================================
print(f"Синтез аудиоподложки для {SCRIPT_NAME}...")

t_full = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False)

# Гул нарастает во время зума и мягко гаснет во тьме на 17.5–18.8 сек
drone_volume = np.zeros_like(t_full)

# Фаза 1: Тихий саспенс на портрете
mask_intro = t_full < INTRO_DELAY
drone_volume[mask_intro] = 0.25

# Фаза 2: Нарастание во время полета вглубь
mask_sim = (t_full >= INTRO_DELAY) & (t_full < (INTRO_DELAY + SIMULATION_TIME))
progress_sim = (t_full[mask_sim] - INTRO_DELAY) / SIMULATION_TIME
drone_volume[mask_sim] = 0.25 + 0.75 * (progress_sim ** 1.5)

# Фаза 3: Плавное растворение в тишину (провал в бездну)
mask_outro = t_full >= (INTRO_DELAY + SIMULATION_TIME)
progress_outro = (t_full[mask_outro] - (INTRO_DELAY + SIMULATION_TIME)) / OUTRO_TIME
drone_volume[mask_outro] = 1.0 * np.exp(-progress_outro * 3.5)

base_sub = np.sin(2 * np.pi * 50 * t_full) * 0.08
second_sub = np.sin(2 * np.pi * 100 * t_full) * 0.04
noise_bed = np.convolve(np.random.uniform(-0.04, 0.04, TOTAL_SAMPLES), np.ones(200)/200, mode='same')

master_drone = (base_sub + second_sub + noise_bed) * drone_volume
audio_data[:, 0] += master_drone
audio_data[:, 1] += master_drone

# =============================================================
# 4. СИНХРОННЫЕ КАПЛИ И НИТИ ЖИЗНИ (КВАДРАТИЧНЫЙ ТЕМП)
# =============================================================
STEPS = 80
current_grid = grid

for s in range(STEPS):
    next_grid = step_life_fast(current_grid)
    
    # КВАДРАТИЧНЫЙ ТАЙМИНГ: точно повторяет ease_in_quad из Manim
    norm_progress = np.sqrt(s / (STEPS - 1))
    t_start = INTRO_DELAY + (norm_progress * SIMULATION_TIME)
    start_sample = int(t_start * SAMPLE_RATE)

    # Фиксируем родившиеся клетки
    born = np.argwhere((next_grid == 1) & (current_grid == 0))
    survived = np.argwhere((next_grid == 1) & (current_grid == 1))
    
    # Объединяем активные точки
    if len(born) > 0:
        active_points = born
    else:
        active_points = survived

    num_active = len(active_points)

    if num_active > 0 and start_sample < TOTAL_SAMPLES:
        # Длина звучания микро-капли (140 мс)
        tone_dur = 0.14
        n_samples = int(SAMPLE_RATE * tone_dur)
        t = np.linspace(0, tone_dur, n_samples, endpoint=False)

        attack = np.minimum(t / 0.003, 1.0)
        decay = np.exp(-t * 26.0)
        env = attack * decay

        # Чтобы хор сотен клеток не перегружал дорожку
        vol = (0.22 / np.sqrt(min(num_active, 40))) * (0.6 + 0.4 * norm_progress)

        # Выбираем до 25 самых выразительных точек шага (убирает кашу)
        sample_size = min(len(active_points), 25)
        chosen_indices = np.random.choice(len(active_points), sample_size, replace=False)

        for idx in chosen_indices:
            r, c = active_points[idx]

            # Выбор гармонической ноты
            note_idx = (r * 5 + c * 3 + s) % len(PENTATONIC_SCALE)
            freq = PENTATONIC_SCALE[note_idx]

            # Органический синус + мягкий стеклянный обертон
            sine_main = np.sin(2 * np.pi * freq * t)
            sine_overtone = np.sin(2 * np.pi * (freq * 2) * t) * 0.2
            soft_hiss = np.random.uniform(-0.03, 0.03, n_samples)

            sound_drop = (sine_main + sine_overtone + soft_hiss) * env * vol

            # Стерео-панорама по координатам X
            pan_x = (c - GRID_W / 2) / (GRID_W / 2)
            l_gain = np.sqrt(0.5 * (1.0 - pan_x))
            r_gain = np.sqrt(0.5 * (1.0 + pan_x))

            end_sample = min(start_sample + n_samples, TOTAL_SAMPLES)
            actual_len = end_sample - start_sample

            if actual_len > 0:
                audio_data[start_sample:end_sample, 0] += sound_drop[:actual_len] * l_gain
                audio_data[start_sample:end_sample, 1] += sound_drop[:actual_len] * r_gain

    current_grid = next_grid

# Пиковая нормализация
peak = np.max(np.abs(audio_data))
if peak > 0:
    audio_data /= peak

# Сохранение файла
wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print(f"Готово! Синхронный файл сохранен в:\n{OUTPUT_FILE}")