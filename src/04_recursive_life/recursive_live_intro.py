from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class TurtleFractalEvolution(Scene):
    def construct(self):
        # ---------------------------------------------------------
        # 1. ПАЛИТРА CATPPUCCIN MOCHA И ФОН
        # ---------------------------------------------------------
        self.camera.background_color = "#000000"

        C_GREEN   = "#A6E3A1"  # Кох
        C_YELLOW  = "#F9E2AF"  # Квадратичный Кох
        C_BLUE    = "#89B4FA"  # Госпер
        C_PEACH   = "#FAB387"  # Оранжевая подсветка активного символа при печати
        C_WHITE   = "#CDD6F4"  # Базовый цвет текста

        FONT_NAME = "Montserrat"
        FONT_WEIGHT = "LIGHT"

        # ---------------------------------------------------------
        # ДВИЖОК L-СИСТЕМ
        # ---------------------------------------------------------
        def get_shape(axiom, rules, angle_deg, iterations, color, stroke_width):
            current_string = axiom
            for _ in range(iterations):
                current_string = "".join([rules.get(char, char) for char in current_string])

            points = [ORIGIN]
            current_angle = 0.0
            current_pos = ORIGIN
            
            for char in current_string:
                if char in ['F', 'L', 'R']:
                    direction = np.array([np.cos(current_angle), np.sin(current_angle), 0])
                    current_pos = current_pos + direction
                    points.append(current_pos)
                elif char == '+': current_angle += np.radians(angle_deg)
                elif char == '-': current_angle -= np.radians(angle_deg)

            pts = np.array(points)
            x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
            y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
            
            pts -= np.array([(x_max + x_min) / 2, (y_max + y_min) / 2, 0])
            width = max(x_max - x_min, y_max - y_min)
            if width > 0: pts *= (7.5 / width)

            path = VMobject()
            path.set_points_as_corners(pts)
            path.set_stroke(color=color, width=stroke_width)
            
            glow = VMobject()
            glow.set_points_as_corners(pts)
            glow.set_stroke(color=color, width=stroke_width * 3.5, opacity=0.22)
            
            return VGroup(glow, path), pts

        # ---------------------------------------------------------
        # ЭТАП 1.1: ПОЯВЛЕНИЕ КВАДРАТА И ВОПРОС
        # ---------------------------------------------------------
        k_rules = {"F": "F-F+F+FF-F-F+F"}
        
        # Генерируем чистый квадрат n=0 и уровни фрактала
        koch_0, _     = get_shape("F-F-F-F", k_rules, 90, 0, C_GREEN, 4.0)
        koch_1, pts_1 = get_shape("F-F-F-F", k_rules, 90, 1, C_GREEN, 4.0)
        koch_2, _     = get_shape("F-F-F-F", k_rules, 90, 2, C_GREEN, 2.0)
        koch_3, _     = get_shape("F-F-F-F", k_rules, 90, 3, C_GREEN, 1.0)
        koch_4, _     = get_shape("F-F-F-F", k_rules, 90, 4, C_GREEN, 0.4)

        intro_square = koch_0.copy()

        # 1. Появление простого квадрата в тишине
        self.play(FadeIn(intro_square, scale=0.92), run_time=0.8)
        
        # 2. Пауза под закадровый вопрос: "How do you pack an infinite line into a finite space?"
        self.wait(1.8)

        # 3. Квадрат плавно затемняется, экран освобождается для правила
        self.play(FadeOut(intro_square, scale=1.05), run_time=0.6)
        self.wait(0.2)

        # ---------------------------------------------------------
        # ЭТАП 1.2: ЧЕРЕПАШЬЯ ЛИНИЯ СО СТРЕЛКАМИ (МИКРО-ПРАВИЛО)
        # ---------------------------------------------------------
        rule_str = "F-F+F+FF-F-F+F"

        # Центрируем первую сторону строго по центру экрана
        side_1_pts = pts_1[0:9]
        side_center = np.array([
            (side_1_pts[:, 0].max() + side_1_pts[:, 0].min()) / 2,
            (side_1_pts[:, 1].max() + side_1_pts[:, 1].min()) / 2,
            0
        ])
        turtle_pts = side_1_pts - side_center

        # Создаем векторные стрелки
        turtle_arrows = []
        pt_idx = 0
        for char in rule_str:
            if char == 'F':
                start_p = turtle_pts[pt_idx]
                end_p = turtle_pts[pt_idx + 1]
                
                arrow = Arrow(
                    start=start_p, end=end_p, buff=0, stroke_width=4.5,
                    max_tip_length_to_length_ratio=0.24, color=C_GREEN
                )
                glow = Arrow(
                    start=start_p, end=end_p, buff=0, stroke_width=14.0,
                    max_tip_length_to_length_ratio=0.28, color=C_GREEN, stroke_opacity=0.22
                )
                turtle_arrows.append((glow, arrow))
                pt_idx += 1

        # Текст формулы
        prefix = Text("F → ", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42)
        rule_chars = VGroup(*[
            Text(c, font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42) 
            for c in rule_str
        ])
        rule_chars.arrange(RIGHT, buff=0.08)
        full_text = VGroup(prefix, rule_chars).arrange(RIGHT, buff=0.2).move_to(UP * 6)

        self.play(FadeIn(prefix, shift=UP * 0.2), run_time=0.4)
        
        current_arrow_idx = 0
        for i, char in enumerate(rule_str):
            char_mobj = rule_chars[i]
            char_mobj.set_color(C_PEACH) # Оранжевая подсветка при печати
            
            if char == 'F':
                glow, arrow = turtle_arrows[current_arrow_idx]
                self.play(
                    GrowArrow(arrow),
                    GrowArrow(glow),
                    FadeIn(char_mobj, shift=UP * 0.1),
                    run_time=0.12,
                    rate_func=rate_functions.ease_out_quad
                )
                current_arrow_idx += 1
            else:
                self.play(
                    FadeIn(char_mobj, shift=UP * 0.1),
                    run_time=0.07
                )
            
            char_mobj.set_color(C_WHITE)

        # Короткая фиксация готового правила
        self.wait(0.5)

        # Черепашья линия и формула исчезают
        all_arrow_mobjects = [m for pair in turtle_arrows for m in pair]
        turtle_group = VGroup(*all_arrow_mobjects)
        
        self.play(
            FadeOut(turtle_group, scale=0.9),
            FadeOut(full_text, shift=UP * 0.4),
            run_time=0.6
        )
        self.wait(0.2)

        # ---------------------------------------------------------
        # ЭТАП 1.3: ПРОРИСОВКА САМОГО ФРАКТАЛА ИЗ КВАДРАТА (МАКРО)
        # ---------------------------------------------------------
        label_k0 = Text("n = 0, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42).move_to(UP * 6)
        label_k1 = Text("n = 1, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42).move_to(UP * 6)
        label_k2 = Text("n = 2, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42).move_to(UP * 6)
        label_k3 = Text("n = 3, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=42).move_to(UP * 6)

        # Квадрат возвращается в центр с надписью n = 0
        self.play(
            FadeIn(koch_0, scale=0.95),
            FadeIn(label_k0, shift=DOWN * 0.2),
            run_time=0.6
        )
        self.wait(0.3)

        # Все 4 грани квадрата ОДНОВРЕМЕННО ломаются по нашему правилу в n = 1
        self.play(
            Transform(koch_0, koch_1),
            Transform(label_k0, label_k1),
            run_time=1.0,
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(0.2)

        # n = 1 ломается в n = 2
        self.play(
            Transform(koch_0, koch_2),
            Transform(label_k0, label_k2),
            run_time=1.0
        )

        # n = 2 ломается в n = 3
        self.play(
            Transform(koch_0, koch_3),
            Transform(label_k0, label_k3),
            run_time=1.2
        )
        self.wait(0.3)

        # ШЕЛКОВЫЙ ПРОЛЕТ СКВОЗЬ КОХА В ТЕМНОТУ (n=3 -> n=4)
        koch_4_target = koch_4.scale(14).set_stroke(opacity=0)
        self.play(
            Transform(koch_0, koch_4_target), 
            FadeOut(label_k0, shift=UP * 0.5), 
            run_time=1.3, 
            rate_func=rate_functions.ease_in_cubic
        )
        self.remove(koch_0)

        # ---------------------------------------------------------
        # ФАЗА 2: КВАДРАТИЧНЫЙ КОХ (Желтый)
        # ---------------------------------------------------------
        kv_rules = {"F": "F-FF--F-F"}
        kvar_1, _ = get_shape("F-F-F-F", kv_rules, 90, 1, C_YELLOW, 4.0)
        kvar_2, _ = get_shape("F-F-F-F", kv_rules, 90, 2, C_YELLOW, 2.0)
        kvar_3, _ = get_shape("F-F-F-F", kv_rules, 90, 3, C_YELLOW, 1.0)
        kvar_4, _ = get_shape("F-F-F-F", kv_rules, 90, 4, C_YELLOW, 0.4)

        self.play(FadeIn(kvar_1, scale=0.08), run_time=0.9, rate_func=rate_functions.ease_out_cubic)
        self.wait(0.2)
        self.play(Transform(kvar_1, kvar_2), run_time=0.9)
        self.play(Transform(kvar_1, kvar_3), run_time=1.1)
        self.wait(0.3)
        
        kvar_4_target = kvar_4.scale(14).set_stroke(opacity=0)
        self.play(
            Transform(kvar_1, kvar_4_target), 
            run_time=1.3, 
            rate_func=rate_functions.ease_in_cubic
        )
        self.remove(kvar_1)

        # ---------------------------------------------------------
        # ФАЗА 3: ПЕАНО-ГОСПЕР (Синий)
        # ---------------------------------------------------------
        g_rules = {"L": "L+R++R-L--LL-R+", "R": "-L+RR++R+L--L-R"}
        gosp_1, _ = get_shape("L", g_rules, 60, 1, C_BLUE, 5.0)
        gosp_2, _ = get_shape("L", g_rules, 60, 2, C_BLUE, 2.5)
        gosp_3, _ = get_shape("L", g_rules, 60, 3, C_BLUE, 1.0)
        gosp_4, _ = get_shape("L", g_rules, 60, 4, C_BLUE, 0.4)

        self.play(FadeIn(gosp_1, scale=0.08), run_time=0.9, rate_func=rate_functions.ease_out_cubic)
        self.wait(0.2)
        self.play(Transform(gosp_1, gosp_2), run_time=0.9)
        self.play(Transform(gosp_1, gosp_3), run_time=1.1)
        self.wait(0.4)
        
        gosp_4_target = gosp_4.scale(15).set_stroke(opacity=0)
        self.play(
            Transform(gosp_1, gosp_4_target), 
            run_time=1.5, 
            rate_func=rate_functions.ease_in_cubic
        )
        self.remove(gosp_1)
        self.wait(0.8)