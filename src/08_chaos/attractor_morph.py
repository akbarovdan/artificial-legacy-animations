import numpy as np
import time
import imageio
try:
    from numba import njit
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

# =========================================================================
# КОНФИГУРАЦИЯ ВИДЕО
# =========================================================================
WIDTH, HEIGHT = 1080, 1920
FPS = 60
FRAMES_DRAW = 120  # Фаза 1: Прорисовка
FRAMES_MORPH = 120 # Фаза 2: Закручивание
TOTAL_FRAMES = FRAMES_DRAW + FRAMES_MORPH

# Базовые параметры (Икона D_5)
N_DEG = 5
LAMBDA = -2.5
ALPHA = 5.0
BETA = -1.9
GAMMA = 1.0

# =========================================================================
# ВЫЧИСЛИТЕЛЬНОЕ ЯДРО (NUMBA)
# =========================================================================
def get_core():
    def _compute(iters, n, lam, alp, bet, gam, om, w, h, x_b, y_b):
        hist = np.zeros((h, w), dtype=np.uint32)
        z = complex(0.01, 0.01)
        
        # Сброс переходного процесса
        for _ in range(200):
            r2 = z.real*z.real + z.imag*z.imag
            p = lam + alp*r2 + bet*(z**n).real
            z = complex(p*z.real - om*z.imag, p*z.imag + om*z.real) + gam*(z.conjugate()**(n-1))

        sx, sy = (w-1)/(2*x_b), (h-1)/(2*y_b)

        for _ in range(iters):
            r2 = z.real*z.real + z.imag*z.imag
            p = lam + alp*r2 + bet*(z**n).real
            z = complex(p*z.real - om*z.imag, p*z.imag + om*z.real) + gam*(z.conjugate()**(n-1))

            px = int((z.real + x_b) * sx)
            py = int((y_b - z.imag) * sy)
            
            if 0 <= px < w and 0 <= py < h:
                hist[py, px] += 1
        return hist

    if HAS_NUMBA:
        return njit(fastmath=True)(_compute)
    return _compute

# =========================================================================
# ГРАДИЕНТНАЯ ПАЛИТРА (CATPPUCCIN MOCHA: VOID -> MAUVE -> TEAL -> WHITE)
# =========================================================================
def apply_colormap(density_norm):
    h, w = density_norm.shape
    img_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Жесткий фикс "Черного экрана" (Гамма-коррекция)
    # Вытаскиваем тусклые пиксели на поверхность
    v = density_norm ** 0.35 

    c0 = np.array([8, 8, 12])      # Void (Фон)
    c1 = np.array([203, 166, 247]) # Mauve (Пурпурный контур)
    c2 = np.array([148, 226, 213]) # Teal (Бирюзовое свечение)
    c3 = np.array([255, 255, 255]) # White (Ядро)
    
    m1 = (v < 0.2)
    m2 = (v >= 0.2) & (v < 0.6)
    m3 = (v >= 0.6)

    def interp(mask, a, b, v_min, v_max):
        t = (v[mask] - v_min) / (v_max - v_min)
        for ch in range(3):
            img_rgb[mask, ch] = (a[ch] + t*(b[ch] - a[ch])).astype(np.uint8)

    interp(m1, c0, c1, 0.00, 0.2)
    interp(m2, c1, c2, 0.2, 0.6)
    interp(m3, c2, c3, 0.6, 1.0)
    return img_rgb

# =========================================================================
# РЕНДЕР ТАЙМЛАЙНА
# =========================================================================
def main():
    core = get_core()
    bound_x = 1.3
    bound_y = bound_x * (HEIGHT / WIDTH)

    print(f"Инициализация рендера ({TOTAL_FRAMES} кадров)...")
    writer = imageio.get_writer("attractor_morph.mp4", fps=FPS, quality=9)
    
    t_start = time.time()

    for frame in range(TOTAL_FRAMES):
        # ФАЗА 1: Прорисовка (Увеличиваем кол-во точек от 10k до 5M)
        if frame < FRAMES_DRAW:
            progress = frame / FRAMES_DRAW
            iters = int(10_000 + progress * 4_990_000)
            omega = 0.0
        # ФАЗА 2: Морфинг (Закручиваем узор)
        else:
            iters = 5_000_000
            progress = (frame - FRAMES_DRAW) / FRAMES_MORPH
            # Плавный ease-in-out для красоты вращения
            smooth_t = (1 - np.cos(progress * np.pi)) / 2
            omega = smooth_t * 0.15 

        # Вычисление кадра
        hist = core(iters, N_DEG, LAMBDA, ALPHA, BETA, GAMMA, omega, 
                    WIDTH, HEIGHT, bound_x, bound_y)
        
        # Нормализация (защита от сингулярности в центре)
        h_max = np.percentile(hist, 99.99) if np.max(hist) > 0 else 1.0
        norm = np.clip(hist / h_max, 0, 1.0)
        
        # Покраска и запись
        img_rgb = apply_colormap(norm)
        writer.append_data(img_rgb)
        
        if frame % 20 == 0:
            print(f"  Рендер кадра {frame}/{TOTAL_FRAMES} | Точек: {iters:,} | Omega: {omega:.3f}")

    writer.close()
    print(f"[УСПЕХ] Файл сохранен: attractor_morph.mp4 за {time.time() - t_start:.1f} сек.")

if __name__ == "__main__":
    main()