from manim import *

# Вертикальный формат Shorts (1080x1920)
config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16

class TreasureRiddle(Scene):
    def construct(self):
        # ==========================================
        # 0. ПАСТЕЛЬНАЯ ПАЛИТРА CATPPUCCIN
        # ==========================================
        BOX_A_COLOR = "#A6E3A1"  # Мятно-зеленый
        BOX_B_COLOR = "#89B4FA"  # Небесно-голубой
        BOX_C_COLOR = "#F38BA8"  # Кораллово-розовый
        SOFT_RED    = "#F38BA8"  # Красный акцент для FALSE / ошибок
        SOFT_GREEN  = "#A6E3A1"  # Зеленый акцент для TRUE / успеха
        
        TEXT_COLOR  = "#CDD6F4"  # Мягкий светлый текст
        GOLD_COLOR  = "#F9E2AF"  # Золотой акцент для правила и сокровища

        # ==========================================
        # 1. СТАРТ: 3 НЕЙТРАЛЬНЫХ СУНДУКА В ЦЕНТРЕ
        # ==========================================
        chest_a = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(TEXT_COLOR).scale(1.0)
        chest_b = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(TEXT_COLOR).scale(1.0)
        chest_c = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(TEXT_COLOR).scale(1.0)

        # Ставим их близко друг к другу в центре
        chest_a.move_to(UP * 2.5)
        chest_b.move_to(ORIGIN)
        chest_c.move_to(DOWN * 2.5)

        self.play(
            DrawBorderThenFill(chest_a),
            DrawBorderThenFill(chest_b),
            DrawBorderThenFill(chest_c),
            run_time=2
        )
        self.wait(1)

        # ==========================================
        # 2. РАЗЪЕЗЖАЮТСЯ И ОКРАШИВАЮТСЯ
        # ==========================================
        pos_a = UP * 3.5
        pos_b = DOWN * 0.2
        pos_c = DOWN * 4.0

        self.play(
            chest_a.animate.move_to(pos_a).set_color(BOX_A_COLOR),
            chest_b.animate.move_to(pos_b).set_color(BOX_B_COLOR),
            chest_c.animate.move_to(pos_c).set_color(BOX_C_COLOR),
            run_time=1.5
        )

        # ==========================================
        # 3. ПООЧЕРЕДНОЕ ПОЯВЛЕНИЕ НАДПИСЕЙ
        # ==========================================
        txt_a = Text("A: Treasure is in this chest", font_size=28, color=BOX_A_COLOR)
        txt_a.next_to(chest_a, UP, buff=0.35)
        bg_a = BackgroundRectangle(txt_a, color=BLACK, fill_opacity=0.9, buff=0.15)
        label_a = VGroup(bg_a, txt_a)

        txt_b = Text("B: Treasure is NOT here", font_size=28, color=BOX_B_COLOR)
        txt_b.next_to(chest_b, UP, buff=0.35)
        bg_b = BackgroundRectangle(txt_b, color=BLACK, fill_opacity=0.9, buff=0.15)
        label_b = VGroup(bg_b, txt_b)

        txt_c = Text("C: Treasure is NOT in A", font_size=28, color=BOX_C_COLOR)
        txt_c.next_to(chest_c, UP, buff=0.35)
        bg_c = BackgroundRectangle(txt_c, color=BLACK, fill_opacity=0.9, buff=0.15)
        label_c = VGroup(bg_c, txt_c)

        self.play(FadeIn(label_a, shift=DOWN), run_time=0.8)
        self.play(FadeIn(label_b, shift=DOWN), run_time=0.8)
        self.play(FadeIn(label_c, shift=DOWN), run_time=0.8)
        self.wait(1.5)

        # Показываем счетчик правды
        rule_txt = Text("TRUTH COUNT: 0/1", font_size=24, color=GOLD_COLOR, weight=BOLD)
        rule_txt.to_edge(UP, buff=1.5)
        rule_bg = BackgroundRectangle(rule_txt, color=BLACK, fill_opacity=0.95, buff=0.15)
        rule_banner = VGroup(rule_bg, rule_txt)
        self.play(FadeIn(rule_banner, shift=DOWN), run_time=0.8)
        self.wait(1.5)

        # 1) Сундук B полностью исчезает
        card_b = VGroup(chest_b, label_b)
        self.play(FadeOut(card_b), run_time=0.8)
        self.wait(0.5)

        # ==========================================
        # 4. СУНДУКИ A И C СЪЕЗЖАЮТСЯ В ЦЕНТР
        # ==========================================
        target_pos_a = DOWN * 0.5 + LEFT * 2.4
        target_pos_c = DOWN * 0.5 + RIGHT * 2.4

        # Сохраняем группу с Z-индексом для анимации съезжания
        card_a = VGroup(chest_a, label_a).set_z_index(5)
        card_c = VGroup(chest_c, label_c).set_z_index(5)

        self.play(
            card_a.animate.scale(0.85).move_to(target_pos_a),
            card_c.animate.scale(0.85).move_to(target_pos_c),
            run_time=1.5
        )
        self.wait(1)

        # ==========================================
        # 5. ПОЯВЛЕНИЕ ПРЕДИКАТОВ (A и ¬A)
        # ==========================================
        # Сохраняем оригинальные позиции ярлыков (они съехали вместе с группой)
        orig_label_a_pos = label_a.get_center()
        orig_label_c_pos = label_c.get_center()

        math_a_txt = MathTex("A", font_size=50, color=BOX_A_COLOR).move_to(UP * 1.8 + LEFT * 2.4)
        math_c_txt = MathTex(r"\neg A", font_size=50, color=BOX_C_COLOR).move_to(UP * 1.8 + RIGHT * 2.4)

        self.play(FadeIn(math_a_txt, shift=UP), run_time=0.8)
        self.play(FadeIn(math_c_txt, shift=UP), run_time=0.8)
        self.wait(1)

        # ==========================================
        # 6. ПРОВЕРКА ПРОТИВОРЕЧИЙ
        # ==========================================
        true_a = Text("TRUE", font_size=36, color=BOX_A_COLOR, weight=BOLD).move_to(math_a_txt)
        true_c = Text("TRUE", font_size=36, color=BOX_C_COLOR, weight=BOLD).move_to(math_c_txt)
        q_mark = Text("?", font_size=60, color=WHITE).move_to(UP * 1.8)

        self.play(
            ReplacementTransform(math_a_txt, true_a),
            ReplacementTransform(math_c_txt, true_c),
            FadeIn(q_mark, scale=0.5),
            run_time=1
        )
        self.wait(0.5)

        cross_mark = Text("✕", font_size=70, color=SOFT_RED, weight=BOLD).move_to(q_mark)
        self.play(ReplacementTransform(q_mark, cross_mark), run_time=0.4)
        self.wait(0.5)

        false_a = Text("FALSE", font_size=36, color=BOX_A_COLOR, weight=BOLD).move_to(true_a)
        false_c = Text("FALSE", font_size=36, color=BOX_C_COLOR, weight=BOLD).move_to(true_c)
        q_mark_2 = Text("?", font_size=60, color=WHITE).move_to(UP * 1.8)

        self.play(
            ReplacementTransform(true_a, false_a),
            ReplacementTransform(true_c, false_c),
            ReplacementTransform(cross_mark, q_mark_2),
            run_time=1
        )
        self.wait(0.5)

        cross_mark_2 = Text("✕", font_size=70, color=SOFT_RED, weight=BOLD).move_to(q_mark_2)
        self.play(ReplacementTransform(q_mark_2, cross_mark_2), run_time=0.4)
        self.wait(0.5)

        math_a_return = MathTex("A", font_size=50, color=BOX_A_COLOR).move_to(false_a)
        math_c_return = MathTex(r"\neg A", font_size=50, color=BOX_C_COLOR).move_to(false_c)

        self.play(
            ReplacementTransform(false_a, math_a_return),
            ReplacementTransform(false_c, math_c_return),
            FadeOut(cross_mark_2, scale=0.5),
            run_time=1
        )
        self.wait(1)

        # ==========================================
        # 7. ЗАКОН ИСКЛЮЧЕННОГО ТРЕТЬЕГО
        # ==========================================
        formula_xor = MathTex("A", r"\oplus", r"\neg A", r"\equiv", r"\text{1 TRUTH}", font_size=42)
        formula_xor[0].set_color(BOX_A_COLOR)
        formula_xor[1].set_color(GOLD_COLOR)
        formula_xor[2].set_color(BOX_C_COLOR)
        formula_xor[3].set_color(TEXT_COLOR)
        formula_xor[4].set_color(GOLD_COLOR)

        formula_bg = BackgroundRectangle(formula_xor, color=BLACK, fill_opacity=0.95, buff=0.2)
        formula_group = VGroup(formula_bg, formula_xor)
        formula_group.next_to(rule_banner, DOWN, buff=0.5)

        self.play(FadeIn(formula_group, shift=UP), run_time=1)
        self.wait(1)

        state1_a = Text("TRUE", font_size=36, color=BOX_A_COLOR, weight=BOLD).move_to(math_a_return)
        state1_c = Text("FALSE", font_size=36, color=BOX_C_COLOR, weight=BOLD).move_to(math_c_return)
        
        self.play(
            ReplacementTransform(math_a_return, state1_a),
            ReplacementTransform(math_c_return, state1_c),
            run_time=0.8
        )
        self.wait(0.8)

        state2_a = Text("FALSE", font_size=36, color=BOX_A_COLOR, weight=BOLD).move_to(state1_a)
        state2_c = Text("TRUE", font_size=36, color=BOX_C_COLOR, weight=BOLD).move_to(state1_c)

        self.play(
            ReplacementTransform(state1_a, state2_a),
            ReplacementTransform(state1_c, state2_c),
            run_time=0.8
        )
        self.wait(0.8)

        math_a_final = MathTex("A", font_size=50, color=BOX_A_COLOR).move_to(state2_a)
        math_c_final = MathTex(r"\neg A", font_size=50, color=BOX_C_COLOR).move_to(state2_c)

        self.play(
            ReplacementTransform(state2_a, math_a_final),
            ReplacementTransform(state2_c, math_c_final),
            run_time=0.8
        )
        self.wait(0.5)

        self.play(FadeOut(formula_group, shift=UP), run_time=1)

        # ==========================================
        # 8. СХЛОПЫВАНИЕ КВОТЫ (ЗЕЛЕНЫЙ ЦВЕТ)
        # ==========================================
        rule_filled_txt = Text("TRUTH COUNT: 1/1", font_size=24, color=SOFT_GREEN, weight=BOLD)
        rule_filled_txt.move_to(rule_txt.get_center())
        
        highlight_box = SurroundingRectangle(rule_filled_txt, color=SOFT_GREEN, buff=0.15, corner_radius=0.1)

        self.play(
            math_a_final.animate.move_to(rule_txt.get_center()).set_opacity(0).scale(0.5),
            math_c_final.animate.move_to(rule_txt.get_center()).set_opacity(0).scale(0.5),
            Transform(rule_txt, rule_filled_txt),
            run_time=1.2
        )
        
        self.play(Create(highlight_box), Flash(rule_filled_txt, color=SOFT_GREEN), run_time=0.8)
        self.wait(1)

        # ==========================================
        # 9. ВОЗВРАТ К ИСХОДНОМУ ЭКРАНУ (Глобальная перегенерация)
        # ==========================================
        
        # 1) Создаем абсолютно новые сундуки и надписи на правильных местах (pos_a, pos_b, pos_c)
        new_chest_a = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(BOX_A_COLOR).scale(1.0).move_to(pos_a)
        
        new_chest_b = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(BOX_B_COLOR).scale(1.0).move_to(pos_b)
        new_chest_b.flip(UP) # Возвращаем оригинальное отзеркаливание
        
        new_chest_c = SVGMobject("src/03_treasure/svg/chest_closed.svg").set_color(BOX_C_COLOR).scale(1.0).move_to(pos_c)

        # Новые, чистые ярлыки строго над сундуками
        new_txt_a = Text("A: Treasure is in this chest", font_size=28, color=BOX_A_COLOR).next_to(new_chest_a, UP, buff=0.35)
        new_label_a = VGroup(BackgroundRectangle(new_txt_a, color=BLACK, fill_opacity=0.9, buff=0.15), new_txt_a)

        new_txt_b = Text("B: Treasure is NOT here", font_size=28, color=BOX_B_COLOR).next_to(new_chest_b, UP, buff=0.35)
        new_label_b = VGroup(BackgroundRectangle(new_txt_b, color=BLACK, fill_opacity=0.9, buff=0.15), new_txt_b)

        new_txt_c = Text("C: Treasure is NOT in A", font_size=28, color=BOX_C_COLOR).next_to(new_chest_c, UP, buff=0.35)
        new_label_c = VGroup(BackgroundRectangle(new_txt_c, color=BLACK, fill_opacity=0.9, buff=0.15), new_txt_c)

        # 2) ОДНОВРЕМЕННО растворяем старую сцену и проявляем новую
        self.play(
            # Убираем старье
            FadeOut(chest_a), FadeOut(label_a),
            FadeOut(chest_c), FadeOut(label_c),
            run_time=1.5
        )
        self.wait(1)

        self.play(
            # Появляем новье
            FadeIn(new_chest_a), FadeIn(new_label_a),
            FadeIn(new_chest_b), FadeIn(new_label_b),
            FadeIn(new_chest_c), FadeIn(new_label_c),
            run_time=1.5
        )
        self.wait(1)

        # ==========================================
        # 10. ЗАТЕМНЕНИЕ A И C (Фокус на B)
        # ==========================================
        # Используем новые ярлыки для затемнения
        dim_ac_group = VGroup(new_chest_a, new_label_a, new_chest_c, new_label_c)
        
        self.play(
            dim_ac_group.animate.set_opacity(0.15),
            run_time=1
        )
        self.wait(1.5)

        # ==========================================
        # 11. ЗОЛОТАЯ ЛОЖЬ (FALSE)
        # ==========================================
        # Надпись сундука B превращается в золотую FALSE (не жирным шрифтом)
        false_b_txt = Text("FALSE", font_size=32, color=GOLD_COLOR).move_to(new_txt_b.get_center())
        false_b_bg = BackgroundRectangle(false_b_txt, color=BLACK, fill_opacity=0.95, buff=0.15)
        false_b_label = VGroup(false_b_bg, false_b_txt)

        self.play(ReplacementTransform(new_label_b, false_b_label), run_time=0.8)
        self.wait(1)

        # ==========================================
        # 12. ФИНАЛ: ОТКРЫТИЕ СУНДУКА
        # ==========================================
        # Загружаем открытый сундук (он будет золотым)
        chest_b_open = SVGMobject("src/03_treasure/svg/chest_open.svg").set_color(GOLD_COLOR).scale(1.2)
        chest_b_open.move_to(pos_b)

        # Распахиваем сундук (без wiggle, только Flash)
        self.play(
            ReplacementTransform(new_chest_b, chest_b_open),
            run_time=1
        )
        self.play(
            Flash(chest_b_open.get_center(), color=GOLD_COLOR, line_length=0.6, num_lines=14),
            run_time=1
        )
        
        self.wait(3)