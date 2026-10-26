from math import pi

from _packing_scene import AngularSeedPacking


class PiPacking(AngularSeedPacking):
    alpha = pi
    angle_label = r"\alpha = \pi\ \mathrm{rad} = 180^\circ"
    inner_color = "#F4A261"
    outer_color = "#E9C46A"
    laser_color = "#FFE2A8"
