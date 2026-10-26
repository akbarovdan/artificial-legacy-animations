from pathlib import Path
import numpy as np
from scipy.io import wavfile

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
TOTAL_DURATION = 23.5  
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

# =============================================================
# 1. 100% ЧИСТАЯ, ПРОЗРАЧНАЯ МАТЕМАТИКА (БЕЗ ДИСТОРШНА)
# =============================================================
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def synth_pure_pad(chord_freqs, duration=3.0, vel=0.6):
    """
    Чистейший космический эмбиент-пэд. Никаких биений, никаких шумов.
    Огибающая (FadeIn): звук выплывает из тишины предельно мягко.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    
    # Сверхокруглая, медленная огибающая для старта
    env = np.ones(n)
    attack_time = min(0.6 * duration, 1.2)
    att_samples = int(attack_time * SAMPLE_RATE)
    
    if att_samples > 0:
        env[:att_samples] = 0.5 * (1.0 - np.cos(np.pi * np.linspace(0, 1, att_samples)))
    env[att_samples:] = np.exp(-t[att_samples:] * 0.4) # Медленный угасающий хвост
    
    left = np.zeros(n)
    right = np.zeros(n)
    
    amp_scaler = 1.0 / (len(chord_freqs) + 1.0)
    for i, f in enumerate(chord_freqs):
        pan = (i / (len(chord_freqs) - 1 + 1e-5)) * 0.8 - 0.4
        
        # ТОЛЬКО идеальные синусоиды (0 искажений)
        sig = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(2 * np.pi * (f * 2) * t)
        
        left += sig * amp_scaler * np.sqrt(0.5 * (1.0 - pan))
        right += sig * amp_scaler * np.sqrt(0.5 * (1.0 + pan))
        
    return np.column_stack((left, right)) * env[:, np.newaxis] * vel

def synth_pure_swell(chord_freqs, duration=1.0, vel=0.8):
    """
    ПЕРЕКАТ ("СВЭЛЛ"): Звучит ровно синхронно с движением фигуры (Transform).
    Не удар, не клик! Это мягкое "дыхание" громкости, растущее к центру 
    тайминга и спадающее к концу анимации.
    """
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    
    # "Форма капли" или "Купол" (Hann Window). 
    # Старт громкости ровно из нуля, пик посередине, угасание в ноль.
    env = 0.5 * (1.0 - np.cos(2 * np.pi * t / duration))
    # Сглаживаем её (делаем еще мягче и более сдержанной по бокам)
    env = env ** 1.5 
    
    left = np.zeros(n)
    right = np.zeros(n)
    amp_scaler = 1.0 / len(chord_freqs)
    
    for i, f in enumerate(chord_freqs):
        pan = (i / (len(chord_freqs) - 1 + 1e-5)) * 0.8 - 0.4
        sig = np.sin(2 * np.pi * f * t) + 0.1 * np.sin(2 * np.pi * (f * 2) * t)
        
        left += sig * amp_scaler * np.sqrt(0.5 * (1.0 - pan))
        right += sig * amp_scaler * np.sqrt(0.5 * (1.0 + pan))
        
    return np.column_stack((left, right)) * env[:, np.newaxis] * vel

def synth_crystal_drop(freq, duration=0.3, vel=0.5, pan=0.0):
    """Капля воды/стекла. Звук чистой прозрачной частоты, остывающей мгновенно"""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    
    env = np.exp(-t * 16.0) # Затухает быстро и мягко
    sig = np.sin(2 * np.pi * freq * t) * env * vel
    
    pan = np.clip(pan, -1.0, 1.0)
    l = sig * np.sqrt(0.5 * (1.0 - pan))
    r = sig * np.sqrt(0.5 * (1.0 + pan))
    return np.column_stack((l, r))

def synth_fade_away(chord_freqs, duration=1.5, vel=0.6):
    """Растворение во тьме без ужасающего рычания саб-баса"""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    
    # Экспоненциальный спад
    env = np.exp(-t * 3.5)
    
    left = np.zeros(n)
    right = np.zeros(n)
    amp_scaler = 1.0 / len(chord_freqs)
    
    for f in chord_freqs:
        # Уходит всего на 1/3 октавы вниз мягко (глиссандо), 
        # частоты остаются высокими и красивыми.
        f_slide = f * (1.0 - 0.3 * (t / duration)) 
        phase = 2 * np.pi * np.cumsum(f_slide) / SAMPLE_RATE
        
        sig = np.sin(phase) * amp_scaler
        left += sig * 0.5
        right += sig * 0.5
        
    return np.column_stack((left, right)) * env[:, np.newaxis] * vel

def add_audio(start_time, sound_data):
    s_idx = int(start_time * SAMPLE_RATE)
    e_idx = min(s_idx + len(sound_data), TOTAL_SAMPLES)
    length = e_idx - s_idx
    if length > 0:
        audio[s_idx:e_idx] += sound_data[:length]

print(f"Синтез хрустального, идеально чистого звука без 'рычаний' для {SCRIPT_NAME}...")

# =============================================================
# 2. ЭТАП 1.1: ПОЯВЛЕНИЕ КВАДРАТА (0.0 — 3.8 сек)
# =============================================================
# Завышенная частота, чтобы бас не напрягал уши (Начинаем от F4 = 349 Гц, без гула в груди)
chord_intro = [midi_to_freq(m) for m in [65, 69, 72, 77]] # Fmaj9
add_audio(0.0, synth_pure_pad(chord_intro, duration=3.2, vel=0.7))

# =============================================================
# 3. ЭТАП 1.2: ЧЕРЕПАШЬЯ ЛИНИЯ СО СТРЕЛКАМИ (3.8 — 6.48 сек)
# =============================================================
t = 3.8 
rule_str = "F-F+F+FF-F-F+F"
tut_pitches = [72, 74, 76, 77, 79, 81, 83, 84]
p_idx = 0

for char in rule_str:
    if char == 'F':
        f = midi_to_freq(tut_pitches[p_idx % len(tut_pitches)])
        pan = (p_idx % 3 - 1) * 0.3
        add_audio(t, synth_crystal_drop(f, duration=0.3, vel=0.6, pan=pan))
        p_idx += 1
        t += 0.12
    else:
        # Микроскопическая роса при повороте угла (супер прозрачная нота)
        add_audio(t, synth_crystal_drop(midi_to_freq(90), duration=0.08, vel=0.15, pan=0.0))
        t += 0.07

# =============================================================
# 4. ЭТАП 1.3: СИНХРОННЫЕ ВДОХИ/ВЫДОХИ ЗЕЛЕНОГО КОХА
# =============================================================
t = 7.38
# Прям чистые мажорные тона
chord_koch = [midi_to_freq(m) for m in [65, 69, 72, 76, 81]] # Fmaj9

# Мягкий вдох фрактала
add_audio(t, synth_pure_swell(chord_koch, duration=1.4, vel=0.85))

t = 8.58  # 7.38 + 1.0 + 0.2
add_audio(t, synth_pure_swell(chord_koch, duration=1.4, vel=0.9))

t = 9.58  # 8.58 + 1.0
add_audio(t, synth_pure_swell(chord_koch, duration=1.6, vel=0.95))

# ПРОЛЕТ: Мягкое чистое растворение без низкочастотного ветра (FadeAway)
t = 11.08  
add_audio(t, synth_fade_away(chord_koch, duration=2.5, vel=0.8))

# =============================================================
# 5. ФАЗА 2: ЖЕЛТЫЙ КРЕСТ (Смена гармонии на светлый С)
# =============================================================
t = 12.38
chord_yellow = [midi_to_freq(m) for m in [67, 71, 74, 76, 79]] # Cmaj9 (G4 старт - безопасно)

add_audio(t, synth_pure_swell(chord_yellow, duration=1.3, vel=0.85))

t = 13.48 
add_audio(t, synth_pure_swell(chord_yellow, duration=1.3, vel=0.9))

t = 14.38
add_audio(t, synth_pure_swell(chord_yellow, duration=1.5, vel=0.95))

t = 15.78 
add_audio(t, synth_fade_away(chord_yellow, duration=2.5, vel=0.8))

# =============================================================
# 6. ФАЗА 3: СИНИЙ ЛАБИРИНТ (Финал в Ля-Минор, но высоком)
# =============================================================
t = 18.18
# Нет никаких C3, D3. Стартуем сразу с E4 (Выше экватора)
chord_blue = [midi_to_freq(m) for m in [69, 72, 76, 79, 81, 84]] # Am9

add_audio(t, synth_pure_swell(chord_blue, duration=1.3, vel=0.85))

t = 19.08
add_audio(t, synth_pure_swell(chord_blue, duration=2.0, vel=0.9))

t = 20.58
# Последний глубокий вздох и исчезновение (Fade away into darkness)
add_audio(t, synth_fade_away(chord_blue, duration=3.0, vel=0.85))

# =============================================================
# 7. ЭКСТРЕМАЛЬНО АККУРАТНЫЙ МАСТЕРИНГ 
# =============================================================
# Легчайшее отражающее пространство (Эхо) - чище воды
delay_time = int(0.24 * SAMPLE_RATE)
audio[delay_time:, 0] += audio[:-delay_time, 1] * 0.15
audio[delay_time:, 1] += audio[:-delay_time, 0] * 0.15

# Самое главное: никаких экстремальных перегибов громкости
peak = np.max(np.abs(audio))
if peak > 0:
    # 0.8 гарантирует, что сигнал абсолютно точно не убьется при сжатии в видео
    audio = (audio / peak) * 0.8 

wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))
print(f"Готово! Вакуумная тишина и чистейшие хрустальные звуки:\n{OUTPUT_FILE}")