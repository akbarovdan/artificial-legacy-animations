from manim import *

class CreateCircle(Scene):
    def construct(self):
        circle = Circle()  # create a circle
        circle.set_fill(PINK, opacity=0.5)  # set the color and transparency
        self.play(Create(circle))  # show the circle on screen

class SquareToCircle(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(PINK, opacity=0.5)

        square = Square()
        square.set_fill(WHITE, opacity=0.1)
        square.rotate(PI / 4)

        self.play(Create(square))
        self.play(Transform(square, circle))
        self.play(FadeOut(square))

class SquareAndCircle(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(PINK, opacity=0.5)

        square = Square()
        square.set_fill(WHITE, opacity=0.1)
        square.rotate(PI / 4)

        square.next_to(circle, RIGHT, buff=0.5)
        self.play(Create(circle), Create(square))

        square.next_to(circle, LEFT, buff=0.5)
        self.play(Create(circle), Create(square))

        square.next_to(circle, DOWN, buff=0.5)
        self.play(Create(circle), Create(square))

        square.next_to(circle, UP, buff=0.5)
        self.play(Create(circle), Create(square))


class CreatingMobject(Scene):
    def construct(self):
        circle = Circle()
        self.add(circle)
        self.wait(1)
        self.remove(circle)
        self.wait(1)

class Shapes(Scene):
    def construct(self):
        circle = Circle()
        square = Square()
        triangle = Triangle()

        circle.shift(LEFT)
        square.shift(UP)
        triangle.shift(RIGHT)

        self.add(circle, square, triangle)
        self.wait(5)

class AnimateExample(Scene):
    def construct(self):
        square = Square()

        self.play(FadeIn(square))
        self.wait(3)
        self.play(square.animate.set_fill(PINK, opacity= 5.0), run_time = 3)
        self.wait(3)