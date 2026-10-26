from manim import *
import numpy as np

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = BLACK

class ConwayRulesAndLogic(MovingCameraScene):
    def construct(self):
        # --- ПАЛИТРА CATPPUCCIN ---
        COLOR_ALIVE  = "#89B4FA"  # Спокойный голубой (Живые соседи)
        COLOR_BORN   = "#A6E3A1"  # Мятно-зеленый (Рождение)
        COLOR_DIE    = "#F38BA8"  # Кораллово-красный (Смерть)
        COLOR_EMPTY  = "#11111B"  # Темный фон пустой клетки
        COLOR_BORDER = "#313244"  # Контур сетки
        TEXT_COLOR   = "#CDD6F4"  # Светлый текст

        # Хелпер для создания мини-сетки 3x3
        def build_cell_grid(center_point, active_neighbors, center_alive=True):
            group = VGroup()
            cells = {}
            for r in [-1, 0, 1]:
                for c in [-1, 0, 1]:
                    pos = center_point + np.array([c * 0.52, -r * 0.52, 0])
                    is_active = (r, c) in active_neighbors or ((r, c) == (0, 0) and center_alive)
                    sq = Square(
                        side_length=0.46,
                        stroke_color=COLOR_BORDER,
                        stroke_width=1.5,
                        fill_color=COLOR_ALIVE if is_active else COLOR_EMPTY,
                        fill_opacity=1.0 if is_active else 0.5
                    ).move_to(pos)
                    cells[(r, c)] = sq
                    group.add(sq)
            return group, cells

        # =========================================================
        # 1. UNDERPOPULATION (< 2) — ВВЕРХУ ЭКРАНА
        # =========================================================
        pos_1 = UP * 4.6
        title_1 = Text(
            "Underpopulation (<2)", 
            font="Montserrat", 
            weight="LIGHT", 
            font_size=32, 
            color=TEXT_COLOR
        ).move_to(pos_1 + UP * 1.3)

        # 1 сосед справа (0, 1)
        grid_1, cells_1 = build_cell_grid(pos_1, active_neighbors=[(0, 1)], center_alive=True)

        self.play(FadeIn(title_1, shift=DOWN), FadeIn(grid_1), run_time=0.8)

        # Центральная клетка краснеет и гаснет
        center_1 = cells_1[(0, 0)]
        self.play(center_1.animate.set_fill(COLOR_DIE), run_time=0.4)
        self.play(
            center_1.animate.set_fill(COLOR_EMPTY, opacity=0.5).set_stroke(COLOR_BORDER),
            run_time=0.5
        )

        # Пауза 0.5 секунды
        self.wait(0.5)

        # =========================================================
        # 2. OVERCROWDING (> 3) — ПО ЦЕНТРУ ЭКРАНА
        # =========================================================
        pos_2 = ORIGIN + DOWN * 0.2
        title_2 = Text(
            "Overcrowding (>3)", 
            font="Montserrat", 
            weight="LIGHT", 
            font_size=32, 
            color=TEXT_COLOR
        ).move_to(pos_2 + UP * 1.3)

        # 4 соседа: сверху, снизу, слева, справа
        grid_2, cells_2 = build_cell_grid(
            pos_2, 
            active_neighbors=[(-1, 0), (1, 0), (0, -1), (0, 1)], 
            center_alive=True
        )

        self.play(FadeIn(title_2, shift=DOWN), FadeIn(grid_2), run_time=0.8)

        # Центральная клетка краснеет и гаснет от перенаселения
        center_2 = cells_2[(0, 0)]
        self.play(center_2.animate.set_fill(COLOR_DIE), run_time=0.4)
        self.play(
            center_2.animate.set_fill(COLOR_EMPTY, opacity=0.5).set_stroke(COLOR_BORDER),
            run_time=0.5
        )

        # Пауза 0.5 секунды
        self.wait(0.5)

        # =========================================================
        # 3. REPRODUCTION (= 3) — ВНИЗУ ЭКРАНА
        # =========================================================
        pos_3 = DOWN * 5.0
        title_3 = Text(
            "Reproduction (=3)", 
            font="Montserrat", 
            weight="LIGHT", 
            font_size=32, 
            color=TEXT_COLOR
        ).move_to(pos_3 + UP * 1.3)

        # 3 соседа вокруг, центр ИЗНАЧАЛЬНО ПУСТОЙ
        grid_3, cells_3 = build_cell_grid(
            pos_3, 
            active_neighbors=[(-1, 0), (0, 1), (1, 0)], 
            center_alive=False
        )

        self.play(FadeIn(title_3, shift=DOWN), FadeIn(grid_3), run_time=0.8)

        # Пустое место вспыхивает сочным мятно-зеленым (рождение новой клетки)
        center_3 = cells_3[(0, 0)]
        self.play(
            center_3.animate.set_fill(COLOR_BORN, opacity=1.0).set_stroke(COLOR_BORN),
            run_time=0.5
        )

        # Финальная фиксация всех 3 правил на одном экране
        self.wait(2.5)

        # =========================================================
        # 4. ЗАТУХАНИЕ ЭКРАНА (ПЕРЕХОД В ТЕМНОТУ)
        # =========================================================
        # Полностью убираем предыдущие 3 правила с экрана
        self.play(
            FadeOut(VGroup(
                title_1, grid_1, 
                title_2, grid_2, 
                title_3, grid_3
            )),
            run_time=0.8
        )
        self.wait(0.3)

        # Создаем единую чистую сетку в центре без надписей
        dark_grid = VGroup()
        grid_cells = {}
        for r in range(-4, 5):
            for c in range(-4, 5):
                pos = np.array([c * 0.52, -r * 0.52, 0])
                sq = Square(
                    side_length=0.46,
                    stroke_color=COLOR_BORDER,
                    stroke_width=1.0,
                    fill_color=COLOR_EMPTY,
                    fill_opacity=0.35
                ).move_to(pos)
                grid_cells[(r, c)] = sq
                dark_grid.add(sq)

        self.play(FadeIn(dark_grid), run_time=0.6)
        self.wait(0.3)

        # =========================================================
        # 5. СЦЕНА 1: УЗОР ПОЛНОСТЬЮ ВЫМИРАЕТ (DIES OUT)
        # =========================================================
        # Точки появляются поочередно, будто их прокликали мышкой
        extinct_coords = [(-2, -2), (-1, -1), (0, 0), (1, 1), (2, 2)]
        extinct_cells = []

        for r, c in extinct_coords:
            cell = grid_cells[(r, c)]
            # Клетка вспыхивает голубым при клике
            self.play(
                cell.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE),
                run_time=0.15
            )
            extinct_cells.append(cell)
        self.wait(0.4)

        # Шаг 1 симуляции: крайние клетки погибают (краснеют и гаснут)
        c_die_1 = [grid_cells[(-2, -2)], grid_cells[(2, 2)]]
        self.play(*[c.animate.set_fill(COLOR_DIE) for c in c_die_1], run_time=0.25)
        self.play(
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in c_die_1],
            run_time=0.35
        )

        # Шаг 2 симуляции: следующие две погибают
        c_die_2 = [grid_cells[(-1, -1)], grid_cells[(1, 1)]]
        self.play(*[c.animate.set_fill(COLOR_DIE) for c in c_die_2], run_time=0.25)
        self.play(
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in c_die_2],
            run_time=0.35
        )

        # Шаг 3: последняя клетка погибает в полной темноте
        c_die_3 = grid_cells[(0, 0)]
        self.play(c_die_3.animate.set_fill(COLOR_DIE), run_time=0.25)
        self.play(
            c_die_3.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER),
            run_time=0.35
        )

        # ТЕМНОТА: 0.5 секунды абсолютной тишины и пустоты
        self.wait(0.5)

        # =========================================================
        # 6. СЦЕНА 2: ЗАСТЫВАНИЕ В БЛОК И ВЕЧНУЮ МИГАЛКУ (STATIC LOOP)
        # =========================================================
        # Точки прокликиваются поочередно:
        # Слева: линия из 3 клеток (Blinker)
        # Справа: L-образная форма из 3 клеток (заготовка под вечный блок)
        loop_coords = [
            (-1, -2), (-1, -1), (-1, 0),  # Мигалка (слева)
            (1, 1), (2, 1), (1, 2)         # Уголок блока (справа)
        ]

        for r, c in loop_coords:
            cell = grid_cells[(r, c)]
            self.play(
                cell.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE),
                run_time=0.15
            )
        self.wait(0.4)

        # --- Эволюция 1 ---
        # Слева: мигалка становится вертикальной
        # Справа: 4-я клетка рождается мятно-зеленым (формируется стабильный блок 2x2)
        blinker_h = [grid_cells[(-1, -2)], grid_cells[(-1, 0)]]
        blinker_v = [grid_cells[(-2, -1)], grid_cells[(0, -1)]]
        block_new = grid_cells[(2, 2)]

        self.play(
            # Мигалка поворачивается
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in blinker_h],
            *[c.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE) for c in blinker_v],
            # Рождение 4-й клетки блока
            block_new.animate.set_fill(COLOR_BORN, opacity=1.0).set_stroke(COLOR_BORN),
            run_time=0.4
        )

        # --- Эволюция 2 ---
        # Блок застыл и успокаивается в голубой цвет
        # Мигалка поворачивается обратно горизонтально
        self.play(
            *[c.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE) for c in blinker_h],
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in blinker_v],
            block_new.animate.set_fill(COLOR_ALIVE).set_stroke(COLOR_ALIVE),
            run_time=0.4
        )

        # --- Эволюция 3 (Цикл продолжается) ---
        self.play(
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in blinker_h],
            *[c.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE) for c in blinker_v],
            run_time=0.4
        )

        # --- Эволюция 4 (Возврат в горизонталь) ---
        self.play(
            *[c.animate.set_fill(COLOR_ALIVE, opacity=1.0).set_stroke(COLOR_ALIVE) for c in blinker_h],
            *[c.animate.set_fill(COLOR_EMPTY, opacity=0.35).set_stroke(COLOR_BORDER) for c in blinker_v],
            run_time=0.4
        )

        # Фиксация вечного цикла: зритель видит застывший монолит справа и вечную мигалку слева
        self.wait(1.5)