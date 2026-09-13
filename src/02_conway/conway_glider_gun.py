import os
import numpy as np
from scipy.signal import convolve2d
from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = BLACK

class ConwayGliderGun(Scene):
    def construct(self):
        # --- ПАЛИТРА CATPPUCCIN (RGB uint8) ---
        COLOR_ALIVE = np.array([137, 180, 250], dtype=np.uint8)  # Голубой (#89B4FA)
        COLOR_BORN  = np.array([166, 227, 161], dtype=np.uint8)  # Мятно-зеленый (#A6E3A1)
        COLOR_DIED  = np.array([243, 139, 168], dtype=np.uint8)  # Кораллово-красный (#F38BA8)

        # ---------------------------------------------------------
        # 1. СЕТКА В ВЫСОКОМ РАЗРЕШЕНИИ (72 строки на 40 колонок)
        # ---------------------------------------------------------
        GRID_H, GRID_W = 288, 162
        CELL_PIXELS = 4
        ROWS, COLS = GRID_H // CELL_PIXELS, GRID_W // CELL_PIXELS  # 72 x 40

        grid = np.zeros((ROWS, COLS), dtype=np.uint8)

        # Координаты оригинальной Пушки Госпера (36 клеток)
        gun_pattern = [
            (5, 1), (5, 2), (6, 1), (6, 2),
            (5, 11), (6, 11), (7, 11), (4, 12), (8, 12), (3, 13), (9, 13), (3, 14), (9, 14), (6, 15), (4, 16), (8, 16), (5, 17), (6, 17), (7, 17), (6, 18),
            (3, 21), (4, 21), (5, 21), (3, 22), (4, 22), (5, 22), (2, 23), (6, 23), (1, 25), (2, 25), (6, 25), (7, 25),
            (3, 35), (4, 35), (3, 36), (4, 36)
        ]

        # Размещаем пушку в верхней левой части
        r_shift, c_shift = 3, 1
        for r, c in gun_pattern:
            if r + r_shift < ROWS and c + c_shift < COLS:
                grid[r + r_shift, c + c_shift] = 1

        # ---------------------------------------------------------
        # 2. ПРОСЧЕТ СИМУЛЯЦИИ (120 ПОКОЛЕНИЙ)
        # ---------------------------------------------------------
        kernel = np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]
        ], dtype=np.uint8)

        def step_life_fast(g):
            neighbors = convolve2d(g, kernel, mode='same', boundary='fill', fillvalue=0)
            return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(np.uint8)

        STEPS = 120
        frames_rgb = []

        current_grid = grid
        for s in range(STEPS):
            next_grid = step_life_fast(current_grid)

            # Отрисовка кадра
            rgb = np.zeros((ROWS, COLS, 3), dtype=np.uint8)
            born = (next_grid == 1) & (current_grid == 0)
            died = (next_grid == 0) & (current_grid == 1)
            survived = (next_grid == 1) & (current_grid == 1)

            rgb[survived] = COLOR_ALIVE
            rgb[born] = COLOR_BORN
            rgb[died] = COLOR_DIED

            # Масштабируем пиксели до четких квадратов
            rgb_scaled = np.repeat(np.repeat(rgb, CELL_PIXELS, axis=0), CELL_PIXELS, axis=1)
            frames_rgb.append(rgb_scaled)

            current_grid = next_grid

        # ---------------------------------------------------------
        # 3. АНИМАЦИЯ В MANIM
        # ---------------------------------------------------------
        display_img = ImageMobject(frames_rgb[0])
        display_img.height = 16  # Отдаление: занимает весь экран 9:16
        display_img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        display_img.move_to(ORIGIN)

        # Просто плавное появление сетки
        self.play(FadeIn(display_img), run_time=1.0)
        self.wait(0.5)

        step_tracker = ValueTracker(0)

        def update_scene(mob):
            idx = int(step_tracker.get_value())
            idx = min(idx, len(frames_rgb) - 1)
            
            # Обновление кадра
            new_mob = ImageMobject(frames_rgb[idx])
            new_mob.height = 16
            new_mob.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
            new_mob.move_to(ORIGIN)
            mob.become(new_mob)

        display_img.add_updater(update_scene)

        # Выстрел планеров через весь экран (12 секунд)
        self.play(
            step_tracker.animate.set_value(len(frames_rgb) - 1),
            run_time=12.0,
            rate_func=linear
        )
        display_img.remove_updater(update_scene)

        # Задержание кадра перед финишем
        self.wait(1.5)
        self.play(FadeOut(display_img), run_time=1.0)