from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class SpacetimeLifeScene6(ThreeDScene):
    def construct(self):
        # Палитра
        BG_COLOR     = "#000000"
        PLANE_COLOR  = "#313244"
        COLOR_START  = ManimColor("#A6E3A1")
        COLOR_END    = ManimColor("#89B4FA")
        
        self.camera.background_color = BG_COLOR

        # ---------------------------------------------------------
        # 1. 3D КАМЕРА
        # ---------------------------------------------------------
        self.set_camera_orientation(phi=70 * DEGREES, theta=-50 * DEGREES)
        self.begin_ambient_camera_rotation(rate=0.1)

        rows, cols = 18, 18
        cell_size = 0.32
        
        def get_coords(r, c, z):
            x = (c - cols / 2 + 0.5) * cell_size
            y = (r - rows / 2 + 0.5) * cell_size
            return np.array([x, y, z])

        # ---------------------------------------------------------
        # 2. СЕМЕНА ЖИЗНИ
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # 3. ПЛОСКОСТЬ ВЫЧИСЛЕНИЙ
        # ---------------------------------------------------------
        z_start = 8.0   # <-- СТАРТУЕМ ЕЩЕ ВЫШЕ
        z_end = -12.0  # <-- ПАДАЕМ ЕЩЕ ГЛУБЖЕ
        steps = 110     # <-- ЕЩЕ БОЛЬШЕ ШАГОВ

        dz = (z_end - z_start) / steps

        active_plane = Square(side_length=cols * cell_size, color=PLANE_COLOR, stroke_width=1.5)
        active_plane.move_to([0, 0, z_start])
        self.add(active_plane)

        # ---------------------------------------------------------
        # 4. СИМУЛЯЦИЯ: ЧИСТАЯ ВИЗУАЛИЗАЦИЯ
        # ---------------------------------------------------------
        current_z = z_start

        for s in range(steps):
            next_grid = step_life(grid)
            next_z = current_z + dz
            
            progress = s / steps
            thread_color = interpolate_color(COLOR_START, COLOR_END, progress)

            new_threads = VGroup()
            live_points_on_plane = VGroup()

            alive_now = np.argwhere(next_grid == 1)
            
            for r, c in alive_now:
                p_curr = get_coords(r, c, next_z)
                
                if grid[r, c] == 1:
                    p_prev = get_coords(r, c, current_z)
                else:
                    nbrs = [
                        (nr, nc) for nr in (r-1, r, r+1) for nc in (c-1, c, c+1)
                        if 0 <= nr < rows and 0 <= nc < cols and grid[nr, nc] == 1
                    ]
                    if nbrs: p_prev = get_coords(nbrs[0][0], nbrs[0][1], current_z)
                    else: p_prev = p_curr + np.array([0, 0, -dz])

                fiber = Line(p_prev, p_curr, stroke_width=2.5, color=thread_color)
                new_threads.add(fiber)

                dot = Dot(p_curr, radius=0.04, color=COLOR_START)
                live_points_on_plane.add(dot)
            
            self.play(
                active_plane.animate.move_to([0, 0, next_z]),
                Create(new_threads),
                FadeIn(live_points_on_plane, run_time=0.1),
                run_time=0.18,
                rate_func=linear
            )

            self.remove(live_points_on_plane)

            grid = next_grid
            current_z = next_z

        self.wait(3)