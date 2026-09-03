from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class ProLogicFlowSVG(Scene):
    def construct(self):
        # --- ПРЕМИАЛЬНАЯ ПАСТЕЛЬНАЯ ПАЛИТРА (Catppuccin Style) ---
        SOFT_GREEN  = "#A6E3A1"
        SOFT_RED    = "#F38BA8"
        SOFT_BLUE   = "#89B4FA"
        SOFT_ORANGE = "#FAB387"
        SOFT_TEXT   = "#CDD6F4"

        # ==========================================
        # 1. ЗАГРУЖАЕМ БАЗОВЫЕ ИКОНКИ (Без текста)
        # ==========================================
        
        door_a_icon = SVGMobject("src/svg/door.svg").set_color(SOFT_TEXT).scale(1)
        door_a_icon.shift(UP*4 + LEFT*2)
        
        door_b_icon = SVGMobject("src/svg/door.svg").set_color(SOFT_TEXT).scale(1)
        door_b_icon.flip(UP) 
        door_b_icon.shift(UP*4 + RIGHT*2)

        g1_icon = SVGMobject("src/svg/knight.svg").set_color(SOFT_TEXT).scale(1.1)
        g1_icon.flip(UP)
        g1_icon.shift(UP*0.5 + LEFT*2)

        g2_icon = SVGMobject("src/svg/knight.svg").set_color(SOFT_TEXT).scale(1.1)
        g2_icon.shift(UP*0.5 + RIGHT*2)

        player_sad = SVGMobject("src/svg/sad_you.svg").set_color(SOFT_TEXT).scale(0.7)
        player_sad.shift(DOWN*4)
        p_txt = Text("YOU", font_size=30, color=SOFT_TEXT).next_to(player_sad, DOWN)
        player_group = VGroup(player_sad, p_txt)

        player_smile = SVGMobject("src/svg/smile_you.svg").set_color(SOFT_TEXT).scale(0.7)
        player_smile.move_to(player_sad.get_center()) 

        # Копия грустного игрока для возврата в исходную позицию позже
        player_sad_return = player_sad.copy()

        # ==========================================
        # 2. АНИМАЦИЯ ПОЯВЛЕНИЯ БАЗЫ
        # ==========================================
        self.play(
            DrawBorderThenFill(door_a_icon),
            DrawBorderThenFill(door_b_icon),
            run_time=1
        )
        self.play(
            DrawBorderThenFill(g1_icon),
            DrawBorderThenFill(g2_icon),
            run_time=1
        )
        self.play(DrawBorderThenFill(player_sad), FadeIn(p_txt, shift=UP))
        self.wait(1)

        # ==========================================
        # 3. СЦЕНА ОБМАНА: "Иллюзия правильного выбора"
        # ==========================================
        
        path1 = Line(player_sad.get_center(), g2_icon.get_center(), buff=0.9, color=GRAY).set_z_index(-1)
        path2 = Line(g2_icon.get_center(), door_b_icon.get_center(), buff=1.1, color=GRAY).set_z_index(-1)
        
        self.play(Create(path1), run_time=1.5)
        self.play(Create(path2), run_time=1.5)

        fake_truth_txt = Text("Truth", font_size=30, color=SOFT_BLUE)
        fake_truth_txt.next_to(g2_icon, DOWN).shift(LEFT * 0.3)
        fake_truth_bg = BackgroundRectangle(fake_truth_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        fake_truth_label = VGroup(fake_truth_bg, fake_truth_txt)

        fake_liar_txt = Text("Liar", font_size=30, color=SOFT_ORANGE)
        fake_liar_txt.next_to(g1_icon, DOWN).shift(RIGHT * 0.3)
        fake_liar_bg = BackgroundRectangle(fake_liar_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        fake_liar_label = VGroup(fake_liar_bg, fake_liar_txt)

        fake_freedom_txt = Text("Freedom", font_size=30, color=SOFT_GREEN)
        fake_freedom_txt.next_to(door_b_icon, UP)
        fake_freedom_bg = BackgroundRectangle(fake_freedom_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        fake_freedom_label = VGroup(fake_freedom_bg, fake_freedom_txt)

        fake_death_txt = Text("Death", font_size=30, color=SOFT_RED)
        fake_death_txt.next_to(door_a_icon, UP)
        fake_death_bg = BackgroundRectangle(fake_death_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        fake_death_label = VGroup(fake_death_bg, fake_death_txt)

        self.play(
            FadeIn(fake_truth_label), 
            FadeIn(fake_freedom_label), 
            FadeIn(fake_liar_label), 
            FadeIn(fake_death_label)
        )

        self.play(
            ReplacementTransform(player_sad, player_smile),
            path1.animate.set_color(SOFT_GREEN),
            path2.animate.set_color(SOFT_GREEN),
            run_time=1
        )
        self.wait(1)

        # ==========================================
        # 4. ВОЗВРАТ К РЕАЛЬНОСТИ (Все встает на свои места)
        # ==========================================
        
        # Запоминаем текущие (ложные) позиции, чтобы поменять ярлыки местами
        pos_truth = fake_truth_label.get_center()
        pos_liar = fake_liar_label.get_center()
        pos_freedom = fake_freedom_label.get_center()
        pos_death = fake_death_label.get_center()

        self.play(
            # 1) Ярлыки стражников и дверей меняются местами
            fake_truth_label.animate.move_to(pos_liar),
            fake_liar_label.animate.move_to(pos_truth),
            fake_freedom_label.animate.move_to(pos_death),
            fake_death_label.animate.move_to(pos_freedom),
            # 2) Путь краснеет и игрок возвращается в грустное состояние
            path1.animate.set_color(SOFT_RED),
            path2.animate.set_color(SOFT_RED),
            ReplacementTransform(player_smile, player_sad_return),
            run_time=1.5
        )
        self.wait(1)

        # ==========================================
        # 5. ВВЕДЕНИЕ К РЕШЕНИЮ
        # ==========================================
        
        # 1) Путь удаляется
        self.play(FadeOut(path1), FadeOut(path2), run_time=1)
        
        # 2) Выделяются двери, остальное уходит в фон (opacity = 0.2)
        background_elements = VGroup(
            g1_icon, g2_icon, 
            fake_truth_label, fake_liar_label, 
            player_sad_return, p_txt
        )
        self.play(background_elements.animate.set_opacity(0.2), run_time=1)

        # 3) Freedom трансформируется в TRUE, 4) Death в FALSE
        true_txt = Text("TRUE", font_size=30, color=SOFT_GREEN)
        true_txt.move_to(fake_freedom_label.get_center())
        true_bg = BackgroundRectangle(true_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        true_label = VGroup(true_bg, true_txt)

        false_txt = Text("FALSE", font_size=30, color=SOFT_RED)
        false_txt.move_to(fake_death_label.get_center())
        false_bg = BackgroundRectangle(false_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        false_label = VGroup(false_bg, false_txt)

        self.play(ReplacementTransform(fake_freedom_label, true_label), run_time=1)
        self.play(ReplacementTransform(fake_death_label, false_label), run_time=1)
        self.wait(1)

        # 5) Возвращаем в исходную позицию вид на общую схему
        self.play(background_elements.animate.set_opacity(1), run_time=1)
        self.wait(1)

        # ==========================================
        # 6. ЗАПРОС К СТРАЖНИКУ (ПРАВДА)
        # ==========================================
        
        # 1) Скручиваем прозрачность у всего, кроме Игрока и Правдолюбца
        dim_group = VGroup(
            door_a_icon, door_b_icon, 
            true_label, false_label, 
            g2_icon, fake_liar_label
        )
        self.play(dim_group.animate.set_opacity(0.2), run_time=1)

        # 2) Путь протягивается к Правдолюбцу
        path_truth = Line(player_sad_return.get_center(), g1_icon.get_center(), buff=0.9, color=GRAY).set_z_index(-1)
        self.play(Create(path_truth), run_time=1)

        # 3) Отправляется "TRUE?" (белым) и возвращается "TRUE" (зеленым)
        q_true = Text("TRUE?", font_size=24, color=WHITE)
        # Ставим текст строго на начало серой линии
        q_true.move_to(path_truth.get_start()) 
        
        self.play(FadeIn(q_true, scale=0.5))
        self.play(MoveAlongPath(q_true, path_truth), run_time=1)
        
        ans_true = Text("TRUE", font_size=24, color=SOFT_GREEN)
        # Результат появляется строго на конце серой линии
        ans_true.move_to(path_truth.get_end()) 
        self.play(ReplacementTransform(q_true, ans_true), run_time=0.2)
        
        # Обратный путь по той же траектории
        path_truth_rev = Line(path_truth.get_end(), path_truth.get_start(), color=GRAY).set_z_index(-1)
        self.play(MoveAlongPath(ans_true, path_truth_rev), run_time=1)
        self.play(FadeOut(ans_true, scale=0.5))

        # ==========================================
        # 7. ПРЕВРАЩЕНИЕ В ФУНКЦИЮ f(x) = x
        # ==========================================
        
        # Запоминаем исходные позиции
        g1_pos_original = g1_icon.get_center()
        
        # Привязываем линию к стражнику, чтобы она тянулась за ним
        path_truth.add_updater(lambda m: m.become(Line(player_sad_return.get_center(), g1_icon.get_center(), buff=0.9, color=GRAY).set_z_index(-1)))
        
        # 1) Выезжает на центр (путь тянется за ним)
        self.play(
            g1_icon.animate.move_to(UP * 1.5),
            fake_truth_label.animate.next_to(UP * 1.5, DOWN).shift(LEFT * 0.3),
            run_time=1
        )
        path_truth.clear_updaters() # Отключаем привязку

        # 2) Превращается в огромную формулу f(x) = x
        formula_f = MathTex("f(", "x", ")", "=", "x", font_size=75, color=SOFT_BLUE).move_to(g1_icon.get_center())
        self.play(
            ReplacementTransform(VGroup(g1_icon, fake_truth_label), formula_f),
            run_time=1
        )
        
        # Обновляем линию под размер большой формулы
        path_to_formula = Line(player_sad_return.get_center(), formula_f.get_center(), buff=1.2, color=GRAY).set_z_index(-1)
        path_truth.become(path_to_formula)

        # Отправляем запрос "TRUE?", который достигает формулы
        q2_true = Text("TRUE?", font_size=24, color=WHITE).move_to(path_to_formula.get_start())
        
        self.play(FadeIn(q2_true, scale=0.5))
        self.play(MoveAlongPath(q2_true, path_to_formula), run_time=1)
        self.play(FadeOut(q2_true, scale=0.5))
        
        # 3) Шаг 1: Заменяет первый x на TRUE в f(x)
        formula_f_sub1 = MathTex("f(", "\\text{TRUE}", ")", "=", "x", font_size=75, color=SOFT_BLUE).move_to(formula_f.get_center())
        formula_f_sub1[1].set_color(SOFT_TEXT)
        
        self.play(TransformMatchingTex(formula_f, formula_f_sub1), run_time=1)
        self.wait(0.5)
        
        # Шаг 2: Заменяет второй x на TRUE (f(TRUE) = TRUE)
        formula_f_sub2 = MathTex("f(", "\\text{TRUE}", ")", "=", "\\text{TRUE}", font_size=75, color=SOFT_BLUE).move_to(formula_f_sub1.get_center())
        formula_f_sub2[1].set_color(SOFT_TEXT)
        formula_f_sub2[4].set_color(SOFT_TEXT)
        
        self.play(TransformMatchingTex(formula_f_sub1, formula_f_sub2), run_time=1)
        self.wait(0.5)
        
        # 4) Возвращает TRUE по пути уже зеленым
        ans2_true = Text("TRUE", font_size=24, color=SOFT_GREEN).move_to(path_to_formula.get_end())
        path_from_formula = Line(path_to_formula.get_end(), path_to_formula.get_start(), color=GRAY).set_z_index(-1)
        
        self.play(FadeIn(ans2_true, scale=0.5))
        self.play(MoveAlongPath(ans2_true, path_from_formula), run_time=1)
        self.play(FadeOut(ans2_true, scale=0.5))

        # 5) Сдвигается обратно в виде формулы (уменьшается) и одновременно исчезает путь
        formula_f_final = MathTex("f(x) = x", font_size=60, color=SOFT_BLUE).move_to(formula_f_sub2.get_center())
        self.play(ReplacementTransform(formula_f_sub2, formula_f_final), run_time=0.5)
        
        # Снова привязываем линию к маленькой формуле для обратного движения
        path_truth.add_updater(lambda m: m.become(Line(player_sad_return.get_center(), formula_f_final.get_center(), buff=0.9, color=GRAY).set_z_index(-1)))
        
        self.play(
            formula_f_final.animate.move_to(g1_pos_original),
            FadeOut(path_truth),
            run_time=1
        )
        path_truth.clear_updaters()

        # 6) Возвращаем обратно всю непрозрачность
        self.play(dim_group.animate.set_opacity(1), run_time=1)
        self.wait(1)

        # ==========================================
        # 8. ЗАПРОС К СТРАЖНИКУ (ЛЖЕЦ)
        # ==========================================
        
        # 1) Скручиваем прозрачность у всего, кроме Игрока и Лжеца
        # (Правдолюбец у нас теперь стал формулой formula_f_final)
        dim_group_liar = VGroup(
            door_a_icon, door_b_icon, 
            true_label, false_label, 
            formula_f_final 
        )
        self.play(dim_group_liar.animate.set_opacity(0.2), run_time=1)

        # 2) Путь протягивается к Лжецу
        path_liar = Line(player_sad_return.get_center(), g2_icon.get_center(), buff=0.9, color=GRAY).set_z_index(-1)
        self.play(Create(path_liar), run_time=1)

        # 3) Отправляется "TRUE?" (белым) и возвращается "FALSE" (красным)
        q_liar = Text("TRUE?", font_size=24, color=WHITE)
        q_liar.move_to(path_liar.get_start()) 
        
        self.play(FadeIn(q_liar, scale=0.5))
        self.play(MoveAlongPath(q_liar, path_liar), run_time=1)
        
        ans_liar = Text("FALSE", font_size=24, color=SOFT_RED)
        ans_liar.move_to(path_liar.get_end()) 
        self.play(ReplacementTransform(q_liar, ans_liar), run_time=0.2)
        
        # Обратный путь
        path_liar_rev = Line(path_liar.get_end(), path_liar.get_start(), color=GRAY).set_z_index(-1)
        self.play(MoveAlongPath(ans_liar, path_liar_rev), run_time=1)
        self.play(FadeOut(ans_liar, scale=0.5))

        # ==========================================
        # 9. ПРЕВРАЩЕНИЕ В ФУНКЦИЮ g(x) = \neg x
        # ==========================================
        
        # Запоминаем исходные позиции
        g2_pos_original = g2_icon.get_center()
        
        # Привязываем линию к стражнику
        path_liar.add_updater(lambda m: m.become(Line(player_sad_return.get_center(), g2_icon.get_center(), buff=0.9, color=GRAY).set_z_index(-1)))
        
        # 1) Выезжает на центр (путь тянется за ним)
        self.play(
            g2_icon.animate.move_to(UP * 1.5),
            fake_liar_label.animate.next_to(UP * 1.5, DOWN).shift(RIGHT * 0.3),
            run_time=1
        )
        path_liar.clear_updaters()

        # 2) Превращается в огромную формулу g(x) = \neg x
        formula_g = MathTex("g(", "x", ")", "=", "\\neg ", "x", font_size=75, color=SOFT_ORANGE).move_to(g2_icon.get_center())
        self.play(
            ReplacementTransform(VGroup(g2_icon, fake_liar_label), formula_g),
            run_time=1
        )
        
        # Обновляем линию под размер формулы
        path_to_formula_g = Line(player_sad_return.get_center(), formula_g.get_center(), buff=1.3, color=GRAY).set_z_index(-1)
        path_liar.become(path_to_formula_g)

        # Отправляем запрос "TRUE?"
        q2_liar = Text("TRUE?", font_size=24, color=WHITE).move_to(path_to_formula_g.get_start())
        
        self.play(FadeIn(q2_liar, scale=0.5))
        self.play(MoveAlongPath(q2_liar, path_to_formula_g), run_time=1)
        self.play(FadeOut(q2_liar, scale=0.5))
        
        # 3) Шаг 1: Заменяет первый x на TRUE в g(x)
        formula_g_sub1 = MathTex("g(", "\\text{TRUE}", ")", "=", "\\neg ", "x", font_size=75, color=SOFT_ORANGE).move_to(formula_g.get_center())
        formula_g_sub1[1].set_color(SOFT_TEXT)
        
        self.play(TransformMatchingTex(formula_g, formula_g_sub1), run_time=1)
        self.wait(0.5)
        
        # Шаг 2: Заменяет \neg x на FALSE
        formula_g_sub2 = MathTex("g(", "\\text{TRUE}", ")", "=", "\\text{FALSE}", font_size=75, color=SOFT_ORANGE).move_to(formula_g_sub1.get_center())
        formula_g_sub2[1].set_color(SOFT_TEXT)
        formula_g_sub2[4].set_color(SOFT_RED) # Окрашиваем финальный FALSE в красный
        
        self.play(TransformMatchingTex(formula_g_sub1, formula_g_sub2), run_time=1)
        self.wait(0.5)
        
        # 4) Возвращает FALSE по пути красным цветом
        ans2_liar = Text("FALSE", font_size=24, color=SOFT_RED).move_to(path_to_formula_g.get_end())
        path_from_formula_g = Line(path_to_formula_g.get_end(), path_to_formula_g.get_start(), color=GRAY).set_z_index(-1)
        
        self.play(FadeIn(ans2_liar, scale=0.5))
        self.play(MoveAlongPath(ans2_liar, path_from_formula_g), run_time=1)
        self.play(FadeOut(ans2_liar, scale=0.5))

        # 5) Сдвигается обратно в виде формулы и исчезает путь
        formula_g_final = MathTex("g(x) = \\neg x", font_size=60, color=SOFT_ORANGE).move_to(formula_g_sub2.get_center())
        self.play(ReplacementTransform(formula_g_sub2, formula_g_final), run_time=0.5)
        
        # Снова привязываем линию для обратного движения
        path_liar.add_updater(lambda m: m.become(Line(player_sad_return.get_center(), formula_g_final.get_center(), buff=0.9, color=GRAY).set_z_index(-1)))
        
        self.play(
            formula_g_final.animate.move_to(g2_pos_original),
            FadeOut(path_liar),
            run_time=1
        )
        path_liar.clear_updaters()

        # 6) Возвращаем обратно всю непрозрачность
        self.play(dim_group_liar.animate.set_opacity(1), run_time=1)
        self.wait(1)

        # ==========================================
        # 10. КРУГОВОРОТ: ВЕРТИКАЛЬНЫЙ ПАЙПЛАЙН (ИДЕАЛЬНАЯ ПЛАВНОСТЬ)
        # ==========================================
        
        def get_signal_badge(text, color):
            txt = Text(text, font_size=24, color=color, weight=BOLD)
            bg = BackgroundRectangle(txt, color=BLACK, fill_opacity=1, buff=0.15)
            # z_index=5: плашка будет над серыми линиями, но ПОД формулами
            return VGroup(bg, txt).set_z_index(5)

        # Поднимаем формулы на передний план, чтобы плашки красиво проплывали под ними
        formula_f_final.set_z_index(10)
        formula_g_final.set_z_index(10)

        dim_group_10 = VGroup(door_a_icon, door_b_icon, true_label, false_label, p_txt)
        self.play(dim_group_10.animate.set_opacity(0.1), run_time=1)

        pos_f_orig = formula_f_final.get_center()
        pos_g_orig = formula_g_final.get_center()

        pos_mid = ORIGIN + DOWN * 0.5
        pos_top = UP * 2.5
        pos_above_top = UP * 3.5 # Точка, куда сигнал вылетает сверху

        # --- ЧАСТЬ 1: Игрок -> f(x) -> g(x) ---
        self.play(
            formula_g_final.animate.move_to(pos_top),
            formula_f_final.animate.move_to(pos_mid),
            run_time=1
        )

        line_up1 = Line(player_sad_return.get_center(), formula_f_final.get_center(), buff=0.6, color=GRAY).set_z_index(-1)
        line_up2 = Line(formula_f_final.get_center(), formula_g_final.get_center(), buff=0.6, color=GRAY).set_z_index(-1)
        self.play(Create(line_up1), Create(line_up2), run_time=1)

        # Запрос стартует от игрока
        sig1 = get_signal_badge("TRUE?", WHITE).move_to(line_up1.get_start())
        self.play(FadeIn(sig1, scale=0.8), run_time=0.3)
        
        # Летит к первой формуле f(x)
        self.play(sig1.animate.move_to(line_up1.get_end()), run_time=0.8)
        
        # ПЛАВНЫЙ ПРОХОД СКВОЗЬ ФОРМУЛУ: Перемещаем в начало следующей линии и одновременно трансформируем
        sig1_true = get_signal_badge("TRUE", SOFT_GREEN).move_to(line_up2.get_start())
        self.play(ReplacementTransform(sig1, sig1_true), run_time=0.7)
        
        # Летит ко второй формуле g(x)
        self.play(sig1_true.animate.move_to(line_up2.get_end()), run_time=0.8)
        
        # ПРОХОД СКВОЗЬ ЛЖЕЦА: Вылетает наверх и плавно красится в красный
        sig1_false = get_signal_badge("FALSE", SOFT_RED).move_to(pos_above_top)
        self.play(ReplacementTransform(sig1_true, sig1_false), run_time=0.7)

        # Возвращается вниз к Игроку длинным пролетом
        self.play(sig1_false.animate.move_to(line_up1.get_start()), run_time=1.2)
        self.play(FadeOut(sig1_false, scale=0.8), run_time=0.3)


        # --- ЧАСТЬ 2: МЕНЯЕМ МЕСТАМИ: Игрок -> g(x) -> f(x) ---
        self.play(
            formula_f_final.animate.move_to(pos_top),
            formula_g_final.animate.move_to(pos_mid),
            run_time=1
        )

        sig2 = get_signal_badge("TRUE?", WHITE).move_to(line_up1.get_start())
        self.play(FadeIn(sig2, scale=0.8), run_time=0.3)
        
        # Летит к первой формуле (теперь это Лжец)
        self.play(sig2.animate.move_to(line_up1.get_end()), run_time=0.8)
        
        # ПРОХОД СКВОЗЬ ЛЖЕЦА: СРАЗУ красится в красный
        sig2_false = get_signal_badge("FALSE", SOFT_RED).move_to(line_up2.get_start())
        self.play(ReplacementTransform(sig2, sig2_false), run_time=0.7)
        
        # Летит ко второй формуле f(x) уже красным
        self.play(sig2_false.animate.move_to(line_up2.get_end()), run_time=0.8)
        
        # ПРОХОД СКВОЗЬ ПРАВДУ: Просто проплывает насквозь, оставаясь красным
        self.play(sig2_false.animate.move_to(pos_above_top), run_time=0.7)

        # Возвращается вниз к Игроку
        self.play(sig2_false.animate.move_to(line_up1.get_start()), run_time=1.2)
        self.play(FadeOut(sig2_false, scale=0.8), run_time=0.3)

        # Возвращаем сцену в исходное состояние
        self.play(
            FadeOut(line_up1, line_up2),
            formula_f_final.animate.move_to(pos_f_orig),
            formula_g_final.animate.move_to(pos_g_orig),
            dim_group_10.animate.set_opacity(1),
            run_time=1
        )

        # ==========================================
        # 11. МАТЕМАТИЧЕСКОЕ РЕШЕНИЕ (СХЛОПЫВАНИЕ)
        # ==========================================
        
        # 1) Скручиваем прозрачность у всего фона 
        # (ОБРАТИ ВНИМАНИЕ: мы не включаем сюда стражников g1 и g2, т.к. они сейчас формулы!)
        dim_group_final = VGroup(
            door_a_icon, door_b_icon, 
            true_label, false_label, 
            player_sad_return, p_txt
        )
        self.play(dim_group_final.animate.set_opacity(0.1), run_time=1)

        # ---------------------------------------------------------
        # ШАГ 1: Создаем вложенные формулы f(g(x)) и g(f(x))
        # ---------------------------------------------------------
        eq0_top = MathTex("f(", "g(", "x", ")", ")", font_size=75)
        eq0_top[0].set_color(SOFT_BLUE)    # f(
        eq0_top[1].set_color(SOFT_ORANGE)  # g(
        eq0_top[2].set_color(WHITE)        # x
        eq0_top[3].set_color(SOFT_ORANGE)  # )
        eq0_top[4].set_color(SOFT_BLUE)    # )

        eq0_bot = MathTex("g(", "f(", "x", ")", ")", font_size=75)
        eq0_bot[0].set_color(SOFT_ORANGE)  # g(
        eq0_bot[1].set_color(SOFT_BLUE)    # f(
        eq0_bot[2].set_color(WHITE)        # x
        eq0_bot[3].set_color(SOFT_BLUE)    # )
        eq0_bot[4].set_color(SOFT_ORANGE)  # )

        VGroup(eq0_top, eq0_bot).arrange(DOWN, buff=2).move_to(ORIGIN)

        # Оригинальные формулы съезжаются в центр и становятся вложенными
        self.play(
            ReplacementTransform(formula_f_final, eq0_top),
            ReplacementTransform(formula_g_final, eq0_bot),
            run_time=1.5
        )
        self.wait(0.5)

        # ---------------------------------------------------------
        # ШАГ 2: Подставляем TRUE вместо x
        # ---------------------------------------------------------
        eq1_top = MathTex("f(", "g(", "\\text{TRUE}", ")", ")", font_size=75).move_to(eq0_top)
        eq1_top[0].set_color(SOFT_BLUE)
        eq1_top[1].set_color(SOFT_ORANGE)
        eq1_top[2].set_color(SOFT_GREEN)   # TRUE
        eq1_top[3].set_color(SOFT_ORANGE)
        eq1_top[4].set_color(SOFT_BLUE)

        eq1_bot = MathTex("g(", "f(", "\\text{TRUE}", ")", ")", font_size=75).move_to(eq0_bot)
        eq1_bot[0].set_color(SOFT_ORANGE)
        eq1_bot[1].set_color(SOFT_BLUE)
        eq1_bot[2].set_color(SOFT_GREEN)   # TRUE
        eq1_bot[3].set_color(SOFT_BLUE)
        eq1_bot[4].set_color(SOFT_ORANGE)

        self.play(
            ReplacementTransform(eq0_top, eq1_top),
            ReplacementTransform(eq0_bot, eq1_bot),
            run_time=1
        )
        self.wait(0.5)

        # ---------------------------------------------------------
        # ШАГ 3: Решаем внутреннюю функцию
        # ---------------------------------------------------------
        # Сверху: g(TRUE) инвертируется в FALSE
        eq2_top = MathTex("f(", "\\text{FALSE}", ")", font_size=75).move_to(eq0_top)
        eq2_top[0].set_color(SOFT_BLUE)
        eq2_top[1].set_color(SOFT_RED)     # FALSE
        eq2_top[2].set_color(SOFT_BLUE)

        # Снизу: f(TRUE) остается TRUE
        eq2_bot = MathTex("g(", "\\text{TRUE}", ")", font_size=75).move_to(eq0_bot)
        eq2_bot[0].set_color(SOFT_ORANGE)
        eq2_bot[1].set_color(SOFT_GREEN)   # TRUE
        eq2_bot[2].set_color(SOFT_ORANGE)

        self.play(
            ReplacementTransform(eq1_top, eq2_top),
            ReplacementTransform(eq1_bot, eq2_bot),
            run_time=1
        )
        self.wait(0.5)

        # ---------------------------------------------------------
        # ШАГ 4: Решаем внешнюю функцию (Итог всегда FALSE)
        # ---------------------------------------------------------
        # Сверху: f(FALSE) остается FALSE
        eq3_top = MathTex("\\text{FALSE}", font_size=90).move_to(eq0_top)
        eq3_top[0].set_color(SOFT_RED)

        # Снизу: g(TRUE) инвертируется в FALSE
        eq3_bot = MathTex("\\text{FALSE}", font_size=90).move_to(eq0_bot)
        eq3_bot[0].set_color(SOFT_RED)

        self.play(
            ReplacementTransform(eq2_top, eq3_top),
            ReplacementTransform(eq2_bot, eq3_bot),
            run_time=1
        )
        self.wait(1)

# ---------------------------------------------------------
        # ШАГ 5: Возврат в исходную позицию (ПРАВИЛЬНАЯ ТРАНСФОРМАЦИЯ)
        # ---------------------------------------------------------
        # Создаем иконки стражников заново
        final_g1_icon = SVGMobject("src/svg/knight.svg").set_color(SOFT_TEXT).scale(1.1)
        final_g1_icon.flip(UP)
        final_g1_icon.move_to(g1_pos_original)
        
        final_g2_icon = SVGMobject("src/svg/knight.svg").set_color(SOFT_TEXT).scale(1.1)
        final_g2_icon.move_to(g2_pos_original)

        # Текст стражников СТРОГО ПО ЦЕНТРУ (убрали .shift)
        final_truth_txt = Text("Truth", font_size=30, color=SOFT_BLUE).next_to(final_g1_icon, DOWN)
        final_truth_bg = BackgroundRectangle(final_truth_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        final_truth_label = VGroup(final_truth_bg, final_truth_txt)

        final_liar_txt = Text("Liar", font_size=30, color=SOFT_ORANGE).next_to(final_g2_icon, DOWN)
        final_liar_bg = BackgroundRectangle(final_liar_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        final_liar_label = VGroup(final_liar_bg, final_liar_txt)

        # Создаем оригинальные надписи дверей для возврата
        final_freedom_txt = Text("Freedom", font_size=30, color=SOFT_GREEN).next_to(door_a_icon, UP)
        final_freedom_bg = BackgroundRectangle(final_freedom_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        final_freedom_label = VGroup(final_freedom_bg, final_freedom_txt)

        final_death_txt = Text("Death", font_size=30, color=SOFT_RED).next_to(door_b_icon, UP)
        final_death_bg = BackgroundRectangle(final_death_txt, color=BLACK, fill_opacity=0.9, buff=0.15)
        final_death_label = VGroup(final_death_bg, final_death_txt)

        # Синхронно: формулы исчезают, появляются стражники, TRUE/FALSE возвращаются в Freedom/Death
        # ВАЖНО: Возвращаем яркость дверям и игроку точечно, чтобы не сломать Transform ярлыков!
        self.play(
            FadeOut(eq3_top, shift=UP),
            FadeOut(eq3_bot, shift=DOWN),
            FadeIn(VGroup(final_g1_icon, final_truth_label), shift=UP),
            FadeIn(VGroup(final_g2_icon, final_liar_label), shift=DOWN),
            ReplacementTransform(true_label, final_freedom_label),
            ReplacementTransform(false_label, final_death_label),
            door_a_icon.animate.set_opacity(1),
            door_b_icon.animate.set_opacity(1),
            player_sad_return.animate.set_opacity(1),
            p_txt.animate.set_opacity(1),
            run_time=1.5
        )
        self.wait(1)

        # ==========================================
        # 12. ФИНАЛ
        # ==========================================
        
        # Рисуем красные лучи от обоих стражников в дверь Смерти
        # Обычная толщина, buff=0.8 делает линию короче, чтобы она аккуратно касалась иконок
        ray_death_1 = Line(final_g1_icon.get_center(), door_b_icon.get_center(), color=SOFT_RED, buff=1.5).set_z_index(-1)
        ray_death_2 = Line(final_g2_icon.get_center(), door_b_icon.get_center(), color=SOFT_RED, buff=1.1).set_z_index(-1)

        self.play(Create(ray_death_1), Create(ray_death_2), run_time=1)

        # ФИНАЛ: Появляется зеленая линия от Игрока в дверь Свободы
        # Собираем всё, что нужно увести в тень (оставляем только Игрока и Дверь Свободы)
        dim_finale = VGroup(
            final_g1_icon, final_g2_icon,
            final_truth_label, final_liar_label,
            door_b_icon, false_label,
            ray_death_1, ray_death_2
        )
        
        # Финальный зеленый путь (Обычная толщина)
        victory_ray = Line(player_sad_return.get_center(), door_a_icon.get_center(), color=SOFT_GREEN, buff=1.1).set_z_index(-1)

        # ВАЖНО: Создаем абсолютно новую иконку улыбки, так как старую мы уже "потратили" в Сцене 3
        final_player_smile = SVGMobject("src/svg/smile_you.svg").set_color(SOFT_TEXT).scale(0.7)
        final_player_smile.move_to(player_sad_return.get_center())

        # Одновременно: фон гаснет, зеленая линия рисуется
        self.play(
            dim_finale.animate.set_opacity(0.15),
            Create(victory_ray),
            ReplacementTransform(player_sad_return, final_player_smile),
            run_time=1.5
        )

        self.wait(2)