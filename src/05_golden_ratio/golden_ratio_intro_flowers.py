from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class GoldenSpiralHook(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        # ---------------------------------------------------------
        # 1. ПАЛИТРА И ДАННЫЕ
        # ---------------------------------------------------------
        C_CENTER  = "#89DCEB"  # Неоновый циановый (ядро)
        C_EDGE    = "#CBA6F7"  # Лавандовый (края лепестков)
        C_GOLD    = "#F9E2AF"  # Золотое свечение спиралей
        
        GOLDEN_RATIO = 1.6180339887
        GOLDEN_ANGLE_RAD = np.radians(137.507764)

        # ---------------------------------------------------------
        # 2. МАТЕМАТИКА ВОГЕЛЯ (ДЛЯ ЦВЕТКА)
        # ---------------------------------------------------------
        def get_vogel_points(N, c_scale):
            points = []
            for i in range(1, N + 1):
                r = c_scale * np.sqrt(i)
                theta = i * GOLDEN_ANGLE_RAD
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                points.append((x, y, theta))
            return points

        def build_lotus_petal(length=1.0, rank_ratio=0.0):
            # Элегантный вытянутый лепесток лотоса
            col = interpolate_color(ManimColor(C_CENTER), ManimColor(C_EDGE), rank_ratio)
            
            points = [
                np.array([0.0, 0.0, 0.0]),
                np.array([length*0.25, length*0.18, 0.0]),
                np.array([length, 0.0, 0.0]),
                np.array([length*0.25, -length*0.18, 0.0])
            ]
            path = VMobject()
            path.set_points_smoothly(points)
            path.add_line_to(points[0]).make_smooth()
            path.set_fill(col, opacity=0.85).set_stroke("#000000", width=1.0)
            return path

        def create_flower_cluster(N_elements, c_scale):
            pts_data = get_vogel_points(N_elements, c_scale)
            cluster_vg = VGroup()
            elements = []
            
            for rank in range(N_elements, 0, -1):
                idx = rank - 1
                x, y, theta = pts_data[idx]
                pos = np.array([x, y, 0])
                
                ratio = rank / N_elements
                shape = build_lotus_petal(length=0.4 + 1.2*np.sqrt(ratio), rank_ratio=ratio)
                shape.move_to(pos).rotate(theta, about_point=pos)
                elements.append(shape)
                
            cluster_vg.add(*elements) 
            return cluster_vg

        def spring_out_anim(target_group):
            """Эффект радиального взрывного цветения из центра"""
            anims = []
            for shape in target_group:
                target_state = shape.copy()
                shape.move_to(ORIGIN).scale(0.001).set_opacity(0)
                anims.append(Transform(shape, target_state, rate_func=rate_functions.ease_out_back))
            return LaggedStart(*anims, lag_ratio=0.012) 


        # ---------------------------------------------------------
        # ФАЗА 1: РОЖДЕНИЕ КОСМИЧЕСКОГО ЛОТОСА
        # ---------------------------------------------------------
        N_petals = 280
        scale_c = 0.28
        lotus_flower = create_flower_cluster(N_petals, scale_c)
        
        # Строго по центру, так как текста нет
        lotus_flower.move_to(ORIGIN)

        self.wait(0.5)
        # Цветок распускается
        self.play(spring_out_anim(lotus_flower), run_time=3.5)
        self.wait(0.5)


        # ---------------------------------------------------------
        # ФАЗА 2: НАЛОЖЕНИЕ ЗОЛОТЫХ СПИРАЛЕЙ
        # ---------------------------------------------------------
        # Слегка гасим цветок, уводя его на фон
        dim_anims = [elem.animate.set_fill(opacity=0.35).set_stroke(opacity=0.1) for elem in lotus_flower]
        self.play(*dim_anims, run_time=1.0, rate_func=rate_functions.ease_in_out_sine)

        # Математика идеальной Золотой Спирали
        b_factor = np.log(GOLDEN_RATIO) / (PI / 2)
        a_factor = 0.15 
        
        golden_spirals = VGroup()
        
        num_spirals = 8
        for i in range(num_spirals):
            rot_offset = i * (2 * PI / num_spirals)
            
            spiral = ParametricFunction(
                lambda t, offset=rot_offset: np.array([
                    a_factor * np.exp(b_factor * t) * np.cos(t + offset),
                    a_factor * np.exp(b_factor * t) * np.sin(t + offset),
                    0
                ]),
                t_range=[0, 4.2 * PI],
                color=C_GOLD,
                stroke_width=3.5
            )
            
            glow = spiral.copy().set_stroke(color=C_GOLD, width=12.0, opacity=0.25)
            spiral_group = VGroup(glow, spiral)
            golden_spirals.add(spiral_group)

        # Спирали завораживающе вырисовываются из центра наружу
        self.play(
            LaggedStart(
                *[Create(sp, rate_func=rate_functions.ease_out_cubic) for sp in golden_spirals],
                lag_ratio=0.1
            ),
            run_time=3.0
        )
        
        # Фиксируем картинку, чтобы зритель осознал идеальное совпадение
        self.wait(2.5)

        # ---------------------------------------------------------
        # ФАЗА 3: СПОКОЙНЫЙ ФИНАЛЬНЫЙ УХОД
        # ---------------------------------------------------------
        # Сначала исчезают математические линии (спирали)
        self.play(FadeOut(golden_spirals), run_time=1.2)
        self.wait(0.3)
        
        # Затем мягко растворяется сам цветок
        self.play(FadeOut(lotus_flower), run_time=1.5)
        self.wait(1.0)