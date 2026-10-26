#!/usr/bin/env python3
"""
SYMMETRIC CHAOS -- vertical story for Shorts (9:16)
Symmetric fractals and icons in the spirit of Field & Golubitsky, "Symmetry in Chaos".
Pure black background, neon-pastel Catppuccin colours, Montserrat Light.
No Manim: numpy computes, Pillow draws, ffmpeg writes the mp4.

    pip install numpy scipy pillow matplotlib imageio-ffmpeg     (ffmpeg in PATH also works)
    pip install numba            # optional: ~20x faster single-dot trajectories

    python attractor_story.py --preview          # 540x960, 30 fps, fast check
    python attractor_story.py --final            # 1080x1920, 60 fps
    python attractor_story.py --list             # scenes and their durations
    python attractor_story.py --scenes hook,linear   # only some scenes
                              (hook, linear, nonlinear, sectors, twist, morph, figs)

SCENES (durations in TIMING below, seconds)
  hook       fractals morph into each other at normal speed: bee (D3) with a small morph -> wheel (Z7)
             -> saw (Z12) -> the "Fig. 7.18" set (8-fold colouring, then 4-fold)
  linear     z -> c*z: the equation, numbers under it, two dots draw a circle of points (no lines); then a disc of
             points goes through the same map: it rotates, shrinks, grows, and we fall into it (zoom
             in over the whole screen until it is dark)
  nonlinear  from the dark: a tiny disc of points; the nonlinear map is switched on, the disc is
             stretched and folded step by step, the traces build the attractor
  sectors    no fades: the picture is rewound -> drawn again, the five zones fade in and count the share
             of visits -> the picture expands
  twist      the term i*omega*z is switched on: the mirrors break, the crystal spins
  morph      lambda, alpha, beta, gamma change smoothly, a new colour family at every stop, the numbers
             fade away on the last leg; then more figures (flower, rounded triangle, clam, wild) follow
             in the same way, now slowly turning (no text)

VOICEOVER (English; one block per scene)
  hook       Symmetric chaos -- one of the most beautiful paradoxes in mathematics.
  linear     A linear equation can't do this. It's too predictable. The dot shrinks to zero,
             flies away, or circles forever.
  nonlinear  A nonlinear one stretches and folds. The stretching makes it unpredictable.
             Folding keeps it from escaping.
  sectors    The path stays chaotic, yet the picture is symmetrical. On average, the dot visits
             every direction equally.
  twist      Add one tiny twist to the equation, and the mirrors break. The crystal starts to spin.
  morph      Change the numbers, and you get a new crystal.

HONESTY NOTES
  * The hook figures are LOOKALIKES found by a random search over affine contractions and
    symmetry groups; they are not the exact figures (or parameters) from the book. The morph between
    them uses the same trick as the book's Fig. 7.18: changing how often each map is picked changes
    the picture's density/colour symmetry, not the underlying fractal set. If you want the book's
    own figures, take the parameters from the book's tables and put them into FRACTALS.
  * The crystal scenes use real single trajectories of the map ("one dot", millions of iterations).
    Only the twist/morph/hook scenes move a lot, so they use 20 000 dots at once.
  * Every number printed on screen (the z values, the distances, the percentages) is computed
    from the actual data.
  * The two dots in the nonlinear scene start 1e-9 apart; floating point limits mean that is about
    as close as a double can follow honestly, which is exactly what chaos amplifies.

The icon map:  F(z) = (lam + alpha|z|^2 + beta Re(z^n) + i*omega) z + gamma conj(z)^(n-1)
omega = 0 -> D_n symmetry (rotations + mirrors);  omega != 0 -> only Z_n (rotations).
"""
import argparse
import glob
import io
import math
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from scipy.ndimage import gaussian_filter

try:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import math_to_image
    HAVE_MPL = True
except Exception:                      # formulas fall back to plain text
    HAVE_MPL = False

try:
    from numba import njit
    HAVE_NUMBA = True
except Exception:
    HAVE_NUMBA = False

# ====================== SETTINGS ======================
FPS_FINAL = 60                 # --final
FPS_PREVIEW = 30               # --preview

# Run times in seconds. Tune these to your voice.
TIMING = dict(
    hook_leg=2.2,        # one morph between two fractals
    hook_hold=0.3,       # short hold on each fractal
    lin_step=0.11,       # one step of the linear map (a dot moves along a line)
    lin_hold=0.5,        # hold at the end of each behaviour
    nl_line_out=0.8,     # the tiny disc of points appears out of the dark
    br_blend=0.4,        # dotted circle -> the dots that draw the disc
    br_spin=2.8,         # the dots turn (|c| = 1) and draw the disc ring after ring
    br_hold=0.5,         # ... the finished disc keeps turning
    br_shrink=1.1,       # ... shrinks (|c| < 1)
    br_grow=1.0,         # ... grows (|c| > 1)
    br_zoom=1.7,         # ... and we fall into it: zoom in until it is dark
    nl_expand_slow=0.7,  # first steps of the map (stretch + fold), slow ...
    nl_expand_fast=0.35, # ... the rest faster
    nl_build=3.0,        # the picture of the attractor builds up
    blend=0.4,           # ensemble picture -> single-dot picture
    rewind=2.5,          # the points are taken back
    sectors=6.0,         # drawn again with the zones counting
    sectors_end=1.0,
    expand=1.3,          # picture grows, zones fade
    twist=4.5,           # omega 0 -> OMEGA_TWIST
    twist_hold=0.4,
    twist_blend=0.5,
    twist_warm=0.7,
    morph_leg=3.2,       # per leg between two icons
    morph_hold=0.1,
    fade=0.35,           # fade in/out of the hook, linear and the end
)
NL_LINE_MAX = 40000
NL_LINE_SLOW_N = 6
NL_EXPAND_STEPS = 9
NL_EXPAND_SLOW_N = 6
PHI_SPIN = 2.4             # how far the swirl turns
SC_MIN = 0.03              # the disc is squeezed to this share of its size
N_TRAJ = 12_000_000        # iterations of the single dot (preview: 1/6)
N_START = 60
LANES = 20_000             # dots used in the moving scenes
HOOK_STEPS_30 = 24         # ensemble steps per frame at 30 fps (scaled for other fps)
MOVE_DECAY_30 = 0.80       # temporal smoothing per frame at 30 fps
OMEGA_TWIST = 0.25
CLOUD_POINTS = 40_000
SEED = 7
FONT_PATH = None           # e.g. r"C:\Windows\Fonts\Montserrat-Light.ttf"; None = auto search
TONE_GAMMA = 1.6
BLOOM = 0.18
V_MAX = 0.94               # brightest allowed density value (no white blobs)
FILL = 0.49                # attractor radius as a share of half the picture (bigger = larger crystals)

# Catppuccin Mocha text colours + neon-pastel accents
CAT = dict(
    base="#000000", text="#cdd6f4", subtext0="#a6adc8", overlay0="#6c7086",
    pink="#ff8fd0", peach="#ffa26b", yellow="#ffe27a", green="#7dff9a", teal="#5df0d6",
    sapphire="#4cc8ff", blue="#6f8bff", mauve="#b68cff", red="#ff6f8f", rosewater="#ffd9ec",
)
RAMPS = {
    # icons
    "dusk":   [(0.00, "#000000"), (0.10, "#14186a"), (0.28, "#5b7bff"), (0.46, "#a98bff"),
               (0.62, "#ff8fd0"), (0.78, "#ffa07a"), (0.92, "#ffd27a"), (1.00, "#ffe7a8")],
    "ember":  [(0.00, "#000000"), (0.10, "#3a0f55"), (0.28, "#b46bff"), (0.46, "#ff6f9f"),
               (0.64, "#ff9a5a"), (0.84, "#ffd070"), (1.00, "#ffeaa0")],
    "lagoon": [(0.00, "#000000"), (0.10, "#0a2f55"), (0.28, "#3fb6ff"), (0.46, "#38e6d0"),
               (0.64, "#7dff9a"), (0.84, "#e8ff7a"), (1.00, "#fff3a0")],
    # fractals of the hook (calm neon pastel)
    "bee":    [(0, "#000000"), (0.12, "#0e1442"), (0.3, "#3347a8"), (0.5, "#6a84e8"),
               (0.72, "#9d9cf5"), (0.9, "#c3bdfa"), (1, "#dcd6ff")],
    "snow":   [(0, "#000000"), (0.12, "#1f0f45"), (0.3, "#5a42b0"), (0.5, "#9a80ee"),
               (0.72, "#e48ac8"), (0.9, "#f5b0d8"), (1, "#fcd0e8")],
    "wheel":  [(0, "#000000"), (0.12, "#1a1042"), (0.3, "#4a47ae"), (0.5, "#a46bd6"),
               (0.75, "#f08fb4"), (0.9, "#fdb8a8"), (1, "#ffd9c4")],
    "saw":    [(0, "#000000"), (0.1, "#061c3a"), (0.3, "#1d5aa8"), (0.5, "#3aa0d8"),
               (0.7, "#6ad8cc"), (0.9, "#a8eedc"), (1, "#d0fbee")],
    "f718":   [(0, "#000000"), (0.12, "#1a1040"), (0.3, "#5438b0"), (0.5, "#9c78ee"),
               (0.75, "#ee8cc6"), (0.9, "#f9b4d6"), (1, "#fdd2e6")],
    # one colour family per stage of the morph (pastel neon, each with its own body colour)
    "azure":  [(0, "#000000"), (0.10, "#0a2468"), (0.28, "#2f78e0"), (0.5, "#58b4ff"), (0.75, "#a4e6ff"),
               (1, "#e8fbff")],
    "mint":   [(0, "#000000"), (0.10, "#04302a"), (0.28, "#1fae8e"), (0.5, "#4fe3b0"), (0.75, "#a8f5c8"),
               (1, "#effff2")],
    "gold":   [(0, "#000000"), (0.10, "#2e1c06"), (0.28, "#c68a20"), (0.5, "#ffc247"), (0.75, "#ffe28a"),
               (1, "#fff6d6")],
    "rose":   [(0, "#000000"), (0.10, "#3a0a2a"), (0.28, "#d83f86"), (0.5, "#ff77aa"), (0.75, "#ffb3cd"),
               (1, "#ffe8f0")],
    "violet": [(0, "#000000"), (0.10, "#1a0a40"), (0.28, "#6a3de0"), (0.5, "#a56bff"), (0.75, "#d3acff"),
               (1, "#f4e6ff")],
    "coral":  [(0, "#000000"), (0.10, "#3a0f0a"), (0.28, "#e0502f"), (0.5, "#ff8a5c"), (0.75, "#ffbf8f"),
               (1, "#fff0e0")],
    "lime":   [(0, "#000000"), (0.10, "#0e2a0a"), (0.28, "#4a9a30"), (0.5, "#86cf5c"), (0.75, "#c4ec9a"),
               (1, "#f2ffe2")],
    # soft pastel families for the finale
    "sage":   [(0, "#000000"), (0.10, "#0d2a1e"), (0.28, "#4f9c7c"), (0.5, "#86c8a6"), (0.75, "#c2e6cc"),
               (1, "#f0fff4")],
    "peach":  [(0, "#000000"), (0.10, "#3a1c22"), (0.28, "#c8707a"), (0.5, "#f0a590"), (0.75, "#f9d0b4"),
               (1, "#fff1e4")],
    "dawn":   [(0, "#000000"), (0.10, "#16164a"), (0.28, "#5c6ccc"), (0.45, "#9c98ee"), (0.62, "#eba0bc"),
               (0.8, "#f8c8a4"), (1, "#fff2dc")],
    "blush":  [(0, "#000000"), (0.10, "#341030"), (0.28, "#b8609a"), (0.5, "#ee9ec0"), (0.75, "#f8d2d6"),
               (1, "#fff4ee")],
    # finale figures (more colours, still pastel-neon)
    "fire":    [(0, "#000000"), (0.10, "#101a5e"), (0.26, "#3f5bdc"), (0.42, "#9a8cff"), (0.58, "#ff7a9a"),
                (0.74, "#ff8a5c"), (0.88, "#ffd278"), (1, "#fff0b8")],
    "sun":     [(0, "#000000"), (0.10, "#2a0d4a"), (0.28, "#c0407a"), (0.46, "#ff6a5c"), (0.64, "#ff9a4a"),
                (0.82, "#ffd060"), (1, "#fff0a8")],
    "amber":   [(0, "#000000"), (0.12, "#2a1060"), (0.3, "#c0405e"), (0.5, "#ff8a3c"), (0.72, "#ffc23c"),
                (0.9, "#ffe48a"), (1, "#fff2c0")],
    "whipper": [(0, "#000000"), (0.10, "#14186a"), (0.28, "#3a56e8"), (0.46, "#6ea8ff"), (0.62, "#c8f4e0"),
                (0.78, "#ff9ab0"), (0.92, "#ffc4cc"), (1, "#ffe6e6")],
    "cyan":   [(0, "#000000"), (0.15, "#0a2a8a"), (0.4, "#2f9bff"), (0.7, "#4fdcff"), (1, "#8aeaff")],
    "orange": [(0, "#000000"), (0.15, "#7a1020"), (0.4, "#ff3d2e"), (0.7, "#ff8a2e"), (1, "#ffbb55")],
}

