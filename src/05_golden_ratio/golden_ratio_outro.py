from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class GoldenSpiralOutro(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        # ---------------------------------------------------------
        # 1. ПАЛИТРА И ШРИФТЫ
        # ---------------------------------------------------------
        C_STEM     = "#A6E3A1"     
        C_FLOWER_C = "#F9E2AF" 
        C_FLOWER_P = "#CDD6F4" 
        C_PEACH    = "#FAB387"    
        C_GUIDE    = "#585B70"    
        C_GOLD     = "#F9E2AF"
        C_WHITE    = "#FFFFFF"
        
        FONT_NAME   = "Montserrat"
        FONT_WEIGHT = "LIGHT"  

        # =========================================================
        # 2. ВОССОЗДАНИЕ ДЕРЕВА ПТАРМИКИ (ТОЧНЫЙ КАДР ИЗ ПРОШЛОЙ СЦЕНЫ)
        # =========================================================
        nodes = {0: {"id": 0, "type": "Y", "tier": 0, "dir": 1, "parent": None, "children": []}}
        tiers = [[0]]
        next_id = 1
        max_tiers = 7 

        for i in range(max_tiers - 1):
            current_tier = tiers[-1]
            next_tier = []
            for node_id in current_tier:
                node = nodes[node_id]
                d = node["dir"]
                if node["type"] == "M":
                    id_m = next_id; next_id += 1
                    id_y = next_id; next_id += 1
                    nodes[id_m] = {"id": id_m, "type": "M", "tier": i+1, "dir": -d, "parent": node_id, "children": []}
                    nodes[id_y] = {"id": id_y, "type": "Y", "tier": i+1, "dir": d, "parent": node_id, "children": []}
                    if d == 1: node["children"] = [id_m, id_y]
                    else: node["children"] = [id_y, id_m]
                    next_tier.extend(node["children"])
                else:
                    id_m = next_id; next_id += 1
                    nodes[id_m] = {"id": id_m, "type": "M", "tier": i+1, "dir": d, "parent": node_id, "children": []}
                    node["children"] = [id_m]
                    next_tier.append(id_m)
            tiers.append(next_tier)

        leaves = []
        def dfs(node_id):
            if not nodes[node_id]["children"]: leaves.append(node_id)
            else:
                for child_id in nodes[node_id]["children"]: dfs(child_id)
        dfs(0)
        
        dx_leaf = 0.85 
        for idx, leaf_id in enumerate(leaves): nodes[leaf_id]["x"] = idx * dx_leaf
        mean_x = sum(nodes[l]["x"] for l in leaves) / len(leaves)
        for leaf_id in leaves: nodes[leaf_id]["x"] -= mean_x

        dy_tier = 3.2 
        for n in nodes.values(): n["y"] = n["tier"] * dy_tier

        for tier in reversed(tiers[:-1]):
            for node_id in tier:
                node = nodes[node_id]
                children = node["children"]
                if len(children) == 1: node["x"] = nodes[children[0]]["x"]
                else:
                    c1, c2 = children
                    x1, x2 = nodes[c1]["x"], nodes[c2]["x"]
                    if nodes[c1]["type"] == "M": node["x"] = x1 * 0.7 + x2 * 0.3
                    else: node["x"] = x1 * 0.3 + x2 * 0.7

        raw_min_x = min(n["x"] for n in nodes.values())
        raw_max_x = max(n["x"] for n in nodes.values())
        raw_w = raw_max_x - raw_min_x
        raw_h = max_tiers * dy_tier
        
        scale_factor = min(5.5 / raw_w, 14.0 / raw_h)
        for n in nodes.values():
            n["sx"] = n["x"] * scale_factor
            n["sy"] = n["y"] * scale_factor
            
        s_min_x = min(n["sx"] for n in nodes.values())
        s_max_x = max(n["sx"] for n in nodes.values())
        
        number_x = s_min_x - 1.2
        bbox_cx = (number_x - 0.5 + s_max_x + 0.5) / 2
        bbox_cy = (0 + max(n["sy"] for n in nodes.values())) / 2
        
        shift_x = -bbox_cx
        shift_y = -0.5 - bbox_cy
        
        for n in nodes.values():
            n["pos"] = np.array([n["sx"] + shift_x, n["sy"] + shift_y, 0])
            
        number_x_pos = number_x + shift_x

        def draw_ptarmica_flower(pos):
            flower = VGroup()
            for angle in np.linspace(0, 2 * PI, 6, endpoint=False):
                petal = Dot(pos + np.array([np.cos(angle), np.sin(angle), 0]) * 0.11, radius=0.065, color=C_FLOWER_P)
                flower.add(petal)
            center = Dot(pos, radius=0.08, color=C_FLOWER_C)
            flower.add(center)
            return flower

        tree_mobjects = VGroup()
        saved_fib_numbers = []

        for i in range(len(tiers)):
            tier_nodes = [nodes[nid] for nid in tiers[i]]
            y_level = tier_nodes[0]["pos"][1]
            is_last_tier = (i == len(tiers) - 1)
            
            if i > 0:
                for node in tier_nodes:
                    start_pos = nodes[node["parent"]]["pos"]
                    end_pos = node["pos"]
                    thickness = max(1.5, 6.0 - i * 0.6)
                    tree_mobjects.add(Line(start_pos, end_pos, color=C_STEM, stroke_width=thickness))
            else:
                tree_mobjects.add(Dot(tier_nodes[0]["pos"], color=C_STEM, radius=0.1))
                
            sorted_nodes = sorted(tier_nodes, key=lambda n: n["pos"][0])
            fib_number = Text(str(len(sorted_nodes)), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=42)
            fib_number.move_to(np.array([number_x_pos, y_level, 0]))
            saved_fib_numbers.append(fib_number)
            
            prev_pt = fib_number.get_right() + RIGHT * 0.2
            for node in sorted_nodes:
                target_pt = node["pos"]
                tree_mobjects.add(DashedLine(prev_pt, target_pt, color=C_GUIDE, stroke_width=2.5, dashed_ratio=0.5))
                if is_last_tier:
                    tree_mobjects.add(draw_ptarmica_flower(target_pt))
                else:
                    tree_mobjects.add(Dot(target_pt, radius=0.12, color=C_PEACH))
                prev_pt = target_pt

        # СТАРТ: Птармика уже на экране
        self.add(tree_mobjects, *saved_fib_numbers)
        self.wait(0.8)

        # =========================================================
        # 3. ТОЧНЫЕ КВАДРАТЫ И ПЕРВАЯ СПИРАЛЬ
        # =========================================================
        S = 0.58 
        rect_center_raw = np.array([6.5, 10.5, 0])
        shift_rect = ORIGIN - rect_center_raw * S

        # 7 квадратов Фибоначчи
        squares_data = [
            {"box": [3, 4, 5, 6],   "center": [4, 6],  "r": 1,  "start_ang": PI,       "val": 1},
            {"box": [4, 5, 5, 6],   "center": [4, 6],  "r": 1,  "start_ang": 3*PI/2,   "val": 1},
            {"box": [3, 5, 6, 8],   "center": [3, 6],  "r": 2,  "start_ang": 0.0,      "val": 2},
            {"box": [0, 3, 5, 8],   "center": [3, 5],  "r": 3,  "start_ang": PI/2,     "val": 3},
            {"box": [0, 5, 0, 5],   "center": [5, 5],  "r": 5,  "start_ang": PI,       "val": 5},
            {"box": [5, 13, 0, 8],  "center": [5, 8],  "r": 8,  "start_ang": 3*PI/2,   "val": 8},
            {"box": [0, 13, 8, 21], "center": [0, 8],  "r": 13, "start_ang": 0.0,      "val": 13},
        ]

        squares_group = VGroup()
        target_positions = []
        target_scales = []
        initial_arcs = []

        for data in squares_data:
            x1, x2, y1, y2 = [c * S for c in data["box"]]
            w = x2 - x1
            h = y2 - y1
            sq_center = np.array([(x1 + x2) / 2, (y1 + y2) / 2, 0]) + shift_rect
            
            sq = Rectangle(width=w, height=h, color=C_GUIDE, stroke_width=2.0)
            sq.move_to(sq_center)
            squares_group.add(sq)

            target_positions.append(sq_center)
            target_scales.append(min(1.1, (data["r"] * S) / 0.8 * 0.45))

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

        initial_spiral_path = VMobject(color=C_GOLD, stroke_width=3.5)
        for a in initial_arcs:
            initial_spiral_path.append_vectorized_mobject(a)
        initial_spiral_glow = initial_spiral_path.copy().set_stroke(color=C_GOLD, width=10.0, opacity=0.25)
        initial_spiral = VGroup(initial_spiral_glow, initial_spiral_path)

        # ТОЧНЫЙ МАТЕМАТИЧЕСКИЙ ЦЕНТР ЗАРОЖДЕНИЯ СПИРАЛИ В СЕТКЕ
        # (Никаких искусственных сдвигов — всё остаётся на своих местах!)
        core_point = initial_arcs[0].get_start()

        # =========================================================
        # 4. ПОЛНАЯ ДЛИННАЯ СПИРАЛЬ (ДО 89) БЕЗ СДВИГОВ
        # =========================================================
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

        # Полная мастер-спираль, остающаяся в координатах квадрата
        full_spiral_template = VMobject()
        for a in initial_arcs:
            full_spiral_template.append_vectorized_mobject(a)
        for a in extended_arcs:
            full_spiral_template.append_vectorized_mobject(a)

        # =========================================================
        # 5. ГАЛАКТИКА ИЗ 21 СПИРАЛИ ВОКРУГ РОДНОГО ЦЕНТРА
        # =========================================================
        NUM_ARMS = 21  # Число Фибоначчи
        galaxy_arms = VGroup()
        galaxy_glows = VGroup()

        for i in range(NUM_ARMS):
            rot_angle = i * (TAU / NUM_ARMS)
            # Вращаем строго вокруг истинного центра core_point, без сдвига в ORIGIN!
            arm = full_spiral_template.copy().rotate(rot_angle, about_point=core_point)
            
            # Роскошный градиент: раскаленный белый центр -> чистое золото -> теплый персик
            arm.set_color_by_gradient(C_WHITE, C_GOLD, C_PEACH)
            arm.set_stroke(width=2.4)

            glow = arm.copy().set_stroke(color=C_GOLD, width=8.0, opacity=0.18)
            
            galaxy_arms.add(arm)
            galaxy_glows.add(glow)

        # =========================================================
        # 6. АНИМАЦИОННАЯ РЕЖИССУРА: ОПЕРАТОРСКИЙ ЗУМ БЕЗ СДВИГОВ
        # =========================================================
        
        # ШАГ 1: Дерево растворяется
        self.play(FadeOut(tree_mobjects), run_time=0.8)
        self.wait(0.2)

        # ШАГ 2: Числа летят в квадраты, квадраты собираются
        morph_anims = [
            saved_fib_numbers[i].animate.move_to(target_positions[i]).scale(target_scales[i])
            for i in range(7)
        ]
        self.play(
            *morph_anims,
            Create(squares_group),
            run_time=1.4,
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(0.3)

        # ШАГ 3: Первая спираль чертится по 7 квадратам
        self.play(
            Create(initial_spiral, rate_func=linear),
            run_time=2.2
        )
        self.wait(0.6)

        # ШАГ 4: БЕЗУПРЕЧНЫЙ ПЕРЕХОД:
        # Квадраты гаснут, а камера сама мягко начинает наезжать на центр спирали (core_point).
        # Сама спираль НЕ сдвигается ни на миллиметр!
        self.play(
            FadeOut(squares_group),
            FadeOut(VGroup(*saved_fib_numbers)),
            self.camera.frame.animate.move_to(core_point),
            run_time=1.0,
            rate_func=rate_functions.ease_in_out_sine
        )

        # ШАГ 5: ВЗРЫВ ГАЛАКТИКИ И НАЧАЛО НЕПРЕРЫВНОГО ОТДАЛЕНИЯ
        # 21 золотая спираль вырывается из родного центра.
        # Камера синхронно начинает мощное непрерывное отдаление.
        self.play(
            FadeOut(initial_spiral), # Одиночная ветка незаметно растворяется в общем потоке
            LaggedStart(
                *[Create(arm, rate_func=rate_functions.ease_out_quad) for arm in galaxy_arms],
                lag_ratio=0.025
            ),
            LaggedStart(
                *[FadeIn(glow, rate_func=rate_functions.ease_out_quad) for glow in galaxy_glows],
                lag_ratio=0.025
            ),
            self.camera.frame.animate.scale(5.0),
            run_time=3.8,
            rate_func=rate_functions.ease_in_sine
        )

        # ШАГ 6: КУЛЬМИНАЦИЯ — КАМЕРА ПРОДОЛЖАЕТ УЛЕТАТЬ В ТЕМНОТУ БЕЗ ОСТАНОВОК!
        # Камера продолжает отдаляться еще дальше в космос (scale 2.0),
        # а вся галактика на глазах зрителя бесшовно тает и растворяется в бесконечной черной пустоте!
        self.play(
            self.camera.frame.animate.scale(2.2),
            galaxy_arms.animate.set_opacity(0),
            galaxy_glows.animate.set_opacity(0),
            run_time=2.8,
            rate_func=rate_functions.ease_out_quad
        )

        self.wait(0.5)