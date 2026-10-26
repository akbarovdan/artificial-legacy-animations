from dataclasses import dataclass
from math import ceil, e, floor, pi, sqrt

from manim import (
    AnimationGroup,
    Arc,
    Circle,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    Line,
    LaggedStart,
    ManimColor,
    MathTex,
    MovingCameraScene,
    ORIGIN,
    PI,
    Polygon,
    Rotate,
    ShowPassingFlash,
    Succession,
    TAU,
    Text,
    Transform,
    VGroup,
    config,
    interpolate_color,
    linear,
    rate_functions,
)
import numpy as np


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60
config.background_color = "#000000"


@dataclass(frozen=True)
class PackingPattern:
    name: str
    alpha: float
    formula: str
    inner_color: str
    outer_color: str
    radial_layers: int | None = None


PATTERNS = (
    PackingPattern(
        name="1/12 оборота",
        alpha=2 * pi / 12,
        formula=r"\alpha = \frac{2\pi}{12} = 30^\circ",
        inner_color="#89DCEB",
        outer_color="#CBA6F7",
        radial_layers=12,
    ),
    PackingPattern(
        name="π",
        alpha=TAU * (pi % 1),
        formula=r"\alpha = 2\pi(\pi \bmod 1) \approx 50.97^\circ",
        inner_color="#F4A261",
        outer_color="#E9C46A",
    ),
    PackingPattern(
        name="√2",
        alpha=2 * pi * sqrt(2),
        formula=(
            r"\alpha = 2\pi\sqrt{2}"
            r"\quad(\Delta\theta \equiv 149.12^\circ)"
        ),
        inner_color="#55C9B8",
        outer_color="#8BD9C8",
    ),
    PackingPattern(
        name="e",
        alpha=TAU * (e % 1),
        formula=r"\alpha = 2\pi(e \bmod 1) \equiv -101.42^\circ",
        inner_color="#B58AE8",
        outer_color="#D6B8FF",
    ),
    PackingPattern(
        name="√3",
        alpha=TAU * (sqrt(3) % 1),
        formula=r"\alpha = 2\pi(\sqrt{3} \bmod 1) \equiv -96.46^\circ",
        inner_color="#6FA8DC",
        outer_color="#A4CEF3",
    ),
    PackingPattern(
        name="Золотой угол",
        alpha=np.radians(137.507764),
        formula=r"\alpha \approx 137.508^\circ",
        inner_color="#E9A86C",
        outer_color="#F1D27A",
    ),
)


