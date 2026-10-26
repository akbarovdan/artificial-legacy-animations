#!/usr/bin/env python3
import os
import math
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import random

# =============================================================
# 0. СТРОГИЕ ПУТИ (ЗАПРЕЩЕНО МЕНЯТЬ) - Замещает один и тот же файл
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem               # "attractor_sound"
PROJECT_ROOT = SCRIPT_PATH.parents[2]        # Корень проекта 
OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"  # Всегда записываем сюда же

SAMPLE_RATE = 44100

# =============================================================
# 1. 100% СИНХРОНИЗАЦИЯ С КОДОМ ФИЛЬДА-ГОЛУБИЦКОГО 
# Точная копия блока параметров "TIMING" из видеоскрипта 
# =============================================================
TIMING = dict(
    hook_leg=2.2, hook_hold=0.3,       
    lin_step=0.38, lin_hold=0.5,        
    nl_line_slow=0.7, nl_line_fast=4.0, nl_line_out=0.7,     
    br_blend=0.7, br_spin=1.4, br_shrink=1.1, br_grow=1.0, br_zoom=1.7,         
    nl_expand_slow=0.7, nl_expand_fast=0.35, nl_build=3.0,        
    blend=0.4, rewind=2.5, zones=0.8, sectors=6.0, sectors_end=1.0, expand=1.3,          
    twist=4.5, twist_hold=0.4, twist_blend=0.5, twist_warm=0.7,
    morph_leg=2.2, morph_hold=0.25, fade=0.35
)
LINEAR = [(None, 0.82, None, 16, None, None),
          (None, 1.30, None, 8, None, None),
          (None, 1.00, None, 15, None, None)] # Только кол-во шагов и параметры нужны звуку
HOOK_PATH_LEN = 6 
MORPH_PATH_LEN = 7
FIG_SEGS = [("icon", 3.2, 0.35), ("ifs", 3.0, 0.35), ("ifs", 3.4, 2.2)]

# Расчет истинного общего времени (из Вашего же кода `scene_seconds()`)
dur_hook = sum((TIMING["hook_leg"] if i > 0 else 1.6) + TIMING["hook_hold"] for i in range(1, HOOK_PATH_LEN))
dur_linear = sum((s[3] * TIMING["lin_step"] + TIMING["lin_hold"]) for s in LINEAR) + \
             TIMING["br_blend"] + TIMING["br_spin"] + TIMING["br_shrink"] + TIMING["br_grow"] + TIMING["br_zoom"]
dur_nonlinear = (6 * TIMING["nl_line_slow"] + TIMING["nl_line_fast"] + TIMING["nl_line_out"] + \
                 6 * TIMING["nl_expand_slow"] + (9 - 6) * TIMING["nl_expand_fast"] + TIMING["nl_build"])
dur_sectors = TIMING["blend"] + TIMING["rewind"] + TIMING["zones"] + TIMING["sectors"] + TIMING["sectors_end"] + TIMING["expand"]
dur_twist = TIMING["twist"] + TIMING["twist_hold"]
dur_morph = (MORPH_PATH_LEN - 1) * (TIMING["morph_leg"] + TIMING["morph_hold"])
dur_figs = sum((f[1] + f[2]) for f in FIG_SEGS)

TOTAL_DURATION = dur_hook + dur_linear + dur_nonlinear + dur_sectors + dur_twist + dur_morph + dur_figs
TAIL = 5.0 # Красивое эхо-убаюкивание в конце

TOTAL_SAMPLES = int((TOTAL_DURATION + TAIL) * SAMPLE_RATE)
audio = np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32)

print(f"\n🎧 Сборка идеального 16-бит Numpy Ambient...\nДлина видео {TOTAL_DURATION:.2f} сек. Аудио {TOTAL_DURATION + TAIL:.2f} сек.")

# =============================================================
# 2. МЯГКОСТЬ - Numpy Синтезаторы Космического сна
# =============================================================
def midi_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

PENTA = [midi_freq(m) for m in [48, 55, 60, 64, 67, 72, 76, 79, 84, 88]]

def draw_sound(start, sound_arr):
    s_idx = int(start * SAMPLE_RATE)
    length = min(len(sound_arr), TOTAL_SAMPLES - s_idx)
    if length > 0:
        audio[s_idx : s_idx + length] += sound_arr[:length]

