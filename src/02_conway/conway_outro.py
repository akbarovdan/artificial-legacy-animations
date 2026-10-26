import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import convolve2d
from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = BLACK

class OutroLegacyScene(Scene):
    def construct(self):
        # --- ТУСКЛАЯ СЕРАЯ ПАЛИТРА (МОНОХРОМ) ---
        COLOR_GRAY = np.array([140, 143, 160], dtype=np.uint8)

        # ---------------------------------------------------------
        # 1. ОТРИСОВКА ТЕКСТА НАПРЯМУЮ В СЕТКУ 270x480 (ДВЕ СТРОКИ)
        # ---------------------------------------------------------
        GRID_W, GRID_H = 270, 480
        canvas_img = Image.new("L", (GRID_W, GRID_H), 0)
        draw = ImageDraw.Draw(canvas_img)

        try:
            import matplotlib.font_manager as fm
            fpath = fm.findfont(fm.FontProperties(family="Montserrat", weight="light"))
            font = ImageFont.truetype(fpath, 34)
        except Exception:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
            except Exception:
                font = ImageFont.load_default()

        bbox1 = draw.textbbox((0, 0), "Artificial", font=font)
        w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

        bbox2 = draw.textbbox((0, 0), "Legacy", font=font)
        w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

        spacing = 16
        total_h = h1 + h2 + spacing
        
        y1 = (GRID_H - total_h) // 2
        x1 = (GRID_W - w1) // 2
        y2 = y1 + h1 + spacing
        x2 = (GRID_W - w2) // 2

        draw.text((x1, y1), "Artificial", font=font, fill=255)
        draw.text((x2, y2), "Legacy", font=font, fill=255)

        # Превращаем в матрицу игры: белые пиксели = 1, фон = 0
        grid = (np.array(canvas_img) > 50).astype(np.uint8)

        # ---------------------------------------------------------
        # 2. РАСПАД ПО ПРАВИЛАМ КОНВЕЯ (УВЕЛИЧЕНО ДО 220 ШАГОВ)
        # ---------------------------------------------------------
        kernel = np.array([
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1]
        ], dtype=np.uint8)

        def step_life(g):
            neighbors = convolve2d(g, kernel, mode='same', boundary='fill', fillvalue=0)
            return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(np.uint8)

        STEPS = 220  # Увеличено количество шагов
        frames_rgb = []
        current_grid = grid

        for s in range(STEPS):
            frame = np.zeros((GRID_H, GRID_W, 3), dtype=np.uint8)
            frame[current_grid == 1] = COLOR_GRAY
            frames_rgb.append(frame)
            current_grid = step_life(current_grid)

        # ---------------------------------------------------------
        # 3. ВОСПРОИЗВЕДЕНИЕ СЕТКИ В MANIM
        # ---------------------------------------------------------
        display_img = ImageMobject(frames_rgb[0])
        display_img.height = 16
        display_img.set_resampling_algorithm(RESAMPLING_ALGORITHMS["nearest"])
        display_img.move_to(ORIGIN)

        # Сетка сразу на экране в чистом виде
        self.add(display_img)
        self.wait(1.8)  # Время показа логотипа без изменений

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

        # Длительность симуляции увеличена до 20 секунд
        self.play(
            step_tracker.animate.set_value(len(frames_rgb) - 1),
            run_time=20.0,
            rate_func=linear
        )
        display_img.remove_updater(update_frame)

        # Задержка в конце: сцена держится еще 3 секунды перед выключением
        self.wait(3.0)

        # Плавный уход в черный экран
        self.play(FadeOut(display_img), run_time=1.0)
        self.wait(0.5)