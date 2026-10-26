from manim import (
    AnimationGroup,
    Circle,
    Create,
    DOWN,
    FadeIn,
    ManimColor,
    MathTex,
    Line,
    MovingCameraScene,
    ORIGIN,
    PI,
    Polygon,
    rate_functions,
    Rotate,
    ShowPassingFlash,
    Succession,
    TAU,
    VGroup,
    config,
    interpolate_color,
    linear,
)
import numpy as np


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60
config.background_color = ManimColor("#000000")


class AngularSeedPacking(MovingCameraScene):
    alpha = TAU / 12
    angle_label = r"\alpha = \frac{2\pi}{12} = 30^\circ"
    inner_color = "#89DCEB"
    outer_color = "#CBA6F7"

    def construct(self):
        field_radius = 3.0
        seed_radius = 0.12
        min_center_distance = 2 * seed_radius + 0.008
        muzzle_radius = 0.40
        field_limit = field_radius - seed_radius

        positions = []
        angles = []
        unit_points = []
        minimum_distance = float("inf")
        best_count = 0
        best_scale = 0.0

        for index in range(1, 1201):
            theta = index * self.alpha
            point = np.array(
                [
                    np.sqrt(index) * np.cos(theta),
                    np.sqrt(index) * np.sin(theta),
                    0.0,
                ]
            )
            if unit_points:
                distances = np.linalg.norm(
                    np.asarray(unit_points) - point,
                    axis=1,
                )
                minimum_distance = min(
                    minimum_distance,
                    float(np.min(distances)),
                )

            unit_points.append(point)
            scale = min_center_distance / minimum_distance
            if scale * np.sqrt(index) <= field_limit:
                best_count = index
                best_scale = scale
            elif best_count:
                break

        if best_count == 0:
            raise RuntimeError("Could not fit seeds inside the packing field.")

        for index, point in enumerate(unit_points[:best_count], start=1):
            position = best_scale * point
            if np.linalg.norm(position) < muzzle_radius + seed_radius + 0.03:
                continue
            positions.append(position)
            angles.append(index * self.alpha)

        for first_index, first in enumerate(positions):
            for second in positions[first_index + 1 :]:
                if np.linalg.norm(first - second) < min_center_distance - 1e-6:
                    raise RuntimeError("Generated seed positions overlap.")

        seed_count = len(positions)
        filled_percent = 100 * seed_count * seed_radius**2 / field_radius**2
        seed_colors = [
            interpolate_color(
                ManimColor(self.inner_color),
                ManimColor(self.outer_color),
                index / max(seed_count - 1, 1),
            )
            for index in range(seed_count)
        ]

        boundary = Circle(
            radius=field_radius,
            stroke_color=self.outer_color,
            stroke_width=1.3,
            stroke_opacity=0.22,
        )

        turret_base = Circle(
            radius=0.18,
            stroke_color="#A9E7EF",
            stroke_width=2.0,
            fill_color="#10151A",
            fill_opacity=1,
        )
        turret_barrel = Polygon(
            np.array([-0.035, 0.06, 0.0]),
            np.array([-0.025, 0.40, 0.0]),
            np.array([0.025, 0.40, 0.0]),
            np.array([0.035, 0.06, 0.0]),
            stroke_color="#A9E7EF",
            stroke_width=1.2,
            fill_color="#A9E7EF",
            fill_opacity=0.95,
        )
        turret_hub = Circle(
            radius=0.055,
            stroke_width=0,
            fill_color="#D5FAFF",
            fill_opacity=1,
        )
        turret = VGroup(turret_base, turret_barrel, turret_hub)

        angle_label = MathTex(
            self.angle_label,
            color=self.outer_color,
            font_size=32,
        ).move_to(np.array([0.0, 4.55, 0.0]))
        count_label = MathTex(
            rf"N = {seed_count}",
            color="#F4FAFF",
            font_size=38,
        ).move_to(np.array([0.0, 3.95, 0.0]))
        fill_label = MathTex(
            rf"\eta \approx {filled_percent:.1f}\%",
            color=self.outer_color,
            font_size=36,
        ).move_to(np.array([0.0, 3.38, 0.0]))

        self.play(
            FadeIn(turret),
            Create(boundary),
            FadeIn(angle_label, shift=0.1 * DOWN),
            run_time=0.9,
        )

        shots = []
        turret_angle = PI / 2
        step_time = max(0.07, min(0.18, 16 / seed_count))

        for position, theta, color in zip(
            positions,
            angles,
            seed_colors,
            strict=True,
        ):
            turn = (theta - turret_angle + PI) % TAU - PI
            turret_angle += turn
            direction = np.array(
                [np.cos(theta), np.sin(theta), 0.0]
            )
            muzzle = muzzle_radius * direction
            seed = Circle(
                radius=seed_radius,
                stroke_color=color,
                stroke_width=1.0,
                stroke_opacity=0.95,
                fill_color=color,
                fill_opacity=0.7,
            ).move_to(position)
            beam_glow = Line(
                muzzle,
                position,
                color=color,
                stroke_width=7,
            ).set_stroke(opacity=0.32).set_stroke(opacity=0.32)
            beam_core = Line(
                muzzle,
                position,
                color="#F4FAFF",
                stroke_width=2,
            )

            shots.append(
                Succession(
                    Rotate(
                        turret,
                        angle=turn,
                        about_point=ORIGIN,
                        rate_func=linear,
                        run_time=step_time * 0.28,
                    ),
                    AnimationGroup(
                        Create(beam_glow, rate_func=linear),
                        Create(beam_core, rate_func=linear),
                        lag_ratio=0,
                        run_time=step_time * 0.42,
                    ),
                    AnimationGroup(
                        ShowPassingFlash(
                            beam_glow,
                            time_width=0.16,
                            rate_func=linear,
                        ),
                        ShowPassingFlash(
                            beam_core,
                            time_width=0.16,
                            rate_func=linear,
                        ),
                        lag_ratio=0,
                        run_time=step_time * 0.15,
                    ),
                    FadeIn(
                        seed,
                        scale=0.1,
                        rate_func=rate_functions.ease_out_back,
                        run_time=step_time * 0.15,
                    ),
                )
            )

        self.play(Succession(*shots))

        self.play(
            FadeIn(count_label, shift=0.1 * DOWN),
            FadeIn(fill_label, shift=0.1 * DOWN),
            run_time=0.6,
        )
        self.wait(1.0)