def m_sine(freq, t_arr, pan=0.0):
    s = np.sin(2 * np.pi * freq * t_arr)
    # Лёгкая фазовая деформация, чтобы не звучало сухо-лабораторно
    s += 0.15 * np.sin(2 * np.pi * freq * 2.02 * t_arr) 
    l = np.sqrt(0.5 * (1.0 - pan)) * s
    r = np.sqrt(0.5 * (1.0 + pan)) * s
    return np.column_stack((l, r))

def soft_pad(freqs, dur, attack, release, vel=0.5):
    """Медленно вдыхающий космо-пэд, обволакивает сцену целиком"""
    N = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, N, endpoint=False)
    # Плавные Fade-кривые без щелчков!
    att_i, rel_i = min(N, int(attack*SAMPLE_RATE)), min(N, int(release*SAMPLE_RATE))
    env = np.ones(N, dtype=np.float32)
    if att_i > 0: env[:att_i] = np.linspace(0, 1, att_i)**2
    if rel_i > 0: env[-rel_i:] = np.linspace(1, 0, rel_i)**2
    
    pad = np.zeros((N, 2), dtype=np.float32)
    for f in freqs:
        # Два сдвинутых осциллятора - огромный, глубокий хорус в наушниках
        pad += m_sine(f * 0.995, t, -0.6) * 0.5 
        pad += m_sine(f * 1.005, t, 0.6) * 0.5
    return pad * env[:, np.newaxis] * vel

def crystal_spark(freq, vel=0.35, pan=0.0):
    """Капсульная звонкая искра - озвучивание отдельных математических точек/зубьев"""
    dur = 1.2
    N = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, N, endpoint=False)
    env = np.exp(-t * 6.5) # резкая, но мягкая перкуссия-колокол 
    sig = m_sine(freq, t, pan)
    return sig * env[:, np.newaxis] * vel

# =============================================================
# 3. ТОЧНОЕ ВОСПРОИЗВЕДЕНИЕ СЦЕНАРНЫХ ВРЕМЕН (Без единой паузы)
# =============================================================
random.seed(42)
t_cur = 0.0 

# SCENE 1. HOOK - Начальные фракталы плывут в неоне. Глубокий распускающийся звук
draw_sound(t_cur, soft_pad([PENTA[0], PENTA[2], PENTA[3]], dur_hook+0.2, attack=1.0, release=1.0, vel=0.6))
for _ in range(int(dur_hook)):
    draw_sound(t_cur + random.uniform(0, 1.5), crystal_spark(random.choice(PENTA[4:7]), pan=random.uniform(-0.8, 0.8), vel=0.25))
t_cur += dur_hook

# SCENE 2. LINEAR - Тона следуют прямо за длиной линии/кадра
# Стягивание -> Полёт -> Сфера (z->c*z)
draw_sound(t_cur, soft_pad([PENTA[0], PENTA[1], PENTA[4]], dur_linear+0.3, 0.5, 3.0, vel=0.4))
for _, c_mod, _, steps, _, _ in LINEAR:
    for s in range(steps): # Линия летит по таймингу
        if c_mod < 1.0: base_p = 50 + (steps-s)
        elif c_mod > 1.0: base_p = 50 + s*3
        else: base_p = 60 # круговорот зациклен
        pan_st = -0.5 if (s%2==0) else 0.5
        draw_sound(t_cur + (s * TIMING["lin_step"]), crystal_spark(midi_freq(base_p), pan=pan_st))
    t_cur += (steps * TIMING["lin_step"]) + TIMING["lin_hold"]
t_cur += (TIMING["br_blend"] + TIMING["br_spin"] + TIMING["br_shrink"] + TIMING["br_grow"] + TIMING["br_zoom"])

# SCENE 3. NON-LINEAR - Модуляция растяжения пространства
draw_sound(t_cur, soft_pad([midi_freq(50), midi_freq(57)], dur_nonlinear+0.2, attack=3.0, release=3.0, vel=0.5))
p1 = 6 * TIMING["nl_line_slow"] + TIMING["nl_line_fast"] + TIMING["nl_line_out"]
for x in range(30):
    time_spark = t_cur + (p1 / 30) * x
    draw_sound(time_spark, crystal_spark(random.choice(PENTA[5:]), vel=x*0.01))
