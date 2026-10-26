"""
WHY DOESN'T THE SUNFLOWER PACK ITS SEEDS HEXAGONALLY?
Manim Community Edition, vertical 1080x1920, ~60 s.

Preview:  manim -pql sunflower_story.py SunflowerStory
Final:    manim -qh  sunflower_story.py SunflowerStory

Font: Montserrat Light (install the Light weight on the rendering machine).
While rendering, the console prints "[CUE ...]" lines with the exact start
time of every scene, so you can line the voiceover up in your editor.
All run times live in TIMING below: stretch or shrink them to match your voice.

=============================== VOICEOVER SCRIPT ===============================
(start times are approximate, the real ones are printed as [CUE] lines)

[0:00]  SCENE 1 - hexagonal packing grows inside the circle (no on-screen text)
    "If hexagonal packing is the most efficient way to fill a circle,
     why doesn't the sunflower use it?"

[0:07]  SCENE 2 - hexagon vs sunflower, counter n freezes at 105
    "Seeds grow from the center, one at a time. And the sunflower pattern
     stays even and round at every single step."

[0:16]  SCENE 3 - hopping over seeds 1, 2, 3, 4: the same angle every time
    "This is achieved by one rule: every new seed turns 137.5 degrees
     from the last one. The same angle, every time."

[0:24]  SCENE 4 - benchmark of every angle (the sweep reaches 137.5 at ~0:37)
    "Let's benchmark every angle from zero to one hundred eighty degrees:
     place the seeds, inflate them until they touch, and measure the fill.
     And look - the most effective angle is 137.5."
    (optional: angles above 180 are mirror images, so half the range is enough)

[0:42]  SCENE 4b - nudge to 137.3 and 137.6
    "Shift it by even 0.1 degree, and the fill drops almost by half."

[0:48]  SCENE 5 - neighbour count, then the sunflower grows endlessly and fades out
    "So the hexagon never went away. Most seeds are surrounded by exactly
     six neighbors. The lattice was just twisted into a spiral, allowing it
     to expand infinitely."
================================================================================
"""
import numpy as np
from scipy.spatial import Delaunay, cKDTree
from manim import *

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16
config.frame_rate = 60
config.background_color = "#08080C"

FONT = "Montserrat"
FONT_WEIGHT = "LIGHT"

C_TEXT = "#F4F4F8"
C_MUTE = "#8B90A8"
C_RING = "#363B52"
C_GOLD = "#F9E2AF"
C_ORANGE = "#FB8500"
C_TEAL = "#5EEAD4"
C_TEAL_D = "#0F766E"
C_SAPPHIRE = "#89B4FA"
C_RED = "#F38BA8"
C_BG = "#08080C"

# Run times in seconds. Tune these to your voice.
TIMING = dict(
    # scene 1: hexagon grows
    hex_ring=0.8, hex_grow=4.2, hex_hold=2.0,
    # scene 2: comparison
    cmp_setup=0.8, rewind=0.9, cmp_grow=4.0, cmp_freeze=3.2,
    # scene 3: hops over seeds 1..4
    wipe=0.5, seeds_in=1.6, dim=0.4, hop=0.55, hop_pause=0.35, hop_end=1.2,
    # scene 4: benchmark
    bench_intro=0.8, bench_lead=1.0, sweep=13.0, back=1.5, back_wait=0.5,
    nudge=1.2, nudge_hold=0.6, nudge_back=0.9, bench_end=0.8,
    # scene 5: finale (sunflower -> six-neighbour colours -> endless growth + fade out)
    fin_base=1.0, fin_wait=1.2, fin_swap=1.2, fin_hold=2.0, fin_revert=1.0, fin_grow=5.0,
)

# Endless growth in the finale
FIN_N0 = 1000       # seeds in the picture before the growth starts
FIN_N_END = 30000   # seeds at the very end
FIN_Z_END = 0.75    # zoom-out: final scale of the picture (1 = no zoom)
FIN_U_FADE = 0.75   # growth progress (0..1) at which the fade-out starts

# --- MATH-BEGIN (pure math, no Manim) -----------------------------------------

