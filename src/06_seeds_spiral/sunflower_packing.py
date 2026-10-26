from manim import *
import numpy as np


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60


class SunflowerPacking(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        c_center = "#89DCEB"
        c_edge = "#CBA6F7"
        c_gold = "#F9E2AF"
        golden_angle = np.radians(137.507764)
        num_seeds = 280
        radial_scale = 0.28

        def build_seed(rank_ratio):
            length = 0.4 + 1.2 * np.sqrt(rank_ratio)
            points = [
                np.array([0.0, 0.0, 0.0]),
                np.array([length * 0.25, length * 0.18, 0.0]),
                np.array([length, 0.0, 0.0]),
                np.array([length * 0.25, -length * 0.18, 0.0]),
            ]
            seed = VMobject()
            seed.set_points_smoothly(points)
            seed.add_line_to(points[0]).make_smooth()
            color = interpolate_color(
                ManimColor(c_center),
                ManimColor(c_edge),
                rank_ratio,
            )
            seed.set_fill(color, opacity=0.85)
            seed.set_stroke("#000000", width=1.0)
            return seed

        seed_animations = []
        seed_targets = []
        seed_angles = []
        for rank in range(1, num_seeds + 1):
            theta = rank * golden_angle
            radius = radial_scale * np.sqrt(rank)
            position = np.array(
                [radius * np.cos(theta), radius * np.sin(theta), 0.0]
            )

            seed = build_seed(rank / num_seeds)
            seed.move_to(position).rotate(theta, about_point=position)
            target_seed = seed.copy()
            seed.scale(0.001, about_point=position)
            seed.set_opacity(0)

            muzzle = 0.32 * np.array(
                [np.cos(theta), np.sin(theta), 0.0]
            )
            beam = Line(
                muzzle,
                position,
                color=c_gold,
                stroke_width=3.5,
            )
            seed_animations.append(
                Succession(
                    Create(beam, rate_func=rate_functions.ease_out_cubic),
                    FadeOut(beam, rate_func=linear),
                    Transform(
                        seed,
                        target_seed,
                        rate_func=rate_functions.ease_out_back,
                    ),
                )
            )
            seed_targets.append(seed)
            seed_angles.append(theta)

        seeds = VGroup(*seed_targets)

        turret_base = Circle(
            radius=0.17,
            stroke_color=c_center,
            stroke_width=2,
            fill_color="#000000",
            fill_opacity=1,
        )
        barrel = Polygon(
            np.array([0.0, -0.045, 0.0]),
            np.array([0.32, -0.035, 0.0]),
            np.array([0.32, 0.035, 0.0]),
            np.array([0.0, 0.045, 0.0]),
            stroke_color=c_gold,
            stroke_width=1,
            fill_color=c_gold,
            fill_opacity=0.9,
        )
        turret = VGroup(turret_base, barrel)
        turret_angle = 0.0
        shot_index = ValueTracker(0)

        def update_turret(mob):
            nonlocal turret_angle
            index = min(
                int(shot_index.get_value()),
                num_seeds - 1,
            )
            target_angle = seed_angles[index]
            angle_delta = (target_angle - turret_angle + PI) % TAU - PI
            mob.rotate(angle_delta, about_point=ORIGIN)
            turret_angle = target_angle

        turret.add_updater(update_turret)
        self.add(seeds, turret)

        self.wait(0.5)
        self.play(
            LaggedStart(*seed_animations, lag_ratio=0.1),
            shot_index.animate.set_value(num_seeds - 1),
            run_time=3.5,
        )
        self.wait(0.5)
