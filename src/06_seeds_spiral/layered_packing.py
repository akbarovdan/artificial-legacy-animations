from dataclasses import dataclass
from math import e, floor, pi, sqrt

import numpy as np
from manim import (
    AnimationGroup,
    Circle,
    Create,
    DOWN,
    Ellipse,
    FadeIn,
    FadeOut,
    LaggedStart,
    ManimColor,
    MathTex,
    MovingCameraScene,
    ORIGIN,
    PI,
    TAU,
    Text,
    Transform,
    VGroup,
    config,
    interpolate_color,
    rate_functions,
)


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60
config.background_color = "#08080C"


@dataclass(frozen=True)
class PackingPattern:
    key: str
    name: str
    alpha: float
    formula: str
    inner_color: str
    outer_color: str
    laser_color: str
    ui_label: str
    spokes: int | None = None


PATTERNS = (
    PackingPattern(
        key="rational_1_12",
        name="30°",
        alpha=TAU / 12,
        formula=r"\alpha = \frac{2\pi}{12} = 30^\circ",
        inner_color="#5EEAD4",
        outer_color="#0F766E",
        laser_color="#CCFBF1",
        ui_label="#5EEAD4",
        spokes=12,
    ),
    PackingPattern(
        key="pi",
        name="π",
        alpha=TAU * (pi % 1),
        formula=r"\alpha = 2\pi(\pi \bmod 1) \approx 50.97^\circ",
        inner_color="#FFB703",
        outer_color="#FB8500",
        laser_color="#FFF3B0",
        ui_label="#FB8500",
    ),
    PackingPattern(
        key="sqrt_2",
        name="√2",
        alpha=TAU * (sqrt(2) % 1),
        formula=r"\alpha = 2\pi\sqrt{2} \equiv 149.12^\circ",
        inner_color="#4ADE80",
        outer_color="#15803D",
        laser_color="#BBF7D0",
        ui_label="#4ADE80",
    ),
    PackingPattern(
        key="sqrt_3",
        name="√3",
        alpha=TAU * (sqrt(3) % 1),
        formula=r"\alpha = 2\pi(\sqrt{3} \bmod 1) \equiv -96.46^\circ",
        inner_color="#38BDF8",
        outer_color="#1E40AF",
        laser_color="#BAE6FD",
        ui_label="#38BDF8",
    ),
    PackingPattern(
        key="euler_e",
        name="e",
        alpha=TAU * (e % 1),
        formula=r"\alpha = 2\pi(e \bmod 1) \equiv -101.42^\circ",
        inner_color="#C084FC",
        outer_color="#581C87",
        laser_color="#F3E8FF",
        ui_label="#C084FC",
    ),
    PackingPattern(
        key="golden_angle",
        name="Golden Angle",
        alpha=np.radians(137.507764),
        formula=r"\alpha \approx 137.508^\circ",
        inner_color="#FFE6A7",
        outer_color="#D48B06",
        laser_color="#FFFFFF",
        ui_label="#FFE6A7",
    ),
)


