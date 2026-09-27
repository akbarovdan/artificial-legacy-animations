from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class AchilleaFibonacci(Scene):
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
        
        FONT_NAME   = "Montserrat"
        FONT_WEIGHT = "LIGHT"  

        # ---------------------------------------------------------
        # 2. АЛГОРИТМ ПЛАНАРНОГО ГРАФА (0 ПЕРЕСЕЧЕНИЙ)
        # ---------------------------------------------------------
        nodes = {0: {"id": 0, "type": "Y", "tier": 0, "dir": 1, "parent": None, "children": []}}
        tiers = [[0]]
        next_id = 1
        max_tiers = 7 # Ярусы: 0(1), 1(1), 2(2), 3(3), 4(5), 5(8), 6(13)

        # 2.1. Создаем связи
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
                    
                    if d == 1:
                        node["children"] = [id_m, id_y]
                    else:
                        node["children"] = [id_y, id_m]
                    next_tier.extend(node["children"])
                else:
                    id_m = next_id; next_id += 1
                    nodes[id_m] = {"id": id_m, "type": "M", "tier": i+1, "dir": d, "parent": node_id, "children": []}
                    node["children"] = [id_m]
                    next_tier.append(id_m)
            tiers.append(next_tier)

        # 2.2. Расставляем листья по оси X 
        leaves = []
        def dfs(node_id):
            if not nodes[node_id]["children"]:
                leaves.append(node_id)
            else:
                for child_id in nodes[node_id]["children"]:
                    dfs(child_id)
        dfs(0)
        
        dx_leaf = 1.0   # Ширина шага по X
        dy_tier = 2.8   # <-- СДЕЛАЛИ ЭТАЖИ В 1.5 РАЗА ВЫШЕ (было 2.0)

        for idx, leaf_id in enumerate(leaves):
            nodes[leaf_id]["x"] = idx * dx_leaf
            nodes[leaf_id]["y"] = nodes[leaf_id]["tier"] * dy_tier

        # 2.3. Вычисляем X родителей (сверху вниз)
        for tier in reversed(tiers[:-1]):
            for node_id in tier:
                node = nodes[node_id]
                children = node["children"]
                if len(children) == 1:
                    node["x"] = nodes[children[0]]["x"]
                else:
                    c1, c2 = children
                    x1, x2 = nodes[c1]["x"], nodes[c2]["x"]
                    if nodes[c1]["type"] == "M":
                        node["x"] = x1 * 0.7 + x2 * 0.3
                    else:
                        node["x"] = x1 * 0.3 + x2 * 0.7
                node["y"] = node["tier"] * dy_tier

        # ---------------------------------------------------------
        # 3. ИДЕАЛЬНОЕ ЦЕНТРИРОВАНИЕ И РАСТЯГИВАНИЕ ДЛЯ 9:16
        # ---------------------------------------------------------
        raw_min_x = min(n["x"] for n in nodes.values())
        raw_max_x = max(n["x"] for n in nodes.values())
        raw_w = raw_max_x - raw_min_x
        raw_h = max_tiers * dy_tier
        
        # Разрешаем дереву занимать 13.5 юнитов в высоту (из 16)
        scale_factor = min(6.5 / raw_w, 13.5 / raw_h)
        
        for n in nodes.values():
            n["sx"] = n["x"] * scale_factor
            n["sy"] = n["y"] * scale_factor
            
        s_min_x = min(n["sx"] for n in nodes.values())
        s_max_x = max(n["sx"] for n in nodes.values())
        
        # Координата X для колонки цифр (слева от веток)
        number_x = s_min_x - 1.2
        
        # Вычисляем габариты
        bbox_min_x = number_x - 0.5 
        bbox_max_x = s_max_x + 0.5  
        bbox_cx = (bbox_min_x + bbox_max_x) / 2
        
        bbox_min_y = 0
        bbox_max_y = max(n["sy"] for n in nodes.values())
        bbox_cy = (bbox_min_y + bbox_max_y) / 2
        
        # Центрируем. Смещаем чуть-чуть вниз (-0.4), чтобы цветы не упирались в потолок
        shift_x = -bbox_cx
        shift_y = -0.4 - bbox_cy
        
        for n in nodes.values():
            n["pos"] = np.array([n["sx"] + shift_x, n["sy"] + shift_y, 0])
            
        number_x_pos = number_x + shift_x

        def draw_flower(pos):
            flower = VGroup()
            for angle in np.linspace(0, 2 * PI, 6, endpoint=False):
                petal = Dot(pos + np.array([np.cos(angle), np.sin(angle), 0]) * 0.11, radius=0.065, color=C_FLOWER_P)
                flower.add(petal)
            center = Dot(pos, radius=0.08, color=C_FLOWER_C)
            flower.add(center)
            return flower

        # ---------------------------------------------------------
        # 4. АНИМАЦИЯ: РОСТ И СЧЕТ
        # ---------------------------------------------------------
        self.wait(0.4)
        
        root_node = nodes[0]
        root_dot = Dot(root_node["pos"], color=C_STEM, radius=0.1)
        self.play(FadeIn(root_dot, scale=0.5), run_time=0.4)

        all_tree_mobjects = VGroup(root_dot)
        saved_fib_numbers = []

        # Ярус 0 (Корень)
        fib_num_root = Text("1", font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=42)
        fib_num_root.move_to(np.array([number_x_pos, root_node["pos"][1], 0]))
        saved_fib_numbers.append(fib_num_root)
        
        self.play(FadeIn(fib_num_root, shift=RIGHT * 0.2), run_time=0.25)
        
        prev_pt_root = fib_num_root.get_right() + RIGHT * 0.2
        line_seg_root = DashedLine(prev_pt_root, root_node["pos"], color=C_GUIDE, stroke_width=2.5, dashed_ratio=0.5)
        marker_root = Dot(root_node["pos"], radius=0.12, color=C_PEACH)
        
        self.play(Create(line_seg_root), run_time=0.25, rate_func=linear)
        self.play(FadeIn(marker_root, scale=2.0), run_time=0.12)
        all_tree_mobjects.add(line_seg_root, marker_root)
        self.wait(0.15)

        # Остальные ярусы
        for i in range(1, len(tiers)):
            tier_nodes = [nodes[nid] for nid in tiers[i]]
            y_level = tier_nodes[0]["pos"][1]
            is_last_tier = (i == len(tiers) - 1)
            
            branches = VGroup()
            for node in tier_nodes:
                start_pos = nodes[node["parent"]]["pos"]
                end_pos = node["pos"]
                # Сделал ствол чуть толще у основания (7.5 вместо 6.5), так как он стал длиннее
                thickness = max(1.5, 7.5 - i * 0.8)
                branches.add(Line(start_pos, end_pos, color=C_STEM, stroke_width=thickness))
            
            all_tree_mobjects.add(branches)
            self.play(Create(branches, rate_func=rate_functions.ease_out_quad), run_time=0.6)
            
            sorted_nodes = sorted(tier_nodes, key=lambda n: n["pos"][0])
            
            fib_number = Text(str(len(sorted_nodes)), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=42)
            fib_number.move_to(np.array([number_x_pos, y_level, 0]))
            saved_fib_numbers.append(fib_number)
            
            self.play(FadeIn(fib_number, shift=RIGHT * 0.2), run_time=0.25)
            
            prev_pt = fib_number.get_right() + RIGHT * 0.2
            guides_and_markers = VGroup()
            anims = []
            
            for node in sorted_nodes:
                target_pt = node["pos"]
                line_seg = DashedLine(prev_pt, target_pt, color=C_GUIDE, stroke_width=2.5, dashed_ratio=0.5)
                
                if is_last_tier:
                    marker = draw_flower(target_pt)
                else:
                    marker = Dot(target_pt, radius=0.12, color=C_PEACH)
                    
                guides_and_markers.add(line_seg, marker)
                
                if i <= 2:
                    self.play(Create(line_seg), run_time=0.25, rate_func=linear)
                    self.play(FadeIn(marker, scale=2.0), run_time=0.12)
                else:
                    anims.append(Succession(
                        Create(line_seg, run_time=0.07),
                        FadeIn(marker, scale=1.5, run_time=0.05)
                    ))
                
                prev_pt = target_pt
            
            if i > 2:
                self.play(LaggedStart(*anims, lag_ratio=0.12))
            
            all_tree_mobjects.add(guides_and_markers)
            self.wait(0.15)

        self.wait(1.5)

        # ---------------------------------------------------------
        # 5. МАГИЧЕСКИЙ ПЕРЕХОД: ДЕРЕВО ИСЧЕЗАЕТ, 7 ЦИФР ОСТАЮТСЯ
        # ---------------------------------------------------------
        self.play(FadeOut(all_tree_mobjects), run_time=0.8)
        self.wait(0.3)

        # ---------------------------------------------------------
        # 6. ИДЕАЛЬНАЯ ЗОЛОТАЯ СПИРАЛЬ ФИБОНАЧЧИ
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

        shift_vector = ORIGIN - squares.get_center()
        squares.shift(shift_vector)
        for a in arcs:
            a.shift(shift_vector)

        spiral_path = VMobject(color=C_GOLD, stroke_width=4.0)
        for a in arcs:
            spiral_path.append_vectorized_mobject(a)

        spiral_glow = spiral_path.copy().set_stroke(color=C_GOLD, width=12.0, opacity=0.25)

        # 7 цифр летят в свои квадраты
        morph_anims = []
        for i in range(len(fib_seq)):
            text_obj = saved_fib_numbers[i]
            target_pos = squares[i].get_center()
            target_scale = min(1.2, (fib_seq[i] * sq_scale) / (text_obj.height + 1e-5) * 0.45)
            morph_anims.append(
                text_obj.animate.move_to(target_pos).scale(target_scale)
            )

        self.play(*morph_anims, run_time=1.4, rate_func=rate_functions.ease_in_out_cubic)
        
        self.play(Create(squares), run_time=1.0)
        
        self.play(
            Create(spiral_glow, rate_func=linear),
            Create(spiral_path, rate_func=linear),
            run_time=2.5
        )
        self.wait(2.2)

        self.play(
            FadeOut(squares),
            FadeOut(spiral_path),
            FadeOut(spiral_glow),
            FadeOut(VGroup(*saved_fib_numbers)),
            run_time=1.2
        )
        self.wait(0.5)