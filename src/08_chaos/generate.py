import math
import time
import numpy as np
from PIL import Image

# =========================================================================
# КОНФИГУРАЦИЯ ПО ГОЛУБИЦКОМУ И ФИЛДУ (D_5 SYMMETRIC ICON)
# =========================================================================
# Параметры из книги "Symmetry in Chaos" (Икона со щитовой 5-лучевой симметрией):
N_DEGREE = 5          # 5-лучевая поворотная симметрия
LAMBDA   = -2.5       # Линейное притяжение/отталкивание
ALPHA    =  5.0       # Нелинейное ограничение масштаба
BETA     = -1.9       # Сила вращающей нелинейности
GAMMA    =  1.0       # Сила зеркального сопряжения
OMEGA    =  0.0       # 0.0 = чистая зеркальная симметрия D_n

ITERATIONS = 20_000_000  # 20 миллионов точек
WIDTH  = 1080
HEIGHT = 1920

OUTPUT_FILE = "symmetric_icon.png"

# =========================================================================
# ЯДРО РАСЧЕТА С УСКОРЕНИЕМ NUMBA (ЕСЛИ ДОСТУПНА)
# =========================================================================
def get_iteration_core():
    try:
        from numba import njit
        @njit(fastmath=True)
        def _core(iters, n, lam, alp, bet, gam, om, w, h, x_min, x_max, y_min, y_max):
            hist = np.zeros((h, w), dtype=np.uint32)
            z = complex(0.01, 0.01)
            
            # Прогрев (сброс первых 100 точек, пока траектория не села на аттрактор)
            for _ in range(100):
                r2 = z.real * z.real + z.imag * z.imag
                zn = z ** n
                p = lam + alp * r2 + bet * zn.real
                z = complex(p * z.real - om * z.imag, p * z.imag + om * z.real) + gam * (z.conjugate() ** (n - 1))

            scale_x = (w - 1) / (x_max - x_min)
            scale_y = (h - 1) / (y_max - y_min)

            for _ in range(iters):
                r2 = z.real * z.real + z.imag * z.imag
                zn = z ** n
                p = lam + alp * r2 + bet * zn.real
                
                # Формула Голубицкого:
                # z_{k+1} = (lambda + alpha*|z|^2 + beta*Re(z^n) + omega*i)*z + gamma*conj(z)^(n-1)
                term1 = complex(p * z.real - om * z.imag, p * z.imag + om * z.real)
                z = term1 + gam * (z.conjugate() ** (n - 1))

                # Проекция на пиксельную матрицу 1080x1920
                px = int((z.real - x_min) * scale_x)
                py = int((y_max - z.imag) * scale_y) # инвертируем Y для экрана

                if 0 <= px < w and 0 <= py < h:
                    hist[py, px] += 1

            return hist
        return _core, True
    except ImportError:
        def _fallback(iters, n, lam, alp, bet, gam, om, w, h, x_min, x_max, y_min, y_max):
            print("[WARN] Numba не найдена. Ограничиваем до 2 млн точек для быстрого теста...")
            iters = min(iters, 2_000_000)
            hist = np.zeros((h, w), dtype=np.uint32)
            z = complex(0.01, 0.01)
            scale_x = (w - 1) / (x_max - x_min)
            scale_y = (h - 1) / (y_max - y_min)

            for _ in range(iters):
                r2 = z.real * z.real + z.imag * z.imag
                zn = z ** n
                p = lam + alp * r2 + bet * zn.real
                z = complex(p * z.real - om * z.imag, p * z.imag + om * z.real) + gam * (z.conjugate() ** (n - 1))

                px = int((z.real - x_min) * scale_x)
                py = int((y_max - z.imag) * scale_y)
                if 0 <= px < w and 0 <= py < h:
                    hist[py, px] += 1
            return hist
        return _fallback, False

# =========================================================================
# ГРАДИЕНТ CATPPUCCIN (ПАЛИТРА ТВОЕГО КАНАЛА)
# =========================================================================
def apply_colormap(density_norm):
    """
    Преобразует нормализованную плотность [0, 1] в неоновый градиент:
    Фон #08080C -> Темно-синий #1E1E2E -> Пурпур #CBA6F7 -> Неоновый циан #89DCEB -> Белое ядро #FFFFFF
    """
    h, w = density_norm.shape
    img_rgb = np.zeros((h, w, 3), dtype=np.uint8)

    # Цветовые точки (Hex в RGB)
    c0 = np.array([8, 8, 12])      # #08080C (Фон)
    c1 = np.array([30, 30, 46])    # #1E1E2E (Темный бейс)
    c2 = np.array([137, 180, 250]) # #89B4FA (Синий сапфир)
    c3 = np.array([137, 220, 235]) # #89DCEB (Циан Manim)
    c4 = np.array([255, 255, 255]) # Раскаленный белый центр

    v = density_norm
    
    # 4-сегментная интерполяция
    m1 = (v < 0.25)
    m2 = (v >= 0.25) & (v < 0.55)
    m3 = (v >= 0.55) & (v < 0.85)
    m4 = (v >= 0.85)

    def interp(mask, a, b, v_min, v_max):
        t = (v[mask] - v_min) / (v_max - v_min)
        for ch in range(3):
            img_rgb[mask, ch] = (a[ch] + t * (b[ch] - a[ch])).astype(np.uint8)

    interp(m1, c0, c1, 0.00, 0.25)
    interp(m2, c1, c2, 0.25, 0.55)
    interp(m3, c2, c3, 0.55, 0.85)
    interp(m4, c3, c4, 0.85, 1.00)

    return img_rgb

# =========================================================================
# ОСНОВНОЙ ПАЙПЛАЙН
# =========================================================================
def main():
    print(f"[1/3] Инициализация ядра Голубицкого (Симметрия n={N_DEGREE})...")
    core, has_numba = get_iteration_core()

    # Границы комплексной плоскости под вертикальный формат 9:16
    BOUND_X = 1.25
    BOUND_Y = BOUND_X * (HEIGHT / WIDTH)  # Сохраняем квадратный масштаб пикселя
    x_min, x_max = -BOUND_X, BOUND_X
    y_min, y_max = -BOUND_Y, BOUND_Y

    print(f"[2/3] Расчет {ITERATIONS:,} итераций...")
    t0 = time.time()
    hist = core(ITERATIONS, N_DEGREE, LAMBDA, ALPHA, BETA, GAMMA, OMEGA, 
                WIDTH, HEIGHT, x_min, x_max, y_min, y_max)
    t_calc = time.time() - t0
    print(f"      Готово за {t_calc:.3f} сек. (Ускорение: {'Numba JIT' if has_numba else 'Чистый Python'})")

    print("[3/3] Логарифмическая компрессия и наложение палитры Catppuccin...")
    # Логарифмический масштаб: I = log(1 + H) / log(1 + H_max)
    hist_float = hist.astype(np.float32)
    max_val = np.max(hist_float)
    if max_val > 0:
        density = np.log1p(hist_float) / np.log1p(max_val)
    else:
        density = hist_float

    rgb_array = apply_colormap(density)

    img = Image.fromarray(rgb_array)
    img.save(OUTPUT_FILE, format="PNG")
    print(f"[УСПЕХ] Файл сохранен: {OUTPUT_FILE} (Разрешение: {WIDTH}x{HEIGHT})")

if __name__ == "__main__":
    main()