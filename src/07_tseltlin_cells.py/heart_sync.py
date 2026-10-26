import numpy as np
from manim import *

# 9:16 Vertical Video (TikTok / Shorts / Reels)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.background_color = "#08080C"
config.frame_rate = 60


# =========================================================================
# МАТЕМАТИЧЕСКОЕ ЯДРО ИГРЫ ГУР (ЧИСТЫЙ ЦЕТЛИН)
# =========================================================================
def run_gur_simulation(
    num_automata=100, memory_depth=6, total_steps=250, target_x=0.70, seed=42
):
    np.random.seed(seed)
    n = memory_depth
    # Состояния: 1..n для действия 0, и 1..n для действия 1
    # Храним: action (0 или 1), state (1..n)
    actions = np.random.choice([0, 1], size=num_automata)
    states = np.random.randint(1, n + 1, size=num_automata)

    # Характеристика среды: P_win(x) имеет пик в точке x0
    def p_win(x):
        return 0.15 + 0.75 * np.exp(-((x - target_x) ** 2) / (2 * (0.12**2)))

    history = []

    for step in range(total_steps):
        k = np.sum(actions)
        x = k / num_automata
        prob = p_win(x)

        history.append(
            {
                "x": x,
                "p_win": prob,
                "actions": actions.copy(),
                "states": states.copy(),
            }
        )

        # Раздача штрафов и наград
        # 1 = награда (s=0 у Цетлина), 0 = штраф (s=1 у Цетлина)
        feedbacks = np.random.rand(num_automata) < prob

        for i in range(num_automata):
            if feedbacks[i]:  # Награда -> углубление памяти
                if states[i] < n:
                    states[i] += 1
            else:  # Штраф -> движение к границе и смена действия
                if states[i] > 1:
                    states[i] -= 1
                else:
                    actions[i] = 1 - actions[i]
                    states[i] = 1

    return history


