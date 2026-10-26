from _packing_scene import AngularSeedPacking
import numpy as np


class SqrtTwoPacking(AngularSeedPacking):
    alpha = 2 * np.pi * np.sqrt(2)
    angle_label = (
        r"\alpha = 2\pi\sqrt{2}"
        r"\quad(\Delta\theta \equiv 149.12^\circ)"
    )
    inner_color = "#55C9B8"
    outer_color = "#8BD9C8"
    laser_color = "#B7FFF2"
