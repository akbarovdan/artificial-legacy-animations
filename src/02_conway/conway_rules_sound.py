from manim import *
import numpy as np

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class TurtleFractalEvolution(Scene):
    def construct(self):
        self.camera.background_color = "#000000"

        C_GREEN   = "#A6E3A1"  # Кох
        C_YELLOW  = "#F9E2AF"  # Квадратичный Кох
        C_BLUE    = "#89B4FA"  # Госпер

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
            glow.set_stroke(color=color, width=stroke_width * 3.5, opacity=0.2)
            
            return VGroup(glow, path), pts

        # ---------------------------------------------------------
        # ФАЗА 1: ЧЕРЕПАШКА И ЭВОЛЮЦИЯ КОХА
        # ---------------------------------------------------------
        k_rules = {"F": "F-F+F+FF-F-F+F"}
        koch_1, pts_1 = get_shape("F-F-F-F", k_rules, 90, 1, C_GREEN, 4.0)
        koch_2, _     = get_shape("F-F-F-F", k_rules, 90, 2, C_GREEN, 2.0)
        koch_3, _     = get_shape("F-F-F-F", k_rules, 90, 3, C_GREEN, 1.0)

        side_1_pts = pts_1[0:9]
        side_center = np.array([
            (side_1_pts[:, 0].max() + side_1_pts[:, 0].min()) / 2,
            (side_1_pts[:, 1].max() + side_1_pts[:, 1].min()) / 2,
            0
        ])
        pts_1_shifted = pts_1 - side_center

        rule_str = "F-F+F+FF-F-F+F"
        turtle_lines = VGroup()
        pt_idx = 0
        for char in rule_str:
            if char == 'F':
                core = Line(pts_1_shifted[pt_idx], pts_1_shifted[pt_idx+1]).set_stroke(color=C_GREEN, width=4.0)
                glow = Line(pts_1_shifted[pt_idx], pts_1_shifted[pt_idx+1]).set_stroke(color=C_GREEN, width=14.0, opacity=0.2)
                turtle_lines.add(VGroup(glow, core))
                pt_idx += 1

        prefix = Text("F → ", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GREEN, font_size=42)
        rule_chars = VGroup(*[Text(c, font=FONT_NAME, weight=FONT_WEIGHT, color=C_GREEN, font_size=42) for c in rule_str])
        rule_chars.arrange(RIGHT, buff=0.08)
        full_text = VGroup(prefix, rule_chars).arrange(RIGHT, buff=0.2).move_to(UP * 6)

        self.play(FadeIn(prefix, shift=UP*0.2), run_time=0.6)
        current_line_idx = 0
        for i, char in enumerate(rule_str):
            if char == 'F':
                self.play(Create(turtle_lines[current_line_idx]), FadeIn(rule_chars[i], shift=UP*0.1), run_time=0.12)
                current_line_idx += 1
            else:
                self.play(FadeIn(rule_chars[i], shift=UP*0.1), run_time=0.08)

        self.wait(0.5)

        rest_pts = pts_1_shifted[8:] 
        rest_core = VMobject().set_points_as_corners(rest_pts).set_stroke(color=C_GREEN, width=4.0)
        rest_glow = VMobject().set_points_as_corners(rest_pts).set_stroke(color=C_GREEN, width=14.0, opacity=0.2)
        rest_group = VGroup(rest_glow, rest_core)

        self.play(Create(rest_group), run_time=1.5, rate_func=rate_functions.ease_in_out_sine)
        self.wait(0.5)

        full_koch_shifted_core = VMobject().set_points_as_corners(pts_1_shifted).set_stroke(color=C_GREEN, width=4.0)
        full_koch_shifted_glow = VMobject().set_points_as_corners(pts_1_shifted).set_stroke(color=C_GREEN, width=14.0, opacity=0.2)
        full_koch_shifted = VGroup(full_koch_shifted_glow, full_koch_shifted_core)
        self.add(full_koch_shifted)
        self.remove(*turtle_lines, rest_group)

        label_k1 = Text("n = 1, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GREEN, font_size=42).move_to(UP * 6)
        
        self.play(
            Transform(full_koch_shifted, koch_1),
            FadeOut(full_text, shift=UP*0.5),
            run_time=1.2, rate_func=rate_functions.ease_in_out_cubic
        )
        self.play(FadeIn(label_k1, shift=DOWN*0.3), run_time=0.5)
        self.wait(0.3)

        label_k2 = Text("n = 2, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GREEN, font_size=42).move_to(UP * 6)
        self.play(Transform(full_koch_shifted, koch_2), Transform(label_k1, label_k2), run_time=1.2)
        
        label_k3 = Text("n = 3, δ = 90°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GREEN, font_size=42).move_to(UP * 6)
        self.play(Transform(full_koch_shifted, koch_3), Transform(label_k1, label_k3), run_time=1.5)
        self.wait(0.8)

        # ---------------------------------------------------------
        # КИНЕМАТОГРАФИЧЕСКИЙ ПРОЛЕТ (ЗОМ) СКВОЗЬ КОХА
        # ---------------------------------------------------------
        # scale(35) растягивает линии далеко за пределы экрана, opacity(0) мягко гасит остатки
        self.play(
            full_koch_shifted.animate.scale(35).set_opacity(0), 
            FadeOut(label_k1, shift=UP), 
            run_time=1.5, 
            rate_func=rate_functions.ease_in_expo
        )
        self.remove(full_koch_shifted)

        # ---------------------------------------------------------
        # ФАЗА 2: КВАДРАТИЧНЫЙ КОХ (Желтый)
        # ---------------------------------------------------------
        kv_rules = {"F": "F-FF--F-F"}
        kvar_1, _ = get_shape("F-F-F-F", kv_rules, 90, 1, C_YELLOW, 4.0)
        kvar_2, _ = get_shape("F-F-F-F", kv_rules, 90, 2, C_YELLOW, 2.0)
        kvar_3, _ = get_shape("F-F-F-F", kv_rules, 90, 3, C_YELLOW, 1.0)

        # Появление из "бесконечности" (scale=0.01)
        self.play(FadeIn(kvar_1, scale=0.01), run_time=1.2, rate_func=rate_functions.ease_out_expo)
        self.wait(0.3)
        self.play(Transform(kvar_1, kvar_2), run_time=1.0)
        self.play(Transform(kvar_1, kvar_3), run_time=1.2)
        self.wait(0.8)
        
        # Пролет сквозь желтую фигуру
        self.play(
            kvar_1.animate.scale(35).set_opacity(0), 
            run_time=1.5, 
            rate_func=rate_functions.ease_in_expo
        )
        self.remove(kvar_1)

        # ---------------------------------------------------------
        # ФАЗА 3: ПЕАНО-ГОСПЕР (Синий)
        # ---------------------------------------------------------
        g_rules = {"L": "L+R++R-L--LL-R+", "R": "-L+RR++R+L--L-R"}
        gosp_1, _ = get_shape("L", g_rules, 60, 1, C_BLUE, 5.0)
        gosp_2, _ = get_shape("L", g_rules, 60, 2, C_BLUE, 2.5)
        gosp_3, _ = get_shape("L", g_rules, 60, 3, C_BLUE, 1.0)

        self.play(FadeIn(gosp_1, scale=0.01), run_time=1.2, rate_func=rate_functions.ease_out_expo)
        self.wait(0.3)
        self.play(Transform(gosp_1, gosp_2), run_time=1.0)
        self.play(Transform(gosp_1, gosp_3), run_time=1.5)
        self.wait(1.5)
        
        # Финальный сверх-глубокий пролет в темноту перед следующим роликом
        self.play(
            gosp_1.animate.scale(40).set_opacity(0), 
            run_time=1.5, 
            rate_func=rate_functions.ease_in_expo
        )
        self.remove(gosp_1)
        self.wait(1.0) # Идеальная черная пустота в конце