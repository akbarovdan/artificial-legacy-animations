from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class GoldenSpiralOutro(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        # ---------------------------------------------------------
        # 1. ПАЛИТРА И ДАННЫЕ
        # ---------------------------------------------------------
        C_GUIDE    = "#585B70"    
        C_PEACH    = "#FAB387" 
        C_GOLD     = "#F9E2AF"
        C_CENTER   = "#89DCEB"  # Неоновый циановый (ядро лотоса)
        C_EDGE     = "#CBA6F7"  # Лавандовый (края лепестков)
        
        FONT_NAME   = "Montserrat"
        FONT_WEIGHT = "LIGHT"  

        GOLDEN_ANGLE_RAD = np.radians(137.507764)

        # ---------------------------------------------------------
        # 2. ВОССОЗДАНИЕ ФИНАЛЬНОГО КАДРА ИЗ ПРОШЛОЙ СЦЕНЫ
        # ---------------------------------------------------------
        fib_seq = [1, 1, 2, 3, 5, 8, 13]
        sq_scale = 0.52 
        
        squares = VGroup()
        arcs = []
        
        dirs   = [RIGHT, UP, LEFT, DOWN]
        aligns = [UP, LEFT, DOWN, RIGHT]
        
        arc_centers_keys = [UR, UL, DL, DR]
        arc_start_angles = [PI, -PI / 2, 0.0, PI / 2]
        
        for i, val in enumerate(fib_seq):
            side = val * sq_scale
            sq = Square(side_length=side, color=C_GUIDE, stroke_width=2.0)
            
            if i == 0:
                sq.move_to(ORIGIN)
            else:
                dir_idx = (i - 1) % 4
                sq.next_to(squares, dirs[dir_idx], buff=0)
                sq.align_to(squares, aligns[dir_idx])
                
            squares.add(sq)
            
            c_idx = i % 4
            center_point = sq.get_corner(arc_centers_keys[c_idx])
            start_ang = arc_start_angles[c_idx]
            
            arc = Arc(
                radius=side,
                start_angle=start_ang,
                angle=PI / 2,
                arc_center=center_point,
                color=C_GOLD,
                stroke_width=4.0
            )
            arcs.append(arc)

        # Центрируем весь блок, как это было в прошлой сцене
        shift_vector = ORIGIN - squares.get_center()
        squares.shift(shift_vector)
        for a in arcs:
            a.shift(shift_vector)

        # Сшиваем дуги в единый объект спирали
        spiral_path = VMobject(color=C_GOLD, stroke_width=4.0)
        for a in arcs:
            spiral_path.append_vectorized_mobject(a)

        spiral_glow = spiral_path.copy().set_stroke(color=C_GOLD, width=12.0, opacity=0.25)

        # Цифры на своих местах
        saved_fib_numbers = VGroup()
        for i in range(len(fib_seq)):
            text_obj = Text(str(fib_seq[i]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46)
            target_scale = min(1.2, (fib_seq[i] * sq_scale) / (text_obj.height + 1e-5) * 0.45)
            text_obj.scale(target_scale).move_to(squares[i].get_center())
            saved_fib_numbers.add(text_obj)

        # ДОБАВЛЯЕМ ВСЁ НА ЭКРАН (СТАРТУЕМ ИЗ ЭТОГО КАДРА)
        self.add(squares, saved_fib_numbers, spiral_glow, spiral_path)

        # ---------------------------------------------------------
        # 3. ПОДГОТОВКА ЦВЕТКА (ЛОТОСА)
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

        N_petals = 280
        scale_c = 0.28
        
        pts_data = get_vogel_points(N_petals, scale_c)
        lotus_flower = VGroup()
        for rank in range(N_petals, 0, -1):
            idx = rank - 1
            x, y, theta = pts_data[idx]
            pos = np.array([x, y, 0])
            ratio = rank / N_petals
            shape = build_lotus_petal(length=0.4 + 1.2*np.sqrt(ratio), rank_ratio=ratio)
            shape.move_to(pos).rotate(theta, about_point=pos)
            lotus_flower.add(shape)
        
        lotus_flower.move_to(ORIGIN)
        
        # Сразу делаем цветок полупрозрачным, чтобы спирали сквозь него светились
        for elem in lotus_flower:
            elem.set_fill(opacity=0.35).set_stroke(opacity=0.1)

        # ---------------------------------------------------------
        # 4. АНИМАЦИОННАЯ РЕЖИССУРА ПЕРЕХОДА
        # ---------------------------------------------------------
        self.wait(1.0)

        # 1. Квадраты и цифры плавно растворяются, оставляя одинокую спираль
        self.play(
            FadeOut(squares),
            FadeOut(saved_fib_numbers),
            run_time=1.0
        )
        self.wait(0.5)

        # 2. ЖЕСТКИЙ СДВИГ БЕЗ ИСКАЖЕНИЙ. 
        # Вычисляем "глаз" спирали (Верхний правый угол первого квадрата 1х1)
        # И сдвигаем всю спираль так, чтобы этот глаз стал центром экрана (ORIGIN)
        eye_point = squares[0].get_corner(UR)
        center_shift = ORIGIN - eye_point
        
        self.play(
            spiral_path.animate.shift(center_shift),
            spiral_glow.animate.shift(center_shift),
            run_time=1.5,
            rate_func=rate_functions.ease_in_out_cubic
        )

        # 3. Генерируем остальные 7 спиралей (абсолютные копии первой, повернутые вокруг центра)
        other_spirals = VGroup()
        other_glows = VGroup()
        
        for i in range(1, 8):
            sp_copy = spiral_path.copy().rotate(i * TAU / 8, about_point=ORIGIN)
            gl_copy = spiral_glow.copy().rotate(i * TAU / 8, about_point=ORIGIN)
            
            # Разворачиваем направление отрисовки, чтобы они влетали из космоса в центр
            sp_copy.reverse_direction()
            gl_copy.reverse_direction()
            
            other_spirals.add(sp_copy)
            other_glows.add(gl_copy)

        # Влет спиралей снаружи внутрь
        self.play(
            LaggedStart(
                *[Create(gl) for gl in other_glows],
                *[Create(sp) for sp in other_spirals],
                lag_ratio=0.1
            ),
            run_time=2.5,
            rate_func=rate_functions.ease_out_sine
        )
        self.wait(0.2)

        # 4. В точке их слияния распускается Лотос
        self.play(FadeIn(lotus_flower, scale=0.8), run_time=2.0)
        
        # Эстетическая пауза
        self.wait(2.5)

        # 5. Линии спиралей исчезают, остается только цветок
        self.play(
            FadeOut(spiral_path),
            FadeOut(spiral_glow),
            FadeOut(other_spirals),
            FadeOut(other_glows),
            run_time=1.5
        )
        self.wait(0.8)

        # 6. Финальный уход цветка во тьму (без закручивания)
        self.play(
            FadeOut(lotus_flower, scale=1.05),
            run_time=1.8,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(1.0)