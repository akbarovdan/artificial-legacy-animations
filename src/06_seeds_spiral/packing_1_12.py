from math import pi

from _packing_scene import AngularSeedPacking


class OneTwelfthPacking(AngularSeedPacking):
    alpha = 2 * pi / 12
    angle_label = (
        r"\alpha = \frac{2\pi}{12} = 30^\circ"
        r"\quad\left(\frac{1}{12}\ \mathrm{turn}\right)"
    )
    inner_color = "#89DCEB"
    outer_color = "#CBA6F7"
    laser_color = "#D5FAFF"
