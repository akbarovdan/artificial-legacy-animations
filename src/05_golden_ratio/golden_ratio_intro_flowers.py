from manim import *
import numpy as np

# Вертикальный формат Shorts 9:16
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class PhyllotaxisArchitect(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        # ---------------------------------------------------------
        # 1. ЦВЕТОВАЯ ПАЛИТРА И ДАННЫЕ ПРОЕКТА
        # ---------------------------------------------------------
        C_JADE      = "#A6E3A1"  # Нефритовый (Эхеверия)
        C_LAVENDER  = "#CBA6F7"  # Лаванда (Роза)
        C_PEACH     = "#FAB387"  # Персик (Георгина)
        C_GOLD      = "#F9E2AF"  # Золото (Георгина)
        C_SAPPHIRE  = "#89B4FA"  # Неоновый спиральный трекинг
        
        FONT_NAME   = "Montserrat"
        FONT_WEIGHT = "LIGHT"

        GOLDEN_ANGLE_DEG = 137.507764
        GOLDEN_ANGLE_RAD = np.radians(GOLDEN_ANGLE_DEG)

        # ---------------------------------------------------------
        # 2. МАТЕМАТИКА ВОГЕЛЯ И АРХИТЕКТУРА
        # ---------------------------------------------------------
        def get_vogel_points(N, c_scale):
            points = []
            for i in range(1, N + 1):
                r = c_scale * np.sqrt(i)
                theta = i * GOLDEN_ANGLE_RAD
                x = r * np.cos(theta)
                y = r * np.sin(theta)
                points.append((x, y, theta))
            return points

        def build_succulent_petal(length=1.0, color=C_JADE):
            # Исправленный суккулент: Однородный 3D массив векторов (x, y, z)
            # Вместо set_points_smoothly (капризный к углам), используем Polygon 
            # со скругленными гранями (make_smooth).
            points = [
                np.array([0.0, 0.0, 0.0]),
                np.array([length*0.2, length*0.4, 0.0]),
                np.array([length*0.9, 0.0, 0.0]),
                np.array([length*0.2, -length*0.4, 0.0])
            ]
            path = VMobject()
            path.set_points_smoothly(points)
            path.add_line_to(points[0]).make_smooth()
            path.set_fill(color, opacity=0.85).set_stroke("#041A18", width=1.5)
            return path

        def build_dahlia_petal(length=1.0, base_color=C_PEACH, tip_color=C_GOLD, rank_ratio=0.0):
            # Жесткий бриллиантовидный кристалл георгины
            col = interpolate_color(ManimColor(base_color), ManimColor(tip_color), rank_ratio)
            path = Polygon(
                [0.0, 0.0, 0.0],
                [length*0.1, length*0.25, 0.0],
                [length*0.8, 0.0, 0.0],
                [length*0.1, -length*0.25, 0.0],
                fill_color=col, fill_opacity=0.9, stroke_color=C_GOLD, stroke_width=0.8
            )
            return path

        def build_rose_sickle(length=1.0, color=C_LAVENDER):
            # Срез "Кочан капусты/роза Питера Стивенса" 
            crescent = AnnularSector(
                inner_radius=length * 0.1, outer_radius=length * 0.45, 
                angle=1.2*PI, start_angle=-0.6*PI, 
                fill_color=color, fill_opacity=0.75, stroke_width=1.0, stroke_color="#1E1E2E"
            )
            return crescent

        def create_phyllotaxis_cluster(N_elements, c_scale, shape_builder):
            pts_data = get_vogel_points(N_elements, c_scale)
            cluster_vg = VGroup()
            elements = []
            
            # Вложенность по Z (сзади вперед)
            for rank in range(N_elements, 0, -1):
                idx = rank - 1
                x, y, theta = pts_data[idx]
                pos = np.array([x, y, 0])
                
                ratio = rank / N_elements
                shape = shape_builder(length=0.4 + 1.1*np.sqrt(ratio), rank_ratio=ratio)
                shape.move_to(pos).rotate(theta, about_point=pos)
                elements.append(shape)
                
            cluster_vg.add(*elements) 
            return cluster_vg, elements, pts_data

        def spring_out_anim(target_group, dur_factor=1.0):
            """Анимация: рождение и выброс цветка радиально из R=0"""
            anims = []
            for target_shape in target_group:
                # Математическое начало "сингулярности"
                dummy = target_shape.copy().move_to(ORIGIN).scale(0.001).set_opacity(0)
                # target_shape запомнил свое "конечное взрослое место" 
                anims.append(Transform(dummy, target_shape, rate_func=rate_functions.ease_out_back))
                target_group.replace(target_shape, dummy)
            
            # Анимация "веера" (самые свежие вылетают быстрее старых)
            return LaggedStart(*anims, lag_ratio=0.015 / dur_factor) 


        # ---------------------------------------------------------
        # ФАЗА 1: КЛИНОВИДНЫЙ СУККУЛЕНТ И ЕГО ЗАВОДНОЙ РОСТ
        # ---------------------------------------------------------
        N_succ = 180
        scale_c_succ = 0.32
        
        # Инъекция зависимости
        succ_builder = lambda length, rank_ratio: build_succulent_petal(length, C_JADE)
        succ_cluster, succ_elements, _ = create_phyllotaxis_cluster(N_succ, scale_c_succ, succ_builder)
        
        # Эмоция "Чудо рождения природы"
        self.play(spring_out_anim(succ_cluster, dur_factor=0.8), run_time=3.5)
        self.wait(0.5)

        # Органическое угасание в темноте: рассыпается по ветру 
        blow_anims = [elem.animate.shift(elem.get_center()*0.3).scale(0.5).set_opacity(0) for elem in succ_cluster]
        self.play(AnimationGroup(*blow_anims), run_time=1.0)
        self.remove(succ_cluster)

        # ---------------------------------------------------------
        # ФАЗА 2: ВЗРЫВ ПЕРСИКОВОЙ ГЕОРГИНЫ И МАТЕМАТИЧЕСКИЙ РЕНДЕР
        # ---------------------------------------------------------
        N_dahlia = 250
        scale_c_dahl = 0.28
        
        dahl_builder = lambda length, rank_ratio: build_dahlia_petal(length, C_PEACH, C_GOLD, rank_ratio)
        dahl_cluster, dahl_elements, dahl_points = create_phyllotaxis_cluster(N_dahlia, scale_c_dahl, dahl_builder)

        # Цветок выплескивается из ядра
        self.play(spring_out_anim(dahl_cluster, dur_factor=1.2), run_time=3.0)

        # ПОКАЗЫВАЕМ ПАРАСТИХИИ (ВСТРЕЧНЫЕ ФИБОНАЧЧЕВЫ СПИРАЛИ)
        def build_spiral_arms(pts_list, fib_jump, max_N, line_col, width):
            family = VGroup()
            for start_i in range(1, fib_jump + 1):
                curr = start_i
                arc_points = []
                while curr <= max_N:
                    # Достаем математические сырые X, Y из вогеля 
                    x, y, _ = pts_list[curr - 1]
                    arc_points.append(np.array([x, y, 0]))
                    curr += fib_jump
                    
                if len(arc_points) > 1:
                    arm = VMobject().set_points_smoothly(arc_points).set_stroke(line_col, width)
                    family.add(arm)
            return family

        # Чудо Природы 1: Влево против часовой летит 21 спираль 
        spiral_ccw = build_spiral_arms(dahl_points, 21, N_dahlia, C_SAPPHIRE, 2.5)
        # Чудо Природы 2: Вправо по часовой ровно 13 спиралей (Фибоначчи)
        spiral_cw  = build_spiral_arms(dahl_points, 13, N_dahlia, C_GOLD, 2.5)
        
        # Гасим яркость Георгины, чтобы неоновый радар Фибоначчи светился ярче
        hud_opacity_darken = [elem.animate.set_fill(opacity=0.35).set_stroke(opacity=0.2) for elem in dahl_cluster]
        
        self.play(
            LaggedStart(
                *[Create(sp) for sp in spiral_cw],
                *[Create(sp) for sp in spiral_ccw],
                lag_ratio=0.03
            ),
            *hud_opacity_darken, 
            run_time=2.2,
            rate_func=rate_functions.ease_out_sine
        )
        self.wait(1.0)

        # ---------------------------------------------------------
        # ФАЗА 3: ЗОУМ-МАКРО СЪЕМКА НА ИДЕАЛЬНЫЙ УГОЛ РОЖДЕНИЯ 
        # ---------------------------------------------------------
        # Корень всего этого — математически нерушимый УГОЛ 137.5 градусов
        p1 = np.array([dahl_points[0][0], dahl_points[0][1], 0])  # n=1
        p2 = np.array([dahl_points[1][0], dahl_points[1][1], 0])  # n=2
        
        vector_1 = Line(ORIGIN, p1).set_stroke(C_JADE, 2.5)
        vector_2 = Line(ORIGIN, p2).set_stroke(C_JADE, 2.5)

        golden_angle_arc = ArcBetweenPoints(p1, p2, radius=1.0, color=C_PEACH)
        hud_label = Text("137.5°", font=FONT_NAME, weight=FONT_WEIGHT, color=C_PEACH, font_size=36)
        hud_label.move_to(ORIGIN + UP*1.0 + RIGHT*0.4)

        zoom_HUD_group = VGroup(vector_1, vector_2, golden_angle_arc, hud_label)

        # Схлопываем макро: камера ныряет внутрь Георгины прямо в n=0 (scale_камеры = 0.22)
        self.play(
            FadeOut(spiral_cw, spiral_ccw),
            dahl_cluster.animate.set_opacity(0.12),
            self.camera.frame.animate.scale(0.22).move_to(ORIGIN),
            run_time=1.8,
            rate_func=rate_functions.ease_in_out_cubic
        )

        # Высвечиваем две самых свежих лепестковых капсулы, где начинается спираль
        # -1 и -2 в Manim: потому что dahl_cluster собирался в обратном порядке N_dahlia -> 1
        last_e = dahl_cluster[-1] 
        scd_last_e = dahl_cluster[-2]
        
        self.play(
            last_e.animate.set_opacity(1.0).set_fill(C_GOLD).scale(1.15),
            scd_last_e.animate.set_opacity(1.0).set_fill(C_GOLD).scale(1.15),
            Create(vector_1),
            Create(vector_2),
            run_time=0.8
        )
        # Математическое "запечатывание" ответа — дуга в 137.5 
        self.play(Create(golden_angle_arc), FadeIn(hud_label), run_time=1.0)
        self.wait(1.5)

        # ---------------------------------------------------------
        # ФАЗА 4: КОСМОЛОГИЯ — ВСПЛЫТИЕ БОЖЕСТВЕННОЙ РОЗЫ ИЗ ОРБИТЫ
        # ---------------------------------------------------------
        self.play(
            FadeOut(dahl_cluster),
            FadeOut(zoom_HUD_group),
            # Камера взмывает обратно на гигантский зум X=1 (исходный 1.0)
            self.camera.frame.animate.scale(1.0/0.22).move_to(ORIGIN),
            run_time=1.2,
            rate_func=rate_functions.ease_in_out_cubic
        )

        N_rose = 150
        scale_c_rose = 0.45
        
        rose_builder = lambda length, rank_ratio: build_rose_sickle(length, C_LAVENDER)
        rose_cluster, _, _ = create_phyllotaxis_cluster(N_rose, scale_c_rose, rose_builder)

        # Вращающийся вихревой влёт гигантских лавандовых сфер 
        self.play(spring_out_anim(rose_cluster, dur_factor=0.6), run_time=3.5)

        # Медленное и торжественное планетарное прокручивание структуры по орбитам Фибоначчи
        self.play(rose_cluster.animate.rotate(-1.5*PI).scale(1.05), run_time=3.5, rate_func=smooth)

        # Финальная тьма. Исчезает в вечности 
        self.play(
            rose_cluster.animate.scale(4.0).set_opacity(0),
            run_time=2.2,
            rate_func=rate_functions.ease_in_cubic
        )
        self.wait(1.0)