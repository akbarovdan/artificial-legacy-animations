from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class ProLogicFlowSVG(Scene):
    def construct(self):
        # --- ЦВЕТОВАЯ ПАЛИТРА ---
        NEON_GREEN = "#00FF66"
        NEON_RED = "#FF3366"
        NEON_BLUE = "#00E5FF"
        NEON_ORANGE = "#FF9900"
        
        # ==================================
        # 1. ЗАГРУЖАЕМ SVG ИКОНКИ И ТЕКСТЫ
        # ==================================
        
        # Дверь Свободы
        door_a_icon = SVGMobject("src/svg/door.svg").set_color(WHITE).scale(1)
        door_a_icon.shift(UP*4 + LEFT*2)
        da_txt = Text("Freedom", font="UnifrakturMaguntia", font_size=40, color=WHITE, weight=BOLD).next_to(door_a_icon, UP)
        
        # Дверь Смерти
        door_b_icon = SVGMobject("src/svg/door.svg").set_color(WHITE).scale(1)
        door_b_icon.flip(UP) 
        door_b_icon.shift(UP*4 + RIGHT*2)
        db_txt = Text("Death",font="UnifrakturMaguntia", font_size=40, color=WHITE, weight=BOLD).next_to(door_b_icon, UP)

        # Стражник 1 Truth
        g_truth_icon = SVGMobject("src/svg/knight.svg").set_color(WHITE).scale(1.1)
        g_truth_icon.flip(UP)
        g_truth_icon.shift(UP*0.5 + LEFT*2)
        gt_txt = Text("Truth",font="UnifrakturMaguntia", font_size=40, color=NEON_BLUE).next_to(g_truth_icon, DOWN)

        # Стражник 2 Liar
        g_liar_icon = SVGMobject("src/svg/knight.svg").set_color(WHITE).scale(1.1)
        g_liar_icon.shift(UP*0.5 + RIGHT*2)
        gl_txt = Text("Liar", font="UnifrakturMaguntia", font_size=40, color=NEON_ORANGE).next_to(g_liar_icon, DOWN)

        # Игрок (Сначала грустный / растерянный)
        player_sad = SVGMobject("src/svg/sad_you.svg").set_color(WHITE).scale(0.8)
        player_sad.shift(DOWN*4)
        p_txt = Text("YOU", font_size=24).next_to(player_sad, DOWN)
        player_group = VGroup(player_sad, p_txt)

        # Игрок (Улыбающийся, для финала. Прячем его пока)
        player_smile = SVGMobject("src/svg/smile_you.svg").set_color(NEON_GREEN).scale(0.8)
        player_smile.move_to(player_sad.get_center()) # Ставим ровно на то же место

        # ==========================================
        # 2. АНИМАЦИЯ ПОЯВЛЕНИЯ
        # ==========================================
        self.play(
            DrawBorderThenFill(door_a_icon),
            DrawBorderThenFill(door_b_icon),
            run_time=3
        )
        self.play(
            DrawBorderThenFill(g_truth_icon), FadeIn(gt_txt, shift=UP),
            DrawBorderThenFill(g_liar_icon), FadeIn(gl_txt, shift=UP),
            run_time=3
        )
        # Отрисовываем грустного Игрока
        self.play(DrawBorderThenFill(player_sad), FadeIn(p_txt, shift=UP))
        self.wait(1)

        # ==========================================
        # 3. РИСУЕМ ПРОВОДА (PATHS)
        # ==========================================
        # Маршрут сигнала от макушки грустной иконки
        path1 = Line(player_sad.get_top(), g_liar_icon.get_bottom(), color=GRAY)
        path2 = Line(g_liar_icon.get_left(), g_truth_icon.get_right(), color=GRAY)
        path3 = Line(g_truth_icon.get_top(), door_b_icon.get_bottom(), color=GRAY)
        
        self.play(Create(path1), Create(path2), Create(path3), run_time=1.5)
        self.wait(0.5)

        # ==========================================
        # 4. АНИМАЦИЯ СИГНАЛА
        # ==========================================
        signal = Dot(color=NEON_GREEN, radius=0.25)
        signal.move_to(player_sad.get_top())
        
        self.play(FadeIn(signal, scale=0.5))
        
        # К Лжецу
        self.play(MoveAlongPath(signal, path1), run_time=1)
        
        # Инверсия (Зеленый -> Красный)
        self.play(
            Indicate(g_liar_icon, color=NEON_RED, scale_factor=1.2), 
            signal.animate.set_color(NEON_RED), 
            run_time=0.8
        )
        
        # К Правде
        self.play(MoveAlongPath(signal, path2), run_time=1)
        
        # Правда пропускает
        self.play(Indicate(g_truth_icon, color=NEON_BLUE, scale_factor=1.2), run_time=0.8)
        
        # В Дверь Смерти
        self.play(MoveAlongPath(signal, path3), run_time=1)
        
        # Вспышка Двери
        self.play(
            Wiggle(door_b_icon, scale_value=1.2), 
            Flash(door_b_icon.get_bottom(), color=NEON_RED, line_length=0.5),
            run_time=1
        )
        self.wait(1)

        # ==========================================
        # 5. ФИНАЛЬНЫЙ ВЫВОД И ТРАНСФОРМАЦИЯ ИГРОКА
        # ==========================================
        conclusion = Text("TRUTH(LIAR(X)) = ALWAYS FALSE", font_size=32, color=YELLOW)
        conclusion.shift(DOWN*1.5)
        
        action = Text("CHOOSE THE OPPOSITE DOOR", font_size=36, color=NEON_GREEN, weight=BOLD)
        action.next_to(conclusion, DOWN, buff=0.5)
        
        self.play(Write(conclusion))
        self.play(FadeIn(action, shift=UP))
        
        # МАГИЯ: Превращаем грустного белого Игрока в зеленого радостного
        self.play(ReplacementTransform(player_sad, player_smile), run_time=1)
        self.play(Wiggle(player_smile)) # Радостное покачивание
        
        self.wait(2)