class PackingProgression(MovingCameraScene):
    field_radius = 3.0
    seed_radius = 0.12
    radial_scale = 0.1576
    turret_muzzle_radius = 0.40
    minimum_center_distance = 2 * seed_radius + 0.008
    boundary_run_time = 0.8
    stage_intro_run_time = 0.8
    transition_run_time = 0.7
    highlight_run_time = 1.25
    metric_run_time = 0.6
    metric_hold_time = 0.8
    final_hold_time = 1.0

    def get_first_index(self):
        return ceil(
            (
                self.turret_muzzle_radius
                + self.seed_radius
                + 0.008
            )
            ** 2
            / self.radial_scale**2
        )

    def get_pattern_seeds(self, pattern):
        """Keep the field, first seed radius, and seed size fixed for every pattern."""
        first_index = self.get_first_index()
        first_radius = self.radial_scale * sqrt(first_index)
        spoke_spacing = self.minimum_center_distance + 0.008
        if pattern.radial_layers is None:
            last_index = floor(
                (self.field_radius - self.seed_radius) ** 2
                / self.radial_scale**2
            )
        else:
            layer_count = floor(
                (self.field_radius - self.seed_radius - first_radius)
                / spoke_spacing
            ) + 1
            last_index = (
                first_index
                + layer_count * pattern.radial_layers
                - 1
            )
        accepted = []

        for index in range(first_index, last_index + 1):
            step = index - first_index
            theta = PI / 2 + step * pattern.alpha
            if pattern.radial_layers is None:
                radius = self.radial_scale * sqrt(index)
            else:
                radius = (
                    first_radius
                    + (step // pattern.radial_layers) * spoke_spacing
                )
            position = radius * np.array(
                [np.cos(theta), np.sin(theta), 0.0]
            )
            if all(
                np.linalg.norm(position - previous)
                >= self.minimum_center_distance - 1e-6
                for previous, _ in accepted
            ):
                accepted.append((position, theta))

        return accepted

    def get_stage_schedule(self):
        schedule = []
        start_time = self.boundary_run_time + self.stage_intro_run_time

        for stage_index, pattern in enumerate(PATTERNS):
            seed_data = self.get_pattern_seeds(pattern)
            step_time = max(0.045, min(0.18, 10 / max(len(seed_data), 1)))
            schedule.append((stage_index, pattern, seed_data, step_time, start_time))
            start_time += (
                len(seed_data) * step_time
                + max(self.highlight_run_time, self.metric_run_time)
                + self.metric_hold_time
            )
            if stage_index < len(PATTERNS) - 1:
                start_time += self.transition_run_time

        return schedule, start_time + self.final_hold_time

    def make_turret(self):
        base = Circle(
            radius=0.18,
            stroke_color="#A9E7EF",
            stroke_width=2.0,
            fill_color="#10151A",
            fill_opacity=1,
        )
        barrel = Polygon(
            np.array([-0.035, 0.06, 0.0]),
            np.array([-0.025, 0.40, 0.0]),
            np.array([0.025, 0.40, 0.0]),
            np.array([0.035, 0.06, 0.0]),
            stroke_color="#A9E7EF",
            stroke_width=1.2,
            fill_color="#A9E7EF",
            fill_opacity=0.95,
        )
        hub = Circle(
            radius=0.055,
            stroke_width=0,
            fill_color="#D5FAFF",
            fill_opacity=1,
        )
        return VGroup(base, barrel, hub)

    def make_seed(self, position, color):
        return Circle(
            radius=self.seed_radius,
            stroke_color=color,
            stroke_width=1.0,
            stroke_opacity=0.95,
            fill_color=color,
            fill_opacity=0.7,
        ).move_to(position)

    def make_angle_indicator(self, pattern):
        delta = (pattern.alpha + PI) % TAU - PI
        reference_direction = np.array([0.0, 1.0, 0.0])
        rotated_direction = np.array(
            [np.cos(PI / 2 + delta), np.sin(PI / 2 + delta), 0.0]
        )
        reference_ray = Line(
            0.22 * reference_direction,
            0.41 * reference_direction,
            color="#F4FAFF",
            stroke_width=1.6,
            stroke_opacity=0.42,
        )
        rotated_ray = Line(
            0.22 * rotated_direction,
            0.41 * rotated_direction,
            color=pattern.outer_color,
            stroke_width=2,
            stroke_opacity=0.6,
        )
        angle_arc = Arc(
            radius=0.32,
            start_angle=PI / 2,
            angle=delta,
            color=pattern.outer_color,
            stroke_width=2.5,
        )
        return VGroup(reference_ray, rotated_ray, angle_arc)

    def make_shot(self, turret, position, theta, color, step_time):
        direction = np.array([np.cos(theta), np.sin(theta), 0.0])
        muzzle = self.turret_muzzle_radius * direction
        glow = Line(
            muzzle,
            position,
            color=color,
            stroke_width=7,
        ).set_stroke(opacity=0.32)
        core = Line(
            muzzle,
            position,
            color="#F4FAFF",
            stroke_width=2,
        )
        seed = self.make_seed(position, color)
        turn = (theta - self.turret_angle + PI) % TAU - PI
        self.turret_angle += turn

        return Succession(
            Rotate(
                turret,
                angle=turn,
                about_point=ORIGIN,
                rate_func=linear,
                run_time=step_time * 0.28,
            ),
            AnimationGroup(
                Create(glow, rate_func=linear),
                Create(core, rate_func=linear),
                lag_ratio=0,
                run_time=step_time * 0.42,
            ),
            AnimationGroup(
                ShowPassingFlash(glow, time_width=0.16, rate_func=linear),
                ShowPassingFlash(core, time_width=0.16, rate_func=linear),
                lag_ratio=0,
                run_time=step_time * 0.15,
            ),
            FadeIn(
                seed,
                scale=0.1,
                rate_func=rate_functions.ease_out_back,
                run_time=step_time * 0.15,
            ),
        ), seed

    def construct(self):
        schedule, _ = self.get_stage_schedule()

        boundary = Circle(
            radius=self.field_radius,
            stroke_color="#CBA6F7",
            stroke_width=1.3,
            stroke_opacity=0.22,
        )
        inner_boundary = Circle(
            radius=(
                self.radial_scale * sqrt(self.get_first_index())
                - self.seed_radius
            ),
            stroke_color="#A9E7EF",
            stroke_width=1.3,
            stroke_opacity=0.35,
        )
        self.play(
            Create(boundary),
            Create(inner_boundary),
            run_time=self.boundary_run_time,
        )

        turret = self.make_turret()
        self.turret_angle = PI / 2
        first_pattern = PATTERNS[0]
        angle_formula = MathTex(
            first_pattern.formula,
            color=first_pattern.outer_color,
            font_size=34,
        ).move_to(np.array([0.0, 5.1, 0.0]))
        stage_name = Text(
            first_pattern.name,
            color=first_pattern.outer_color,
            font_size=38,
        ).move_to(np.array([0.0, -4.25, 0.0]))
        angle_indicator = self.make_angle_indicator(first_pattern)
        current_seeds = []
        count_label = None
        fill_label = None

        for pattern_index, (
            _,
            pattern,
            seed_data,
            step_time,
            _,
        ) in enumerate(schedule):
            next_formula = MathTex(
                pattern.formula,
                color=pattern.outer_color,
                font_size=34,
            ).move_to(np.array([0.0, 5.1, 0.0]))
            next_name = Text(
                pattern.name,
                color=pattern.outer_color,
                font_size=38,
            ).move_to(np.array([0.0, -4.25, 0.0]))
            next_indicator = self.make_angle_indicator(pattern)

            if pattern_index:
                fading = [FadeOut(seed) for seed in current_seeds]
                if count_label is not None:
                    fading.append(FadeOut(count_label))
                if fill_label is not None:
                    fading.append(FadeOut(fill_label))
                fading.append(FadeOut(angle_indicator))
                self.play(
                    AnimationGroup(*fading, lag_ratio=0),
                    Transform(angle_formula, next_formula),
                    Transform(stage_name, next_name),
                    FadeIn(next_indicator),
                    run_time=self.transition_run_time,
                )
                angle_indicator = next_indicator
                current_seeds = []
                count_label = None
                fill_label = None
            else:
                self.play(
                    FadeIn(turret),
                    FadeIn(angle_formula),
                    FadeIn(stage_name),
                    Create(angle_indicator),
                    run_time=self.stage_intro_run_time,
                )

            count = len(seed_data)
            colors = [
                interpolate_color(
                    ManimColor(pattern.inner_color),
                    ManimColor(pattern.outer_color),
                    index / max(count - 1, 1),
                )
                for index in range(count)
            ]
            shot_animations = []

            for (position, theta), color in zip(
                seed_data,
                colors,
                strict=True,
            ):
                shot, seed = self.make_shot(
                    turret,
                    position,
                    theta,
                    color,
                    step_time,
                )
                shot_animations.append(shot)
                current_seeds.append(seed)

            self.play(Succession(*shot_animations))
            sweep_order = sorted(
                zip(current_seeds, colors, strict=True),
                key=lambda item: item[0].get_center()[1],
                reverse=False,
            )

            fill_percent = (
                100
                * count
                * self.seed_radius**2
                / self.field_radius**2
            )
            count_label = MathTex(
                rf"N = {count}",
                color="#F4FAFF",
                font_size=38,
            ).move_to(np.array([0.0, 4.45, 0.0]))
            fill_label = MathTex(
                rf"\eta \approx {fill_percent:.1f}\%",
                color=pattern.outer_color,
                font_size=36,
            ).move_to(np.array([0.0, 3.85, 0.0]))
            highlight_animations = [
                seed.animate.set_stroke(
                    color="#FFFFFF",
                    width=2.0,
                ).set_fill(
                    color=interpolate_color(
                        ManimColor(color),
                        ManimColor("#FFFFFF"),
                        0.42,
                    ),
                    opacity=0.98,
                )
                for seed, color in sweep_order
            ]
            self.play(
                AnimationGroup(
                    LaggedStart(*highlight_animations, lag_ratio=0.002),
                    FadeIn(count_label, shift=0.1 * DOWN),
                    FadeIn(fill_label, shift=0.1 * DOWN),
                    lag_ratio=0,
                ),
                run_time=max(
                    self.highlight_run_time,
                    self.metric_run_time,
                ),
            )
            self.wait(self.metric_hold_time)

        self.wait(self.final_hold_time)