# Fractals: x -> g * rho(x),  rho(x,y) = (a x + b y + alpha, c x + d y + beta),  g from a group
#   kind "D": dihedral (rotations and mirrors), "Z": rotations only.  rho = (a, b, c, d, alpha, beta)
FRACTALS = {
    "bee":   dict(kind="D", n=3, ramp="bee",
                  rho=(-0.35752024118007764, -0.14567974695210628, 0.6226349282588393,
                       -0.17252164089859356, 0.09918737534611899, -0.9448817735138633)),
    "snow":  dict(kind="D", n=6, ramp="snow",
                  rho=(-0.35752024118007764, -0.14567974695210628, 0.6226349282588393,
                       -0.17252164089859356, 0.09918737534611899, -0.9448817735138633)),
    "wheel": dict(kind="Z", n=7, ramp="wheel",
                  rho=(-0.40623074628133815, 0.1696637497874236, -0.5028210771027601,
                       -0.02592172526047476, 0.8233558626872097, 0.11122458720857265)),
    "ring":  dict(kind="Z", n=48, ramp="amber",
                  rho=(-0.06982427874078945, 0.6376590147386745, -0.16061543750929919, 0.5540982666079901,
                       -0.6830006793624013, 0.6621799685978476)),
    "whip":  dict(kind="Z", n=48, ramp="whipper",
                  rho=(0.5233007201370441, -0.5689142827119639, 0.22118689959663485, -0.22676024262449634,
                       0.12051011272707357, -0.6041416423327555)),
    "saw":   dict(kind="Z", n=12, ramp="saw",
                  rho=(-0.17012927907437092, 0.2955896328485852, 0.8638767953379689,
                       -0.22866694216960437, -0.857861112623741, -0.6147556278116229)),
    "f718":  dict(kind="Z", n=8, ramp="f718",
                  rho=(0.2008161343953887, -0.5553955467448286, -0.09771679415915835,
                       -0.6904790116937327, -0.576201098238498, -0.5001833694920517)),
}
# waypoints of the hook; odd_boost = how much more often maps 2,4,6,8 are picked than 1,3,5,7;
# split = how much of the two-colour picture (colour = parity of the last map) is shown
HOOK_PATH = [
    dict(frac="bee"),
    dict(frac="bee", rho=(-0.33, -0.22, 0.58, -0.09, 0.12, -0.93), odd_boost=3.0, leg=1.6),   # small morph of the bee
    dict(frac="wheel"), dict(frac="saw"),
    dict(frac="f718", parity=True),
    dict(frac="f718", parity=True, odd_boost=4.0),
]

# Icons found by random search (n = 5, omega = 0)
ICONS = [
    dict(lam=-2.1574682660217137, alpha=4.542569946288982, beta=1.6942109406070767, gamma=1.466898182525472, n=5),
    dict(lam=-2.1321327769710137, alpha=4.622502604240703, beta=-0.7711984596497166, gamma=2.2789127158854, n=5),
    dict(lam=-2.2560167350667975, alpha=5.8593722543974724, beta=1.0190056220638422, gamma=1.5995661664389265, n=5),
    dict(lam=-1.8301693281222975, alpha=1.066839704150194, beta=0.11211071964778041, gamma=0.2726796003537122, n=5),
    dict(lam=-2.1451464031975593, alpha=8.214210587866177, beta=-1.203903715705811, gamma=1.6810346333270134, n=5),
    dict(lam=-2.2155290288337133, alpha=2.9048062193519666, beta=-0.19072740380825692, gamma=-0.31757000171469574, n=5),
    dict(lam=-2.143164329116847, alpha=3.1318086104058143, beta=-0.6869686589571682, gamma=-0.39848555433708177, n=5),
    dict(lam=-2.4917518943333574, alpha=6.918580205123343, beta=2.6176517332060296, gamma=-0.9251343182092324, n=5),
    dict(lam=-2.3743910885991255, alpha=5.362373878049764, beta=2.602273902679639, gamma=1.7572337821482886, n=5),
    dict(lam=2.4430424995048083, alpha=-3.163341061806799, beta=-0.5075546173241019, gamma=1.3851204488713478, n=5),
    dict(lam=-2.5610499621814276, alpha=5.788700218031279, beta=-2.4696745836216794, gamma=1.7686363077918168, n=5),
    dict(lam=-2.29180730699777, alpha=2.648675494358997, beta=-0.4086455540927467, gamma=0.4595148393524515, n=5),
    # 13: a "pinwheel" lookalike (needs the twist omega = 0.35)
    dict(lam=-2.294511743761362, alpha=4.950164313321382, beta=1.553985089958072, gamma=0.40893679187231124, n=5),
    # 14: "flower" (n = 5, a flower-shaped hole; needs omega = 0.0513)
    dict(lam=-2.309424415719023, alpha=5.419793505358346, beta=-1.4795965485261175, gamma=-0.03210835238009979, n=5),
    # 15: "clam" (n = 3)
    dict(lam=-2.5030586989857335, alpha=4.324182697917024, beta=-2.15267890149292, gamma=0.6471763889176654, n=3),
    # 16: "wild" (n = 3)
    dict(lam=-2.0884907155256114, alpha=3.874741554146187, beta=1.5737596778576304, gamma=-0.8696387057828041, n=3),
    # 17: "rounded triangle" (n = 3)
    dict(lam=-2.584745759261574, alpha=6.2881039679572766, beta=-2.85608480838079, gamma=1.1325662088980497, n=3),
]
HERO = 1
MORPH_PATH = [(1, OMEGA_TWIST, "dusk"), (3, 0.0, "rose"), (5, 0.0, "mint"),
              (11, 0.0, "gold"), (8, 0.0, "azure"), (1, 0.0, "violet"), (13, 0.3503009070522778, "coral")]
SECTOR_COLORS = ["pink", "peach", "yellow", "teal", "mauve"]
CLOUD_HUES = ["pink", "mauve", "blue", "sapphire", "teal", "blue", "mauve"]
# linear behaviours: (label, |c|, angle of c, steps, |z0|, relative gap of the two dots)
LINEAR = [("circles forever", 1.00, 0.50, 32, 0.62, 0.11)]
# the disc of points of the bridge: (|c|, angle of c) while it rotates / shrinks / grows
BR_ROT, BR_SHRINK, BR_GROW = (1.00, 0.50), (0.82, 0.42), (1.30, 0.30)
BR_RMAX = 0.68              # the disc of the bridge reaches the circle that the two dots have drawn
LINEAR_R = 0.75           # the linear panel shows |z| up to this value
# ======================================================

LUT_N = 1024


