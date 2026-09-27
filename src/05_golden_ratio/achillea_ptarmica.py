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
        C_WHITE    = "#CDD6F4"
        
        FONT_NAME   = "Montserrat"
        FONT_WEIGHT = "LIGHT"  

        # ---------------------------------------------------------
        # 2. АЛГОРИТМ ПЛАНАРНОГО ГРАФА (ИДЕАЛЬНОЕ ДЕРЕВО)
        # ---------------------------------------------------------
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

        leaves = []
        def dfs(node_id):
            if not nodes[node_id]["children"]:
                leaves.append(node_id)
            else:
                for child_id in nodes[node_id]["children"]:
                    dfs(child_id)
        dfs(0)
        
        dx_leaf = 0.85 
        for idx, leaf_id in enumerate(leaves):
            nodes[leaf_id]["x"] = idx * dx_leaf
            
        mean_x = sum(nodes[l]["x"] for l in leaves) / len(leaves)
        for leaf_id in leaves:
            nodes[leaf_id]["x"] -= mean_x

        dy_tier = 3.2 
        for n in nodes.values():
            n["y"] = n["tier"] * dy_tier

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

        def draw_flower(pos):
            flower = VGroup()
            for angle in np.linspace(0, 2 * PI, 6, endpoint=False):
                petal = Dot(pos + np.array([np.cos(angle), np.sin(angle), 0]) * 0.11, radius=0.065, color=C_FLOWER_P)
                flower.add(petal)
            center = Dot(pos, radius=0.08, color=C_FLOWER_C)
            flower.add(center)
            return flower

        # ---------------------------------------------------------
        # 3. АНИМАЦИЯ РОСТА ДЕРЕВА
        # ---------------------------------------------------------
        self.wait(0.4)
        root_node = nodes[0]
        root_pos = root_node["pos"]
        
        root_dot = Dot(root_pos, color=C_STEM, radius=0.1)
        self.play(FadeIn(root_dot, scale=0.5), run_time=0.4)

        all_tree_mobjects = VGroup(root_dot)
        saved_fib_numbers = []

        fib_num_root = Text("1", font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=42)
        fib_num_root.move_to(np.array([number_x_pos, root_pos[1], 0]))
        saved_fib_numbers.append(fib_num_root)
        
        self.play(FadeIn(fib_num_root, shift=RIGHT * 0.2), run_time=0.25)
        
        prev_pt_root = fib_num_root.get_right() + RIGHT * 0.2
        line_seg_root = DashedLine(prev_pt_root, root_pos, color=C_GUIDE, stroke_width=2.5, dashed_ratio=0.5)
        marker_root = Dot(root_pos, radius=0.12, color=C_PEACH)
        
        self.play(Create(line_seg_root), run_time=0.25, rate_func=linear)
        self.play(FadeIn(marker_root, scale=2.0), run_time=0.12)
        all_tree_mobjects.add(line_seg_root, marker_root)
        self.wait(0.15)

        for i in range(1, len(tiers)):
            tier_nodes = [nodes[nid] for nid in tiers[i]]
            y_level = tier_nodes[0]["pos"][1]
            is_last_tier = (i == len(tiers) - 1)
            
            branches = VGroup()
            for node in tier_nodes:
                start_pos = nodes[node["parent"]]["pos"]
                end_pos = node["pos"]
                thickness = max(1.5, 6.0 - i * 0.6)
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

        self.wait(1.0)

        # ---------------------------------------------------------
        # 4. ДЕРЕВО ЗАТУХАЕТ, ЦИФРЫ ВЫСТРАИВАЮТСЯ В РЯД
        # ---------------------------------------------------------
        orig_numbers_copies = VGroup(*[n.copy() for n in saved_fib_numbers])
        self.play(all_tree_mobjects.animate.set_opacity(0.15), run_time=0.8)

        # Расширенная последовательность (25 чисел)
        fib_seq_ext = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368, 75025]
        
        seq_texts_ext = VGroup(*[Text(str(val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46) for val in fib_seq_ext])
        seq_texts_ext.arrange(RIGHT, buff=0.5)
        
        # Центрируем первые 7
        center_of_first_7 = seq_texts_ext[:7].get_center()
        seq_texts_ext.shift(UP * 3.5 - center_of_first_7)

        self.play(
            *[ReplacementTransform(saved_fib_numbers[i], seq_texts_ext[i]) for i in range(7)], 
            FadeIn(seq_texts_ext[7:], shift=LEFT*0.3),
            run_time=1.5, 
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(0.5)

        # ---------------------------------------------------------
        # 5. МАТЕМАТИКА И МЕДЛЕННЫЙ СТАРТ
        # ---------------------------------------------------------
        frac_line = Line(LEFT*1.2, RIGHT*1.2, color=C_WHITE, stroke_width=3).move_to(DOWN * 0.5 + LEFT * 1.5)
        num_pos = frac_line.get_center() + UP * 0.6
        den_pos = frac_line.get_center() + DOWN * 0.6
        eq_sign = Text("=", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=46).next_to(frac_line, RIGHT, buff=0.4)
        
        box = SurroundingRectangle(VGroup(seq_texts_ext[0], seq_texts_ext[1]), color=C_GOLD, corner_radius=0.1, buff=0.15)
        self.play(Create(box))

        curr_num = Text("1", font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(num_pos)
        curr_den = Text("1", font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(den_pos)
        curr_res = Text("1.0", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GOLD, font_size=46).next_to(eq_sign, RIGHT, buff=0.4)
        
        self.play(
            FadeIn(frac_line), FadeIn(eq_sign),
            TransformFromCopy(seq_texts_ext[1], curr_num),
            TransformFromCopy(seq_texts_ext[0], curr_den),
            FadeIn(curr_res, shift=DOWN*0.2)
        )
        self.wait(0.5)

        # МЕДЛЕННЫЕ ШАГИ ДЛЯ ЧИТАЕМОСТИ (до 5/3)
        val_strs = ["2.0", "1.5", "1.666..."]
        for i in range(1, 4):
            new_box = SurroundingRectangle(VGroup(seq_texts_ext[i], seq_texts_ext[i+1]), color=C_GOLD, corner_radius=0.1, buff=0.15)
            new_num = Text(str(fib_seq_ext[i+1]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(num_pos)
            new_den = Text(str(fib_seq_ext[i]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(den_pos)
            new_res = Text(val_strs[i-1], font=FONT_NAME, weight=FONT_WEIGHT, color=C_GOLD, font_size=46).next_to(eq_sign, RIGHT, buff=0.4)
            
            # Четкий механический счетчик
            self.play(
                Transform(box, new_box),
                curr_num.animate.shift(UP*0.4).set_opacity(0),
                curr_den.animate.shift(UP*0.4).set_opacity(0),
                curr_res.animate.shift(UP*0.4).set_opacity(0),
                FadeIn(new_num, shift=UP*0.4),
                FadeIn(new_den, shift=UP*0.4),
                FadeIn(new_res, shift=UP*0.4),
                run_time=0.6
            )
            self.remove(curr_num, curr_den, curr_res)
            curr_num, curr_den, curr_res = new_num, new_den, new_res
            self.wait(0.4)

        # ---------------------------------------------------------
        # 6. БЕЗУПРЕЧНЫЙ ТАБЛО-СЛАЙД (БЕЗ КАШИ И ШЛЕЙФОВ)
        # ---------------------------------------------------------
        # Убираем старые текстовые объекты из движка, они нам больше не нужны
        self.remove(curr_num, curr_den, curr_res)

        # Создаем трекер - он будет указывать, на каком мы индексе в массиве
        tracker = ValueTracker(3.0)
        
        # Функция, которая вычисляет, куда должна сдвинуться длинная лента
        def get_shift():
            idx = int(tracker.get_value())
            # Центрируем рамку на текущих 2-х элементах
            target_center = VGroup(seq_texts_ext[idx], seq_texts_ext[idx+1]).get_center()
            return ORIGIN[0] - target_center[0]

        # Привязываем движение ленты и рамки к трекеру
        seq_texts_ext.add_updater(lambda m: m.set_x(m.get_x() + get_shift()))
        
        # Эти элементы (Счетчик) перерисовываются СТРОГО 1 раз за кадр. 
        # Никаких Transform, никаких шлейфов! Чистое цифровое табло.
        dynamic_num = always_redraw(lambda: Text(str(fib_seq_ext[int(tracker.get_value()) + 1]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(num_pos))
        dynamic_den = always_redraw(lambda: Text(str(fib_seq_ext[int(tracker.get_value())]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46).move_to(den_pos))
        
        # Динамический результат. Если трекер дошел до конца - выводим заветное число
        def get_res_text():
            val = tracker.get_value()
            idx = int(val)
            if val < 21.0:
                calc = fib_seq_ext[idx + 1] / fib_seq_ext[idx]
                return Text(f"{calc:.6f}...", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GOLD, font_size=46).next_to(eq_sign, RIGHT, buff=0.4)
            else:
                return Text("1.61803398...", font=FONT_NAME, weight="BOLD", color=C_GOLD, font_size=48).next_to(eq_sign, RIGHT, buff=0.4)

        dynamic_res = always_redraw(get_res_text)

        self.add(dynamic_num, dynamic_den, dynamic_res)

        # КИМЕНАТОГРАФИЧНЫЙ СЛАЙД
        # Лента летит до 22-го индекса (до десятков тысяч), постепенно замедляясь в конце
        self.play(
            tracker.animate.set_value(22.0),
            run_time=3.5,
            rate_func=rate_functions.ease_in_out_cubic
        )
        self.wait(1.5)

        # ---------------------------------------------------------
        # 7. ВОЗВРАЩЕНИЕ ЦВЕТКА (МЯГКИЙ ФИНАЛ)
        # ---------------------------------------------------------
        # Отключаем апдейтеры, чтобы чисто убрать объекты
        dynamic_num.clear_updaters()
        dynamic_den.clear_updaters()
        dynamic_res.clear_updaters()
        seq_texts_ext.clear_updaters()

        self.play(
            FadeOut(seq_texts_ext, shift=UP*0.2),
            FadeOut(box, scale=1.1),
            FadeOut(dynamic_num, shift=UP*0.2), 
            FadeOut(dynamic_den, shift=DOWN*0.2), 
            FadeOut(dynamic_res), 
            FadeOut(frac_line), 
            FadeOut(eq_sign),
            all_tree_mobjects.animate.set_opacity(1.0),
            run_time=1.2
        )
        
        # Возвращаем 7 оригинальных цифр на ветки
        self.play(*[FadeIn(n) for n in orig_numbers_copies], run_time=0.8)
        self.wait(2.0)

        self.play(
            FadeOut(Group(*self.mobjects), scale=1.05),
            run_time=1.5,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(0.5)