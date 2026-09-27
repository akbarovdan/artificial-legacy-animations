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
        C_STEM = "#A6E3A1"     
        C_LEAF = "#89DCEB"     
        C_FLOWER_C = "#F9E2AF" 
        C_FLOWER_P = "#CDD6F4" 
        C_PEACH = "#FAB387"    
        C_GUIDE = "#585B70"    
        C_GOLD = "#F9E2AF"     
        
        FONT_NAME = "Montserrat"
        FONT_WEIGHT = "LIGHT"  

        # ---------------------------------------------------------
        # 2. АЛГОРИТМ РОСТА
        # ---------------------------------------------------------
        tiers = [ [{"pos": np.array([0.0, 0.0, 0.0]), "is_m": False, "dir": 1, "parent": None}] ]
        
        max_tiers = 7 # Этажи: 1, 1, 2, 3, 5, 8, 13
        dy = 1.45 # Увеличено расстояние по вертикали
        dx_base = 2.8 # Увеличено расстояние по горизонтали

        for i in range(1, max_tiers + 1):
            prev_tier = tiers[-1]
            next_tier = []
            
            for p_idx, p_node in enumerate(prev_tier):
                x, y, _ = p_node["pos"]
                is_m = p_node["is_m"]
                d = p_node["dir"]

                if is_m:
                    pos_main = np.array([x - d * 0.35, y + dy, 0.0])
                    next_tier.append({"pos": pos_main, "is_m": True, "dir": -d, "parent": p_idx})
                    
                    pos_branch = np.array([x + d * dx_base * (0.68 ** i), y + dy, 0.0])
                    next_tier.append({"pos": pos_branch, "is_m": False, "dir": d, "parent": p_idx})
                else:
                    pos_main = np.array([x, y + dy, 0.0])
                    next_tier.append({"pos": pos_main, "is_m": True, "dir": d, "parent": p_idx})
                    
            tiers.append(next_tier)

        # ---------------------------------------------------------
        # 3. МАСШТАБИРОВАНИЕ ДЕРЕВА
        # ---------------------------------------------------------
        all_x = [node["pos"][0] for tier in tiers for node in tier]
        global_min_x = min(all_x)
        
        scale_factor = 11.5 / (max_tiers * dy)
        root_offset = DOWN * 6.8 + RIGHT * 0.8 

        for tier in tiers:
            for node in tier:
                node["pos"] = node["pos"] * scale_factor + root_offset

        number_x_pos = global_min_x * scale_factor + root_offset[0] - 1.2

        def draw_leaf(start, end, direction):
            midpoint = (start + end) / 2
            vec = end - start
            perp = np.array([-vec[1], vec[0], 0]) * direction * 0.15
            return Polygon(
                midpoint, midpoint + perp * 0.6 + vec * 0.25, midpoint + perp,
                color=C_LEAF, fill_opacity=0.6, stroke_width=1.0
            )

        def draw_flower(pos):
            flower = VGroup()
            for angle in np.linspace(0, 2*PI, 6, endpoint=False):
                petal = Dot(pos + np.array([np.cos(angle), np.sin(angle), 0]) * 0.12, radius=0.07, color=C_FLOWER_P)
                flower.add(petal)
            center = Dot(pos, radius=0.09, color=C_FLOWER_C)
            flower.add(center)
            return flower

        # ---------------------------------------------------------
        # 4. АНИМАЦИЯ ДЕРЕВА И УСКОРЯЮЩИЙСЯ СЧЕТЧИК
        # ---------------------------------------------------------
        self.wait(0.5)
        root_dot = Dot(tiers[0][0]["pos"], color=C_STEM, radius=0.1)
        self.play(FadeIn(root_dot, scale=0.5), run_time=0.5)

        all_tree_mobjects = VGroup(root_dot)
        saved_fib_numbers = []

        for i in range(1, len(tiers)):
            tier_nodes = tiers[i]
            prev_tier_nodes = tiers[i-1]
            y_level = tier_nodes[0]["pos"][1]
            
            branches = VGroup()
            leaves = VGroup()
            
            for node in tier_nodes:
                p_idx = node["parent"]
                start_pos = prev_tier_nodes[p_idx]["pos"]
                end_pos = node["pos"]
                
                thickness = max(1.5, 6.5 - i * 0.7)
                branches.add(Line(start_pos, end_pos, color=C_STEM, stroke_width=thickness))
                
                if node["is_m"] == False or i % 2 == 0:
                    leaves.add(draw_leaf(start_pos, end_pos, node["dir"]))
            
            all_tree_mobjects.add(branches, leaves)
            self.play(Create(branches, rate_func=rate_functions.ease_out_quad), FadeIn(leaves, scale=0.5), run_time=0.8)
            
            sorted_nodes = sorted(tier_nodes, key=lambda n: n["pos"][0])
            
            fib_number = Text(str(len(sorted_nodes)), font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=46)
            fib_number.move_to(np.array([number_x_pos, y_level, 0]))
            saved_fib_numbers.append(fib_number)
            
            self.play(FadeIn(fib_number, shift=RIGHT * 0.2), run_time=0.3)
            
            prev_pt = fib_number.get_right() + RIGHT * 0.2
            guides_and_dots = VGroup()
            
            # --- УМНАЯ СКОРОСТЬ СЧЕТА ---
            anims = []
            for node in sorted_nodes:
                target_pt = node["pos"]
                line_seg = DashedLine(prev_pt, target_pt, color=C_GUIDE, stroke_width=2.5, dashed_ratio=0.5)
                node_dot = Dot(target_pt, radius=0.14, color=C_PEACH)
                guides_and_dots.add(line_seg, node_dot)
                
                if i <= 2:
                    # Медленный пошаговый счет для ярусов 1 и 2
                    self.play(Create(line_seg), run_time=0.3, rate_func=linear)
                    self.play(FadeIn(node_dot, scale=2.5), run_time=0.15)
                else:
                    # Быстрый счет для высоких ярусов
                    anims.append(Succession(
                        Create(line_seg, run_time=0.1),
                        FadeIn(node_dot, scale=2.5, run_time=0.05)
                    ))
                
                prev_pt = target_pt
            
            if i > 2:
                # Запуск цепной реакции точек
                self.play(LaggedStart(*anims, lag_ratio=0.15))
            
            all_tree_mobjects.add(guides_and_dots)
            self.wait(0.2)

        flowers = VGroup()
        for node in tiers[-1]:
            flowers.add(draw_flower(node["pos"]))
        all_tree_mobjects.add(flowers)
            
        self.play(LaggedStart(*[FadeIn(fl, scale=0.2) for fl in flowers], lag_ratio=0.1), run_time=1.5)
        self.wait(1.5)

        # ---------------------------------------------------------
        # 5. МАГИЧЕСКИЙ ПЕРЕХОД К ГЕОМЕТРИИ
        # ---------------------------------------------------------
        # Дерево растворяется, цифры остаются
        self.play(FadeOut(all_tree_mobjects), run_time=1.0)
        self.wait(0.5)

        # ---------------------------------------------------------
        # 6. ИДЕАЛЬНЫЕ КВАДРАТЫ ФИБОНАЧЧИ
        # ---------------------------------------------------------
        fib_seq = [1, 1, 2, 3, 5, 8, 13]
        sq_scale = 0.35 
        
        squares = VGroup()
        arcs = VGroup()
        
        # Строгая математическая последовательность привязки квадратов Фибоначчи
        dirs = [LEFT, DOWN, RIGHT, UP]
        aligns = [UP, LEFT, DOWN, RIGHT]
        
        # Центры и углы для Золотой Спирали (внутри квадратов)
        centers = [DR, UR, UL, DL]
        start_angles = [PI/2, PI, -PI/2, 0]
        
        for i, val in enumerate(fib_seq):
            side = val * sq_scale
            sq = Square(side_length=side, color=C_GUIDE, stroke_width=2.0)
            
            if i == 0:
                sq.move_to(ORIGIN + DOWN * 1.5 + RIGHT * 1.5)
            else:
                # Привязываем новый квадрат ко ВСЕЙ группе предыдущих квадратов!
                dir_idx = (i - 1) % 4
                sq.next_to(squares, dirs[dir_idx], buff=0)
                sq.align_to(squares, aligns[dir_idx])

            squares.add(sq)
            
            # Строим спираль
            arc_idx = i % 4
            arc_center = sq.get_corner(centers[arc_idx])
            start_angle = start_angles[arc_idx]
            
            arc = Arc(
                radius=side,
                start_angle=start_angle,
                angle=PI/2,
                arc_center=arc_center,
                color=C_GOLD,
                stroke_width=4.0
            )
            arcs.add(arc)

        # Анимация: Цифры летят в центры своих квадратов
        morph_anims = []
        for i, text_obj in enumerate(saved_fib_numbers):
            target_scale = min(1.0, (fib_seq[i] * sq_scale) / text_obj.height * 0.4)
            morph_anims.append(
                text_obj.animate.move_to(squares[i].get_center()).scale(target_scale)
            )

        self.play(*morph_anims, run_time=1.5, rate_func=rate_functions.ease_in_out_cubic)
        
        # Вырисовываются квадраты
        self.play(Create(squares), run_time=1.5)
        
        # Финальный аккорд: Идеальная Золотая Спираль
        self.play(Create(arcs), run_time=2.5, rate_func=linear)
        self.wait(2.0)

        # Финальный уход в темноту
        self.play(
            FadeOut(squares),
            FadeOut(arcs),
            FadeOut(VGroup(*saved_fib_numbers)),
            run_time=1.2
        )