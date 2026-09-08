import numpy as np
from scipy.io import wavfile

# --- НАСТРОЙКИ СИНХРОНИЗАЦИИ С MANIM ---
SAMPLE_RATE = 44100
STEPS = 140            # <--- ОБНОВЛЕНО ДО 140 ШАГОВ!
STEP_DURATION = 0.18   # run_time одного шага в Manim
TAIL_WAIT = 3.0        # self.wait(3) в конце сцены

TOTAL_DURATION = (STEPS * STEP_DURATION) + TAIL_WAIT # ~28.2 секунды
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# --- 1. МЯГКИЕ ЛЕДЯНЫЕ НОТЫ (Основа для резонанса) ---
PENTATONIC_SCALE = np.array([
    146.83, 164.81, 196.00, 220.00, 261.63,
    293.66, 329.63, 392.00, 440.00, 523.25,
    587.33, 659.25, 783.99, 880.00, 1046.50
])

# --- 2. МАТРИЦА ЖИЗНИ ИЗ MANIM ---
rows, cols = 18, 18
grid = np.zeros((rows, cols), dtype=int)

glider = [(2, 2), (3, 3), (4, 1), (4, 2), (4, 3)]
for r, c in glider: grid[r, c] = 1

blinker = [(12, 4), (12, 5), (12, 6)]
for r, c in blinker: grid[r, c] = 1

block = [(11, 12), (11, 13), (12, 12), (12, 13)]
for r, c in block: grid[r, c] = 1

r_pent = [(8, 8), (8, 9), (9, 7), (9, 8), (10, 8)]
for r, c in r_pent: grid[r, c] = 1

def step_life(g):
    neighbors = sum(
        np.roll(np.roll(g, i, 0), j, 1)
        for i in (-1, 0, 1)
        for j in (-1, 0, 1)
        if not (i == 0 and j == 0)
    )
    return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(int)

# --- 3. ФОНОВЫЙ ГУЛ ЛЕДНИКА С ПЛАВНЫМ FADE-OUT В КОНЦЕ ---
t_full = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False)

# Огибающая громкости гула: растет во время шагов, плавно гаснет во время wait(3)
active_time = STEPS * STEP_DURATION
env_drone = np.ones_like(t_full)
# Растущая часть
mask_grow = t_full <= active_time
env_drone[mask_grow] = 0.2 + 0.8 * (t_full[mask_grow] / active_time) ** 1.3
# Затухающая часть в конце (wait)
mask_fade = t_full > active_time
env_drone[mask_fade] = 1.0 * np.exp(-(t_full[mask_fade] - active_time) * 1.5)

base_hum = np.sin(2 * np.pi * 50 * t_full) * 0.07
sub_drone = np.sin(2 * np.pi * 100 * t_full) * 0.04
master_drone = (base_hum + sub_drone) * env_drone

audio_data[:, 0] += master_drone
audio_data[:, 1] += master_drone

# --- 4. СИНТЕЗ МЯГКОГО ЛЕДЯНОГО ХРУСТА (SOFT ICE CRUNCH) ---
print(f"Синтез мягкого хруста льда на {STEPS} шагов ({TOTAL_DURATION:.1f} сек)...")

for s in range(STEPS):
    next_grid = step_life(grid)
    t_start = s * STEP_DURATION
    start_sample = int(t_start * SAMPLE_RATE)
    
    alive_now = np.argwhere(next_grid == 1)
    num_alive = len(alive_now)
    
    if num_alive > 0 and start_sample < TOTAL_SAMPLES:
        # Длина хруста (120 мс - острая атака)
        snap_dur = 0.12
        n_samples = int(SAMPLE_RATE * snap_dur)
        t = np.linspace(0, snap_dur, n_samples, endpoint=False)
        
        # Мягкая огибающая: быстрый щелчок и экспоненциальный спад
        attack = np.minimum(t / 0.002, 1.0)
        decay = np.exp(-t * 45.0)  # Резкий хруст
        env = attack * decay
        
        # Баланс громкости от количества клеток
        cell_vol = (0.28 / np.sqrt(num_alive)) * (0.6 + 0.4 * (s / STEPS))
        
        for r, c in alive_now:
            note_idx = (r * 3 + c * 2 + s) % len(PENTATONIC_SCALE)
            freq = PENTATONIC_SCALE[note_idx]
            
            # Акустика льда: мягкий шум + тонкий стеклянный резонанс
            raw_noise = np.random.uniform(-0.8, 0.8, n_samples)
            # Сглаживание шума (убираем лишний песок)
            soft_noise = np.convolve(raw_noise, np.ones(3)/3, mode='same')
            
            sine_tone = np.sin(2 * np.pi * freq * t) * 0.3
            
            # Микс: 65% сухой лед + 35% резонанс
            snap_sound = (soft_noise * 0.65 + sine_tone * 0.35) * env * cell_vol
            
            # Панорама X
            pan_x = (c - cols / 2 + 0.5) / (cols / 2)
            l_gain = np.sqrt(0.5 * (1.0 - pan_x))
            r_gain = np.sqrt(0.5 * (1.0 + pan_x))
            
            end_sample = min(start_sample + n_samples, TOTAL_SAMPLES)
            length = end_sample - start_sample
            
            if length > 0:
                audio_data[start_sample:end_sample, 0] += snap_sound[:length] * l_gain
                audio_data[start_sample:end_sample, 1] += snap_sound[:length] * r_gain
    
    grid = next_grid

# Нормализация
peak = np.max(np.abs(audio_data))
if peak > 0:
    audio_data /= peak

output_file = "spacetime_life_synced_v2.wav"
wavfile.write(output_file, SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print(f"Готово! Создан файл: {output_file}")