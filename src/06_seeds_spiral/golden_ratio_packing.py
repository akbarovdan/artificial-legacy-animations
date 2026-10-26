from _packing_scene import AngularSeedPacking
import numpy as np


class GoldenRatioPacking(AngularSeedPacking):
    alpha = np.radians(137.507764)
    angle_label = r"\alpha \approx 137.508^\circ"
    inner_color = "#E9A86C"
    outer_color = "#F1D27A"
    laser_color = "#FFE8A6"
