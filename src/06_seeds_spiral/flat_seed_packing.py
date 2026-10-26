from manim import *
import numpy as np


config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60


class FlatSeedPacking(MovingCameraScene):
    def construct(self):
        self.camera.background_color = "#000000"

        packing_radius = 3.05
        seed_diameter = 0.40
        seed_radius = seed_diameter / 2
        ray_count = 12
        row_time = 0.42
        pi_approx = 22 / 7

        seed_inner = ManimColor("#89DCEB")
        seed_outer = ManimColor("#CBA6F7")
        pi_seed_inner = ManimColor("#F4A261")
        pi_seed_outer = ManimColor("#E9C46A")
        laser_inner = ManimColor("#D5FAFF")
        laser_outer = ManimColor("#EAD8FF")
        turret_color = "#A9E7EF"
        guide_color = "#CBA6F7"

        boundary = Circle(
            radius=packing_radius,
            stroke_color=guide_color,
            stroke_width=1.2,
            stroke_opacity=0.16,
            fill_color="#CBA6F7",
            fill_opacity=0,
        )

        base = Circle(
            radius=0.18,
            stroke_color=turret_color,
            stroke_width=2,
            fill_color="#10151A",
            fill_opacity=1,
        )
        barrel = Polygon(
            np.array([-0.035, 0.0, 0.0]),
            np.array([-0.028, 0.34, 0.0]),
            np.array([0.028, 0.34, 0.0]),
            np.array([0.035, 0.0, 0.0]),
            stroke_color=turret_color,
            stroke_width=1.2,
            fill_color=turret_color,
            fill_opacity=0.9,
        )
        hub = Circle(
            radius=0.06,
            stroke_width=0,
            fill_color="#D5FAFF",
            fill_opacity=1,
        )
        turret = VGroup(base, barrel, hub)
        laser = Line(
            0.2 * UP,
            packing_radius * UP,
            color=laser_inner,
            stroke_width=2.5,
            stroke_opacity=0,
        )

        minimum_center_radius = (
            seed_diameter / (2 * np.sin(PI / ray_count)) + 0.015
        )
        radial_steps = int(
            (packing_radius - seed_radius - minimum_center_radius)
            / seed_diameter
        ) + 1
        ray_angles = [
            PI / 2 - ray_index * TAU / ray_count
            for ray_index in range(ray_count)
        ]
        ray_points = [
            [
                np.array([np.cos(theta), np.sin(theta), 0.0])
                * (minimum_center_radius + step * seed_diameter)
                for step in range(radial_steps)
            ]
            for theta in ray_angles
        ]

        seed_centers = [point for points in ray_points for point in points]
        for index, first in enumerate(seed_centers):
            for second in seed_centers[index + 1 :]:
                assert np.linalg.norm(first - second) >= seed_diameter - 1e-6

        seed_count = len(seed_centers)
        disk_area = pi_approx * packing_radius**2
        filled_area = seed_count * pi_approx * seed_radius**2
        filled_percent = 100 * filled_area / disk_area

        all_seeds = VGroup()
        seed_colors = []
        ray_seed_groups = []
        ray_seed_targets = []
        for ray_index, points in enumerate(ray_points):
            color_ratio = ray_index / max(ray_count - 1, 1)
            seed_color = interpolate_color(
                seed_inner,
                seed_outer,
                color_ratio,
            )
            seed_colors.extend([seed_color] * len(points))

            row_seeds = VGroup()
            row_targets = VGroup()
            for position in points:
                seed = Circle(
                    radius=seed_radius,
                    stroke_color=seed_color,
                    stroke_width=1.0,
                    stroke_opacity=0.9,
                    fill_color=seed_color,
                    fill_opacity=0.56,
                ).move_to(position)
                target = seed.copy()
                seed.scale(0.001, about_point=position)
                seed.set_opacity(0)
                all_seeds.add(seed)
                row_seeds.add(seed)
                row_targets.add(target)
            ray_seed_groups.append(row_seeds)
            ray_seed_targets.append(row_targets)

        def build_ray_animations():
            animations = []
            previous_angle = PI / 2
            for ray_index, (theta, points, row_seeds, row_targets) in enumerate(
                zip(
                    ray_angles,
                    ray_points,
                    ray_seed_groups,
                    ray_seed_targets,
                    strict=True,
                )
            ):
                color_ratio = ray_index / max(ray_count - 1, 1)
                laser_color = interpolate_color(
                    laser_inner,
                    laser_outer,
                    color_ratio,
                )
                seed_animations = [
                    Transform(
                        seed,
                        target,
                        rate_func=rate_functions.ease_out_back,
                    )
                    for seed, target in zip(
                        row_seeds,
                        row_targets,
                        strict=True,
                    )
                ]
                direction = np.array(
                    [np.cos(theta), np.sin(theta), 0.0]
                )
                muzzle_radius = 0.2

                def draw_laser(
                    mob,
                    alpha,
                    angle=theta,
                    color=laser_color,
                ):
                    beam_direction = np.array(
                        [np.cos(angle), np.sin(angle), 0.0]
                    )
                    mob.put_start_and_end_on(
                        muzzle_radius * beam_direction,
                        (
                            muzzle_radius
                            + alpha * (packing_radius - muzzle_radius)
                        )
                        * beam_direction,
                    )
                    mob.set_stroke(color=color, opacity=0.9)

                animations.append(
                    Succession(
                        Rotate(
                            turret,
                            angle=theta - previous_angle,
                            about_point=ORIGIN,
                            rate_func=linear,
                            run_time=0.08,
                        ),
                        UpdateFromAlphaFunc(
                            laser,
                            draw_laser,
                            rate_func=linear,
                            run_time=0.16,
                        ),
                        FadeOut(laser, rate_func=linear, run_time=0.06),
                        LaggedStart(
                            *seed_animations,
                            lag_ratio=0.18,
                            run_time=row_time - 0.30,
                        ),
                        run_time=row_time,
                    )
                )
                previous_angle = theta
            return animations

        self.play(FadeIn(turret), run_time=0.8)
        self.play(
            Create(boundary, rate_func=rate_functions.ease_out_sine),
            run_time=1.2,
        )
        self.add(laser, all_seeds)
        self.play(Succession(*build_ray_animations()))

        first_ray = Line(
            0.22
            * np.array([np.cos(ray_angles[0]), np.sin(ray_angles[0]), 0.0]),
            packing_radius
            * np.array([np.cos(ray_angles[0]), np.sin(ray_angles[0]), 0.0]),
            color=seed_inner,
            stroke_width=1.1,
            stroke_opacity=0.3,
        )
        second_ray = Line(
            0.22
            * np.array([np.cos(ray_angles[1]), np.sin(ray_angles[1]), 0.0]),
            packing_radius
            * np.array([np.cos(ray_angles[1]), np.sin(ray_angles[1]), 0.0]),
            color=seed_outer,
            stroke_width=1.1,
            stroke_opacity=0.3,
        )
        angle_arc = Arc(
            radius=0.64,
            start_angle=ray_angles[1],
            angle=PI / 6,
            color="#F4FAFF",
            stroke_width=2,
        )
        angle_label = MathTex(
            r"30^\circ",
            color="#F4FAFF",
            font_size=32,
        ).move_to(
            2.45
            * np.array(
                [
                    np.cos((ray_angles[0] + ray_angles[1]) / 2),
                    np.sin((ray_angles[0] + ray_angles[1]) / 2),
                    0.0,
                ]
            )
        )
        fraction_label = MathTex(
            r"\frac{1}{12}",
            color="#F4FAFF",
            font_size=38,
        ).move_to(np.array([0.0, -3.72, 0.0]))
        self.play(
            Create(first_ray),
            Create(second_ray),
            Create(angle_arc),
            FadeIn(angle_label),
            FadeIn(fraction_label),
            run_time=0.8,
        )

        count_label = MathTex(
            rf"N = {seed_count}",
            color="#F4FAFF",
            font_size=38,
        ).move_to(np.array([0.0, 4.05, 0.0]))
        fill_label = MathTex(
            rf"\eta = \frac{{N\pi r^2}}{{\pi R^2}}"
            rf" \approx {filled_percent:.1f}\%",
            color="#F9E2AF",
            font_size=30,
        ).move_to(np.array([0.0, 3.48, 0.0]))

        glow_groups_by_height = {}
        for seed, color in zip(all_seeds, seed_colors, strict=True):
            center = seed.get_center()
            band = int((packing_radius - center[1]) / seed_diameter)
            glow = Circle(
                radius=seed_radius * 1.12,
                stroke_color=color,
                stroke_width=5,
                stroke_opacity=0.7,
                fill_opacity=0,
            ).move_to(center)
            glow_groups_by_height.setdefault(band, VGroup()).add(glow)
        glow_bands = [
            glow_groups_by_height[band]
            for band in sorted(glow_groups_by_height)
        ]
        glow_sweep = LaggedStart(
            *[
                Succession(
                    FadeIn(group, rate_func=rate_functions.ease_out_sine),
                    FadeOut(group, rate_func=rate_functions.ease_in_sine),
                )
                for group in glow_bands
            ],
            lag_ratio=0.13,
            run_time=2.1,
        )
        self.add(*glow_bands)
        self.play(
            glow_sweep,
            all_seeds.animate.set_fill(opacity=0.72).set_stroke(
                opacity=1,
                width=1.4,
            ),
            FadeIn(count_label, shift=0.12 * DOWN),
            FadeIn(fill_label, shift=0.12 * DOWN),
            run_time=2.1,
        )
        self.wait(0.5)

        self.play(
            all_seeds.animate.set_fill(opacity=0.16).set_stroke(
                opacity=0.25,
                width=1.0,
            ),
            count_label.animate.set_opacity(0.18),
            fill_label.animate.set_opacity(0.18),
            Create(first_ray),
            Create(second_ray),
            Create(angle_arc),
            FadeIn(angle_label),
            FadeIn(fraction_label),
            run_time=0.9,
        )
        self.wait(0.5)

        self.play(
            FadeOut(all_seeds),
            FadeOut(laser),
            FadeOut(first_ray),
            FadeOut(second_ray),
            FadeOut(angle_arc),
            FadeOut(angle_label),
            FadeOut(fraction_label),
            FadeOut(count_label),
            FadeOut(fill_label),
            run_time=0.8,
        )

        pi_label = MathTex(
            r"\pi \approx \frac{22}{7}",
            color="#F9E2AF",
            font_size=38,
        ).move_to(np.array([0.0, -4.15, 0.0]))
        self.play(FadeIn(pi_label, shift=0.12 * UP), run_time=0.6)

        lattice_spacing_y = seed_diameter * np.sqrt(3) / 2
        max_lattice_row = int(packing_radius / lattice_spacing_y) + 1
        max_lattice_column = int(packing_radius / seed_diameter) + 1
        efficient_centers = []
        for row in range(-max_lattice_row, max_lattice_row + 1):
            y = row * lattice_spacing_y
            x_offset = (row % 2) * seed_diameter / 2
            for column in range(-max_lattice_column, max_lattice_column + 1):
                x = column * seed_diameter + x_offset
                center = np.array([x, y, 0.0])
                if np.linalg.norm(center) <= packing_radius - seed_radius:
                    efficient_centers.append(center)

        for index, first in enumerate(efficient_centers):
            for second in efficient_centers[index + 1 :]:
                assert np.linalg.norm(first - second) >= seed_diameter - 1e-6

        efficient_count = len(efficient_centers)
        efficient_percent = 100 * efficient_count * seed_radius**2 / packing_radius**2
        efficient_seeds = VGroup()
        efficient_shots = []
        efficient_color = ManimColor("#F4A261")
        efficient_highlight = ManimColor("#E9C46A")
        sorted_centers = sorted(
            efficient_centers,
            key=lambda point: (np.linalg.norm(point), np.arctan2(point[1], point[0])),
        )
        for index, center in enumerate(sorted_centers):
            color_ratio = index / max(len(sorted_centers) - 1, 1)
            seed_color = interpolate_color(
                efficient_color,
                efficient_highlight,
                color_ratio,
            )
            seed = Circle(
                radius=seed_radius,
                stroke_color=seed_color,
                stroke_width=1.0,
                stroke_opacity=0.95,
                fill_color=seed_color,
                fill_opacity=0.78,
            ).move_to(center)
            seed.scale(0.001, about_point=center)
            seed.set_opacity(0)
            efficient_seeds.add(seed)

            center_norm = np.linalg.norm(center)
            if center_norm < 1e-9:
                efficient_shots.append(
                    Transform(
                        seed,
                        Circle(
                            radius=seed_radius,
                            stroke_color=seed_color,
                            stroke_width=1.0,
                            stroke_opacity=0.95,
                            fill_color=seed_color,
                            fill_opacity=0.78,
                        ).move_to(center),
                        rate_func=rate_functions.ease_out_back,
                        run_time=0.05,
                    )
                )
                continue

            beam = Line(
                0.2 * (center / center_norm),
                center,
                color=seed_color,
                stroke_width=1.5,
            )
            target = Circle(
                radius=seed_radius,
                stroke_color=seed_color,
                stroke_width=1.0,
                stroke_opacity=0.95,
                fill_color=seed_color,
                fill_opacity=0.78,
            ).move_to(center)
            efficient_shots.append(
                Succession(
                    Create(beam, rate_func=linear, run_time=0.018),
                    FadeOut(beam, rate_func=linear, run_time=0.008),
                    Transform(
                        seed,
                        target,
                        rate_func=rate_functions.ease_out_back,
                        run_time=0.024,
                    ),
                )
            )

        self.add(efficient_seeds)
        self.play(Succession(*efficient_shots))

        efficient_count_label = MathTex(
            rf"N = {efficient_count}",
            color="#F4FAFF",
            font_size=38,
        ).move_to(np.array([0.0, 4.05, 0.0]))
        efficient_percent_label = MathTex(
            rf"\eta = \frac{{N\pi r^2}}{{\pi R^2}}"
            rf" \approx {efficient_percent:.1f}\%",
            color="#F9E2AF",
            font_size=30,
        ).move_to(np.array([0.0, 3.48, 0.0]))
        self.play(
            FadeIn(efficient_count_label, shift=0.12 * DOWN),
            FadeIn(efficient_percent_label, shift=0.12 * DOWN),
            run_time=0.8,
        )
        self.wait(1.5)