t_cur += dur_nonlinear

# SCENE 4. SECTORS - (Хаос с ограничением). Арпеджио плотностью до максимума
draw_sound(t_cur, soft_pad([midi_freq(52), midi_freq(55), midi_freq(62)], dur_sectors, 2.0, 3.0, vel=0.45))
accel_start = t_cur + TIMING["blend"] + TIMING["rewind"] + TIMING["zones"]
for point in range(65):
    p_curv = accel_start + (point/65)**1.5 * TIMING["sectors"] # сжимается по экспоненте (множатся точки)
    f = random.choice(PENTA[4:9])
    # Удары тише, так как точек миллион
    draw_sound(p_curv, crystal_spark(f, vel=0.15 * (1.0 - point/100))) 
t_cur += dur_sectors

# SCENE 5. TWIST - Наблюдение Вращения "breaking of mirror symmetry" (Плавная сдвижка Стерео фазы)
twist_time = t_cur
dur_t = dur_twist + 0.1
draw_sound(t_cur, soft_pad([midi_freq(45), midi_freq(62)], dur_t, 0.8, 1.0, vel=0.6))
N_spin = int(dur_t * SAMPLE_RATE)
t_arr = np.linspace(0, dur_t, N_spin, endpoint=False)
rot_lfo = np.sin(2 * np.pi * 0.8 * t_arr) # Скорость вращения 0.8 герца из уха в ухо
twist_core = m_sine(midi_freq(64), t_arr, 0.0)
twist_core[:, 0] = twist_core[:, 0] * (1.0 - rot_lfo) # панорамное утягивание 
twist_core[:, 1] = twist_core[:, 1] * (1.0 + rot_lfo)
twist_env = np.ones(N_spin) * np.exp(-t_arr * 0.1) # Длинный плавный сустейн
draw_sound(t_cur, twist_core * twist_env[:, np.newaxis] * 0.5)
t_cur += dur_twist

# SCENE 6 & 7: MORPH + FIGURES - Гигантский Корал на 3 аккордах в конце в Тишину 
finale_dur = dur_morph + dur_figs
draw_sound(t_cur, soft_pad([PENTA[0], PENTA[3], PENTA[4]], finale_dur+1.0, attack=4.0, release=6.0, vel=0.55))

final_pulse_T = TIMING["morph_leg"] + TIMING["morph_hold"]
for p in range(MORPH_PATH_LEN - 1): # Точное количество финальных морганий Morph фигур!
    f = PENTA[2 + (p%3)]
    draw_sound(t_cur + p * final_pulse_T, soft_pad([f], final_pulse_T*1.8, 1.0, 3.0, vel=0.35))
t_cur += dur_morph
for (name, fd, ft) in FIG_SEGS:
    f = PENTA[5]
    draw_sound(t_cur, soft_pad([f], (fd+ft), 0.5, (fd+ft)*0.8, vel=0.3))
    t_cur += (fd+ft)

# =============================================================
# 4. ФИНАЛЬНАЯ КОСМИЧЕСКАЯ ОБРАБОТКА МАССИВА И ВЫХОД
# =============================================================

# Мягчайший Delay 370ms (~протяжный космос)
echo = int(0.37 * SAMPLE_RATE) 
if echo < len(audio):
    audio[echo:, 0] += audio[:-echo, 1] * 0.35  # Уносится влево
    audio[echo:, 1] += audio[:-echo, 0] * 0.35  # Уносится вправо 

# 5 секунд абсолютно ровного фейд-аута в черный холст в конце хвоста
N_tail = int(TAIL * SAMPLE_RATE)
env_fade = (np.linspace(1.0, 0.0, N_tail) ** 1.8)[:, np.newaxis] 
audio[-N_tail:, :] *= env_fade 

# Нормализуем по Громкости (Нежный транзиент без жесткой обрезки)
max_amp = np.max(np.abs(audio))
if max_amp > 0:
    audio = audio / max_amp * 0.88 # 0.88 (-1dBFS) Мягчайший не клиппующий запас для YouTube

# Сохраняем поверх того самого одного файла! Никаких танцев с библиотеками.
wavfile.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))

print(f"✅ Вся обработка идеальна и математична. Numpy закончил генерацию!")
print(f"📁 Файл перезаписан здесь:  =>  {OUTPUT_FILE}")