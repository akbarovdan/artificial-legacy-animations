import numpy as np
from scipy.io import wavfile

# --- НАСТРОЙКИ СИНХРОНИЗАЦИИ С MANIM ---
SAMPLE_RATE = 44100
STEPS = 150            # Количество шагов в Manim
STEP_DURATION = 0.18   # run_time одного шага в Manim
TAIL_WAIT = 3.0        # self.wait(3) в конце сцены

TOTAL_DURATION = (STEPS * STEP_DURATION) + TAIL_WAIT
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# --- 1. ГАРМОНИЧЕСКАЯ ПАЛИТРА (Пентатоника - мягкие органические ноты) ---
# Частоты в Гц (от теплых низких до прозрачных высоких)
PENTATONIC_SCALE = np.array([
    130.81, 146.83, 164.81, 196.00, 220.00,  # C3, D3, E3, G3, A3
    261.63, 293.66, 329.63, 392.00, 440.00,  # C4, D4, E4, G4, A4
    523.25, 587.33, 659.25, 783.99, 880.00,  # C5, D5, E5, G5, A5
    1046.50, 1174.66, 1318.51, 1567.98       # C6, D6, E6, G6
])

# --- 2. ВОССОЗДАЕМ МАТРИЦУ ЖИЗНИ ИЗ СЦЕНЫ MANIM ---
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

# --- 3. СИНТЕЗ ОРГАНИЧЕСКИХ НИТЕЙ И КАПЕЛЬ ---
print("Синтез аудио с точной синхронизацией Manim...")

# Акустический фоновый гул (растущее основание)
t_full = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False)
base_hum = np.sin(2 * np.pi * 55 * t_full) * 0.08  # Глубокий 55 Гц гул (A1)
sub_drone = np.sin(2 * np.pi * 110 * t_full) * 0.05
master_drone = (base_hum + sub_drone) * (0.2 + 0.8 * (t_full / TOTAL_DURATION) ** 1.2)

audio_data[:, 0] += master_drone
audio_data[:, 1] += master_drone

# Генерация отклика для каждого шага s
for s in range(STEPS):
    next_grid = step_life(grid)
    t_start = s * STEP_DURATION
    start_sample = int(t_start * SAMPLE_RATE)
    
    alive_now = np.argwhere(next_grid == 1)
    num_alive = len(alive_now)
    
    if num_alive > 0 and start_sample < TOTAL_SAMPLES:
        # Длина звучания одного шага (чуть перекрывает следующий шаг для мягкости)
        tone_dur = 0.22  
        n_samples = int(SAMPLE_RATE * tone_dur)
        t = np.linspace(0, tone_dur, n_samples, endpoint=False)
        
        # Мягкая огибающая: быстрая атака (5мс) и плавный затухающий хвост
        attack = np.minimum(t / 0.005, 1.0)
        decay = np.exp(-t * 18.0)
        env = attack * decay
        
        # Автоматическая балансировка громкости, чтобы хор клеток не перегружал динамик
        cell_vol = (0.25 / np.sqrt(num_alive)) * (0.5 + 0.5 * (s / STEPS))
        
        for r, c in alive_now:
            # Выбираем ноту из пентатоники по координатам клетки
            note_idx = (r * 3 + c * 2 + s) % len(PENTATONIC_SCALE)
            freq = PENTATONIC_SCALE[note_idx]
            
            # Гармонический синтез: основная нота + мягкая обертоновая колокольная гармоника
            sine_base = np.sin(2 * np.pi * freq * t)
            sine_harmonic = np.sin(2 * np.pi * (freq * 2) * t) * 0.25
            soft_noise = np.random.uniform(-0.05, 0.05, n_samples)  # Совсем каплю теплого шума
            
            note_sound = (sine_base + sine_harmonic + soft_noise) * env * cell_vol
            
            # Панорама X по колонкам (от -1.0 слева до +1.0 справа)
            pan_x = (c - cols / 2 + 0.5) / (cols / 2)
            l_gain = np.sqrt(0.5 * (1.0 - pan_x))
            r_gain = np.sqrt(0.5 * (1.0 + pan_x))
            
            end_sample = min(start_sample + n_samples, TOTAL_SAMPLES)
            length = end_sample - start_sample
            
            if length > 0:
                audio_data[start_sample:end_sample, 0] += note_sound[:length] * l_gain
                audio_data[start_sample:end_sample, 1] += note_sound[:length] * r_gain
    
    grid = next_grid

# Пиковая нормализация
peak = np.max(np.abs(audio_data))
if peak > 0:
    audio_data /= peak

output_file = "spacetime_life_synced.wav"
wavfile.write(output_file, SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print(f"Готово! Создан синхронный аудиофайл: {output_file}")