ALPHA_DEG = 137.507764
ALPHA_GOLD = np.radians(ALPHA_DEG)
GAP = 0.96     # seeds are drawn slightly smaller than "touching"
N_B = 500      # number of seeds in the benchmark
HEX_K = 8      # hexagonal rings -> 3*K*(K+1)+1 = 217 seeds
FREEZE_N = 105 # the comparison freezes here (hexagon: 6th ring is 14/36 full)


def vogel(N, alpha=ALPHA_GOLD, offset=0.5):
    """Vogel's model: angle n*alpha, radius sqrt(n + offset). Unit scale."""
    n = np.arange(N)
    r = np.sqrt(n + offset)
    th = n * alpha
    return np.c_[r * np.cos(th), r * np.sin(th)]


def min_nn(P):
    """Smallest distance between any two seeds."""
    d, _ = cKDTree(P).query(P, k=2)
    return d[:, 1].min()


def vogel_c(N, R):
    """Golden-angle sunflower of N seeds inside radius R: scale c and seed radius."""
    P = vogel(N)
    m = min_nn(P)
    rmax = np.linalg.norm(P, axis=1).max()
    c = R / (rmax + GAP * m / 2)
    return c, GAP * c * m / 2


def fit_vogel(N, R, alpha=ALPHA_GOLD):
    """Scale and seed radius so seeds do not overlap and fit inside radius R."""
    P = vogel(N, alpha)
    m = min_nn(P)
    rmax = np.linalg.norm(P, axis=1).max()
    c = R / (rmax + GAP * m / 2)
    return P * c, GAP * c * m / 2


def hex_rings(K, a):
    """Hexagonal lattice with spacing a and K rings, ordered ring by ring and,
    inside a ring, counter-clockwise from angle 0. 3K(K+1)+1 points."""
    items = []
    for q in range(-K, K + 1):
        for s in range(-K, K + 1):
            ring = max(abs(q), abs(s), abs(q + s))
            if ring > K:
                continue
            x = a * (q + 0.5 * s)
            y = a * (np.sqrt(3) / 2) * s
            ang = (np.arctan2(y, x) % (2 * np.pi)) if ring else 0.0
            items.append((ring, ang, x, y))
    items.sort()
    return np.array([[x, y] for _, _, x, y in items])


def bench(alpha, N=N_B):
    """Benchmark of one angle: N seeds, all inflated equally until the first two
    touch. Returns positions in a field of radius 1, seed radius, fill in %."""
    P = vogel(N, alpha)
    m = min_nn(P)
    rmax = np.sqrt(N - 0.5)
    c = 1.0 / (rmax + m / 2)
    rad = c * m / 2
    return P * c, rad, N * rad ** 2 * 100


def neighbor_stats(P):
    """Neighbour count from the Delaunay triangulation and a mask of inner seeds."""
    tri = Delaunay(P)
    nb = [set() for _ in range(len(P))]
    for a, b, c in tri.simplices:
        nb[a].update((b, c))
        nb[b].update((a, c))
        nb[c].update((a, b))
    deg = np.array([len(s) for s in nb])
    r = np.linalg.norm(P, axis=1)
    inner = r < 0.85 * r.max()
    return deg, inner

# --- MATH-END -----------------------------------------------------------------


def T(text, size=34, color=C_TEXT, max_w=8.4):
    t = Text(text, font=FONT, weight=FONT_WEIGHT, font_size=size, color=color)
    if t.width > max_w:
        t.scale(max_w / t.width)
    return t


def make_balls(P, center, radius, colors, stroke_width=1.0):
    balls = VGroup()
    for (x, y), col in zip(P, colors):
        b = Circle(
            radius=radius,
            stroke_width=stroke_width,
            stroke_color=col,
            fill_color=col,
            fill_opacity=0.85,
        )
        b.move_to(center + np.array([x, y, 0.0]))
        balls.add(b)
    return balls


def attach_growth(balls, trk, base=0.85):
    """Seed i fades in while the tracker passes value i (growth one by one)."""
    subs = balls.submobjects

    def upd(_):
        t = trk.get_value()
        for i, b in enumerate(subs):
            o = min(max(t - i, 0.0), 1.0)
            b.set_fill(opacity=base * o)
            b.set_stroke(opacity=o)

    balls.add_updater(upd)
    upd(balls)


