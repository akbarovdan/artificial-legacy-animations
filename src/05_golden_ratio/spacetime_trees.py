from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class SpacetimeTrees(ThreeDScene):
    def construct(self):
        # ---------------------------------------------------------
        # 1. ПАЛИТРА И НАСТРОЙКИ СЦЕНЫ
        # ---------------------------------------------------------
        self.camera.background_color = "#000000"
        
        PALETTES = {
            "MAPLE": ["#FAB387", "#F38BA8", "#E64553"],   # Персиковый -> Багровый
            "PINE":  ["#94E2D5", "#A6E3A1", "#40A02B"],   # Бирюзовый -> Изумрудный
            "FIBO":  ["#CBA6F7", "#89B4FA", "#F9E2AF"]    # Лавандовый -> Золотой
        }

        LEAF_COLORS = {
            "MAPLE": "#F5C2E7", # Пышные розовые листья
            "PINE":  "#A6E3A1", # Изумрудные иголки
            "FIBO":  "#FFFFFF"  # Золотое свечение
        }

        # Камера отдалена, чтобы показать деревья в полный рост
        self.set_camera_orientation(phi=72 * DEGREES, theta=-45 * DEGREES, zoom=0.68)
        self.begin_ambient_camera_rotation(rate=0.25)

        # ---------------------------------------------------------
        # 2. ФИЗИЧЕСКИЙ УЗЕЛ ДЕРЕВА
        # ---------------------------------------------------------
        class Node:
            def __init__(self, pos, vel, gen, state=None, is_leaf=False):
                self.pos = np.array(pos, dtype=float)
                self.vel = np.array(vel, dtype=float)
                self.gen = gen         
                self.age = 0           
                self.state = state or {} 
                self.active = True     
                self.is_leaf = is_leaf 

        def get_gradient_color(palette_name, progress):
            pal = PALETTES[palette_name]
            n = len(pal) - 1
            idx = min(int(progress * n), n - 1)
            local_p = (progress * n) - idx
            return interpolate_color(ManimColor(pal[idx]), ManimColor(pal[idx+1]), local_p)

        # ---------------------------------------------------------
        # 3. УНИВЕРСАЛЬНЫЙ ДВИЖОК РОСТА (ТОЛЬКО ИСКРЫ И СВЕТ)
        # ---------------------------------------------------------
        def run_tree_simulation(tree_type):
            np.random.seed(42) # Фиксируем сид для предсказуемой красоты

            z_start = -7.5
            z_end   = 7.5
            steps   = 130
            dz      = (z_end - z_start) / steps
            
            GOLDEN_ANGLE = 137.507764 * DEGREES

            start_state = {}
            if tree_type == "PINE":
                start_state = {'theta': 0}
            elif tree_type == "FIBO":
                start_state = {'theta': 0, 'mature': True}

            # Стартовый импульс
            active_nodes = [Node([0, 0, z_start], [0, 0, dz * 1.5], 0, start_state)]

            tree_mobjects = VGroup()
            current_z = z_start

            for s in range(steps):
                next_z = current_z + dz
                progress = s / steps
                
                new_lines = VGroup()
                live_points = VGroup()
                new_nodes_to_add = []

                for node in active_nodes:
                    if not node.active:
                        continue

                    old_pos = node.pos.copy()
                    node.pos += node.vel
                    node.age += 1

                    # Отрисовка
                    if node.is_leaf:
                        color = LEAF_COLORS[tree_type]
                        thickness = 2.5
                        dot_radius = 0.08
                        glow_opacity = 0.8 
                    else:
                        color = get_gradient_color(tree_type, progress)
                        thickness = max(1.5, 7.0 - node.gen * 1.0) # Толстый ствол, тонкие ветки
                        dot_radius = 0.06
                        glow_opacity = 0.2

                    core = Line(old_pos, node.pos, stroke_width=thickness, color=color)
                    glow = Line(old_pos, node.pos, stroke_width=thickness * 3.5, color=color, stroke_opacity=glow_opacity)
                    new_lines.add(VGroup(glow, core))
                    live_points.add(Dot(node.pos, radius=dot_radius, color=color))

                    # ==========================================
                    # ЛОГИКА 1: КЛЕН (MAPLE) - Лиственное дерево
                    # ==========================================
                    if tree_type == "MAPLE":
                        if node.is_leaf:
                            if node.age > 4: node.active = False
                        else:
                            # Ветви загибаются в купол (боковое сопротивление)
                            node.vel[0] *= 0.88
                            node.vel[1] *= 0.88

                            # Ствол растет долго, ветки ветвятся быстрее
                            branching_age = 22 if node.gen == 0 else 10
                            
                            if node.age >= branching_age:
                                if node.gen < 6:
                                    # Раздвоение крест-накрест
                                    angle_offset = node.gen * (np.pi / 2) 
                                    rot = angle_offset + np.random.uniform(-0.3, 0.3)
                                    spread = 0.35 * (0.80 ** node.gen) # Разлет ветвей
                                    
                                    axis1 = np.array([np.cos(rot), np.sin(rot), 0])
                                    
                                    # Обе ветви получают сильный боковой импульс
                                    v1 = node.vel * 0.7 + axis1 * spread; v1[2] = dz * 1.2
                                    v2 = node.vel * 0.7 - axis1 * spread; v2[2] = dz * 1.2
                                    
                                    new_nodes_to_add.extend([Node(node.pos, v1, node.gen + 1), Node(node.pos, v2, node.gen + 1)])
                                    node.active = False
                                else:
                                    # Густая крона листьев
                                    for _ in range(3):
                                        v_leaf = np.array([np.random.uniform(-0.1, 0.1), np.random.uniform(-0.1, 0.1), dz * 0.6])
                                        new_nodes_to_add.append(Node(node.pos, node.vel * 0.3 + v_leaf, node.gen + 1, is_leaf=True))
                                    node.active = False

