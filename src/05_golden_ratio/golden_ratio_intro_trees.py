from manim import *
import numpy as np
import random

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class StochasticOrganicIntro(Scene):
    def construct(self):
        self.camera.background_color = "#000000"

        # =========================================================
        # 1. 3 АНАЛОГОВЫХ И НЕПОВТОРИМЫХ ПАЛИТРЫ (Биолюминесценция)
        # =========================================================
        PALETTES_EPIC = {
            # 1. Монументальный купол: Изумруд и ледяное золото
            "royal_oak": ["#051A10", "#0D4D36", "#268C63", "#A6E3A1", "#F5E0DC"],
            
            # 2. ИЗОГНУТАЯ ПЛАКУЧАЯ ВЕТВЬ: Вулкан и раскаленное золото
            "flame":     ["#290606", "#610C1A", "#AB2331", "#EB7C36", "#F9E2AF"],
            
            # 3. Сумеречный папоротник: Ультрафиолет и белый неон
            "velvet":    ["#160829", "#3A115E", "#7223B3", "#CBA6F7", "#FFFFFF"]
        }

        plants_data = [
            {
                # СИЛУЭТ 1: Огромный купол (Царский дуб), растущий в стороны
                "name": "The Royal Canopy",
                "axiom": "X", 
                "rules": {"X": "F[+X][-X]F[+X][-X]FX", "F": "FF"},
                "angle": 24.0, "n": 5, 
                "ang_chaos": 0.35, "ext_chaos": 0.20,
                "pal": PALETTES_EPIC["royal_oak"]
            },
            {
                # СИЛУЭТ 2: (НОВЫЙ!) Изящно согнутое асимметричное дерево (каскадные лозы).
                # Из-за асимметричных углов (++ в одну, и много - в другую) ветки стекают водопадом
                "name": "Luminous Weeper",
                "axiom": "X", 
                "rules": {"X": "F[++X][-X]F[-X][+F-X]", "F": "FF"},
                "angle": 17.5, "n": 5, # Острый угол (хвойное строение)
                "ang_chaos": 0.40, "ext_chaos": 0.28, # Достаточно высокий хаос (имитация ветра)
                "pal": PALETTES_EPIC["flame"]
            },
            {
                # СИЛУЭТ 3: Вытянутое бархатное перо (дикий папоротник), растущий строго вверх
                "name": "Dense Velvet Polypody",
                "axiom": "X", 
                "rules": {"X": "F[+X]F[-X]+F[+X]-X", "F": "FF"},
                "angle": 22.5, "n": 5, 
                "ang_chaos": 0.40, "ext_chaos": 0.15,
                "pal": PALETTES_EPIC["velvet"]
            }
        ]

        # =========================================================
        # 2. ОРГАНИЧЕСКИЙ ДВИЖОК С ХАОСОМ ВЕТВЕЙ (БИОФИЗИКА)
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
            curr_angle = np.pi / 2 # Ствол растет вверх
            
            segments = []
            all_pts = [curr_pos]

            angle_deg = p_info["angle"]
            ang_chaos = p_info["ang_chaos"]
            ext_chaos = p_info["ext_chaos"]

            # ГЛОБАЛЬНЫЙ И АБСОЛЮТНО СТАБИЛЬНЫЙ СИД!
            stable_seed = sum(ord(c) for c in p_info["name"])
            np.random.seed(42 + stable_seed)

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
            scale_factor = 10.4 / max(height, width * 1.30)

            root_offset = np.array([(x_max + x_min) / 2, y_min, 0])
            max_depth = max([s[2] for s in segments]) if segments else 1
            depth_groups = [VGroup() for _ in range(max_depth + 1)]

            palette = p_info["pal"]

            for start, end, depth in segments:
                p_start = (start - root_offset) * scale_factor + DOWN * 5.8
                p_end = (end - root_offset) * scale_factor + DOWN * 5.8

                # Магия света (распределение свечения от ствола к кончикам)
                y_ratio = np.clip((p_start[1] - (DOWN * 5.8)[1]) / 10.5, 0.0, 1.0)
                d_ratio = depth / max_depth
                blend_t = 0.5 * d_ratio + 0.5 * y_ratio
                
                branch_col = get_rich_gradient(blend_t, palette)
                
                # Природная упругость: низ ствола толстый, хвоя прозрачная и микроскопическая
                thickness = max(0.5, 6.2 * (0.75 ** depth)) 

                core = Line(p_start, p_end, stroke_width=thickness, color=branch_col)
                glow = Line(p_start, p_end, stroke_width=thickness * 3.8, color=branch_col, stroke_opacity=0.18)
                depth_groups[depth].add(VGroup(glow, core))

            return VGroup(*depth_groups), depth_groups

        # =========================================================
        # 3. АНИМАЦИОННЫЙ КАСКАД РОСТА
        # =========================================================
        self.wait(1.0)

        for i, p_info in enumerate(plants_data):
            plant, depth_levels = build_stochastic_plant(p_info)

            # Элегантный органический график раскрытия 
            growth_anims = [
                Create(lvl, rate_func=rate_functions.ease_out_sine)
                for lvl in depth_levels
            ]

            # Мощный рост из семени в роскошную структуру
            self.play(
                LaggedStart(*growth_anims, lag_ratio=0.14),
                run_time=2.2,
                rate_func=linear
            )
            
            self.wait(0.7)

            is_last = (i == len(plants_data) - 1)
            
            if not is_last:
                self.play(
                    FadeOut(plant, scale=0.92, shift=DOWN * 0.4),
                    run_time=0.7,
                    rate_func=rate_functions.ease_in_cubic
                )
                self.wait(0.15)
            else:
                # Третье дерево (Финал интро) величественно падает во тьму, оставляя нас в космосе
                self.play(
                    plant.animate.scale(1.15).set_opacity(0).shift(DOWN*0.5),
                    run_time=2.0,
                    rate_func=rate_functions.ease_in_expo
                )

        self.wait(1.0)