# ---------- colours ----------
def hexrgb(c):
    c = CAT.get(c, c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


BG = (0, 0, 0)


def build_lut(stops):
    pos = np.array([p for p, _ in stops])
    cols = np.array([hexrgb(c) for _, c in stops], dtype=np.float64)
    x = np.linspace(0, 1, LUT_N)
    return np.stack([np.interp(x, pos, cols[:, k]) for k in range(3)], axis=1)


LUTS = {name: build_lut(stops) for name, stops in RAMPS.items()}   # float, 0..255


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def smoother(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * x * (x * (x * 6 - 15) + 10)


def lerp(a, b, t):
    return a + (b - a) * t


# ---------- icon map: ensemble of dots ----------
class Lanes:
    def __init__(self, ic, rng, m):
        self.ic, self.rng, self.m = dict(ic), rng, m
        self.z = self.fresh()

    def fresh(self):
        return (self.rng.normal(size=self.m) + 1j * self.rng.normal(size=self.m)) * 0.3

    @staticmethod
    def f(z, ic, om):
        n = ic["n"]
        zc = z.conjugate()
        r2 = z.real * z.real + z.imag * z.imag
        w = zc
        for _ in range(n - 2):          # w = conj(z)^(n-1)
            w = w * zc
        re_zn = (z * w.conjugate()).real
        return (ic["lam"] + ic["alpha"] * r2 + ic["beta"] * re_zn + 1j * om) * z + ic["gamma"] * w

    def advance(self, om):
        z = self.f(self.z, self.ic, om)
        rr = z.real * z.real + z.imag * z.imag
        bad = ~(rr < 1e6)               # also catches NaN
        if bad.any():
            good = np.flatnonzero(~bad)
            if good.size == 0:
                z = self.fresh()
            else:
                z[bad] = z[self.rng.choice(good, int(bad.sum()))]
        self.z = z
        return z


def estimate_radius(ic, rng, om):
    L = Lanes(ic, rng, 4000)
    for _ in range(120):
        L.advance(om)
    r = np.concatenate([np.abs(L.advance(om)) for _ in range(30)])
    return float(np.percentile(r, 99.8))


# ---------- icon map: ONE dot (pure python, or numba if installed) ----------
def _py_iter(N, lam, al, be, ga, n, x, y):
    xs = [0.0] * N
    ys = [0.0] * N
    for i in range(N):
        r2 = x * x + y * y
        cx, cy = x, -y
        wx, wy = cx, cy
        for _ in range(n - 2):
            wx, wy = wx * cx - wy * cy, wx * cy + wy * cx
        s = lam + al * r2 + be * (x * wx + y * wy)
        x, y = s * x + ga * wx, s * y + ga * wy
        xs[i] = x
        ys[i] = y
    return xs, ys, x, y


if HAVE_NUMBA:
    @njit(cache=True)
    def _nb_iter(xs, ys, lam, al, be, ga, n, x, y):
        for i in range(xs.shape[0]):
            r2 = x * x + y * y
            cx, cy = x, -y
            wx, wy = cx, cy
            for _ in range(n - 2):
                t = wx * cx - wy * cy
                wy = wx * cy + wy * cx
                wx = t
            s = lam + al * r2 + be * (x * wx + y * wy)
            nx = s * x + ga * wx
            ny = s * y + ga * wy
            x, y = nx, ny
            xs[i] = x
            ys[i] = y
        return x, y


def run_dot(ic, N, x, y):
    p = (ic["lam"], ic["alpha"], ic["beta"], ic["gamma"], ic["n"])
    if HAVE_NUMBA:
        xs = np.empty(N, np.float64)
        ys = np.empty(N, np.float64)
        x, y = _nb_iter(xs, ys, *p, x, y)
        return xs.astype(np.float32), ys.astype(np.float32), x, y
    xs = np.empty(N, np.float32)
    ys = np.empty(N, np.float32)
    done, chunk = 0, 500_000
    while done < N:
        c = min(chunk, N - done)
        a, b, x, y = _py_iter(c, *p, x, y)
        xs[done:done + c] = a
        ys[done:done + c] = b
        done += c
    return xs, ys, x, y


def exact_path(ic, x, y, k):
    """z_0 = (x, y) and the next k iterates, float64."""
    a, b, _, _ = _py_iter(k, ic["lam"], ic["alpha"], ic["beta"], ic["gamma"], ic["n"], x, y)
    return np.concatenate([[x + 1j * y], np.array(a) + 1j * np.array(b)])


def settle(ic, rng):
    for _ in range(50):
        x, y = rng.normal() * 0.3, rng.normal() * 0.3
        _, _, x, y = _py_iter(3000, ic["lam"], ic["alpha"], ic["beta"], ic["gamma"], ic["n"], x, y)
        if math.isfinite(x) and 1e-3 < abs(x) + abs(y) < 1e3:
            return x, y
    raise RuntimeError("could not find an orbit that stays bounded")


# ---------- fractals (IFS with symmetry) ----------
def group(kind, n):
    els = []
    flip = np.array([[1.0, 0.0], [0.0, -1.0]])
    for j in range(n):
        t = 2 * np.pi * j / n
        R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        els.append(R)
        if kind == "D":
            els.append(R @ flip)
    return np.array(els)


class IFSMorph:
    """Ensemble of dots on a symmetric fractal; the fractal can morph between waypoints."""

    def __init__(self, c, wps):
        self.c, self.wps, self.rng = c, wps, c.rng
        self.m = c.lanes_m
        self.E, self.W, self.P, self.rho, self.R = [], [], [], [], []
        for wp in wps:
            f = FRACTALS[wp["frac"]]
            E = group(f["kind"], f["n"])
            w = np.ones(len(E))
            if wp.get("odd_boost", 1.0) != 1.0:
                w[1::2] *= wp["odd_boost"]
            par = (np.arange(len(E)) % 2) if wp.get("parity") else np.zeros(len(E), dtype=int)
            self.E.append(E)
            self.W.append(w / w.sum())
            self.P.append(par)
            rho_w = np.array(wp.get("rho", f["rho"]), dtype=np.float64)
            self.rho.append(rho_w)
            self.R.append(self.radius(E, w / w.sum(), rho_w))
        self.x = self.rng.normal(size=self.m) * 0.1
        self.y = self.rng.normal(size=self.m) * 0.1
        for _ in range(80):
            self.step(self.rho[0], self.E[0], self.W[0], self.P[0], record=False)

    def step(self, rho, E, w, par, record=True):
        cum = np.cumsum(w)
        cum /= cum[-1]
        nx = rho[0] * self.x + rho[1] * self.y + rho[4]
        ny = rho[2] * self.x + rho[3] * self.y + rho[5]
        k = np.minimum(np.searchsorted(cum, self.rng.random(self.m)), len(cum) - 1)
        self.x = E[k, 0, 0] * nx + E[k, 0, 1] * ny
        self.y = E[k, 1, 0] * nx + E[k, 1, 1] * ny
        return (self.x, self.y, par[k]) if record else None

    def radius(self, E, w, rho):
        sv, rng = self, np.random.default_rng(1)
        m = 6000
        x, y = rng.normal(size=m) * 0.1, rng.normal(size=m) * 0.1
        cum = np.cumsum(w) / w.sum()
        out = []
        for i in range(110):
            nx = rho[0] * x + rho[1] * y + rho[4]
            ny = rho[2] * x + rho[3] * y + rho[5]
            k = np.minimum(np.searchsorted(cum, rng.random(m)), len(cum) - 1)
            x = E[k, 0, 0] * nx + E[k, 0, 1] * ny
            y = E[k, 1, 0] * nx + E[k, 1, 1] * ny
            if i >= 50:
                out.append(np.hypot(x, y))
        return float(np.percentile(np.concatenate(out), 99.95)) * 1.04

    def mix(self, a, b, t):
        rho = lerp(self.rho[a], self.rho[b], t)
        fa, fb = self.wps[a]["frac"], self.wps[b]["frac"]
        if fa == fb:
            E, w, par = self.E[a], lerp(self.W[a], self.W[b], t), self.P[a]
        else:
            E = np.concatenate([self.E[a], self.E[b]])
            w = np.concatenate([self.W[a] * (1 - t), self.W[b] * t])
            par = np.concatenate([self.P[a], self.P[b]])
        s = lerp(self.wps[a].get("split", 0.0), self.wps[b].get("split", 0.0), t)
        return rho, E, np.maximum(w, 1e-12), par, s, lerp(self.R[a], self.R[b], t)


# ---------- text, math ----------
def find_font(size):
    cands = [FONT_PATH] if FONT_PATH else []
    home = os.path.expanduser("~")
    dirs = [os.path.join(home, ".fonts"), os.path.join(home, ".local/share/fonts"), "/usr/share/fonts",
            "/usr/local/share/fonts", os.path.join(home, "Library/Fonts"), "/Library/Fonts",
            "/System/Library/Fonts", r"C:\Windows\Fonts",
            os.path.join(home, r"AppData\Local\Microsoft\Windows\Fonts")]
    for d in dirs:
        for p in ("Montserrat-Light.ttf", "Montserrat-Light.otf", "Montserrat Light.ttf"):
            cands += glob.glob(os.path.join(d, "**", p), recursive=True)
    for cnd in cands:
        try:
            return ImageFont.truetype(cnd, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


_MATH_CACHE = {}
_GREEK = {"lambda": "\u03bb", "alpha": "\u03b1", "beta": "\u03b2", "gamma": "\u03b3", "omega": "\u03c9",
          "theta": "\u03b8"}
_FONTS_REG = ["DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "segoeui.ttf", "LiberationSans-Regular.ttf",
              "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"]
_FONTS_ITA = ["DejaVuSans-Oblique.ttf", "ariali.ttf", "Arial Italic.ttf", "segoeuii.ttf",
              "LiberationSans-Italic.ttf", "/System/Library/Fonts/Supplemental/Arial Italic.ttf"]


def _math_font(italic, size):
    for nm in (_FONTS_ITA if italic else _FONTS_REG):
        try:
            return ImageFont.truetype(nm, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


def _tex_items(tex):
    """tiny TeX subset -> [(text, italic, level, bar)]; level 0 normal, 1 superscript, -1 subscript"""
    items, i, lvl = [], 0, 0
    def grab(i):                                   # {...} or one char
        if i < len(tex) and tex[i] == "{":
            j = tex.index("}", i)
            return tex[i + 1:j], j + 1
        return tex[i], i + 1
    while i < len(tex):
        ch = tex[i]
        if ch == "\\":
            j = i + 1
            while j < len(tex) and tex[j].isalpha():
                j += 1
            name = tex[i + 1:j]
            if name in _GREEK:
                items.append((_GREEK[name], True, 0, False))
                i = j
            elif name == "mathrm":
                txt, i = grab(j)
                items.append((txt, False, 0, False))
            elif name == "bar":
                txt, i = grab(j)
                items.append((txt, True, 0, True))
            else:                                  # "\\," and friends = small space
                items.append((" ", False, 0, False))
                i = j if j > i + 1 else i + 2
        elif ch in "^_":
            txt, i = grab(i + 1)
            sub = _tex_items(txt)
            lv = 1 if ch == "^" else -1
            items += [(t, it, lv, b) for t, it, _, b in sub]
        elif ch == " ":
            i += 1
        else:
            items.append((ch, ch.isalpha(), 0, False))
            i += 1
    return items


def pil_math_mask(tex, base=110):
    """Formula without matplotlib: Greek letters, super/subscripts and bars drawn with Pillow (L mask)."""
    items = _tex_items(tex)
    W = int(base * (len(items) * 0.9 + 4))
    H = int(base * 2.2)
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    x, y0 = base * 0.3, base * 0.5
    for t, ita, lvl, bar in items:
        size = base if lvl == 0 else int(base * 0.66)
        f = _math_font(ita, size)
        dy = 0 if lvl == 0 else (-0.38 * base if lvl > 0 else 0.30 * base)
        w = d.textlength(t, font=f)
        pad = base * 0.16 if (t in "=+" and lvl == 0) else 0.0
        x += pad
        d.text((x, y0 + dy + (base - size) * 0.1), t, font=f, fill=255)
        if bar:
            d.line([(x, y0 + dy + base * 0.06), (x + w, y0 + dy + base * 0.06)], fill=255, width=max(2, base // 18))
        x += w + pad + base * (0.12 if bar else 0.03)
    return m

EM_PX = 111.0          # natural em size (px) of the rendered math at size 40 / dpi 200


def math_img(tex, color, scale=1.0, px_w=None):
    """LaTeX-ish string -> RGBA (coloured text on transparent). None if matplotlib is missing."""
    key = (tex, color, round(scale, 4), px_w, HAVE_MPL)
    if key in _MATH_CACHE:
        return _MATH_CACHE[key]
    if HAVE_MPL:
        buf = io.BytesIO()
        math_to_image("$" + tex + "$", buf, prop=FontProperties(size=40), dpi=200, format="png")
        g = Image.open(buf).convert("L")
        mask = Image.eval(g, lambda v: 255 - v)
    else:
        mask = pil_math_mask(tex)
    bb = mask.getbbox()
    if bb:
        mask = mask.crop(bb)
    k = (px_w / mask.width) if px_w else scale
    mask = mask.resize((max(1, int(mask.width * k)), max(1, int(mask.height * k))), Image.LANCZOS)
    img = Image.new("RGBA", mask.size, hexrgb(color) + (255,))
    img.putalpha(mask)
    _MATH_CACHE[key] = img
    return img


def formula_tex(n):
    pre = r"F(z)=(\lambda+\alpha\,|z|^{2}+\beta\,\mathrm{Re}(z^{%d})+" % n
    return pre, pre + r"i\omega", pre + r"i\omega)\,z+\gamma\,\bar{z}^{%d}" % (n - 1)


def cfmt(z):
    return f"{z.real:.2f}{'+' if z.imag >= 0 else '-'}{abs(z.imag):.2f}\\,i"


# ---------- panels, glow dots, canvas ----------
class Panel:
    """A square density picture: grid GxG, radius R maps to FILL * G/2."""

    def __init__(self, G, R, ramp="dusk"):
        self.G, self.R, self.lut = int(G), R, LUTS[ramp]
        self.s = G / 1080.0

    def to_px(self, x, y):
        k = self.G * FILL / self.R
        return x * k + self.G / 2, self.G / 2 - y * k

    def new_hist(self):
        return np.zeros((self.G, self.G), dtype=np.float32)

    def splat(self, hist, x, y, sign=1.0):
        G = self.G
        px, py = self.to_px(np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64))
        ix, iy = px.astype(np.int32), py.astype(np.int32)
        m = (ix >= 0) & (ix < G) & (iy >= 0) & (iy < G)
        hist += sign * np.bincount(iy[m] * G + ix[m], minlength=G * G).reshape(G, G)

    def render(self, hist, n_points, lut=None, expo=0.55):
        sigma = float(np.clip(1.8 * (5.0 - math.log10(max(n_points, 10))), 0, 5)) * max(self.s, 0.5)
        h = gaussian_filter(hist, sigma) if sigma > 0.3 else hist
        sub = h[::3, ::3]
        nz = sub[sub > sub.max() * 1e-3] if sub.max() > 0 else sub
        ref = max(float(np.percentile(nz, 99.7)) if nz.size else 1.0, 1e-9)
        sc = max(1.0, 20.0 / ref)
        v = np.clip(np.log1p(h * sc) / np.log1p(ref * sc), 0, 1) ** TONE_GAMMA
        vs = v[::3, ::3]
        vs = vs[vs > 0.02]
        if vs.size:                                   # auto-exposure: only ever brightens dim pictures
            p90 = float(np.percentile(vs, 90))
            v = v ** float(np.clip(math.log(0.45) / math.log(max(p90, 1e-3)), expo, 1.0))
        v = v * V_MAX
        L = self.lut if lut is None else lut
        rgb = L[(v * (LUT_N - 1)).astype(np.int32)].astype(np.uint8)
        return bloom(Image.fromarray(rgb, "RGB"))


def bloom(img):
    small = img.resize((max(8, img.width // 4), max(8, img.height // 4)), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(5))
    b = small.resize(img.size, Image.BILINEAR).point(lambda p: int(p * BLOOM))
    return ImageChops.add(img, b)


def dim(img, k):
    return img.point(lambda p: int(p * k))


_SPR = {}


def sprite(color, s, big=False):
    """Thin bright core with a soft halo (added on top of the picture)."""
    key = (color, round(s, 2), big)
    if key not in _SPR:
        R = int(30 * s) + 3
        yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float64)
        d2 = xx * xx + yy * yy
        rc = (2.4 if not big else 3.2) * s
        sg = (9.0 if not big else 14.0) * s
        core, halo = np.exp(-d2 / (2 * rc * rc)), np.exp(-d2 / (2 * sg * sg))
        col = np.array(hexrgb(color)) / 255.0
        rgb = (core[..., None] * (0.45 + 0.55 * col) + 0.5 * halo[..., None] * col) * 255
        _SPR[key] = (Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB"), R)
    return _SPR[key]


def blit(img, spr, cx, cy):
    s_img, R = spr
    x, y = int(round(cx)) - R, int(round(cy)) - R
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + s_img.width, img.width), min(y + s_img.height, img.height)
    if x1 <= x0 or y1 <= y0:
        return
    sub = s_img.crop((x0 - x, y0 - y, x1 - x, y1 - y))
    img.paste(ImageChops.add(img.crop((x0, y0, x1, y1)), sub), (x0, y0))


def fade_col(color, f):
    return tuple(int(v * f) for v in hexrgb(color))


class Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.s = W / 1080.0
        self.fonts = {}

    def font(self, size):
        size = max(10, int(size * self.s))
        if size not in self.fonts:
            self.fonts[size] = find_font(size)
        return self.fonts[size]

    def new(self):
        self.base = Image.new("RGB", (self.W, self.H), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.base)
        return self

    def paste(self, img, x, y):
        self.base.paste(img, (int(x), int(y)))

    def paste_rgba(self, img, x, y, alpha=1.0):
        if img is None or alpha <= 0:
            return
        a = img.split()[3].point(lambda p: int(p * alpha))
        self.base.paste(img.convert("RGB"), (int(x), int(y)), a)

    def text(self, s, cx, y, color="overlay0", size=34, alpha=1.0):
        f = self.font(size)
        w = self.draw.textlength(s, font=f)
        self.draw.text((cx - w / 2, y), s, font=f, fill=fade_col(color, alpha))
        return w

    def finish(self, fade=1.0):
        if fade >= 1.0:
            return self.base
        return self.base.point(lambda p: int(p * fade))


class Sink:
    def __init__(self, path, W, H, fps, png_dir=None, png_every=0, video=True):
        self.i = 0
        self.png_dir, self.png_every = png_dir, png_every
        self.proc = None
        if png_dir:
            os.makedirs(png_dir, exist_ok=True)
        if video:
            ff = shutil.which("ffmpeg")
            if not ff:
                try:
                    import imageio_ffmpeg
                    ff = imageio_ffmpeg.get_ffmpeg_exe()
                except Exception:
                    sys.exit("ffmpeg not found: install it or `pip install imageio-ffmpeg`")
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            self.proc = subprocess.Popen(
                [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                 "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)

    def write(self, img):
        if self.proc:
            self.proc.stdin.write(img.tobytes())
        if self.png_dir and self.png_every and self.i % self.png_every == 0:
            img.save(os.path.join(self.png_dir, f"f{self.i:05d}.png"))
        self.i += 1

    def close(self):
        if self.proc:
            self.proc.stdin.close()
            self.proc.wait()


class Ctx:
    pass


def fade_k(k, K, fi, fo):
    a = smooth(k / fi) if fi > 0 else 1.0
    b = smooth((K - k + 1) / fo) if fo > 0 else 1.0
    return min(a, b)


def nframes(c, sec):
    return max(1, int(round(sec * c.fps)))


def make_ctx(W, H, fps, preview, rng):
    c = Ctx()
    c.W, c.H, c.fps, c.s, c.rng, c.preview = W, H, fps, W / 1080.0, rng, preview
    c.canvas = Canvas(W, H)
    c.ic = ICONS[HERO - 1]
    c.R = 1.06 * estimate_radius(c.ic, rng, 0.0)
    c.n_traj = max(N_TRAJ // 6, 1_000_000) if preview else N_TRAJ
    c.lanes_m = LANES // 2 if preview else LANES
    c.fi = int(round(TIMING["fade"] * fps))
    c.k30 = 30.0 / fps
    c.S = max(3, int(round(HOOK_STEPS_30 * c.k30)))          # ensemble steps per frame
    c.decay = MOVE_DECAY_30 ** c.k30
    c.mdecay = 0.88 ** c.k30                 # morph and finale: longer memory = smoother
    c.ens_img = c.carry_img = c.carry_hist = None
    c.expo = 0.55
    c.last_img = None
    c.rot_target = c.rot_cur = c.rot_ang = 0.0     # slow turning of the whole picture (rad/s) in the last scenes
    return c


def prepare_dots(c):
    t0 = time.time()
    print(f"  computing the single dot, {c.n_traj:,} iterations "
          f"({'numba' if HAVE_NUMBA else 'pure python; pip install numba makes this ~20x faster'}) ...", flush=True)
    x, y = settle(c.ic, c.rng)
    c.start = (x, y)
    c.A = run_dot(c.ic, c.n_traj, x, y)[:2]
    c.pathA = exact_path(c.ic, x, y, 8)
    print(f"  done in {time.time() - t0:.0f} s", flush=True)


def full_hist(panel, xs, ys):
    h = panel.new_hist()
    for a in range(0, len(xs), 2_000_000):
        panel.splat(h, xs[a:a + 2_000_000], ys[a:a + 2_000_000])
    return h


def log_targets(n_end, K):
    return [int(round(N_START * (n_end / N_START) ** (k / K))) for k in range(1, K + 1)]


# ---------- text blocks ----------
def formula_block(c, cv, y, alpha=1.0, highlight=0.0, width=0.90):
    n = c.ic["n"]
    pre_a, pre_b, full = formula_tex(n)
    wpx = int(c.W * width)
    img = math_img(full, "subtext0", px_w=wpx)
    if img is None:
        cv.text("F(z) = (lam + alpha|z|^2 + beta Re(z^%d) + i omega) z + gamma conj(z)^%d" % (n, n - 1),
                c.W / 2, y, "subtext0", 26, alpha)
        return
    x0 = (c.W - img.width) // 2
    cv.paste_rgba(img, x0, y, alpha)
    if highlight > 0:
        k = wpx / math_img(full, "subtext0", scale=1.0).width
        xa = x0 + math_img(pre_a, "subtext0", scale=k).width
        xb = x0 + math_img(pre_b, "subtext0", scale=k).width
        col = fade_col("peach", highlight * alpha)
        cv.draw.rounded_rectangle([xa - 6 * c.s, y - 8 * c.s, xb + 6 * c.s, y + img.height + 8 * c.s],
                                  radius=int(8 * c.s), outline=col, width=max(1, int(2 * c.s)))


def param_line(c, cv, y, p, alpha=1.0):
    names = [("lambda", p[0]), ("alpha", p[1]), ("beta", p[2]), ("gamma", p[3]), ("omega", p[4])]
    f = cv.font(30)
    gap, sp = 26 * c.s, 10 * c.s
    k = 30 * c.s * 1.1 / EM_PX
    items = []
    for nm, v in names:
        g = math_img("\\" + nm, "text", scale=k)
        txt = f"{v:+.2f}" if nm != "omega" else f"{v:.2f}"
        items.append((g, nm, txt))
    total = 0.0
    for g, nm, txt in items:
        total += (g.width if g is not None else cv.draw.textlength(nm, font=f)) + sp
        total += cv.draw.textlength(txt, font=f) + gap
    x = (c.W - total + gap) / 2
    col = fade_col("subtext0", alpha)
    for g, nm, txt in items:
        if g is not None:
            cv.paste_rgba(g, x, y + 3 * c.s, alpha)
            x += g.width + sp
        else:
            cv.draw.text((x, y), nm, font=f, fill=col)
            x += cv.draw.textlength(nm, font=f) + sp
        cv.draw.text((x, y), txt, font=f, fill=col)
        x += cv.draw.textlength(txt, font=f) + gap


# ---------- helpers for pictures ----------
def hue_color(theta):
    cols = np.array([hexrgb(h) for h in CLOUD_HUES + [CLOUD_HUES[0]]], dtype=np.float64) / 255.0
    t = (np.mod(theta, 2 * np.pi) / (2 * np.pi)) * (len(cols) - 1)
    i = np.minimum(t.astype(int), len(cols) - 2)
    f = (t - i)[:, None]
    return cols[i] * (1 - f) + cols[i + 1] * f


def render_cloud(panel, z, cols, gain=2.6):
    """Coloured cloud: hue = average colour of the points in a pixel, brightness = how many there are."""
    G = panel.G
    px, py = panel.to_px(z.real, z.imag)
    ix, iy = px.astype(np.int32), py.astype(np.int32)
    m = (ix >= 0) & (ix < G) & (iy >= 0) & (iy < G)
    idx = iy[m] * G + ix[m]
    cnt = np.bincount(idx, minlength=G * G).reshape(G, G).astype(np.float64)
    acc = np.stack([np.bincount(idx, weights=cols[m, k], minlength=G * G).reshape(G, G) for k in range(3)], axis=2)
    sg = 1.3 * max(panel.s, 0.5)
    cnt = gaussian_filter(cnt, sg)
    acc = gaussian_filter(acc, (sg, sg, 0))
    hue = acc / np.maximum(cnt, 1e-9)[..., None]
    hue = hue / np.maximum(hue.max(axis=2, keepdims=True), 1e-9)          # keep the colour saturated
    bright = (1 - np.exp(-cnt * gain)) * 0.80
    return bloom(Image.fromarray((hue * bright[..., None] * 255).astype(np.uint8), "RGB"))


def draw_path(img, panel, pts, k, color, frac=1.0, width=2.2, base=0.30, gain=1.0):
    """Lines z_0..z_k (last one only partly drawn: frac), fading with age."""
    d = ImageDraw.Draw(img)
    w = max(1, int(round(width * panel.s * 1.5)))
    for j in range(k):
        a = base + (1 - base) * (j + 1) / max(k, 1)
        p0 = panel.to_px(pts[j].real, pts[j].imag)
        p1 = panel.to_px(pts[j + 1].real, pts[j + 1].imag)
        if j == k - 1:
            p1 = (p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac)
        d.line([p0, p1], fill=fade_col(color, 0.9 * a * gain), width=w)


# ---------- scene: hook (fractals morph) ----------
def hook_frame(c, mo, panel_cache, a, b, t, h0, h1, S, decay):
    rho, E, w, par, s, R = mo.mix(a, b, t)
    G = c.W
    h0 *= decay
    h1 *= decay
    xs, ys, ps = [], [], []
    for _ in range(S):
        x, y, p = mo.step(rho, E, w, par)
        xs.append(x)
        ys.append(y)
        ps.append(p)
    x, y, p = np.concatenate(xs), np.concatenate(ys), np.concatenate(ps)
    # the size of the picture follows the real extent of the points (smoothed), so morphs never shrink to a dot
    r_now = float(np.percentile(np.hypot(x[::4], y[::4]), 99.9)) * 1.04
    mo.Rcur = r_now if not hasattr(mo, "Rcur") else max(r_now, 0.85 * mo.Rcur + 0.15 * r_now)   # grows at once, shrinks slowly
    panel = Panel(G, mo.Rcur, "bee")
    m0 = p == 0
    panel.splat(h0, x[m0], y[m0])
    if (~m0).any():
        panel.splat(h1, x[~m0], y[~m0])
    la, lb = LUTS[FRACTALS[mo.wps[a]["frac"]]["ramp"]], LUTS[FRACTALS[mo.wps[b]["frac"]]["ramp"]]
    img = panel.render(h0 + h1, 10 ** 6, lut=lerp(la, lb, t))
    if s > 0.002:
        ia = np.asarray(panel.render(h0, 10 ** 6, lut=LUTS["cyan"]))
        ib = np.asarray(panel.render(h1, 10 ** 6, lut=LUTS["orange"]))
        pick = (ia.sum(axis=2) >= ib.sum(axis=2))[..., None]      # the brighter of the two, never their sum
        sp = Image.fromarray(np.where(pick, ia, ib).astype(np.uint8), "RGB")
        img = Image.blend(img, sp, s)
    return img


def scene_hook(c, sink):
    G = c.W
    y0 = (c.H - G) // 2
    mo = IFSMorph(c, HOOK_PATH)
    h0 = np.zeros((G, G), np.float32)
    h1 = np.zeros((G, G), np.float32)
    legs = len(HOOK_PATH) - 1
    Kh = nframes(c, TIMING["hook_hold"])
    total = sum(nframes(c, HOOK_PATH[i + 1].get("leg", TIMING["hook_leg"])) + Kh for i in range(legs))
    n = 0
    for leg in range(legs):
        Kl = nframes(c, HOOK_PATH[leg + 1].get("leg", TIMING["hook_leg"]))
        for f in range(1, Kl + Kh + 1):
            t = smooth(f / Kl) if f <= Kl else 1.0
            img = hook_frame(c, mo, None, leg, leg + 1, t, h0, h1, c.S, c.decay)
            n += 1
            cv = c.canvas.new()
            cv.paste(img, 0, y0)
            sink.write(cv.finish(fade_k(n, total, c.fi, c.fi)))


# ---------- scene: linear ----------
def scene_linear(c, sink):
    Gp = int(c.W * 0.90)
    x0 = (c.W - Gp) // 2
    yp = int(c.H * 0.085)
    panel = Panel(Gp, LINEAR_R, "dusk")
    kf = 28 * c.s * 1.1 / EM_PX
    for bi, (label, mag, ang, steps, z0m, rel) in enumerate(LINEAR):
        cc = mag * np.exp(1j * ang)
        zA = [z0m * np.exp(0.6j)]
        zB = [zA[0] + rel * z0m * np.exp(2.0j)]
        for _ in range(steps):
            zA.append(cc * zA[-1])
            zB.append(cc * zB[-1])
        zA, zB = np.array(zA), np.array(zB)
        Ks = nframes(c, TIMING["lin_step"])
        Kh = nframes(c, TIMING["lin_hold"])
        total = steps * Ks + Kh
        n = 0
        ctex = r"c=%.2f\,e^{%.2f\,i}" % (mag, ang)
        for k in range(steps):
            for f in range(1, Ks + 1):
                u = smooth(f / Ks)
                pa = zA[k] + (zA[k + 1] - zA[k]) * u
                pb = zB[k] + (zB[k + 1] - zB[k]) * u
                n += 1
                sink.write(linear_frame(c, panel, x0, yp, label, zA, zB, k, u, pa, pb, ctex, kf, steps,
                                        fade_k(n, total, c.fi, 0)))
        for f in range(1, Kh + 1):
            n += 1
            last = bi == len(LINEAR) - 1
            sink.write(linear_frame(c, panel, x0, yp, label, zA, zB, steps, 0.0, zA[steps], zB[steps], ctex, kf,
                                    steps, 1.0 if last else fade_k(n, total, 0, c.fi)))
    linear_bridge(c, sink, panel, x0, yp, kf, zA, zB, steps, ctex)


def render_full(c, hist, lut):
    """Density picture on the whole W x H screen (log tone, calm ramp)."""
    sg = 0.9 * max(c.s, 0.5)
    h = gaussian_filter(hist, sg)
    single = 1.0 / (2 * math.pi * sg * sg)               # peak of one blurred point
    sub = h[::3, ::3]
    nz = sub[sub > single * 0.05]
    ref = max(float(np.percentile(nz, 99.7)) if nz.size else 0.0, 6 * single)
    sc = max(1.0, 20.0 / ref)
    v = np.clip(np.log1p(h * sc) / np.log1p(ref * sc), 0, 1) ** TONE_GAMMA * 0.68
    rgb = lut[(v * (LUT_N - 1)).astype(np.int32)].astype(np.uint8)
    return bloom(Image.fromarray(rgb, "RGB"))


def bridge_text(c, cv, panel, yp, label, ctex, kf, ta):
    cv.text(label, c.W / 2, yp - 58 * c.s, "subtext0", 34, ta)
    eq = math_img(r"z_{k+1}=c\,z_{k}", "text", scale=kf * 1.25)
    cm = math_img(ctex, "subtext0", scale=kf)
    yy = yp + panel.G + 22 * c.s + 70 * c.s
    cv.paste_rgba(eq, (c.W - eq.width) / 2, yy, ta)
    cv.paste_rgba(cm, (c.W - cm.width) / 2, yy + eq.height + 14 * c.s, ta)


def linear_bridge(c, sink, panel, x0, yp, kf, zA, zB, steps, ctex_last):
    """The two dots are joined by thousands of others. Every dot runs through z -> c z and leaves a trace:
    first they only turn (|c| = 1) and the traces draw a disc, ring after ring from the outside;
    then |c| < 1 (everything spirals in), |c| > 1 (spirals out), and we fall into it until it is dark."""
    T = TIMING
    rng = np.random.default_rng(SEED + 3)
    N = 9000 if c.preview else 30000
    r = BR_RMAX * np.sqrt(rng.uniform(size=N))
    th = rng.uniform(0, 2 * np.pi, N)
    o = np.argsort(-r)                                    # the outer dots start first
    r, th = r[o], th[o]
    (m_r, a_r), (m_s, a_s), (m_g, a_g) = BR_ROT, BR_SHRINK, BR_GROW
    tex = lambda mg, an: r"c=%.2f\,e^{%.2f\,i}" % (mg, an)
    kpx = panel.G * FILL / panel.R
    cx, cy = x0 + panel.G / 2, yp + panel.G / 2
    lut = LUTS["dusk"]
    hist = np.zeros((c.H, c.W), np.float32)
    S_MIN, ZOOM, OMEGA = 0.14, 45.0, 4.0                  # OMEGA: radians per second
    T_act = T["br_spin"]
    stages = [("rotates", T["br_spin"] + T["br_hold"]), ("shrinks", T["br_shrink"]),
              ("grows", T["br_grow"]), ("grows", T["br_zoom"])]
    old = linear_frame(c, panel, x0, yp, LINEAR[-1][0], zA, zB, steps, 0.0, zA[steps], zB[steps], ctex_last, kf,
                       steps, 1.0)
    Kx = nframes(c, T["br_blend"])
    t_all, prev_a, prev_s = 0.0, 0.0, 1.0
    first = True
    for si, (label, dur) in enumerate(stages):
        K = nframes(c, dur) + (Kx if si == 0 else 0)
        s0 = {0: 1.0, 1: 1.0, 2: S_MIN, 3: 1.0}[si]
        for f in range(1, K + 1):
            x = f / K
            t_all += 1.0 / c.fps
            if si <= 1 and si == 0:
                sc, ct, fade, ta = 1.0, tex(m_r, a_r), 1.0, 1.0
            elif si == 1:
                sc, ct, fade, ta = 1 - (1 - S_MIN) * smooth(x), tex(m_s, a_s), 1.0, 1.0
            elif si == 2:
                sc, ct, fade, ta = S_MIN + (1 - S_MIN) * smooth(x), tex(m_g, a_g), 1.0, 1.0
            else:
                sc, ct = math.exp(math.log(ZOOM) * x ** 1.6), tex(m_g, a_g)
                fade, ta = 1.0 - smooth((x - 0.6) / 0.4), 1.0 - smooth(x / 0.3)
            A = OMEGA * t_all
            act = int(max(2, N * smooth(t_all / T_act))) if t_all < T_act else N
            hist *= (0.97 if t_all < T_act + 0.3 else 0.86) ** c.k30
            for sub in (1, 2, 3):                           # three points per frame: a smooth trace
                a_ = prev_a + (A - prev_a) * sub / 3
                s_ = prev_s + (sc - prev_s) * sub / 3
                z = s_ * r[:act] * np.exp(1j * (th[:act] + a_))
                px, py = z.real * kpx + cx, cy - z.imag * kpx
                m = (px >= 0) & (px < c.W) & (py >= 0) & (py < c.H)
                hist += np.bincount(py[m].astype(np.int64) * c.W + px[m].astype(np.int64),
                                    minlength=c.W * c.H).reshape(c.H, c.W).astype(np.float32)
            prev_a, prev_s = A, sc
            img = render_full(c, hist, lut)
            cv = c.canvas.new()
            cv.paste(img, 0, 0)
            bridge_text(c, cv, panel, yp, label, ct, kf, ta)
            fr = cv.finish(fade)
            if si == 0 and f <= Kx:
                fr = Image.blend(old, fr, smooth(f / Kx))
            sink.write(fr)


def linear_frame(c, panel, x0, yp, label, zA, zB, k, u, pa, pb, ctex, kf, steps, fade):
    G = panel.G
    img = Image.new("RGB", (G, G), (0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = G / 2, G / 2
    r = 12 * panel.s
    d.line([(cx - r, cy), (cx + r, cy)], fill=fade_col("overlay0", 0.5), width=max(1, int(2 * panel.s)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=fade_col("overlay0", 0.5), width=max(1, int(2 * panel.s)))
    kk = min(k, steps)
    sa, sb = sprite("sapphire", panel.s * 0.55), sprite("peach", panel.s * 0.55)
    for j in range(kk + 1):                 # no lines: every place the dots have been stays as a point
        blit(img, sb, *panel.to_px(zB[j].real, zB[j].imag))
        blit(img, sa, *panel.to_px(zA[j].real, zA[j].imag))
    blit(img, sprite("peach", panel.s, big=True), *panel.to_px(pb.real, pb.imag))
    blit(img, sprite("sapphire", panel.s), *panel.to_px(pa.real, pa.imag))
    cv = c.canvas.new()
    cv.paste(img, x0, yp)
    cv.text(label, c.W / 2, yp - 58 * c.s, "subtext0", 34)
    yb = yp + G + 22 * c.s
    cv.text(f"distance  {abs(pa - pb):.3f}", c.W / 2, yb, "subtext0", 34)
    # equation and the numbers running under it
    eq = math_img(r"z_{k+1}=c\,z_{k}", "text", scale=kf * 1.25)
    cm = math_img(ctex, "subtext0", scale=kf)
    yy = yb + 70 * c.s
    if eq is not None:
        cv.paste_rgba(eq, (c.W - eq.width) / 2 - 0, yy)
        cv.paste_rgba(cm, (c.W - cm.width) / 2, yy + eq.height + 14 * c.s)
    else:
        cv.text("z(k+1) = c z(k)", c.W / 2, yy, "text", 36)
    cur = min(k, steps)
    shown = 5
    nums_alpha = 1.0 - smooth((cur - 7) / 4.0)          # too many numbers: the running list fades away
    if nums_alpha > 0.01 and eq is not None:
        ytop = yy + eq.height + cm.height + 40 * c.s
        for i in range(shown):
            j = cur - (shown - 1 - i)
            if j < 0:
                continue
            ln = math_img(r"z_{%d}=%s" % (j, cfmt(zA[j])), "subtext0", scale=kf * 0.95)
            cv.paste_rgba(ln, (c.W - ln.width) / 2, ytop + i * 40 * c.s, nums_alpha * (0.25 + 0.75 * (i + 1) / shown))
    return cv.finish(fade)


# ---------- scene: nonlinear (a dot with a line -> swirling points -> the attractor appears) ----------
def nl_geom(c):
    G = int(c.W * 0.80)
    return G, (c.W - G) // 2, (c.H - G) // 2 - int(40 * c.s)


def twist_geom(c):
    return c.W, 0, (c.H - c.W) // 2 - int(70 * c.s)


def nl_compose(c, img, geo, label=None, label_alpha=1.0, fy=None):
    G, x0, y0 = geo
    cv = c.canvas.new()
    cv.paste(img, x0, y0)
    if label:
        cv.text(label, c.W / 2, y0 + G + 78 * c.s, "overlay0", 34, label_alpha)
    formula_block(c, cv, (y0 + G + 150 * c.s) if fy is None else fy)
    return cv


def add_dot(img, spr, pos, alpha):
    if alpha >= 0.99:
        blit(img, spr, *pos)
    elif alpha > 0.01:
        lay = Image.new("RGB", img.size, (0, 0, 0))
        blit(lay, spr, *pos)
        img.paste(ImageChops.add(img, lay.point(lambda p: int(p * alpha))), (0, 0))


def scene_nonlinear(c, sink):
    T = TIMING
    geo = nl_geom(c)
    G, x0, y0 = geo
    panel = Panel(G, c.R, "dusk")
    pts = c.pathA
    spr = sprite("sapphire", panel.s)
    blank = lambda: Image.new("RGB", (G, G), (0, 0, 0))

    # 1. from the dark: a tiny disc of points (we have fallen into the linear picture)
    rng = np.random.default_rng(SEED + 1)
    m = CLOUD_POINTS // 2 if c.preview else CLOUD_POINTS
    r0 = 0.50 * c.R
    rr = r0 * np.sqrt(rng.uniform(size=m))
    th = rng.uniform(0, 2 * np.pi, size=m)
    cols = hue_color(th)

    def disc(phi, sc):                                   # inner points turn faster: a swirl
        return sc * rr * np.exp(1j * (th + phi * (1.0 + 1.5 * (1.0 - rr / r0))))

    Kf = nframes(c, T["nl_line_out"])
    for f in range(1, Kf + 1):
        sink.write(nl_compose(c, render_cloud(panel, disc(PHI_SPIN, SC_MIN), cols), geo)
                   .finish(smooth(f / Kf)))

    # 4. the map is switched on: the tiny disc is stretched and folded, the points leave a trace
    its = [disc(PHI_SPIN, SC_MIN)]
    for _ in range(NL_EXPAND_STEPS):
        its.append(Lanes.f(its[-1], c.ic, 0.0))
    ok = np.all([np.isfinite(z) & (np.abs(z) < 1e3) for z in its], axis=0)
    its = [z[ok] for z in its]
    colsN = cols[ok]
    hist = panel.new_hist()
    dec = 0.93 ** c.k30
    durs = [T["nl_expand_slow"] if i < NL_EXPAND_SLOW_N else T["nl_expand_fast"] for i in range(NL_EXPAND_STEPS)]
    for i in range(NL_EXPAND_STEPS):
        Ks = nframes(c, durs[i])
        for f in range(1, Ks + 1):
            u = smooth(f / Ks)
            z = its[i] + (its[i + 1] - its[i]) * u
            hist *= dec
            panel.splat(hist, z.real, z.imag)
            wh = smooth((i + u) / NL_EXPAND_STEPS)
            img = ImageChops.lighter(render_cloud(panel, z, colsN), dim(panel.render(hist, 10 ** 5), 0.85 * wh))
            sink.write(nl_compose(c, img, geo, label=f"step {i + (1 if u > 0.5 else 0)}").finish())

    # 5. the points keep going: the picture of the attractor builds up
    L = Lanes(c.ic, c.rng, len(its[-1]))
    L.z = its[-1].copy()
    cum = 0
    Kb = nframes(c, T["nl_build"])
    dec = 0.99 ** c.k30
    img = None
    for f in range(1, Kb + 1):
        zs = np.concatenate([L.advance(0.0) for _ in range(c.S)])
        hist *= dec
        panel.splat(hist, zs.real, zs.imag)
        cum += zs.size
        img = panel.render(hist, max(cum, 10 ** 5))
        wc = 1.0 - smooth(f / (0.5 * Kb))
        if wc > 0.01:
            img = ImageChops.lighter(img, dim(render_cloud(panel, L.z, colsN), wc))
        sink.write(nl_compose(c, img, geo, label=f"{cum:,} points").finish())
    c.ens_img = img


# ---------- scene: sectors (rewind, zones, redraw, expand) ----------
def sector_counts(xs, ys):
    ang = np.arctan2(ys.astype(np.float64), xs.astype(np.float64))
    k = np.floor(np.mod(ang - np.radians(90 - 36), 2 * np.pi) / np.radians(72)).astype(np.int64) % 5
    return np.bincount(k, minlength=5)


def draw_zones(c, cv, cx, cy, g, cnt, alpha):
    if alpha <= 0.01:
        return
    r_arc, r_lab = 0.50 * g, 0.565 * g
    for j in range(5):
        phi = 90 + 72 * j
        cv.draw.arc([cx - r_arc, cy - r_arc, cx + r_arc, cy + r_arc], -(phi + 36) + 2.5, -(phi - 36) - 2.5,
                    fill=fade_col(SECTOR_COLORS[j], alpha), width=max(2, int(6 * c.s)))
        lx = cx + r_lab * math.cos(math.radians(phi))
        ly = cy - r_lab * math.sin(math.radians(phi))
        tot = max(1, int(cnt.sum()))
        pct = 100.0 * cnt[j] / tot
        cv.text(f"{pct:.2f}%" if tot >= 100_000 else f"{pct:.1f}%", lx, ly - 18 * c.s, SECTOR_COLORS[j], 32, alpha)


def scene_sectors(c, sink):
    T = TIMING
    geo = nl_geom(c)
    G, x0, y0 = geo
    cx, cy = x0 + G / 2, y0 + G / 2
    panel = Panel(G, c.R, "dusk")
    xs, ys = c.A
    N = c.n_traj
    zero = np.zeros(5, dtype=np.int64)

    def frame(img, n, cnt, za):
        cv = nl_compose(c, img, geo, label=f"{n:,} points")
        draw_zones(c, cv, cx, cy, G, cnt, za)
        return cv.finish()

    # 1. rewind: the single dot's picture is taken back, points disappear
    h = full_hist(panel, xs, ys)
    full = panel.render(h, N)
    Kb = nframes(c, T["blend"])
    for f in range(1, Kb + 1):
        img = Image.blend(c.ens_img, full, smooth(f / Kb)) if c.ens_img is not None else full
        sink.write(frame(img, N, zero, 0.0))
    Kr = nframes(c, T["rewind"])
    rev = log_targets(N, Kr)[::-1] + [N_START]
    for i in range(1, len(rev)):
        panel.splat(h, xs[rev[i]:rev[i - 1]], ys[rev[i]:rev[i - 1]], -1.0)
        sink.write(frame(panel.render(h, rev[i]), rev[i], zero, 0.0))

    # 2. draw it again; the zones fade in once there are enough points for the shares to mean something
    counts = sector_counts(xs[:N_START], ys[:N_START])
    done = N_START
    Kc = nframes(c, T["sectors"])
    for f, n in enumerate(log_targets(N, Kc), 1):
        panel.splat(h, xs[done:n], ys[done:n])
        counts = counts + sector_counts(xs[done:n], ys[done:n])
        done = n
        img = panel.render(h, n)
        sink.write(frame(img, n, counts, smooth((n - 3000) / 20000.0)))
    img = panel.render(h, N)
    for f in range(nframes(c, T["sectors_end"])):
        sink.write(frame(img, N, counts, 1.0))

    # 4. expand: the picture grows to the size used by the next scenes, the zones fade
    Gt, _, yT = twist_geom(c)
    fy0, fy1 = y0 + G + 150 * c.s, yT + Gt + 110 * c.s
    ly0, ly1 = y0 + G + 78 * c.s, yT + Gt + 30 * c.s
    Ke = nframes(c, T["expand"])
    for f in range(1, Ke + 1):
        u = smooth(f / Ke)
        g = int(round(lerp(G, Gt, u)))
        im = img.resize((g, g), Image.LANCZOS)
        ccy = lerp(cy, yT + Gt / 2, u)
        cv = c.canvas.new()
        cv.paste(im, c.W / 2 - g / 2, ccy - g / 2)
        za = 1.0 - smooth(u / 0.5)
        draw_zones(c, cv, c.W / 2, ccy, g, counts, za)
        cv.text(f"{N:,} points", c.W / 2, lerp(ly0, ly1, u), "overlay0", 34, za)
        formula_block(c, cv, lerp(fy0, fy1, u))
        sink.write(cv.finish())
    c.carry_img = im



# ---------- scenes: twist and icon morph ----------
class Morph:
    """Ensemble of icon dots whose parameters change from frame to frame."""

    def __init__(self, c, wp_list):
        self.c, self.wp = c, wp_list
        self.L = Lanes(ICONS[wp_list[0][0] - 1], c.rng, c.lanes_m)
        for _ in range(100):
            self.L.advance(wp_list[0][1])
        self.radii = [1.06 * estimate_radius(ICONS[no - 1], c.rng, om) for no, om, _ in wp_list]

    def params(self, a, b, t):
        ia, oa, _ = self.wp[a]
        ib, ob, _ = self.wp[b]
        A, B = ICONS[ia - 1], ICONS[ib - 1]
        p = {k: lerp(A[k], B[k], t) for k in ("lam", "alpha", "beta", "gamma")}
        p["n"] = A["n"]
        return p, lerp(oa, ob, t), lerp(self.radii[a], self.radii[b], t)


class NullSink:
    def write(self, img):
        pass


def run_morph_frames(c, sink, mo, a, b, K, text_fn, hist, y0, G, fade_in=0, fade_out=0, blend_img=None, kb=0, blend_fn=None):
    S, decay = c.S, c.mdecay
    eff = S * c.lanes_m / (1 - decay)
    if hist is None:
        hist = np.zeros((G, G), dtype=np.float32)
    else:
        hist = hist * (eff / max(float(hist.sum()), 1.0))
    for f in range(1, K + 1):
        t = smoother(f / K)
        p, om, R = mo.params(a, b, t)
        panel = Panel(G, R, "dusk")
        mo.L.ic = p
        hist *= decay
        zs = np.concatenate([mo.L.advance(om) for _ in range(S)])
        if c.rot_target or c.rot_cur:
            c.rot_cur += (c.rot_target - c.rot_cur) * 0.03
            c.rot_ang += c.rot_cur / c.fps          # the rendered picture is turned (turning the dots smears it)
        panel.splat(hist, zs.real, zs.imag)
        lut = lerp(LUTS[mo.wp[a][2]], LUTS[mo.wp[b][2]], t)
        img = panel.render(hist, 10 ** 6, lut=lut, expo=c.expo)
        if c.rot_ang:
            img = img.rotate(math.degrees(c.rot_ang), resample=Image.BICUBIC)
        if blend_img is not None and f <= kb:
            img = Image.blend(blend_img, img, smooth(f / kb))
        elif blend_fn is not None and f <= kb:
            img = blend_fn(img, smoother(f / kb))
        c.last_img = img
        cv = c.canvas.new()
        cv.paste(img, 0, y0)
        text_fn(cv, p, om, t, f / K)
        sink.write(cv.finish(fade_k(f, K, fade_in, fade_out)))
    return hist


def spiral_transition(old, new, u):
    """Old picture swirls outward into a soft ring and dissolves; the new one blooms from the centre.
    Colours slide from the old tint to the new one through a shared glow."""
    G = old.width
    yy, xx = np.mgrid[0:G, 0:G].astype(np.float32)
    rad = np.hypot(xx - G / 2, yy - G / 2) / (G / 2)
    soft = np.clip((1.02 - rad) / 0.22, 0, 1)            # round soft edge, no square corners

    def xf(img, scale, ang, k):
        im = img.rotate(ang, resample=Image.BICUBIC).resize((max(8, int(G * scale)),) * 2, Image.LANCZOS)
        lay = Image.new("RGB", (G, G), (0, 0, 0))
        lay.paste(im, ((G - im.width) // 2, (G - im.height) // 2))
        a = np.asarray(lay, dtype=np.float32) * (soft * k)[..., None]
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

    uo = smooth(min(1.0, u / 0.75))
    un = smooth(max(0.0, (u - 0.25) / 0.75))
    o = xf(old, 1.0 + 0.45 * uo, 70 * uo, (1 - uo) ** 1.2)
    n = xf(new, 0.55 + 0.45 * un, -60 * (1 - un), un)
    return ImageChops.lighter(o, n)


def run_hold(c, sink, mo, idx, K, text_fn, hist, y0, G, **kw):
    """stay at waypoint idx for K frames (the radius is held too)"""
    saved = (mo.wp, mo.radii)
    mo.wp, mo.radii = [saved[0][idx]] * 2, [saved[1][idx]] * 2
    hist = run_morph_frames(c, sink, mo, 0, 1, K, text_fn, hist, y0, G, **kw)
    mo.wp, mo.radii = saved
    return hist


def scene_twist(c, sink):
    G = c.W
    y0 = twist_geom(c)[2]
    mo = Morph(c, [(HERO, 0.0, "dusk"), (HERO, OMEGA_TWIST, "dusk")])
    carry = c.carry_img
    hist = None
    if carry is not None:                       # warm up the ensemble so the picture continues the expanded crystal
        saved_wp, saved_r = mo.wp, mo.radii
        mo.wp, mo.radii = [(HERO, 0.0, "dusk")] * 2, [saved_r[0]] * 2
        hist = run_morph_frames(c, NullSink(), mo, 0, 1, nframes(c, TIMING["twist_warm"]), lambda *a: None, None, y0, G)
        mo.wp, mo.radii = saved_wp, saved_r

    def txt(cv, p, om, t, u):
        formula_block(c, cv, y0 + G + 110 * c.s, highlight=smooth(u / 0.2))
        cv.text(f"twist  {om:.2f}", c.W / 2, y0 + G + 30 * c.s, "peach", 38)

    K = nframes(c, TIMING["twist"])
    hist = run_morph_frames(c, sink, mo, 0, 1, K, txt, hist, y0, G, fade_in=0 if carry is not None else c.fi,
                            blend_img=carry, kb=nframes(c, TIMING["twist_blend"]))

    def txt_hold(cv, p, om, t, u):
        formula_block(c, cv, y0 + G + 110 * c.s, highlight=1.0)
        cv.text(f"twist  {OMEGA_TWIST:.2f}", c.W / 2, y0 + G + 30 * c.s, "peach", 38)

    c.carry_hist = run_hold(c, sink, mo, 1, nframes(c, TIMING["twist_hold"]), txt_hold, hist, y0, G)


def scene_morph(c, sink):
    G = c.W
    y0 = (c.H - G) // 2 - int(70 * c.s)
    mo = Morph(c, MORPH_PATH)
    hist = c.carry_hist
    legs = len(MORPH_PATH) - 1

    def txt(cv, p, om, t, u):
        a = 1.0 if mo.cur_leg < legs - 1 else 1.0 - smooth(u * 1.6)      # the last leg: numbers fade away
        if a > 0.01:
            formula_block(c, cv, y0 + G + 110 * c.s, alpha=a)
            param_line(c, cv, y0 + G + 40 * c.s, (p["lam"], p["alpha"], p["beta"], p["gamma"], om), alpha=a)

    mo.cur_leg = 0
    for leg in range(legs):
        mo.cur_leg = leg
        c.rot_target = 0.0 if leg < legs - 2 else 0.30          # the last two legs start to turn
        hist = run_morph_frames(c, sink, mo, leg, leg + 1, nframes(c, TIMING["morph_leg"]), txt, hist, y0, G,
                                fade_in=c.fi if (leg == 0 and c.carry_hist is None) else 0)
        hist = run_hold(c, sink, mo, leg + 1, 1 if leg == legs - 1 else nframes(c, TIMING["morph_hold"]),
                        txt, hist, y0, G)
    c.carry_hist = hist


# ---------- finale: more figures, the same morph, now turning ----------
# lookalikes (found by random search) of the book's "flower", "Clam Triple" and "Wild Chaos"
FIG_A = [(13, 0.3503009070522778, "coral"), (14, 0.05131288491163592, "blush")]            # n = 5
FIG_B = [(15, 0.0, "peach"), (16, 0.0, "dawn")]                                              # n = 3: clam -> wild
# Sierpinski-like polygons (chaos game): (name, vertices, ratio, centre map, ramp)
POLYS = []   # Sierpinski polygons removed
FIG_LEG, FIG_HOLD, FIG_SPIN = 3.4, 0.5, 0.45
FIG_IN, POLY_HOLD = 1.4, 1.9


def poly_segment(c, sink, old_img, nv, r, centre, ramp, y0, G, fade_out=0):
    """Chaos game for a regular polygon: the previous picture dissolves into the growing fractal."""
    ang = np.pi / 2 + np.arange(nv) * 2 * np.pi / nv
    V = np.exp(1j * ang)
    if centre:
        V = np.concatenate([V, [0j]])
    R = 1.06
    panel = Panel(G, R, "dusk")
    hist = panel.new_hist()
    rng = np.random.default_rng(SEED + nv)
    z = (rng.uniform(-1, 1, 60000) + 1j * rng.uniform(-1, 1, 60000)) * 0.5
    Kt, Kh = nframes(c, FIG_IN), nframes(c, POLY_HOLD)
    total = Kt + Kh
    lut = LUTS[ramp]
    last = None
    for f in range(1, total + 1):
        hist *= 0.985 ** c.k30
        for _ in range(c.S * 2):
            k = rng.integers(0, len(V), z.size)
            z = V[k] + r * (z - V[k])
            panel.splat(hist, z.real, z.imag)
        h = gaussian_filter(hist, 0.8 * max(c.s, 0.5))          # linear tone: keeps the inner structure visible
        nz = h[h > h.max() * 1e-3] if h.max() > 0 else h
        ref = max(float(np.percentile(nz, 99.5)) if nz.size else 1.0, 1e-9)
        v = np.clip(h / ref, 0, 1) ** 0.9 * V_MAX
        img = bloom(Image.fromarray(lut[(v * (LUT_N - 1)).astype(np.int32)].astype(np.uint8), "RGB"))
        if f <= Kt and old_img is not None:
            img = spiral_transition(old_img, img, smoother(f / Kt))
        last = img
        cv = c.canvas.new()
        cv.paste(img, 0, y0)
        sink.write(cv.finish(fade_k(f, total, 0, fade_out) if fade_out else 1.0))
    return last


def scene_figs(c, sink):
    G = c.W
    y0 = (c.H - G) // 2 - int(70 * c.s)
    hist = c.carry_hist
    saved_S, saved_md = c.S, c.mdecay
    nop = lambda *a: None

    def icons(path, first, old_img, last_fade):
        nonlocal hist
        c.rot_target = FIG_SPIN
        c.S, c.mdecay, c.expo = saved_S * 2, 0.93 ** c.k30, 0.42
        mo = Morph(c, path)
        if first is None:                        # dissolve from the previous picture
            hist = run_hold(c, sink, mo, 0, nframes(c, FIG_HOLD + FIG_IN), nop, None, y0, G,
                            blend_fn=lambda new, u, o=old_img: spiral_transition(o, new, u), kb=nframes(c, FIG_IN))
        for leg in range(len(path) - 1):
            hist = run_morph_frames(c, sink, mo, leg, leg + 1, nframes(c, FIG_LEG), nop, hist, y0, G)
            end = last_fade and leg == len(path) - 2
            hist = run_hold(c, sink, mo, leg + 1, nframes(c, FIG_HOLD + (1.0 if end else 0.0)), nop, hist, y0, G,
                            fade_out=c.fi * 2 if end else 0)
        c.rot_target = 0.0
        c.S, c.mdecay, c.expo = saved_S, saved_md, 0.55

    icons(FIG_A, True, None, False)              # pin-wheel -> flower
    img = c.last_img
    for nv, r, centre, ramp in POLYS:            # Sierpinski pentagon, hexagon
        img = poly_segment(c, sink, img, nv, r, centre, ramp, y0, G)
    icons(FIG_B, None, img, True)                # clam -> wild


SCENES = [("hook", scene_hook), ("linear", scene_linear), ("nonlinear", scene_nonlinear),
          ("sectors", scene_sectors), ("twist", scene_twist), ("morph", scene_morph), ("figs", scene_figs)]


def scene_seconds():
    T = TIMING
    line = (T["nl_line_out"]
            + NL_EXPAND_SLOW_N * T["nl_expand_slow"] + (NL_EXPAND_STEPS - NL_EXPAND_SLOW_N) * T["nl_expand_fast"]
            + T["nl_build"])
    return {
        "hook": sum(p.get("leg", T["hook_leg"]) + T["hook_hold"] for p in HOOK_PATH[1:]),
        "linear": (sum(s[3] * T["lin_step"] + T["lin_hold"] for s in LINEAR) + T["br_blend"] + T["br_spin"] + T["br_hold"]
                   + T["br_shrink"] + T["br_grow"] + T["br_zoom"]),
        "nonlinear": line,
        "sectors": (T["blend"] + T["rewind"] + T["sectors"] + T["sectors_end"] + T["expand"]),
        "twist": T["twist"] + T["twist_hold"],
        "morph": (len(MORPH_PATH) - 1) * (T["morph_leg"] + T["morph_hold"]),
        "figs": FIG_LEG + FIG_HOLD + len(POLYS) * (FIG_IN + POLY_HOLD) + FIG_IN + 2 * FIG_HOLD + FIG_LEG + 1.0,
    }


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--preview", action="store_true", help="540x960, 30 fps, fewer points")
    g.add_argument("--final", action="store_true", help="1080x1920, 60 fps")
    ap.add_argument("--scenes", help="comma list: hook,linear,nonlinear,sectors,twist,morph,figs")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--plain-math", action="store_true", help="draw formulas with Pillow only (no matplotlib)")
    ap.add_argument("--out", help="output mp4 path")
    ap.add_argument("--png-dir")
    ap.add_argument("--png-every", type=int, default=0)
    ap.add_argument("--no-video", action="store_true")
    a = ap.parse_args()

    secs = scene_seconds()
    if a.list:
        for n, _ in SCENES:
            print(f"{n:10s} ~{secs[n]:5.1f} s")
        print(f"total      ~{sum(secs.values()):5.1f} s")
        return
    global HAVE_MPL
    if a.plain_math:
        HAVE_MPL = False
    if not HAVE_MPL:
        print("note: matplotlib not used, formulas are drawn with Pillow (pip install matplotlib for TeX quality)")

    final = a.final or not a.preview
    W, H, fps = (1080, 1920, FPS_FINAL) if final else (540, 960, FPS_PREVIEW)
    names = a.scenes.split(",") if a.scenes else [n for n, _ in SCENES]
    rng = np.random.default_rng(SEED)
    c = make_ctx(W, H, fps, not final, rng)
    out = a.out or ("symmetric_chaos_final.mp4" if final else "symmetric_chaos_preview.mp4")
    sink = Sink(out, W, H, fps, a.png_dir, a.png_every, video=not a.no_video)
    t0 = time.time()
    print(f"{W}x{H} @ {fps} fps, ~{sum(secs[n] for n in names):.0f} s of video")
    if any(n in names for n in ("nonlinear", "sectors")):
        prepare_dots(c)
    for n, fn in SCENES:
        if n in names:
            print(f"  scene {n} ...", flush=True)
            fn(c, sink)
    sink.close()
    print(f"done in {time.time() - t0:.0f} s -> {out}")


if __name__ == "__main__":
    main()