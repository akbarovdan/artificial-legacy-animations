from manim import *
import numpy as np


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60


class FirstFlower(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        center_color = ManimColor("#89DCEB")
        edge_color = ManimColor("#CBA6F7")
        petal_count = 280
        golden_angle = np.radians(137.507764)
        radial_scale = 0.235
        display_scale = 0.76

        petals = VGroup()
        for rank in range(1, petal_count + 1):
            theta = rank * golden_angle
            radius = radial_scale * np.sqrt(rank)
            position = np.array(
                [radius * np.cos(theta), radius * np.sin(theta), 0.0]
            )
            length = 0.4 + 1.2 * np.sqrt(rank / petal_count)
            outline = [
                np.array([0.0, 0.0, 0.0]),
                np.array([length * 0.25, length * 0.18, 0.0]),
                np.array([length, 0.0, 0.0]),
                np.array([length * 0.25, -length * 0.18, 0.0]),
            ]

            petal = VMobject()
            petal.set_points_smoothly(outline)
            petal.add_line_to(outline[0]).make_smooth()
            color = interpolate_color(
                center_color,
                edge_color,
                rank / petal_count,
            )
            petal.set_fill(color, opacity=0.85)
            petal.set_stroke("#000000", width=1.0)
            petal.move_to(position)
            petal.rotate(theta, about_point=position)
            petals.add(petal)

        petals.scale(display_scale, about_point=ORIGIN)
        growth_animations = []
        for petal in petals:
            target = petal.copy()
            petal.move_to(ORIGIN)
            petal.scale(0.001, about_point=ORIGIN)
            petal.set_opacity(0)
            growth_animations.append(
                Transform(
                    petal,
                    target,
                    rate_func=rate_functions.ease_out_back,
                )
            )

        self.add(petals)
        self.wait(0.5)
        self.play(
            LaggedStart(*growth_animations, lag_ratio=0.012),
            run_time=3.5,
        )
        self.wait(0.8)