def smooth01(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


def make_growth_bins(c, rad, center, n_end, n_color=12000, levels=48):
    """A sunflower of up to n_end seeds built from a few big shapes instead of
    tens of thousands of separate circles (that would take forever to render).
    Seeds are grouped by colour (gold -> orange along the seed index); each group
    is one VMobject. Returns (group, set_state); set_state(n, zoom, alpha) shows the
    first n seeds, scaled by `zoom` around `center`, with opacity factor `alpha`."""
    k = 0.5522847498   # four cubic Bezier arcs make a circle
    unit = rad * np.array([
        [1, 0, 0], [1, k, 0], [k, 1, 0], [0, 1, 0],
        [0, 1, 0], [-k, 1, 0], [-1, k, 0], [-1, 0, 0],
        [-1, 0, 0], [-1, -k, 0], [-k, -1, 0], [0, -1, 0],
        [0, -1, 0], [k, -1, 0], [1, -k, 0], [1, 0, 0],
    ], dtype=float)
    P = np.zeros((n_end, 3))
    P[:, :2] = vogel(n_end) * c
    palette = color_gradient([C_GOLD, C_ORANGE], levels)
    edges = np.linspace(0, n_color, levels + 1).astype(int)
    edges[-1] = n_end
    group = VGroup()
    for b in range(levels):
        lo, hi = int(edges[b]), int(edges[b + 1])
        base = (P[lo:hi, None, :] + unit[None, :, :]).reshape(-1, 3)
        m = VMobject(stroke_width=0, fill_color=palette[b], fill_opacity=0.85)
        m.set_points(base[:16])
        m.lo, m.hi, m.base = lo, hi, base
        group.add(m)

    def set_state(n, zoom, alpha):
        for m in group.submobjects:
            seeds = int(min(max(n - m.lo, 0), m.hi - m.lo))
            m.set_points(center + zoom * m.base[: max(seeds, 1) * 16])
            m.set_fill(opacity=0.85 * alpha if seeds > 0 else 0.0)

    return group, set_state


R_PANEL = 3.0
TOP_C = np.array([0.0, 4.1, 0.0])     # hexagon panel
BOT_C = np.array([0.0, -3.2, 0.0])    # sunflower panel
COUNTER_POS = np.array([0.0, 0.45, 0.0])


class SunflowerStory(Scene):
    # ------------------------------------------------------------------
    def cue(self, name):
        try:
            t = self.renderer.time
        except Exception:
            t = float("nan")
        print(f"[CUE {t:6.2f}s] {name}")

    def wipe(self, t=None):
        t = TIMING["wipe"] if t is None else t
        mobs = list(self.mobjects)
        for m in mobs:
            m.clear_updaters()
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=t)

    # ------------------------------------------------------------------
    # SCENE 1. No text. The hexagonal packing grows inside the circle,
    # exactly where the comparison will happen.
    # VO: "If hexagonal packing is the most efficient way to fill a circle,
    #      why doesn't the sunflower use it?"
    def hex_intro(self):
        self.cue("scene 1: hexagon")
        K = HEX_K
        a = R_PANEL / (K + GAP / 2)
        P = hex_rings(K, a)
        N = len(P)
        self.n_cmp = N
        self.hex_balls = make_balls(
            P, TOP_C, GAP * a / 2, color_gradient([C_TEAL, C_TEAL_D], N)
        )
        self.hex_trk = ValueTracker(0)
        attach_growth(self.hex_balls, self.hex_trk)
        self.ring_top = Circle(
            radius=R_PANEL, stroke_color=C_RING, stroke_width=2
        ).move_to(TOP_C)

        self.add(self.hex_balls)
        self.play(Create(self.ring_top), run_time=TIMING["hex_ring"])
        self.play(
            self.hex_trk.animate.set_value(N),
            run_time=TIMING["hex_grow"],
            rate_func=linear,
        )
        self.wait(TIMING["hex_hold"])

    # ------------------------------------------------------------------
    # SCENE 2. Counter n appears. The hexagon rewinds and both patterns grow
    # one seed at a time until n = 105, where everything freezes.
    # VO: "Seeds grow from the center, one at a time. And the sunflower
    #      pattern stays even and round at every single step."
    def compare(self):
        self.cue("scene 2: comparison")
        N = self.n_cmp
        P_g, r_g = fit_vogel(N, R_PANEL)
        self.gold_balls = make_balls(
            P_g, BOT_C, r_g, color_gradient([C_GOLD, C_ORANGE], N)
        )
        self.gold_trk = ValueTracker(0)
        attach_growth(self.gold_balls, self.gold_trk)
        self.ring_bot = Circle(
            radius=R_PANEL, stroke_color=C_RING, stroke_width=2
        ).move_to(BOT_C)
        self.add(self.gold_balls)

        def counter():
            v = max(self.hex_trk.get_value(), self.gold_trk.get_value())
            return T(f"n = {int(round(v))}", 40, C_TEXT).move_to(COUNTER_POS)

        self.play(Create(self.ring_bot), run_time=TIMING["cmp_setup"])
        self.add(always_redraw(counter))

        # the hexagon rewinds to zero (outer seeds vanish first)
        self.play(
            self.hex_trk.animate.set_value(0),
            run_time=TIMING["rewind"],
            rate_func=smooth,
        )
        # both grow together
        self.play(
            self.hex_trk.animate.set_value(FREEZE_N),
            self.gold_trk.animate.set_value(FREEZE_N),
            run_time=TIMING["cmp_grow"],
            rate_func=linear,
        )
        self.wait(TIMING["cmp_freeze"])

    # ------------------------------------------------------------------
    # SCENE 3. A marker hops over seeds 1, 2, 3, 4. Every hop turns the
    # direction by the same 137.5 degrees.
    # VO: "This is achieved by one rule: every new seed turns 137.5 degrees
    #      from the last one. The same angle, every time."
    def angle_hops(self):
        self.wipe()
        self.cue("scene 3: angle hops")
        N = 34
        P = vogel(N, offset=0.0) * 0.6   # seed 0 sits in the center, as in Vogel's formula
        rad = GAP * min_nn(P) / 2
        center = np.array([0.0, 1.0, 0.0])
        balls = make_balls(
            P, center, rad, color_gradient([C_GOLD, C_ORANGE], N), stroke_width=1.5
        )
        trk = ValueTracker(0)
        attach_growth(balls, trk)
        self.add(balls)
        self.play(
            trk.animate.set_value(N),
            run_time=TIMING["seeds_in"],
            rate_func=linear,
        )
        balls.clear_updaters()

        # focus on seeds 1..4 (seed 0 is the center and stays bright)
        self.play(
            *[balls[i].animate.set_opacity(0.28) for i in range(5, N)],
            run_time=TIMING["dim"],
        )

        # seeds 1..4 sit at angles 1*a, 2*a, 3*a, 4*a
        pos = [center + np.array([P[k + 1, 0], P[k + 1, 1], 0.0]) for k in range(4)]
        theta = [(k + 1) * ALPHA_GOLD for k in range(4)]
        ray_len = 2.8
        rays = [
            Line(
                center,
                center + ray_len * np.array([np.cos(t), np.sin(t), 0.0]),
                stroke_color=C_TEXT,
                stroke_width=3,
            )
            for t in theta
        ]
        arc_r = [1.7, 1.95, 2.2]
        arcs, labels = [], []
        for k in range(3):
            arcs.append(
                Arc(
                    radius=arc_r[k],
                    start_angle=theta[k],
                    angle=ALPHA_GOLD,
                    arc_center=center,
                    stroke_color=C_SAPPHIRE,
                    stroke_width=5,
                )
            )
            mid = theta[k] + ALPHA_GOLD / 2
            lab = T("137.5°", 30, C_SAPPHIRE).move_to(
                center + (arc_r[k] + 0.45) * np.array([np.cos(mid), np.sin(mid), 0.0])
            )
            lab.set_stroke(C_BG, width=6, background=True)
            labels.append(lab)
        nums = [T(str(k + 1), 28, C_BG).move_to(pos[k]) for k in range(4)]
        origin = Dot(center, radius=0.06, color=C_BG)
        marker = Circle(
            radius=rad * 1.4, stroke_color=C_TEXT, stroke_width=3, fill_opacity=0
        ).move_to(pos[0])

        hop = TIMING["hop"]
        self.play(
            FadeIn(marker, scale=1.4),
            FadeIn(origin),
            Create(rays[0]),
            FadeIn(nums[0]),
            run_time=hop,
        )
        for k in range(1, 4):
            self.wait(TIMING["hop_pause"])
            self.play(
                marker.animate.move_to(pos[k]),
                Create(rays[k]),
                FadeIn(nums[k]),
                run_time=hop,
            )
            self.play(
                Create(arcs[k - 1]),
                FadeIn(labels[k - 1], scale=0.8),
                run_time=hop,
            )
        self.wait(TIMING["hop_end"])

    # ------------------------------------------------------------------
    # SCENE 4. Benchmark of every angle from 0 to 180 degrees. Seeds inflate
    # until two touch; the curve shows how much of the circle they fill.
    # VO: "Let's benchmark every angle from zero to one hundred eighty degrees:
    #      place the seeds, inflate them until they touch, and measure the fill.
    #      And look - the most effective angle is 137.5."
    # then, on the nudge to 137.3 / 137.6:
    # VO: "Shift it by even 0.1 degree, and the fill drops almost by half."
    def benchmark(self):
        self.wipe()
        self.cue("scene 4: benchmark")
        N = N_B
        R = 3.0
        C = np.array([0.0, 3.5, 0.0])

        ang = np.arange(0.0, 180.0001, 0.25)
        sc = np.array([bench(np.radians(a))[2] for a in ang])

        ring = Circle(radius=R, stroke_color=C_RING, stroke_width=2).move_to(C)
        balls = make_balls(
            np.zeros((N, 2)), C, 0.05,
            color_gradient([C_GOLD, C_ORANGE], N), stroke_width=0.6,
        )

        axes = Axes(
            x_range=[0, 180, 30], y_range=[0, 64, 16],
            x_length=7.6, y_length=3.0, tips=False,
            axis_config={
                "include_ticks": False, "include_numbers": False,
                "stroke_color": C_MUTE, "stroke_width": 2,
            },
        ).move_to([0, -4.5, 0])
        tick_labels = VGroup(
            *[T(f"{x}°", 24, C_MUTE).move_to(axes.c2p(x, 0) + 0.3 * DOWN) for x in (0, 90, 180)],
            T("50%", 24, C_MUTE).next_to(axes.c2p(0, 50), LEFT, buff=0.1),
            T("0%", 24, C_MUTE).next_to(axes.c2p(0, 0), LEFT, buff=0.1),
        )

        full = VMobject(stroke_color=C_GOLD, stroke_width=3.5)
        full.set_points_as_corners([axes.c2p(a, s) for a, s in zip(ang, sc)])

        a_trk = ValueTracker(0.0)   # tested angle
        d_trk = ValueTracker(0.0)   # how much of the curve is drawn

        def upd_balls(g):
            pos, rad, _ = bench(np.radians(a_trk.get_value()))
            d = 2 * rad * R
            for b, p in zip(g.submobjects, pos):
                b.scale(d / b.width)
                b.move_to(C + np.array([p[0] * R, p[1] * R, 0.0]))

        balls.add_updater(upd_balls)
        upd_balls(balls)

        curve = full.copy()
        curve.add_updater(
            lambda m: m.pointwise_become_partial(
                full, 0, min(max(d_trk.get_value() / 180, 1e-3), 1.0)
            )
        )

        dot = Dot(radius=0.1, color=C_TEXT)
        dot.add_updater(
            lambda m: m.move_to(
                axes.c2p(a_trk.get_value(), float(np.interp(a_trk.get_value(), ang, sc)))
            )
        )

        def readout():
            a = a_trk.get_value()
            fill = bench(np.radians(a))[2]
            col = C_GOLD if fill > 50 else (C_RED if fill < 20 else C_TEXT)
            return T(f"{a:.1f}°  ·  fill {fill:.0f}%", 36, col).move_to([0, -0.4, 0])

        title = T("Let's test every angle from 0° to 180°", 32).move_to([0, 7.45, 0])
        sub = T("seeds inflate until two touch", 28, C_MUTE).move_to([0, -1.2, 0])

        self.add(ring, balls, axes, tick_labels, curve, dot)
        self.add(always_redraw(readout))
        self.play(FadeIn(title), FadeIn(sub), run_time=TIMING["bench_intro"])
        self.wait(TIMING["bench_lead"])
        self.play(
            a_trk.animate.set_value(180),
            d_trk.animate.set_value(180),
            run_time=TIMING["sweep"],
            rate_func=linear,
        )

        # back to the winner, then nudge by 0.1 degree each way
        self.cue("scene 4b: back to the peak")
        self.play(
            a_trk.animate.set_value(ALPHA_DEG),
            run_time=TIMING["back"],
            rate_func=smooth,
        )
        self.wait(TIMING["back_wait"])
        for target in (137.3, 137.6):
            self.play(a_trk.animate.set_value(target), run_time=TIMING["nudge"])
            self.wait(TIMING["nudge_hold"])
            self.play(a_trk.animate.set_value(ALPHA_DEG), run_time=TIMING["nudge_back"])
        self.wait(TIMING["bench_end"])

    # ------------------------------------------------------------------
    # SCENE 5. The sunflower is coloured by neighbour count (only the legend is
    # on screen), turns gold again and then grows endlessly: it zooms out, the
    # pattern keeps filling the whole screen, and everything fades to black.
    # VO: "So the hexagon never went away. Most seeds are surrounded by exactly
    #      six neighbors. The lattice was just twisted into a spiral, allowing it
    #      to expand infinitely."
    def finale(self):
        self.wipe()
        self.cue("scene 5: neighbours, then endless growth")
        R = 3.6
        C = np.array([0.0, 0.0, 0.0])
        c, rad = vogel_c(FIN_N0, R)
        P0 = vogel(FIN_N0) * c
        deg, inner = neighbor_stats(P0)

        cols = []
        for d, inn in zip(deg, inner):
            if not inn:
                cols.append(C_RING)
            elif d == 6:
                cols.append(C_TEAL)
            else:
                cols.append(C_RED)
        colored = make_balls(P0, C, rad, cols, stroke_width=0.4)
        legend = VGroup(
            VGroup(Dot(color=C_TEAL, radius=0.08), T("6 neighbors", 28)).arrange(RIGHT, buff=0.2),
            VGroup(Dot(color=C_RED, radius=0.08), T("5 or 7: defects", 28)).arrange(RIGHT, buff=0.2),
        ).arrange(RIGHT, buff=0.7).move_to([0, -5.0, 0])

        bins, set_state = make_growth_bins(c, rad, C, FIN_N_END)
        set_state(FIN_N0, 1.0, 1.0)

        self.play(FadeIn(bins), run_time=TIMING["fin_base"])
        self.wait(TIMING["fin_wait"])
        self.play(FadeOut(bins), FadeIn(colored), FadeIn(legend), run_time=TIMING["fin_swap"])
        self.wait(TIMING["fin_hold"])
        set_state(FIN_N0, 1.0, 1.0)   # back to the plain gold picture before it fades in again
        self.play(FadeOut(colored), FadeOut(legend), FadeIn(bins), run_time=TIMING["fin_revert"])

        # endless growth: seeds multiply exponentially, the picture zooms out,
        # the pattern covers the screen, then the whole thing fades out
        self.cue("scene 5b: endless growth")
        trk = ValueTracker(0.0)

        def state(u):
            n = FIN_N0 * (FIN_N_END / FIN_N0) ** u
            zoom = 1.0 - (1.0 - FIN_Z_END) * smooth01(u)
            alpha = 1.0 - smooth01((u - FIN_U_FADE) / (1.0 - FIN_U_FADE))
            return n, zoom, alpha

        bins.add_updater(lambda g: set_state(*state(trk.get_value())))
        self.play(trk.animate.set_value(1.0), run_time=TIMING["fin_grow"], rate_func=linear)
        bins.clear_updaters()

    # ------------------------------------------------------------------
    def construct(self):
        self.hex_intro()
        self.compare()
        self.angle_hops()
        self.benchmark()
        self.finale()