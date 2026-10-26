from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class GoldenRatioIntro(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        # ---------------------------------------------------------
        # 1. ПАЛИТРА И СТИЛЬ
        # ---------------------------------------------------------
        C_GUIDE = "#45475A"    # Линии квадратов
        C_GOLD  = "#F9E2AF"    # Золотая спираль
        C_PEACH = "#FAB387"    # Теплый хвост градиента
        C_WHITE = "#FFFFFF"    # Раскаленное ядро

        # =========================================================
        # 2. АНАЛИТИЧЕСКАЯ ГЕОМЕТРИЯ (100% СОВПАДЕНИЕ С OUTRO)
        # =========================================================
        S = 0.58 
        rect_center_raw = np.array([6.5, 10.5, 0])
        shift_rect = ORIGIN - rect_center_raw * S

        # 7 квадратов Фибоначчи (БЕЗ ЧИСЕЛ)
        squares_data = [
            {"box": [3, 4, 5, 6],   "center": [4, 6],  "r": 1,  "start_ang": PI},
            {"box": [4, 5, 5, 6],   "center": [4, 6],  "r": 1,  "start_ang": 3*PI/2},
            {"box": [3, 5, 6, 8],   "center": [3, 6],  "r": 2,  "start_ang": 0.0},
            {"box": [0, 3, 5, 8],   "center": [3, 5],  "r": 3,  "start_ang": PI/2},
            {"box": [0, 5, 0, 5],   "center": [5, 5],  "r": 5,  "start_ang": PI},
            {"box": [5, 13, 0, 8],  "center": [5, 8],  "r": 8,  "start_ang": 3*PI/2},
            {"box": [0, 13, 8, 21], "center": [0, 8],  "r": 13, "start_ang": 0.0},
        ]

        squares_group = VGroup()
        initial_arcs = []

        for data in squares_data:
            x1, x2, y1, y2 = [c * S for c in data["box"]]
            w = x2 - x1
            h = y2 - y1
            sq_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2, 0]) + shift_rect
            
            sq = Rectangle(width=w, height=h, color=C_GUIDE, stroke_width=2.0)
            sq.move_to(sq_center)
            squares_group.add(sq)

            cx, cy = [c * S for c in data["center"]]
            c_pos = np.array([cx, cy, 0]) + shift_rect
            arc = Arc(
                radius=data["r"] * S,
                start_angle=data["start_ang"],
                angle=PI / 2,
                arc_center=c_pos,
                color=C_GOLD,
                stroke_width=3.5
            )
            initial_arcs.append(arc)

        # САМОЕ ВАЖНОЕ: Точный математический глаз (ядро) спирали!
        core_point = initial_arcs[0].get_start()

        # Дуги космического продолжения (21, 34, 55, 89)
        ext_arcs_data = [
            {"center": [0, 0],    "r": 21, "start_ang": PI / 2},
            {"center": [13, 0],   "r": 34, "start_ang": PI},
            {"center": [13, 21],  "r": 55, "start_ang": 3 * PI / 2},
            {"center": [-21, 21], "r": 89, "start_ang": 0.0},
        ]

        extended_arcs = []
        for data in ext_arcs_data:
            cx, cy = [c * S for c in data["center"]]
            c_pos = np.array([cx, cy, 0]) + shift_rect
            arc = Arc(
                radius=data["r"] * S,
                start_angle=data["start_ang"],
                angle=PI / 2,
                arc_center=c_pos,
                color=C_GOLD,
                stroke_width=3.5
            )
            extended_arcs.append(arc)

        # Часть 1: Спираль внутри квадратов (та, что останется в итоге)
        primary_core_path = VMobject()
        for a in initial_arcs:
            primary_core_path.append_vectorized_mobject(a)
        primary_core_glow = primary_core_path.copy().set_stroke(color=C_GOLD, width=10.0, opacity=0.25)
        primary_single_spiral = VGroup(primary_core_glow, primary_core_path)

        # Часть 2: Внешний хвост базовой спирали
        primary_tail_path = VMobject()
        for a in extended_arcs:
            primary_tail_path.append_vectorized_mobject(a)
        primary_tail_glow = primary_tail_path.copy().set_stroke(color=C_GOLD, width=10.0, opacity=0.25)
        primary_tail = VGroup(primary_tail_glow, primary_tail_path)

        # Полная спираль для генерации галактики
        full_spiral_template = VMobject()
        for a in initial_arcs:
            full_spiral_template.append_vectorized_mobject(a)
        for a in extended_arcs:
            full_spiral_template.append_vectorized_mobject(a)

        # =========================================================
        # 3. ПОСТРОЕНИЕ ГАЛАКТИКИ ИЗ 21 СПИРАЛИ
        # =========================================================
        NUM_ARMS = 21
        other_arms = VGroup()
        other_glows = VGroup()

        for i in range(1, NUM_ARMS):
            rot_angle = i * (TAU / NUM_ARMS)
            # Вращаем строго вокруг истинного ЯДРА!
            arm = full_spiral_template.copy().rotate(rot_angle, about_point=core_point)
            
            arm.set_color_by_gradient(C_WHITE, C_GOLD, C_PEACH)
            arm.set_stroke(width=2.4)
            glow = arm.copy().set_stroke(color=C_GOLD, width=8.0, opacity=0.18)
            
            other_arms.add(arm)
            other_glows.add(glow)

        primary_core_path.set_color_by_gradient(C_WHITE, C_GOLD)
        primary_tail_path.set_color_by_gradient(C_GOLD, C_PEACH)

        # Добавляем раскаленную сингулярность ровно в центр вихря
        core_star = VGroup(
            Dot(core_point, radius=0.4, color=C_GOLD).set_opacity(0.4),
            Dot(core_point, radius=0.15, color=C_WHITE)
        )

        full_galaxy = VGroup(
            other_glows, other_arms, 
            primary_tail, primary_single_spiral,
            core_star
        )

        # =========================================================
        # 4. РЕЖИССУРА: ДАЙВ ИЗ КОСМОСА СТРОГО В ЦЕНТР
        # =========================================================
        
        CAMERA_GALAXY_ZOOM = 7.5

        # СТАРТ: Камера смотрит СТРОГО на ядро галактики (core_point)
        self.camera.frame.set_width(config.frame_width * CAMERA_GALAXY_ZOOM)
        self.camera.frame.move_to(core_point)

        # ШАГ 1: Галактика проявляется, камера плавно начинает наезд точно в центр
        self.wait(0.5)
        self.play(
            FadeIn(full_galaxy),
            self.camera.frame.animate.set_width(config.frame_width * 4.5).move_to(core_point),
            run_time=2.5,
            rate_func=rate_functions.ease_out_sine
        )

        # ШАГ 2: Резкий кинематографичный дайв.
        # В самом конце полета камера чуть-чуть смещается к ORIGIN, чтобы идеально кадрировать прямоугольник.
        self.play(
            self.camera.frame.animate.set_width(config.frame_width * 1.0).move_to(ORIGIN),
            FadeOut(other_arms),
            FadeOut(other_glows),
            FadeOut(primary_tail),
            FadeOut(core_star),
            primary_core_path.animate.set_color(C_GOLD),
            run_time=3.8,
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(0.2)

        # ШАГ 3: Вокруг оставшейся Золотой Спирали вычерчивается математический каркас
        self.play(
            Create(squares_group),
            run_time=1.5,
            rate_func=rate_functions.ease_out_sine
        )

        # Пауза для созерцания 
        self.wait(2.0)

        # ШАГ 4: Сцена плавно растворяется в темноту
        self.play(
            FadeOut(squares_group),
            FadeOut(primary_single_spiral),
            run_time=1.5,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(0.5)