# =========================================================================
# СЦЕНА MANIM
# =========================================================================
class GurGameSimulation(Scene):
    def construct(self):
        # Цветовая палитра (Catppuccin / Stealth-Tech)
        C_CYAN = "#89DCEB"  # Действие 1 (Целевое)
        C_RED = "#F38BA8"  # Действие 0 (Ошибочное)
        C_BG_CELL = "#1E1E2E"  # Фон пустой ячейки
        C_CURVE = "#F9E2AF"  # Кривая среды (Янтарь)
        C_TARGET = "#A6E3A1"  # Цель (Зеленый)

        TARGET_X = 0.70
        N_AGENTS = 100
        MEM_DEPTH = 6
        STEPS = 240

        # Предварительный расчет математики
        data = run_gur_simulation(
            num_automata=N_AGENTS,
            memory_depth=MEM_DEPTH,
            total_steps=STEPS,
            target_x=TARGET_X,
        )

        # --- 1. ВЕРХНИЙ БЛОК: ГРАФИК СРЕДЫ P_win(x) ---
        axes = Axes(
            x_range=[0, 1.05, 0.2],
            y_range=[0, 1.05, 0.5],
            x_length=7.0,
            y_length=3.0,
            axis_config={
                "color": "#45475A",
                "stroke_width": 2,
                "include_numbers": False,
            },
        ).to_edge(UP, buff=1.4)

        # Функция кривой
        curve = axes.plot(
            lambda x: 0.15 + 0.75 * np.exp(-((x - TARGET_X) ** 2) / (2 * 0.12**2)),
            x_range=[0, 1.0],
            color=C_CURVE,
            stroke_width=3.5,
        )

        # Маркер целевого оптимума (x = 0.70)
        target_line = axes.get_vertical_line(
            axes.c2p(TARGET_X, 0.90),
            color=C_TARGET,
            stroke_width=2,
            line_func=DashedLine,
        )
        target_dot = Dot(axes.c2p(TARGET_X, 0.90), color=C_TARGET, radius=0.08)
        target_label = MathTex(
            r"x^* = 0.70", color=C_TARGET, font_size=28
        ).next_to(target_dot, UP, buff=0.15)

        # Бегущий маркер текущего состояния системы x(t)
        current_x_tracker = ValueTracker(data[0]["x"])

        needle = always_redraw(
            lambda: DashedLine(
                axes.c2p(current_x_tracker.get_value(), 0),
                axes.c2p(
                    current_x_tracker.get_value(),
                    0.15
                    + 0.75
                    * np.exp(
                        -((current_x_tracker.get_value() - TARGET_X) ** 2)
                        / (2 * 0.12**2)
                    ),
                ),
                color=C_CYAN,
                stroke_width=3,
            )
        )
        tracker_dot = always_redraw(
            lambda: Dot(
                axes.c2p(
                    current_x_tracker.get_value(),
                    0.15
                    + 0.75
                    * np.exp(
                        -((current_x_tracker.get_value() - TARGET_X) ** 2)
                        / (2 * 0.12**2)
                    ),
                ),
                color=C_CYAN,
                radius=0.1,
            )
        )

        chart_label = Text(
            "ENVIRONMENT PAYOFF: P(win | x)",
            font="monospace",
            font_size=20,
            color="#A6ADC8",
        ).next_to(axes, UP, buff=0.2)

        self.add(
            axes,
            curve,
            target_line,
            target_dot,
            target_label,
            chart_label,
            needle,
            tracker_dot,
        )

        # --- 2. ЦЕНТРАЛЬНЫЙ БЛОК: МАТРИЦА 10x10 АВТОМАТОВ ---
        GRID_SIZE = 10
        CELL_SPACING = 0.46
        grid_cells = []
        grid_group = VGroup()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                idx = r * GRID_SIZE + c
                cell_bg = Square(
                    side_length=0.40,
                    stroke_color="#313244",
                    stroke_width=1.0,
                    fill_color=C_BG_CELL,
                    fill_opacity=1.0,
                )
                cell_core = Square(
                    side_length=0.32, stroke_width=0, fill_opacity=0.9
                )
                cell = VGroup(cell_bg, cell_core)
                cell.move_to(
                    np.array(
                        [
                            (c - (GRID_SIZE - 1) / 2) * CELL_SPACING,
                            -1.5 - (r - (GRID_SIZE - 1) / 2) * CELL_SPACING,
                            0,
                        ]
                    )
                )
                grid_cells.append(cell_core)
                grid_group.add(cell)

        grid_title = Text(
            "100 INDEPENDENT TSETLIN AUTOMATA (NO COMMS)",
            font="monospace",
            font_size=20,
            color="#A6ADC8",
        ).next_to(grid_group, UP, buff=0.35)

        self.add(grid_group, grid_title)

        # --- 3. НИЖНИЙ БЛОК: HUD И МЕТРИКИ ---
        hud_ratio = Text(
            "ACTION 1 RATIO: 0.00",
            font="monospace",
            font_size=26,
            color="#CDD6F4",
        ).move_to(DOWN * 4.9)
        hud_status = Text(
            "CONSENSUS: STOCHASTIC CHAOS",
            font="monospace",
            font_size=22,
            color=C_RED,
        ).next_to(hud_ratio, DOWN, buff=0.2)

        self.add(hud_ratio, hud_status)

        # --- 4. ЦИКЛ АНИМАЦИИ И СХОДИМОСТИ ---
        step_tracker = ValueTracker(0)

        def update_grid(mob, dt):
            step = min(int(step_tracker.get_value()), STEPS - 1)
            frame_data = data[step]
            x_val = frame_data["x"]
            current_x_tracker.set_value(x_val)

            acts = frame_data["actions"]
            sts = frame_data["states"]

            # Обновление ячеек матрицы
            for i in range(N_AGENTS):
                color = C_CYAN if acts[i] == 1 else C_RED
                # Глубина памяти определяет яркость/насыщенность
                opacity = 0.25 + 0.75 * (sts[i] / MEM_DEPTH)
                grid_cells[i].set_fill(color, opacity=opacity)

            # Обновление HUD
            hud_ratio.become(
                Text(
                    f"ACTION 1 RATIO: {x_val:.2f} / {TARGET_X:.2f}",
                    font="monospace",
                    font_size=26,
                    color="#CDD6F4",
                ).move_to(DOWN * 4.9)
            )

            if abs(x_val - TARGET_X) < 0.04:
                hud_status.become(
                    Text(
                        "CONSENSUS: GLOBAL OPTIMUM LOCKED",
                        font="monospace",
                        font_size=22,
                        color=C_TARGET,
                    ).next_to(hud_ratio, DOWN, buff=0.2)
                )
            else:
                hud_status.become(
                    Text(
                        "CONSENSUS: SEARCHING...",
                        font="monospace",
                        font_size=22,
                        color="#F9E2AF",
                    ).next_to(hud_ratio, DOWN, buff=0.2)
                )

        grid_group.add_updater(update_grid)

        # Фаза 1: Начальный хаос (медленно)
        self.play(step_tracker.animate.set_value(25), run_time=3, rate_func=linear)

        # Фаза 2: Экспоненциальная сходимость роя
        self.play(
            step_tracker.animate.set_value(180),
            run_time=7,
            rate_func=rate_functions.ease_in_out_quad,
        )

        # Фаза 3: Фиксация в оптимуме 0.70
        self.play(
            step_tracker.animate.set_value(STEPS - 1),
            run_time=4,
            rate_func=linear,
        )

        self.wait(1.5)