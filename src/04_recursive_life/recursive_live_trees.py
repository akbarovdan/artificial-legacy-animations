from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class RecursiveTreesScene(Scene):
    def construct(self):
        self.camera.background_color = "#000000"

        FONT_NAME = "Montserrat"
        FONT_WEIGHT = "LIGHT"
        C_WHITE = "#CDD6F4"
        C_PEACH = "#FAB387"
        C_GREEN = "#A6E3A1"

        # =========================================================
        # ЧАСТЬ 1: ОБУЧАЮЩИЙ ПОБЕГ (СО СТРЕЛКАМИ И ФОРМУЛОЙ)
        # =========================================================
        tree_str = "F[+F][-F[-F]F]F[+F][-F]"
        angle_deg = 45.0
        step_len = 1.7

        stack = []
        curr_pos = np.array([0.0, 0.0, 0.0])
        curr_angle = np.pi / 2
        all_points = [curr_pos]

        for char in tree_str:
            if char == 'F':
                next_pos = curr_pos + step_len * np.array([np.cos(curr_angle), np.sin(curr_angle), 0])
                all_points.append(next_pos)
                curr_pos = next_pos
            elif char == '+': curr_angle += np.radians(angle_deg)
            elif char == '-': curr_angle -= np.radians(angle_deg)
            elif char == '[': stack.append((curr_pos.copy(), curr_angle))
            elif char == ']': curr_pos, curr_angle = stack.pop()

        all_pts_arr = np.array(all_points)
        x_min, x_max = all_pts_arr[:, 0].min(), all_pts_arr[:, 0].max()
        y_min, y_max = all_pts_arr[:, 1].min(), all_pts_arr[:, 1].max()

        center_offset = np.array([(x_max + x_min) / 2, (y_max + y_min) / 2, 0])
        start_origin = -center_offset + DOWN * 1.5

        chars_group = VGroup(*[
            Text(c, font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=38)
            for c in tree_str
        ])
        chars_group.arrange(RIGHT, buff=0.07).move_to(UP * 5.8)

        curr_pos = start_origin.copy()
        curr_angle = np.pi / 2
        stack = []
        active_nodes = []
        tutorial_arrows = VGroup()

        self.wait(0.3)

        for i, char in enumerate(tree_str):
            char_mobj = chars_group[i]
            char_mobj.set_color(C_PEACH)
            
            if char == 'F':
                next_pos = curr_pos + step_len * np.array([np.cos(curr_angle), np.sin(curr_angle), 0])
                arrow = Arrow(
                    start=curr_pos, end=next_pos, buff=0, stroke_width=4.5, 
                    max_tip_length_to_length_ratio=0.22, color=C_GREEN
                )
                glow = Arrow(
                    start=curr_pos, end=next_pos, buff=0, stroke_width=14.0, 
                    max_tip_length_to_length_ratio=0.26, color=C_GREEN, stroke_opacity=0.22
                )
                arrow_group = VGroup(glow, arrow)
                tutorial_arrows.add(arrow_group)
                
                self.play(
                    GrowArrow(arrow),
                    GrowArrow(glow),
                    FadeIn(char_mobj, shift=UP * 0.1),
                    run_time=0.18,
                    rate_func=rate_functions.ease_out_quad
                )
                curr_pos = next_pos

            elif char == '[':
                stack.append((curr_pos.copy(), curr_angle))
                node_dot = Dot(curr_pos, radius=0.07, color=C_PEACH)
                active_nodes.append(node_dot)
                self.play(FadeIn(char_mobj, shift=UP * 0.1), FadeIn(node_dot, scale=1.5), run_time=0.10)

            elif char == ']':
                curr_pos, curr_angle = stack.pop()
                last_node = active_nodes.pop() if active_nodes else None
                anims = [FadeIn(char_mobj, shift=UP * 0.1)]
                if last_node: anims.append(FadeOut(last_node, scale=0.5))
                self.play(*anims, run_time=0.10)

            elif char in ['+', '-']:
                curr_angle += np.radians(angle_deg) if char == '+' else -np.radians(angle_deg)
                self.play(FadeIn(char_mobj, shift=UP * 0.1), run_time=0.07)

            char_mobj.set_color(C_WHITE)

        self.wait(0.6)

        self.play(
            FadeOut(chars_group, shift=UP * 0.4),
            FadeOut(tutorial_arrows, scale=0.9),
            run_time=0.8,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(0.2)

        # =========================================================
        # ЧАСТЬ 2: 7 РАСТЕНИЙ (ГЕНЕРАТИВНЫЙ ТАЙМЛАПС)
        # =========================================================
        def get_rich_gradient(t, palette):
            n = len(palette) - 1
            idx = min(int(t * n), n - 1)
            local_t = (t * n) - idx
            return interpolate_color(ManimColor(palette[idx]), ManimColor(palette[idx + 1]), local_t)

        def build_plant(axiom, rules, angle_deg, iterations, palette):
            current_string = axiom
            for _ in range(iterations):
                current_string = "".join([rules.get(char, char) for char in current_string])

            stack = []
            curr_pos = np.array([0.0, 0.0, 0.0])
            curr_angle = np.pi / 2
            
            segments = []
            all_pts = [curr_pos]

            for char in current_string:
                if char == 'F':
                    depth = len(stack)
                    next_pos = curr_pos + 1.0 * np.array([np.cos(curr_angle), np.sin(curr_angle), 0])
                    segments.append((curr_pos, next_pos, depth))
                    all_pts.append(next_pos)
                    curr_pos = next_pos
                elif char == '+': curr_angle += np.radians(angle_deg)
                elif char == '-': curr_angle -= np.radians(angle_deg)
                elif char == '[': stack.append((curr_pos.copy(), curr_angle))
                elif char == ']': curr_pos, curr_angle = stack.pop()

            all_pts_arr = np.array(all_pts)
            x_min, x_max = all_pts_arr[:, 0].min(), all_pts_arr[:, 0].max()
            y_min, y_max = all_pts_arr[:, 1].min(), all_pts_arr[:, 1].max()

            height = y_max - y_min
            width = x_max - x_min
            scale_factor = 10.8 / max(height, width * 1.25)

            root_offset = np.array([(x_max + x_min) / 2, y_min, 0])
            max_depth = max([s[2] for s in segments]) if segments else 1
            depth_groups = [VGroup() for _ in range(max_depth + 1)]

            for start, end, depth in segments:
                p_start = (start - root_offset) * scale_factor + DOWN * 5.2
                p_end = (end - root_offset) * scale_factor + DOWN * 5.2

                y_ratio = np.clip((p_start[1] - (DOWN * 5.2)[1]) / 10.0, 0.0, 1.0)
                d_ratio = depth / max_depth
                blend_t = 0.55 * d_ratio + 0.45 * y_ratio
                
                branch_col = get_rich_gradient(blend_t, palette)
                thickness = max(0.7, 4.8 * (0.82 ** depth))

                core = Line(p_start, p_end, stroke_width=thickness, color=branch_col)
                glow = Line(p_start, p_end, stroke_width=thickness * 2.8, color=branch_col, stroke_opacity=0.18)
                depth_groups[depth].add(VGroup(glow, core))

            plant_group = VGroup(*depth_groups)
            return plant_group, depth_groups

        PALETTES = {
            "a": ["#1A3D1A", "#338A2E", "#A6E3A1", "#F9E2AF", "#FAB387"],
            "b": ["#361A28", "#883955", "#F38BA8", "#F5C2E7", "#F9E2AF"],
            "c": ["#1B3828", "#40A02B", "#A6E3A1", "#F9E2AF", "#FAB387"],
            "d": ["#0B2E36", "#04A5E5", "#89DCEB", "#94E2D5", "#E8FAF8"],
            "e": ["#0D1D3A", "#1E66F5", "#89B4FA", "#94E2D5", "#C9FBF4"],
            "f": ["#26103B", "#7223B3", "#CBA6F7", "#F5C2E7", "#F9E2AF"],
            # g: "Космическое Золото и Алмазные Звезды"
            "g": ["#0B2418", "#1E6B45", "#50C878", "#F9E2AF", "#FFFFFF"]
        }

        # 7 уникальных растений
        plants_data = [
            {"axiom": "F", "rules": {"F": "F[+F]F[-F]F"}, "angle": 25.7, "n": 5, "pal": PALETTES["a"]},
            {"axiom": "F", "rules": {"F": "F[+F]F[-F][F]"}, "angle": 20.0, "n": 5, "pal": PALETTES["b"]},
            {"axiom": "F", "rules": {"F": "FF-[-F+F+F]+[+F-F-F]"}, "angle": 22.5, "n": 4, "pal": PALETTES["c"]},
            {"axiom": "X", "rules": {"X": "F[+X]F[-X]+X", "F": "FF"}, "angle": 20.0, "n": 7, "pal": PALETTES["d"]},
            {"axiom": "X", "rules": {"X": "F[+X][-X]FX", "F": "FF"}, "angle": 25.7, "n": 7, "pal": PALETTES["e"]},
            {"axiom": "X", "rules": {"X": "F-[[X]+X]+F[+FX]-X", "F": "FF"}, "angle": 22.5, "n": 5, "pal": PALETTES["f"]},
            # 7. НОВОЕ ДРЕВО ЖИЗНИ: 5-лучевой радиальный веер кроны
            {"axiom": "X", "rules": {"X": "F[+++X][+X][X][-X][---X]", "F": "FF"}, "angle": 18.0, "n": 5, "pal": PALETTES["g"]}
        ]

        for i, p_info in enumerate(plants_data):
            plant, depth_levels = build_plant(
                p_info["axiom"], p_info["rules"], p_info["angle"], p_info["n"], p_info["pal"]
            )

            is_last = (i == len(plants_data) - 1)
            growth_time = 1.8 if is_last else 1.6
            wait_time = 1.0 if is_last else 0.5

            growth_anims = [
                Create(lvl, rate_func=rate_functions.ease_out_quad)
                for lvl in depth_levels
            ]

            self.play(
                LaggedStart(*growth_anims, lag_ratio=0.15),
                run_time=growth_time,
                rate_func=linear
            )
            
            self.wait(wait_time)

            if not is_last:
                self.play(
                    FadeOut(plant, scale=0.92),
                    run_time=0.45,
                    rate_func=rate_functions.ease_in_cubic
                )
                self.wait(0.1)
            else:
                # Финальное дерево плавно растворяется в черную бездну
                self.play(
                    plant.animate.scale(1.08).set_opacity(0),
                    run_time=1.6,
                    rate_func=rate_functions.ease_in_cubic
                )

        self.wait(1.0)