# ==========================================
                    # ЛОГИКА 2: СОСНА (PINE) - Конус / Елочка
                    # ==========================================
                    elif tree_type == "PINE":
                        if node.gen == 0:
                            # Уменьшаем скорость ствола (0.95 вместо 1.2), чтобы высота совпадала с остальными
                            node.vel = np.array([0, 0, dz * 1.1]) 
                            if node.age % 14 == 0 and node.age > 10 and node.age < steps - 15:
                                # Выстреливает кольцо ветвей
                                num_branches = 5
                                node.state['theta'] += np.pi / 5 + np.random.uniform(-0.1, 0.1)
                                
                                # Чем выше ярус, тем короче ветки (коническая форма)
                                height_ratio = node.age / steps
                                branch_speed = 0.35 * (1.0 - height_ratio * 0.85)
                                
                                for i in range(num_branches):
                                    th = node.state['theta'] + i * (2 * np.pi / num_branches)
                                    # Лапы растут горизонтально
                                    v_side = np.array([np.cos(th) * branch_speed, np.sin(th) * branch_speed, dz * 0.2])
                                    new_nodes_to_add.append(Node(node.pos, v_side, node.gen + 1))
                        else:
                            if node.is_leaf:
                                if node.age > 3: node.active = False
                            elif node.age > 14 * (0.8 ** node.gen): 
                                # Рождение мелких веточек и иголок на лапах
                                if node.gen < 2:
                                    th_base = np.arctan2(node.vel[1], node.vel[0])
                                    for sign in [-1, 1]:
                                        th = th_base + sign * np.pi/3
                                        v_sub = np.array([np.cos(th)*0.08, np.sin(th)*0.08, dz*0.3])
                                        new_nodes_to_add.append(Node(node.pos, v_sub, node.gen + 1))
                                    node.active = False
                                else:
                                    for _ in range(3):
                                        v_leaf = np.array([np.random.uniform(-0.06, 0.06), np.random.uniform(-0.06, 0.06), dz * 0.8])
                                        new_nodes_to_add.append(Node(node.pos, node.vel * 0.3 + v_leaf, node.gen + 1, is_leaf=True))
                                    node.active = False
                            else:
                                # Ветки сначала падают (гравитация), кончики смотрят вверх
                                node.vel[0] *= 0.96
                                node.vel[1] *= 0.96
                                node.vel[2] += 0.005 # Тяга к свету
                                
                    # ==========================================
                    # ЛОГИКА 3: ФИБОНАЧЧИ (FIBO) 
                    # ==========================================
                    elif tree_type == "FIBO":
                        if node.is_leaf:
                            if node.age > 4: node.active = False
                        else:
                            # Сильно гасим боковую скорость, чтобы дерево было компактным
                            node.vel[0] *= 0.85
                            node.vel[1] *= 0.85
                            # Мягкое торможение роста вверх
                            node.vel[2] *= 0.98

                            # ГЛАВНЫЙ ФИКС: Если время симуляции заканчивается, макушка и все пустые концы взрываются пышной листвой!
                            if s > steps - 6:
                                for _ in range(4): # На макушке делаем 4 листика для пышности
                                    v_leaf = np.array([np.random.uniform(-0.05, 0.05), np.random.uniform(-0.05, 0.05), dz * 0.6])
                                    new_nodes_to_add.append(Node(node.pos, node.vel * 0.4 + v_leaf, node.gen + 1, is_leaf=True))
                                node.active = False
                                continue

                            branching_age = 15 if node.gen == 0 else 10
                            
                            if node.age >= branching_age:
                                if node.gen < 5: # Снизили лимит, чтобы боковые ветки тоже успели обрасти
                                    if node.state['mature']:
                                        th = node.state['theta']
                                        spawn_dir = np.array([np.cos(th), np.sin(th), 0])
                                        
                                        v_side = node.vel * 0.5 + spawn_dir * 0.12
                                        v_side[2] = dz * 0.75
                                        
                                        new_nodes_to_add.append(Node(node.pos, v_side, node.gen + 1, {'theta': 0, 'mature': False}))
                                        node.state['theta'] += GOLDEN_ANGLE
                                        
                                        node.vel[0] -= spawn_dir[0] * 0.06
                                        node.vel[1] -= spawn_dir[1] * 0.06
                                        node.vel[2] *= 0.92
                                        
                                        node.age = 0
                                    else:
                                        node.state['mature'] = True
                                        node.age = 0
                                else:
                                    # Обычные листья на концах боковых веток
                                    for _ in range(3):
                                        v_leaf = np.array([np.random.uniform(-0.04, 0.04), np.random.uniform(-0.04, 0.04), dz * 0.5])
                                        new_nodes_to_add.append(Node(node.pos, node.vel * 0.4 + v_leaf, node.gen + 1, is_leaf=True))
                                    node.active = False

                active_nodes.extend(new_nodes_to_add)
                active_nodes = [n for n in active_nodes if n.active]
                tree_mobjects.add(new_lines)

                # Отрисовка шага (без плоскости)
                self.play(
                    Create(new_lines),
                    FadeIn(live_points, run_time=0.04),
                    run_time=0.07, 
                    rate_func=linear
                )
                self.remove(live_points)
                current_z = next_z

            self.wait(1.5)
            self.play(
                FadeOut(tree_mobjects, scale=1.05),
                run_time=1.2,
                rate_func=rate_functions.ease_in_cubic
            )
            self.wait(0.5)

        # ---------------------------------------------------------
        # 4. РЕЖИССУРА: 3 ПАТТЕРНА
        # ---------------------------------------------------------
        run_tree_simulation("MAPLE")
        run_tree_simulation("PINE")
        run_tree_simulation("FIBO")