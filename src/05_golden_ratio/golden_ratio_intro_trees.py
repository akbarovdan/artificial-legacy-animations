from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class StochasticOrganicIntro(Scene):
    def construct(self):
        self.camera.background_color = "#000000"

        # =========================================================
        # 1. 3 АНАЛОГОВЫХ И НЕПОВТОРИМЫХ ПАЛИТРЫ 
        # =========================================================
        plants_data = [
            # -------------------------------------------------------------
            # 1. СИММЕТРИЧНЫЙ ПЫШНЫЙ КЛЕН / ДУБ (Рис. 1.24c)
            # -------------------------------------------------------------
            {
                "name": "Maple",
                "axiom": "F",
                "rules": {
                    "F": "FF-[-F+F+F]+[+F-F-F]"
                },
                "angle": 22.5,
                "n": 4,
                "ang_chaos": 0.08,
                "ext_chaos": 0.12,
                "pal": ["#2B0C1E", "#7A1C4B", "#F38BA8", "#FAB387", "#F9E2AF"] 
            },

            # -------------------------------------------------------------
            # 2. СТРОЙНОЕ ХВОЙНОЕ / КИПАРИС (Рис. 1.24e)
            # -------------------------------------------------------------
            {
                "name": "Pine",
                "axiom": "X",
                "rules": {
                    "X": "F[+X][-X]FX",
                    "F": "FF"
                },
                "angle": 25.7,
                "n": 7,
                "ang_chaos": 0.05,
                "ext_chaos": 0.10,
                "pal": ["#03140C", "#0B3D2B", "#1E6B45", "#74C7EC", "#C9FBF4"] 
            },

            # -------------------------------------------------------------
            # 3. РАСКИДИСТОЕ ЗОЛОТОЕ ДРЕВО (Рис. 1.24f)
            # -------------------------------------------------------------
            {
                "name": "GoldenTree",
                "axiom": "X",
                "rules": {
                    "X": "F-[[X]+X]+F[+FX]-X",
                    "F": "FF"
                },
                "angle": 22.5,
                "n": 5,
                "ang_chaos": 0.15,
                "ext_chaos": 0.12,
                "pal": ["#0B1F14", "#1E5E3A", "#40A02B", "#F9E2AF", "#FFFFFF"] 
            }
        ]

        # =========================================================
        # 2. ДВИЖОК ОРГАНИКИ С ЖЕСТКИМ АВТОМАСШТАБИРОВАНИЕМ
        # =========================================================
        def get_rich_gradient(t, palette):
            n = len(palette) - 1
            idx = min(int(t * n), n - 1)
            local_t = (t * n) - idx
            return interpolate_color(ManimColor(palette[idx]), ManimColor(palette[idx + 1]), local_t)

        def build_stochastic_plant(p_info):
            current_string = p_info["axiom"]
            for _ in range(p_info["n"]):
                current_string = "".join([p_info["rules"].get(char, char) for char in current_string])

            stack = []
            curr_pos = np.array([0.0, 0.0, 0.0])
            curr_angle = np.pi / 2 # Ствол растет строго вверх
            
            segments = []
            all_pts = [curr_pos]

            angle_deg = p_info["angle"]
            ang_chaos = p_info["ang_chaos"]
            ext_chaos = p_info["ext_chaos"]

            # ГЛОБАЛЬНЫЙ СИД: чтобы дерево не дрожало при рендеринге
            np.random.seed(42 + sum(ord(c) for c in p_info["name"]))

            for char in current_string:
                depth = len(stack)

                if char in ['F', 'G']: 
                    length_tapering = 0.85 ** depth
                    noise_extension = length_tapering * np.random.uniform(1.0 - ext_chaos, 1.0 + ext_chaos)
                    
                    next_pos = curr_pos + noise_extension * np.array([np.cos(curr_angle), np.sin(curr_angle), 0])
                    segments.append((curr_pos, next_pos, depth))
                    all_pts.append(next_pos)
                    curr_pos = next_pos

                elif char == '+': 
                    noise_ang = np.radians(angle_deg) * np.random.uniform(-ang_chaos, ang_chaos)
                    curr_angle += np.radians(angle_deg) + noise_ang

                elif char == '-': 
                    noise_ang = np.radians(angle_deg) * np.random.uniform(-ang_chaos, ang_chaos)
                    curr_angle -= np.radians(angle_deg) + noise_ang

                elif char == '[': stack.append((curr_pos.copy(), curr_angle))
                elif char == ']': curr_pos, curr_angle = stack.pop()

            all_pts_arr = np.array(all_pts)
            x_min, x_max = all_pts_arr[:, 0].min(), all_pts_arr[:, 0].max()
            y_min, y_max = all_pts_arr[:, 1].min(), all_pts_arr[:, 1].max()

            height = y_max - y_min
            width = x_max - x_min
            
            # ИДЕАЛЬНЫЙ АВТОМАСШТАБ (ГАРАНТИЯ БОЛЬШОГО РАЗМЕРА):
            # Дерево будет либо 12.5 юнитов в высоту, либо 8.0 юнитов в ширину,
            # в зависимости от того, что наступит раньше. Оно всегда заполнит экран!
            scale_factor = min(8.0 / width, 12.5 / height)

            # Центрируем ствол по оси X, а корень опускаем вниз
            root_offset = np.array([(x_max + x_min) / 2, y_min, 0])
            base_y_pos = DOWN * 6.5 # Корни растут с самого низа экрана

            max_depth = max([s[2] for s in segments]) if segments else 1
            depth_groups = [VGroup() for _ in range(max_depth + 1)]

            palette = p_info["pal"]

            for start, end, depth in segments:
                p_start = (start - root_offset) * scale_factor + base_y_pos
                p_end = (end - root_offset) * scale_factor + base_y_pos

                # Магия света (распределение свечения от ствола к кончикам)
                y_ratio = np.clip((p_start[1] - base_y_pos[1]) / 12.5, 0.0, 1.0)
                d_ratio = depth / max_depth
                blend_t = 0.4 * d_ratio + 0.6 * y_ratio
                
                branch_col = get_rich_gradient(blend_t, palette)
                
                # Природная упругость: низ ствола толстый, хвоя прозрачная и тонкая
                thickness = max(0.6, 7.0 * (0.75 ** depth)) 

                core = Line(p_start, p_end, stroke_width=thickness, color=branch_col)
                glow = Line(p_start, p_end, stroke_width=thickness * 3.8, color=branch_col, stroke_opacity=0.20)
                depth_groups[depth].add(VGroup(glow, core))

            return VGroup(*depth_groups), depth_groups

        # =========================================================
        # 3. АНИМАЦИОННЫЙ КАСКАД РОСТА (БЕЗ ТЕКСТА)
        # =========================================================
        self.wait(0.5)

        for i, p_info in enumerate(plants_data):
            plant, depth_levels = build_stochastic_plant(p_info)

            # Элегантный органический график раскрытия 
            growth_anims = [
                Create(lvl, rate_func=rate_functions.ease_out_sine)
                for lvl in depth_levels
            ]

            # Мощный рост из семени в роскошную структуру
            self.play(
                LaggedStart(*growth_anims, lag_ratio=0.18),
                run_time=2.5, # Чуть медленнее для величественности
                rate_func=linear
            )
            
            self.wait(1.0)

            is_last = (i == len(plants_data) - 1)
            
            if not is_last:
                # Мягкое втягивание и растворение
                self.play(
                    FadeOut(plant, scale=0.92, shift=DOWN * 0.4),
                    run_time=0.7,
                    rate_func=rate_functions.ease_in_cubic
                )
                self.wait(0.2)
            else:
                # Финал: последнее Золотое дерево проваливается во тьму (Переход)
                self.play(
                    plant.animate.scale(1.15).set_opacity(0).shift(DOWN * 0.5),
                    run_time=2.0,
                    rate_func=rate_functions.ease_in_expo
                )

        self.wait(1.0)