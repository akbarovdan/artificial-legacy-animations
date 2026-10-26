from manim import *
import numpy as np

# Вертикальный формат 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class VectorLifeScene(Scene):
    def construct(self):
        # Палитра: Глубокая космическая тьма и светящийся мятный неон
        BG_COLOR    = "#08080C"
        GLOW_COLOR  = "#A6E3A1"  # Мятно-зеленый
        TEXT_COLOR  = "#CDD6F4"
        ACCENT_RED  = "#F38BA8"

        self.camera.background_color = BG_COLOR

        # Масштабная сетка на весь экран (64 строки на 36 колонок)
        rows, cols = 64, 36
        dx = 9.0 / cols
        dy = 16.0 / rows

        # ==========================================
        # 1. ЗАВЯЗКА: 7 ТОЧЕК В ПУСТОТЕ
        # ==========================================
        hook = Text("7 dots. 4 rules.", font_size=38, color=TEXT_COLOR, weight=BOLD)
        hook.to_edge(UP, buff=1.8)
        self.play(FadeIn(hook, shift=DOWN), run_time=0.8)

        # Матрица симуляции
        grid = np.zeros((rows, cols), dtype=int)

        # Легендарный паттерн "Acorn" (Желудь) — ровно 7 точек
        # Из этой микроскопической фигуры вырастает целая вселенная
        r0, c0 = 32, 16
        acorn = [
            (0, 1),
            (1, 3),
            (2, 0), (2, 1), (2, 4), (2, 5), (2, 6)
        ]
        for dr, dc in acorn:
            grid[r0 + dr, c0 + dc] = 1

        # Функция для конвертации координат матрицы в векторные точки Manim
        def get_dots_group(state):
            dots = VGroup()
            alive_indices = np.argwhere(state == 1)
            for r, c in alive_indices:
                x = (c - cols / 2 + 0.5) * dx
                y = -(r - rows / 2 + 0.5) * dy
                dot = Dot(point=[x, y, 0], radius=0.08, color=GLOW_COLOR)
                dots.add(dot)
            return dots

        # Появление стартовых 7 точек
        current_dots = get_dots_group(grid)
        self.play(Create(current_dots), run_time=1)
        self.wait(0.5)
        self.play(FadeOut(hook), run_time=0.5)

        # ==========================================
        # 2. БЫСТРАЯ СИМУЛЯЦИЯ (16 ПОКОЛЕНИЙ В СЕКУНДУ)
        # ==========================================
        def step_life(g):
            # Быстрый подсчет соседей на NumPy
            neighbors = sum(
                np.roll(np.roll(g, i, 0), j, 1)
                for i in (-1, 0, 1)
                for j in (-1, 0, 1)
                if not (i == 0 and j == 0)
            )
            return ((neighbors == 3) | ((g == 1) & (neighbors == 2))).astype(int)

        # Прогоняем 65 поколений на высокой скорости
        generations = 65
        for step in range(generations):
            grid = step_life(grid)
            new_dots = get_dots_group(grid)
            
            # Мгновенная замена кадра без тормозов
            self.remove(current_dots)
            self.add(new_dots)
            current_dots = new_dots
            
            # Шаг 0.055 сек = плавная кинематографичная жизнь частиц
            self.wait(0.055)

        # ==========================================
        # 3. ФИНАЛ: ВЗРЫВ СЛОЖНОСТИ
        # ==========================================
        # Приглушаем частицы на фоне
        self.play(current_dots.animate.set_opacity(0.2), run_time=0.6)

        title = Text("EMERGENCE", font_size=48, color=GLOW_COLOR, weight=BOLD).shift(UP * 2)
        sub = Text("Simple rules. Infinite complexity.", font_size=28, color=TEXT_COLOR).next_to(title, DOWN, buff=0.4)
        badge = Text("TURING COMPLETE", font_size=32, color=ACCENT_RED, weight=BOLD).shift(DOWN * 2)

        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(sub, shift=UP), run_time=0.6)
        self.play(FadeIn(badge, scale=1.2), run_time=0.6)
        self.wait(2)