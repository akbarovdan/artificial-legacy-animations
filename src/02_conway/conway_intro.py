import os
import numpy as np
from PIL import Image
from scipy.signal import convolve2d
from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = BLACK

# ВАЖНО: Используем MovingCameraScene для плавного зума
class ConwayIntroScene(MovingCameraScene):
    def construct(self):
        # --- ЦВЕТА (Старт - Голубой, Конец - Зеленый) ---
        COLOR_START = np.array([137, 180, 250], dtype=np.float32)  # Спокойный голубой (#89B4FA)
        COLOR_END   = np.array([166, 227, 161], dtype=np.float32)  # Мятно-зеленый (#A6E3A1)
        
        # ---------------------------------------------------------
        # 1. СОЗДАЕМ ОГРОМНЫЙ МИР НА ВЕСЬ ЭКРАН (16:9)
        # ---------------------------------------------------------
        GRID_W = 270
        GRID_H = 480
        grid = np.zeros((GRID_H, GRID_W), dtype=np.uint8)

        # ---------------------------------------------------------
        # 2. ЗАГРУЖАЕМ ФОТО В ЦЕНТР ПУСТОТЫ
        # ---------------------------------------------------------
        script_dir = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(script_dir, "conway.png")

        if not os.path.exists(img_path):
            print(f"Ошибка: положите conway.png в {script_dir}")
            return

        FACE_SIZE = 180
        raw_img = Image.open(img_path).convert("L").resize((FACE_SIZE, FACE_SIZE), Image.Resampling.LANCZOS)
        face_arr = np.array(raw_img)

        # Белые точки = 1, Черные = 0
        face_bin = (face_arr > 105).astype(np.uint8)

        r_start = (GRID_H - FACE_SIZE) // 2
        c_start = (GRID_W - FACE_SIZE) // 2

        grid[r_start:r_start+FACE_SIZE, c_start:c_start+FACE_SIZE] = face_bin

        # ---------------------------------------------------------
        # 3. ЧИСТЫЙ ПРОСЧЕТ СИМУЛЯЦИИ (Увеличили до 120 шагов)
        # ---------------------------------------------------------
        kernel = np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]
        ], dtype=np.uint8)

        def step_life_fast(g):
            neighbors = convolve2d(g, kernel, mode='same', boundary='fill', fillvalue=0)
            return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(np.uint8)

        STEPS = 160  # Больше шагов для долгой анимации
        frames_rgb = []

        current_grid = grid
        for s in range(STEPS):
            progress = s / STEPS

            # Плавный переход от голубого к зеленому
            current_color = (1.0 - progress) * COLOR_START + progress * COLOR_END

            frame_rgb = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
            frame_rgb[current_grid == 1] = current_color.astype(np.uint8)
            
            frames_rgb.append(frame_rgb)
            current_grid = step_life_fast(current_grid)

        # ---------------------------------------------------------
        # 4. ВОСПРОИЗВЕДЕНИЕ В MANIM (СТАБИЛЬНЫЙ ПОЛЕТ В ТЕМНОТУ)
        # ---------------------------------------------------------
        display_img = ImageMobject(frames_rgb[0])
        display_img.height = 16  
        display_img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        display_img.move_to(ORIGIN)

        self.play(FadeIn(display_img), run_time=1.0)
        self.wait(1.5)  # Портрет зафиксирован перед стартом

        step_tracker = ValueTracker(0)

        def update_frame(mob):
            idx = int(step_tracker.get_value())
            idx = min(idx, len(frames_rgb) - 1)
            new_mob = ImageMobject(frames_rgb[idx])
            new_mob.height = 16
            new_mob.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
            new_mob.move_to(ORIGIN)
            mob.become(new_mob)

        display_img.add_updater(update_frame)

        # 1-Й ЭТАП: Непрерывное ускоряющееся падение вглубь пикселей (15 секунд)
        self.play(
            step_tracker.animate.set_value(len(frames_rgb) - 1),
            self.camera.frame.animate.scale(0.08).move_to(ORIGIN), 
            run_time=15.0,
            rate_func=rate_functions.ease_in_quad
        )
        display_img.remove_updater(update_frame)

        # 2-Й ЭТАП: Мгновенный уход в темноту (БЕЗ раздувания масштаба в 8 раз!)
        # scale=1.2 дает аккуратный толчок вперед и чисто растворяет картинку в черную пустоту
        self.play(
            FadeOut(display_img, scale=1.2),
            run_time=0.8
        )
        self.wait(0.5)