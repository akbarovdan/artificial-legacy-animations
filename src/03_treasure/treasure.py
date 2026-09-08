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
        pos_c = DOWN * 4

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
        self.wait(2)

        # 1) Сундук B исчезает
        card_b = VGroup(chest_b, label_b)
        self.play(card_b.animate.set_opacity(0), run_time=0.8)

        # ==========================================
        # 5. ЗАКОН ИСКЛЮЧЕННОГО ТРЕТЬЕГО (A против ¬A)
        # ==========================================
        
        # Теперь меняем длинные надписи на строгие формулы A и ¬A
        math_a_txt = MathTex("A", font_size=42, color=BOX_A_COLOR).move_to(txt_a.get_center())
        math_c_txt = MathTex(r"\neg A", font_size=42, color=BOX_C_COLOR).move_to(txt_c.get_center())

        self.play(
            Transform(txt_a, math_a_txt),
            Transform(txt_c, math_c_txt),
            run_time=1
        )
        self.wait(1)

        # ==========================================
        # 4. СУНДУКИ A И C СЪЕЗЖАЮТСЯ В ЦЕНТР
        # ==========================================

        # 2) Сундуки A и C съезжаются на середину и встают напротив друг друга
        target_pos_a = UP * 0.8 + LEFT * 2.2
        target_pos_c = UP * 0.8 + RIGHT * 2.2

        card_a = VGroup(chest_a, label_a)
        card_c = VGroup(chest_c, label_c)

        self.play(
            card_a.animate.move_to(target_pos_a),
            card_c.animate.move_to(target_pos_c),
            run_time=1.5
        )
        self.wait(0.5)