class LayeredPacking(MovingCameraScene):
    field_radius = 3.45
    marble_radius = 0.17
    radial_scale = 0.22
    minimum_center_distance = 2 * marble_radius + 0.018
    reveal_run_time = 3.5
    highlight_run_time = 1.3
    metric_hold_time = 1.0
    transition_run_time = 0.7

    def get_pattern_seeds(
        self,
        pattern: PackingPattern,
    ) -> list[tuple[np.ndarray, float]]:
        max_radius = self.field_radius - self.marble_radius
        accepted = [(ORIGIN.copy(), PI / 2)]
        if pattern.spokes is not None:
            first_ring_radius = self.minimum_center_distance / (
                2 * np.sin(PI / pattern.spokes)
            )
            radial_spacing = self.minimum_center_distance + 0.002
            layer_count = floor(
                (max_radius - first_ring_radius) / radial_spacing
            ) + 1
            for layer in range(layer_count):
                radius = first_ring_radius + layer * radial_spacing
                for spoke in range(pattern.spokes):
                    theta = PI / 2 + spoke * pattern.alpha
                    position = radius * np.array(
                        [np.cos(theta), np.sin(theta), 0.0]
                    )
                    accepted.append((position, theta))
            return accepted

        last_index = floor((max_radius / self.radial_scale) ** 2)
        for index in range(1, last_index + 1):
            theta = PI / 2 + index * pattern.alpha
            radius = self.radial_scale * sqrt(index)
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

    def make_marble(
        self,
        position: np.ndarray,
        color: ManimColor,
    ) -> VGroup:
        halo = Circle(
            radius=self.marble_radius * 1.16,
            stroke_width=0,
            fill_color=color,
            fill_opacity=0.16,
        )
        body = Circle(
            radius=self.marble_radius,
            stroke_color=color,
            stroke_width=1.2,
            stroke_opacity=0.9,
            fill_color=color,
            fill_opacity=0.66,
        )
        glint = Ellipse(
            width=self.marble_radius * 0.74,
            height=self.marble_radius * 0.28,
            stroke_width=0,
            fill_color="#FFFFFF",
            fill_opacity=0.34,
        ).move_to(
            position
            + np.array(
                [-self.marble_radius * 0.16, self.marble_radius * 0.38, 0.0]
            )
        )
        halo.move_to(position)
        body.move_to(position)
        return VGroup(halo, body, glint)

    def spring_out_animation(
        self,
        marbles: VGroup,
    ) -> LaggedStart:
        animations = []
        for marble in marbles:
            target_state = marble.copy()
            marble.move_to(ORIGIN)
            marble.scale(0.001)
            marble.set_opacity(0)
            animations.append(
                Transform(
                    marble,
                    target_state,
                    rate_func=rate_functions.ease_out_back,
                )
            )
        return LaggedStart(*animations, lag_ratio=0.012)

    def make_stage_marbles(
        self,
        pattern: PackingPattern,
    ) -> tuple[VGroup, list[ManimColor]]:
        seed_data = self.get_pattern_seeds(pattern)
        max_radius = max(
            (float(np.linalg.norm(position)) for position, _ in seed_data),
            default=1.0,
        )
        marbles = VGroup()
        colors = []
        for position, _ in seed_data:
            rank_ratio = float(np.linalg.norm(position)) / max_radius
            color_ratio = rank_ratio**0.7
            color = interpolate_color(
                ManimColor(pattern.inner_color),
                ManimColor(pattern.outer_color),
                color_ratio,
            )
            marbles.add(self.make_marble(position, color))
            colors.append(color)
        return marbles, colors

    def construct(self) -> None:
        boundary = Circle(
            radius=self.field_radius,
            stroke_color="#2A2E3D",
            stroke_width=2.0,
            stroke_opacity=0.95,
        )
        self.play(
            Create(boundary, rate_func=rate_functions.ease_out_sine),
            run_time=0.9,
        )

        first_pattern = PATTERNS[0]
        formula = MathTex(
            first_pattern.formula,
            color=first_pattern.ui_label,
            font_size=32,
        ).move_to(np.array([0.0, 5.05, 0.0]))
        label = Text(
            first_pattern.name,
            color=first_pattern.ui_label,
            font_size=34,
        ).move_to(np.array([0.0, -4.4, 0.0]))
        metrics = VGroup()
        current_marbles = VGroup()
        current_colors: list[ManimColor] = []

        for pattern_index, pattern in enumerate(PATTERNS):
            next_formula = MathTex(
                pattern.formula,
                color=pattern.ui_label,
                font_size=32,
            ).move_to(np.array([0.0, 5.05, 0.0]))
            next_label = Text(
                pattern.name,
                color=pattern.ui_label,
                font_size=34,
            ).move_to(np.array([0.0, -4.4, 0.0]))
            if pattern_index:
                self.play(
                    FadeOut(current_marbles),
                    FadeOut(metrics),
                    Transform(formula, next_formula),
                    Transform(label, next_label),
                    run_time=0.7,
                )
            else:
                self.play(
                    FadeIn(formula),
                    FadeIn(label),
                    run_time=0.8,
                )

            current_marbles, current_colors = self.make_stage_marbles(pattern)
            self.play(
                self.spring_out_animation(current_marbles),
                run_time=self.reveal_run_time,
            )
            count = len(current_marbles)
            fill_percent = (
                100 * count * self.marble_radius**2 / self.field_radius**2
            )
            count_label = Text(
                f"Seed count: {count}",
                color="#F4F4F8",
                font_size=30,
            ).move_to(np.array([0.0, 4.42, 0.0]))
            fill_label = Text(
                f"Area coverage: {fill_percent:.1f}%",
                color=pattern.ui_label,
                font_size=30,
            ).move_to(np.array([0.0, 3.87, 0.0]))
            metrics = VGroup(count_label, fill_label)

            highlight_animations = []
            for marble, color in zip(
                current_marbles,
                current_colors,
                strict=True,
            ):
                halo, body, _ = marble
                highlight_animations.extend(
                    [
                        halo.animate.set_fill(opacity=0.34),
                        body.animate.set_stroke(
                            color="#FFFFFF",
                            width=2.0,
                        ).set_fill(
                            color=interpolate_color(
                                color,
                                ManimColor("#FFFFFF"),
                                0.36,
                            ),
                            opacity=0.96,
                        ),
                    ]
                )
            self.play(
                AnimationGroup(
                    LaggedStart(
                        *highlight_animations,
                        lag_ratio=0.0015,
                    ),
                    FadeIn(count_label, shift=0.1 * DOWN),
                    FadeIn(fill_label, shift=0.1 * DOWN),
                    lag_ratio=0,
                ),
                run_time=max(self.highlight_run_time, 0.6),
            )
            self.wait(self.metric_hold_time)

        self.wait(1.2)
