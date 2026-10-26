import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44100
DURATION = 30.0  # Длина твоего видео в секундах
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION)

# Создаем пустой стерео-трек (2 канала)
audio_data = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

def add_crystal_click(timestamp_sec, height_z, pan_x):
    """
    Генерирует один щелчок растущего кристалла:
    height_z (0.0 - 1.0) -> частота звона
    pan_x (-1.0 - 1.0)  -> панорама лево/право
    """
    start_sample = int(timestamp_sec * SAMPLE_RATE)
    if start_sample >= TOTAL_SAMPLES:
        return
    
    # 1. Длина щелчка (очень короткий: 0.05 сек)
    click_len = int(SAMPLE_RATE * 0.05)
    t = np.linspace(0, 0.05, click_len, False)
    
    # 2. Частота (чем выше выросла структура, тем тоньше и выше звон)
    freq = 1200 + height_z * 2400  # от 1.2 кГц до 3.6 кГц (стекло/лед)
    
    # 3. Синтез: Синусоида + легкий шум трещины + экспоненциальное затухание
    sine_wave = np.sin(2 * np.pi * freq * t)
    crack_noise = np.random.uniform(-0.3, 0.3, click_len)
    envelope = np.exp(-t * 90)  # Резкое затухание (щелчок)
    
    sound = (sine_wave * 0.7 + crack_noise * 0.3) * envelope * 0.2
    
    # 4. Стерео панорамирование
    left_gain = np.sqrt(0.5 * (1 - pan_x))
    right_gain = np.sqrt(0.5 * (1 + pan_x))
    
    end_sample = min(start_sample + click_len, TOTAL_SAMPLES)
    actual_len = end_sample - start_sample
    
    audio_data[start_sample:end_sample, 0] += sound[:actual_len] * left_gain
    audio_data[start_sample:end_sample, 1] += sound[:actual_len] * right_gain

# --- СИМУЛЯЦИЯ РОСТА ---
# Здесь ты просто вызываешь функцию в цикле появления твоих клеток:
# Пример: 400 микро-кристаллов появляются за 30 секунд
np.random.seed(42)
for i in range(400):
    t_sec = (i / 400.0) * (DURATION - 1.0) + np.random.uniform(-0.02, 0.02)
    z_norm = (i / 400.0)  # Структура растет вверх
    x_pan = np.random.uniform(-0.8, 0.8) # Разлетается влево-вправо
    add_crystal_click(max(0, t_sec), z_norm, x_pan)

# Нормализация и сохранение в WAV
max_val = np.max(np.abs(audio_data))
if max_val > 0:
    audio_data /= max_val

wavfile.write("ice_growth_asmr.wav", SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
print("Файл ice_growth_asmr.wav успешно сгенерирован!")