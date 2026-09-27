from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16 (1080x1920)
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
        # 2. АЛГОРИТМ ПЛАНАРНОГО ГРАФА ДЕРЕВА
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

        self.wait(1.2)

        # ---------------------------------------------------------
        # 4. ПОЛНОЕ ЗАТЕМНЕНИЕ В ЧЕРНУЮ ПУСТОТУ (НА 100%)
        # ---------------------------------------------------------
        orig_numbers_copies = VGroup(*[n.copy() for n in saved_fib_numbers])
        
        self.play(
            FadeOut(all_tree_mobjects),
            FadeOut(VGroup(*saved_fib_numbers)),
            run_time=0.8
        )
        self.wait(0.3)

        # ---------------------------------------------------------
        # 5. ВЕРТИКАЛЬНАЯ ЛЕНТА (26 ЧИСЕЛ)
        # ---------------------------------------------------------
        fib_vals = [1, 1]
        for _ in range(24):
            fib_vals.append(fib_vals[-1] + fib_vals[-2])

        col_x = -2.7
        row_dy = 0.95

        reel_mobjects = []
        for idx, val in enumerate(fib_vals):
            txt = Text(str(val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=34)
            y_pos = -0.475 + idx * row_dy
            txt.move_to(np.array([col_x, y_pos, 0]))
            reel_mobjects.append(txt)

        reel_group = VGroup(*reel_mobjects)

        # Контроллер прозрачности для плавного растворения ленты
        reel_fade_mult = ValueTracker(1.0)

        def reel_focus_updater(mob):
            mult = reel_fade_mult.get_value()
            for item in mob:
                dist = abs(item.get_center()[1])
                if dist < 0.65:
                    item.set_opacity(1.0 * mult)
                elif dist < 1.3:
                    t = (dist - 0.65) / 0.65
                    item.set_opacity((1.0 - 0.82 * t) * mult)
                elif dist < 3.8:
                    item.set_opacity(0.18 * mult)
                elif dist < 5.0:
                    t = (dist - 3.8) / 1.2
                    item.set_opacity(max(0.0, 0.18 * (1.0 - t)) * mult)
                else:
                    item.set_opacity(0.0)

        reel_group.add_updater(reel_focus_updater)

        # Дробь
        frac_x = -0.4
        frac_line = Line(LEFT * 1.05, RIGHT * 1.05, color=C_WHITE, stroke_width=2.5).move_to(np.array([frac_x, 0.0, 0]))
        num_pos = np.array([frac_x, 0.6, 0])
        den_pos = np.array([frac_x, -0.6, 0])
        
        eq_sign = Text("=", font=FONT_NAME, weight=FONT_WEIGHT, color=C_WHITE, font_size=38).next_to(frac_line, RIGHT, buff=0.3)
        res_anchor = eq_sign.get_right() + RIGHT * 0.3

        curr_num = Text(str(fib_vals[1]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(num_pos)
        curr_den = Text(str(fib_vals[0]), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(den_pos)
        curr_res = Text("= 1.0", font=FONT_NAME, weight=FONT_WEIGHT, color=C_GOLD, font_size=38)
        curr_res.move_to(res_anchor, aligned_edge=LEFT)

        self.play(
            FadeIn(reel_group),
            FadeIn(frac_line),
            FadeIn(eq_sign),
            FadeIn(curr_num),
            FadeIn(curr_den),
            FadeIn(curr_res),
            run_time=0.8
        )
        self.wait(0.4)

        # ---------------------------------------------------------
        # 6. ЧЕТКИЙ ХОД ВЫЧИСЛЕНИЙ (ШАГИ 1..17)
        # ---------------------------------------------------------
        step_times = [
            0.55, 0.50, 0.45,                     # 1..3 (медленно)
            0.38, 0.34, 0.30, 0.26, 0.22, 0.19,  # 4..9
            0.16, 0.14, 0.13, 0.12, 0.11, 0.10,  # 10..15
            0.09, 0.08                            # 16..17
        ]

        for step in range(1, 18):
            t_dur = step_times[step - 1]
            num_val = fib_vals[step + 1]
            den_val = fib_vals[step]
            ratio = num_val / den_val

            next_num = Text(str(num_val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(num_pos)
            next_den = Text(str(den_val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(den_pos)

            if step < 3:
                res_str = f"= {ratio:.1f}"
            elif step < 5:
                res_str = f"≈ {ratio:.3f}..."
            elif step < 16:
                res_str = f"≈ {ratio:.5f}..."
            else:
                # Фиксация строгого значения
                res_str = "≈ 1.618..."

            next_res = Text(res_str, font=FONT_NAME, weight=FONT_WEIGHT, color=C_GOLD, font_size=38)
            next_res.move_to(res_anchor, aligned_edge=LEFT)

            self.play(
                reel_group.animate.shift(DOWN * row_dy),
                curr_num.animate.shift(DOWN * 0.25).set_opacity(0),
                curr_den.animate.shift(DOWN * 0.25).set_opacity(0),
                curr_res.animate.shift(DOWN * 0.15).set_opacity(0),
                FadeIn(next_num, shift=DOWN * 0.25),
                FadeIn(next_den, shift=DOWN * 0.25),
                FadeIn(next_res, shift=DOWN * 0.15),
                run_time=t_dur,
                rate_func=linear
            )

            self.remove(curr_num, curr_den, curr_res)
            curr_num, curr_den, curr_res = next_num, next_den, next_res

        # ---------------------------------------------------------
        # 7. НЕПРЕРЫВНЫЙ ПЕРЕСЧЕТ С УХОДОМ В FADE OUT + ВЫПЛЫВАНИЕ В ЦЕНТР
        # ---------------------------------------------------------
        # Пересчет ПРОДОЛЖАЕТСЯ еще 6 шагов (до 75025/46368), но на каждом шаге
        # вся математическая обвязка становится всё прозрачнее и прозрачнее,
        # а число ≈ 1.618... плавно выплывает строго в центр экрана!
        
        fade_opacities = [0.70, 0.48, 0.30, 0.16, 0.06, 0.0]
        start_res_pos = curr_res.get_center()
        
        # Смещение к центру и масштабирование за 6 микро-шагов
        step_shift = (ORIGIN - start_res_pos) / 6.0
        step_scale = (1.4) ** (1.0 / 6.0)

        for j in range(6):
            step = 18 + j
            num_val = fib_vals[step + 1]
            den_val = fib_vals[step]
            op = fade_opacities[j]

            next_num = Text(str(num_val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(num_pos)
            next_den = Text(str(den_val), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=38).move_to(den_pos)
            next_num.set_opacity(op)
            next_den.set_opacity(op)

            # Числа продолжают двигаться и считать, фон гаснет, число плывет в центр
            self.play(
                reel_group.animate.shift(DOWN * row_dy),
                reel_fade_mult.animate.set_value(op),
                frac_line.animate.set_opacity(op),
                eq_sign.animate.set_opacity(op),
                curr_num.animate.shift(DOWN * 0.25).set_opacity(0),
                curr_den.animate.shift(DOWN * 0.25).set_opacity(0),
                FadeIn(next_num, shift=DOWN * 0.25),
                FadeIn(next_den, shift=DOWN * 0.25),
                curr_res.animate.shift(step_shift).scale(step_scale),
                run_time=0.11,
                rate_func=linear
            )

            self.remove(curr_num, curr_den)
            curr_num, curr_den = next_num, next_den

        # Удаляем окончательно растворившийся аппарат
        reel_group.clear_updaters()
        self.remove(reel_group, frac_line, eq_sign, curr_num, curr_den)

        # Выравниваем число строго в абсолютный центр ORIGIN
        curr_res.move_to(ORIGIN)

        # ФИКСАЦИЯ НА ЧИСТОМ ЧЕРНОМ ФОНЕ СТРОГО НА 2 СЕКУНДЫ
        self.wait(2.0)

        # Число плавно исчезает
        self.play(FadeOut(curr_res), run_time=0.5)
        self.wait(0.2)

        # ---------------------------------------------------------
        # 8. ВОЗВРАЩЕНИЕ ЦВЕТКА И ФИНАЛ СЦЕНЫ
        # ---------------------------------------------------------
        # Дерево расцветает в 100% яркости
        self.play(FadeIn(all_tree_mobjects), run_time=1.0)
        self.play(*[FadeIn(n) for n in orig_numbers_copies], run_time=0.6)
        self.wait(2.0)

        # Финальный уход сцены в темноту
        self.play(
            FadeOut(Group(*self.mobjects), scale=1.05),
            run_time=1.2,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(0.4)