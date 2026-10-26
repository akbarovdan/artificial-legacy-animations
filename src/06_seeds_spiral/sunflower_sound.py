"""
SONIFICATION FOR "WHY DOESN'T THE SUNFLOWER PACK ITS SEEDS HEXAGONALLY?"
Renders one stereo WAV (44.1 kHz, 16 bit, ~58 s) that follows sunflower_story.py.

Run:  python sunflower_sound.py

SYNC WITH THE VIDEO
  The TIMING dict below is a copy of the one in sunflower_story.py.
  With SYNC_WITH_VIDEO = True (default) the script reads TIMING straight from
  sunflower_story.py (it must lie next to this file), so sound and picture move
  together whenever you retune the video. Set SYNC_WITH_VIDEO = False to tune
  the sound on its own with the values in this file.
  Console lines "[CUE ...]" print the start time of every scene.

HARMONY
  Everything lives in D major pentatonic (D E F# A B), so any combination of notes
  is consonant. Pads walk G - Bm - Em - Asus - D (a gentle "lift and resolve").
  Soft octave "shimmer" layers pulse inside every pad (the iridescent sparkle).

WHAT YOU HEAR
  1  hexagon grows        one bell per ring, rising, plus a rain of tiny sparkles.
  2  comparison           hexagon = left, stepwise bells (one per ring);
                          sunflower = right, an even flowing arpeggio.
                          They freeze together on a resolved chord at n = 105.
  3  hops over seeds 1-4  each hop climbs the same two scale steps, each angle arc
                          rings the SAME chime: the same angle, every time.
  4  benchmark            the sweep plays the fill curve as a melody: higher note =
                          fuller circle, left-to-right pan = angle. A build-up
                          sparkle accelerando leads to 137.5 deg: the top note D6
                          and a resolving chord. The nudges to 137.3 / 137.6 pull
                          the chord out of tune (beating), then back in tune.
  5  neighbours, then     the colour change gets a short harp glissando; the legend
     endless growth       appears in silence (no chimes on text). When the pattern
                          turns gold again an endless cascade starts: climbing runs
                          of 13 notes with panning that cycles every 21 notes
                          (Fibonacci against Fibonacci), speeding up as the seeds
                          multiply, plus a rising glitter. It fades out together
                          with the picture.

MIX
  PAD_LEVEL controls the chord bed under the notes (0 = no bed at all, only notes).
  LEVEL lowers or raises the whole track (keep it near 0.5-0.7 under a voiceover).
  EXPORT_STEMS = True also writes one WAV per scene (all start at 0:00, so they
  line up when dropped into an editor).
"""
import ast
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import fftconvolve, lfilter
from scipy.spatial import cKDTree

# =============================================================
# 0. PATHS AND SETTINGS
# =============================================================
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_NAME = SCRIPT_PATH.stem
SCRIPT_DIR = SCRIPT_PATH.parent
# Your layout: <project>/<a>/<b>/script.py with <project>/media next to it.
# Anywhere else the "media" folder is created next to this file.
_root = SCRIPT_PATH.parents[2] if len(SCRIPT_PATH.parents) > 2 else None
if _root is not None and _root != Path(_root.anchor) and (_root / "media").is_dir():
    PROJECT_ROOT = _root
else:
    PROJECT_ROOT = SCRIPT_DIR

OUTPUT_DIR = PROJECT_ROOT / "media" / "sounds" / SCRIPT_NAME
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"{SCRIPT_NAME}.wav"

SAMPLE_RATE = 44100
SR = SAMPLE_RATE

LEVEL = 0.5            # master peak, 0..1 (0.5 sits comfortably under a voiceover)
REVERB_WET = 0.38      # amount of shimmering reverb
PAD_LEVEL = 0.01       # chord bed under the notes: 0 removes it, 1.0 = the old loud bed
PAD_FLOOR = 55         # lowest MIDI note allowed in the bed (no low rumble)
COLOR_WASH = True      # finale: harp glissando when the colours appear (set False for silence)
TAIL = 2.0             # seconds of ring-out after the last frame of the video
EXPORT_STEMS = False
SEED = 7

SYNC_WITH_VIDEO = True
VIDEO_FILE = SCRIPT_DIR / "sunflower_story.py"

# Run times in seconds. Tune these to your voice (same keys as the video file).
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

# Endless growth in the finale (same names as in the video file)
FIN_N0 = 1000
FIN_N_END = 30000
FIN_Z_END = 0.75
FIN_U_FADE = 0.75   # growth progress (0..1) at which the picture starts to fade out


def load_video_settings(path):
    """Read TIMING = dict(...) and the FIN_* constants from the video file (no Manim needed)."""
    timing, consts = None, {}
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                continue
            name = node.targets[0].id
            if name == "TIMING" and isinstance(node.value, ast.Call):
                timing = {kw.arg: ast.literal_eval(kw.value) for kw in node.value.keywords}
            elif name.startswith("FIN_"):
                consts[name] = ast.literal_eval(node.value)
    except Exception as exc:
        print(f"Could not read settings from {path.name}: {exc}")
    return timing, consts


if SYNC_WITH_VIDEO:
    _video_timing, _video_consts = load_video_settings(VIDEO_FILE) if VIDEO_FILE.exists() else (None, {})
    if _video_timing:
        TIMING.update(_video_timing)
        globals().update(_video_consts)
        print(f"TIMING taken from {VIDEO_FILE.name}")
    else:
        print(f"{VIDEO_FILE.name} not found next to this file, using TIMING from this file")

# --- MATH-BEGIN (same benchmark as in the video) ------------------------------
N_B = 500
FREEZE_N = 105
HEX_K = 8
ALPHA_DEG = 137.507764


def vogel(N, alpha=np.radians(ALPHA_DEG), offset=0.5):
    n = np.arange(N)
    r = np.sqrt(n + offset)
    th = n * alpha
    return np.c_[r * np.cos(th), r * np.sin(th)]


def min_nn(P):
    d, _ = cKDTree(P).query(P, k=2)
    return d[:, 1].min()


def bench_fill(alpha, N=N_B):
    """Fill in % for one angle: seeds inflate until two touch."""
    P = vogel(N, alpha)
    m = min_nn(P)
    c = 1.0 / (np.sqrt(N - 0.5) + m / 2)
    rad = c * m / 2
    return N * rad ** 2 * 100
# --- MATH-END -----------------------------------------------------------------

# =============================================================
# 1. TIMELINE (mirrors the scene structure of the video)
# =============================================================


def plan(T):
    P = {}
    t = 0.0
    # scene 1
    P["s1"] = t
    P["hex_grow_at"] = t + T["hex_ring"]
    t += T["hex_ring"] + T["hex_grow"] + T["hex_hold"]
    # scene 2
    P["s2"] = t
    P["rewind_at"] = t + T["cmp_setup"]
    P["cmp_grow_at"] = P["rewind_at"] + T["rewind"]
    P["freeze_at"] = P["cmp_grow_at"] + T["cmp_grow"]
    t = P["freeze_at"] + T["cmp_freeze"]
    # scene 3
    P["s3"] = t
    P["seeds_at"] = t + T["wipe"]
    P["dim_at"] = P["seeds_at"] + T["seeds_in"]
    h = P["dim_at"] + T["dim"]
    P["hop_at"] = [h]
    h += T["hop"]
    P["arc_at"] = []
    for _ in range(3):
        h += T["hop_pause"]
        P["hop_at"].append(h)
        h += T["hop"]
        P["arc_at"].append(h)
        h += T["hop"]
    t = h + T["hop_end"]
    # scene 4
    P["s4"] = t
    P["sweep_at"] = t + T["wipe"] + T["bench_intro"] + T["bench_lead"]
    P["peak_at"] = P["sweep_at"] + T["sweep"] * ALPHA_DEG / 180.0
    P["back_at"] = P["sweep_at"] + T["sweep"]
    P["return_at"] = P["back_at"] + T["back"]
    n0 = P["return_at"] + T["back_wait"]
    one = T["nudge"] + T["nudge_hold"] + T["nudge_back"]
    P["nudge_at"] = [n0, n0 + one]
    t = n0 + 2 * one + T["bench_end"]
    # scene 5
    P["s5"] = t
    P["fin_base_at"] = t + T["wipe"]
    P["fin_swap_at"] = P["fin_base_at"] + T["fin_base"] + T["fin_wait"]
    P["fin_revert_at"] = P["fin_swap_at"] + T["fin_swap"] + T["fin_hold"]
    P["fin_grow_at"] = P["fin_revert_at"] + T["fin_revert"]
    P["end"] = P["fin_grow_at"] + T["fin_grow"]
    return P


# =============================================================
# 2. SYNTHESIZERS
# =============================================================
TWO_PI = 2.0 * np.pi
D_PENT = [0, 2, 4, 7, 9]        # D E F# A B


def mtof(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def pent(idx):
    """Index in the D major pentatonic scale: 0 = D3, 5 = D4, 10 = D5, 15 = D6."""
    octv, deg = divmod(int(idx), 5)
    return 50 + 12 * octv + D_PENT[deg]


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def pan_gains(pan):
    pan = float(np.clip(pan, -1.0, 1.0))
    return np.sqrt(0.5 * (1.0 - pan)), np.sqrt(0.5 * (1.0 + pan))


def synth_pad(notes, dur, vel=0.5, attack=0.9, release=1.4, bend_cents=None,
              seed=0, shimmer=0.35):
    """Warm detuned pad with slowly pulsing octave 'shimmer' layers.
    notes: MIDI numbers. bend_cents: optional array (cents over time) for detuning."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    phase_t = t if bend_cents is None else np.cumsum(2.0 ** (bend_cents[:n] / 1200.0)) / SR
    out = np.zeros((n, 2))
    g = 0.22
    for m in notes:
        f = mtof(m)
        for ch, dets in enumerate(((-3.0,), (3.0,))):
            for d in dets:
                fe = f * 2.0 ** (d / 1200.0)
                pm = 0.5 * np.sin(TWO_PI * rng.uniform(0.18, 0.5) * t + rng.uniform(0, TWO_PI))
                ph = TWO_PI * fe * phase_t + pm
                v = np.sin(ph) + 0.10 * np.sin(2 * ph)
                am = 1.0 + 0.18 * np.sin(TWO_PI * rng.uniform(0.1, 0.35) * t + rng.uniform(0, TWO_PI))
                out[:, ch] += g * v * am
        for octv, amp in ((2.0, 1.0), (4.0, 0.5)):
            pulse = (0.5 * (1.0 + np.sin(TWO_PI * rng.uniform(0.2, 0.8) * t + rng.uniform(0, TWO_PI)))) ** 2
            s = np.sin(TWO_PI * f * octv * phase_t + rng.uniform(0, TWO_PI)) * pulse * shimmer * amp * 0.22
            gl, gr = pan_gains(rng.uniform(-0.8, 0.8))
            out[:, 0] += s * gl
            out[:, 1] += s * gr
    env = smoothstep(t / attack) * smoothstep((dur - t) / release)
    return out * env[:, None] * vel


def synth_pluck(freq, vel=0.35, pan=0.0, decay=5.5, bright=1.0, dur=None):
    """Glassy harp/bell pluck: three harmonics, each decaying faster than the last."""
    if dur is None:
        dur = 6.0 / decay
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for ratio, amp, dm in ((1, 1.0, 1.0), (2, 0.35 * bright, 1.8), (3, 0.12 * bright, 2.8)):
        for det in (1 - 0.0006, 1 + 0.0006):
            s += 0.5 * amp * np.sin(TWO_PI * freq * ratio * det * t) * np.exp(-t * decay * dm)
    s *= (1.0 - np.exp(-t / 0.003)) * smoothstep((dur - t) / 0.03) * vel
    gl, gr = pan_gains(pan)
    return np.column_stack((s * gl, s * gr))


def make_bend(dur, nudge, hold, back, cents):
    """Detune curve: 0 -> cents over `nudge`, hold, then back to 0 over `back`."""
    t = np.arange(int(dur * SR)) / SR
    return cents * (smoothstep(t / nudge) - smoothstep((t - nudge - hold) / back))


# =============================================================
# 3. MIXING HELPERS
# =============================================================
rng = np.random.default_rng(SEED)
T_ = TIMING
P_ = plan(T_)
TOTAL_DURATION = P_["end"] + TAIL
TOTAL_SAMPLES = int(SR * TOTAL_DURATION)

SCENES = ["s1", "s2", "s3", "s4", "s5"]
buses = {name: np.zeros((TOTAL_SAMPLES, 2), dtype=np.float32) for name in SCENES}


def add(bus, start, data):
    s = int(start * SR)
    e = min(s + len(data), TOTAL_SAMPLES)
    if s < 0 or e <= s:
        return
    buses[bus][s:e] += data[: e - s].astype(np.float32)


def pluck(bus, start, idx, vel=0.3, pan=0.0, decay=5.5, bright=1.0, octave=0):
    add(bus, start, synth_pluck(mtof(pent(idx) + 12 * octave), vel, pan, decay, bright))


def sparkle(bus, start, idx, vel=0.07, pan=None):
    pan = rng.uniform(-0.85, 0.85) if pan is None else pan
    add(bus, start, synth_pluck(mtof(pent(idx)), vel, pan, decay=13.0, bright=1.4))


def pad(bus, start, notes, dur, vel=0.5, **kw):
    """Chord bed. Scaled by PAD_LEVEL and kept above PAD_FLOOR so it never rumbles."""
    notes = [m for m in notes if m >= PAD_FLOOR]
    if PAD_LEVEL <= 0 or not notes:
        return
    add(bus, start, synth_pad(notes, dur, vel * PAD_LEVEL, seed=int(rng.integers(1_000_000)), **kw))


# Pentatonic-safe voicings (every note belongs to D E F# A B)
G_ADD9 = [43, 55, 62, 66, 69]    # G2 G3 D4 F#4 A4
B_MIN7 = [47, 54, 57, 62, 66]    # B2 F#3 A3 D4 F#4
E_MIN7 = [40, 52, 59, 62, 66]    # E2 E3 B3 D4 F#4
A_SUS2 = [45, 52, 57, 64, 71]    # A2 E3 A3 E4 B4
D_ADD9 = [50, 57, 64, 66, 69]    # D3 A3 E4 F#4 A4
D_HIGH = [57, 64, 66, 69, 74, 78] # A3 E4 F#4 A4 D5 F#5 (the same notes as the chord: a copy to detune)

print(f"Synthesizing the sunflower soundtrack, {TOTAL_DURATION:.1f} s ...")
for name, key in (("1: hexagon", "s1"), ("2: comparison", "s2"), ("3: angle hops", "s3"),
                  ("4: benchmark", "s4"), ("5: neighbours", "s5"), ("5b: endless growth", "fin_grow_at")):
    print(f"[CUE {P_[key]:6.2f}s] scene {name}")

# =============================================================
# 4. SCENE 1 - the hexagon grows
# =============================================================
s1 = "s1"
pad(s1, P_["s1"], D_ADD9, P_["s2"] - P_["s1"] + 2.0, vel=0.5, attack=1.0, release=2.0)

N_HEX = 3 * HEX_K * (HEX_K + 1) + 1
g1 = P_["hex_grow_at"]
for ring in range(HEX_K + 1):
    first_seed = 0 if ring == 0 else 3 * ring * (ring - 1) + 1
    at = g1 + T_["hex_grow"] * first_seed / N_HEX
    pluck(s1, at, 5 + ring, vel=0.30, pan=-0.25, decay=3.2)          # one bell per ring
for i in range(0, N_HEX, 3):                                           # rain of sparkles
    sparkle(s1, g1 + T_["hex_grow"] * i / N_HEX, 15 + int(rng.integers(0, 5)),
            vel=rng.uniform(0.04, 0.08))
done = g1 + T_["hex_grow"]
for k, idx in enumerate((5, 7, 9, 11)):                                # the full hexagon: a question mark
    pluck(s1, done + 0.12 * k, idx, vel=0.16, pan=-0.1 + 0.1 * k, decay=3.5)

# =============================================================
# 5. SCENE 2 - hexagon (left) vs sunflower (right)
# =============================================================
s2 = "s2"
pad(s2, P_["s2"], G_ADD9, P_["freeze_at"] - P_["s2"] + 0.6, vel=0.5, attack=0.8, release=1.2)

r0 = P_["rewind_at"]
for k in range(15):                                                    # rewind: harp falls
    pluck(s2, r0 + T_["rewind"] * k / 15, 19 - k, vel=0.11, pan=-0.35, decay=9.0)

g0 = P_["cmp_grow_at"]
for n in range(0, FREEZE_N, 2):                                        # sunflower: even flow
    u = n / FREEZE_N
    pluck(s2, g0 + T_["cmp_grow"] * u, 5 + int(12 * u), vel=0.14 + 0.07 * u,
          pan=0.3 + rng.uniform(-0.1, 0.1), decay=6.5)
for r, first_seed in enumerate((0, 1, 7, 19, 37, 61, 91)):             # hexagon: stepwise bells
    pluck(s2, g0 + T_["cmp_grow"] * first_seed / FREEZE_N, 5 + 2 * r, vel=0.30,
          pan=-0.35, decay=3.2)

fz = P_["freeze_at"]                                                   # frozen at n = 105
pad(s2, fz, D_ADD9, T_["cmp_freeze"] + 2.2, vel=0.6, attack=0.5, release=1.8)
pluck(s2, fz, 15, vel=0.30, pan=0.3, decay=3.0)
pluck(s2, fz + 0.05, 10, vel=0.22, pan=-0.3, decay=3.0)
for k in range(8):
    sparkle(s2, fz + 0.4 + 0.35 * k, 15 + int(rng.integers(0, 5)), vel=0.05)

# =============================================================
# 6. SCENE 3 - hops over seeds 1, 2, 3, 4
# =============================================================
s3 = "s3"
pad(s3, P_["s3"], B_MIN7, P_["hop_at"][2] - P_["s3"] + 1.2, vel=0.5, attack=0.6, release=1.4)
pad(s3, P_["hop_at"][2], G_ADD9, P_["s4"] - P_["hop_at"][2] + 2.0, vel=0.5, attack=0.8, release=2.0)

for i in range(34):                                                    # seeds appear
    sparkle(s3, P_["seeds_at"] + T_["seeds_in"] * i / 34, 8 + int(10 * i / 34),
            vel=0.09, pan=rng.uniform(-0.6, 0.6))

for k, at in enumerate(P_["hop_at"]):                                  # each hop: same two steps up
    pluck(s3, at + 0.1 * T_["hop"], 5 + 2 * k, vel=0.42, pan=-0.3 + 0.2 * k, decay=3.0)
for at in P_["arc_at"]:                                                # each arc: the SAME chime
    pluck(s3, at + 0.1 * T_["hop"], 13, vel=0.30, pan=0.0, decay=3.5)

# =============================================================
# 7. SCENE 4 - benchmark: the fill curve played as a melody
# =============================================================
s4 = "s4"
sweep, x0, peak = T_["sweep"], P_["sweep_at"], P_["peak_at"]

ang = np.arange(0.0, 180.0001, 0.25)
fill = np.array([bench_fill(np.radians(a)) for a in ang])
FILL_MAX = fill.max()
BIN = 1.25                                    # degrees per note (peak-hold, so narrow peaks are heard)

pad(s4, P_["s4"], G_ADD9, (x0 - P_["s4"]) + 0.22 * sweep + 1.4, vel=0.34, attack=0.8, release=1.4)
chords = [(0.22, B_MIN7), (0.42, E_MIN7), (0.60, A_SUS2)]
for k, (frac, notes) in enumerate(chords):
    nxt = chords[k + 1][0] * sweep if k + 1 < len(chords) else peak - x0
    pad(s4, x0 + frac * sweep, notes, nxt - frac * sweep + 1.4, vel=0.34, attack=0.9, release=1.4)

for k in range(int(round(180 / BIN))):                                 # the melody
    a0 = k * BIN
    f = fill[(ang >= a0 - 1e-9) & (ang < a0 + BIN - 1e-9)].max()
    ratio = f / FILL_MAX
    idx = 5 + int(round(10 * ratio ** 1.5))                            # D4 ... D6
    pluck(s4, x0 + sweep * a0 / 180.0, idx, vel=0.12 + 0.16 * ratio,
          pan=-0.6 + 1.2 * a0 / 180.0, decay=6.0)

M = 40                                                                 # build-up: accelerating sparkles
for j in range(M):
    u = j / M
    at = x0 + (peak - x0) * (1.0 - (1.0 - u) ** 1.6)
    sparkle(s4, at, 12 + int(7 * u), vel=0.05 + 0.07 * u)

res_end = P_["s5"]                                                     # 137.5: resolution
pad(s4, peak, D_ADD9, res_end - peak + 1.4, vel=0.95, attack=0.25, release=2.0)
pluck(s4, peak, 15, vel=0.60, pan=0.0, decay=2.4)                      # D6
pluck(s4, peak, 10, vel=0.40, pan=-0.2, decay=2.4)                     # D5
pluck(s4, peak, 13, vel=0.36, pan=0.2, decay=2.4)                      # A5
for k in range(12):
    sparkle(s4, peak + 0.06 * k, 19 - k // 2, vel=0.12)

rt = P_["return_at"]                                                   # back to the peak
for k, idx in enumerate((10, 13)):
    pluck(s4, rt - 0.45 + 0.2 * k, idx, vel=0.20, pan=-0.2 + 0.4 * k, decay=3.5)
pluck(s4, rt, 15, vel=0.40, pan=0.0, decay=2.4)
pluck(s4, rt, 10, vel=0.26, pan=-0.2, decay=2.4)

one = T_["nudge"] + T_["nudge_hold"] + T_["nudge_back"]
for sign, at in zip((-1.0, 1.0), P_["nudge_at"]):                      # 137.3 / 137.6: out of tune and back
    bdur = one + 0.8
    bend = make_bend(bdur, T_["nudge"], T_["nudge_hold"], T_["nudge_back"], 50.0 * sign)
    # two clean sine layers (same chord), one of them detuned: audible beating, independent of PAD_LEVEL
    add(s4, at, synth_pad(D_HIGH, bdur, 0.16, attack=0.15, release=0.5, shimmer=0.0, seed=11))
    add(s4, at, synth_pad(D_HIGH, bdur, 0.16, attack=0.15, release=0.5, bend_cents=bend, shimmer=0.0, seed=12))
    pluck(s4, at + one, 15, vel=0.36, pan=0.0, decay=2.6)              # resolved again

# =============================================================
# 8. SCENE 5 - neighbour colours, then endless growth
# =============================================================
s5 = "s5"
pad(s5, P_["s5"], E_MIN7, P_["fin_swap_at"] - P_["s5"] + 1.2, vel=0.45, attack=0.7, release=1.2)
pad(s5, P_["fin_swap_at"], G_ADD9, P_["fin_revert_at"] - P_["fin_swap_at"] + 1.0, vel=0.5, attack=0.6, release=1.2)
pad(s5, P_["fin_grow_at"], D_ADD9, T_["fin_grow"] + TAIL, vel=0.8, attack=2.5, release=TAIL + 0.5)

for i in range(30):                                                    # the gold sunflower fades in
    sparkle(s5, P_["fin_base_at"] + T_["fin_base"] * i / 30, 14 + int(5 * i / 30), vel=0.06)
for k in range(20 if COLOR_WASH else 0):                               # colour wash: harp glissando
    pluck(s5, P_["fin_swap_at"] + 0.9 * T_["fin_swap"] * k / 20, 5 + int(14 * k / 19),
          vel=0.15, pan=-0.5 + 1.0 * k / 19, decay=5.0)
# the legend appears in silence: no chimes on text

for k in range(8):                                                     # back to gold: a short rising harp
    pluck(s5, P_["fin_revert_at"] + 0.8 * T_["fin_revert"] * k / 8, 5 + 2 * k,
          vel=0.10, pan=-0.4 + 0.8 * k / 7, decay=5.0)

# endless growth: the cascade follows the picture (u = progress of the growth, 0..1)
Tg, g_at = T_["fin_grow"], P_["fin_grow_at"]


def fade_gain(u):
    return 1.0 - float(smoothstep((u - FIN_U_FADE) / (1.0 - FIN_U_FADE)))


M = 170
for j in range(M):
    x = j / M
    u = 1.0 - (1.0 - x) ** 1.5                      # notes bunch up as the seeds multiply
    step = j % 13                                   # climbing run of 13 notes (a Fibonacci number)
    swell = np.sin(np.pi * (step + 0.5) / 13) ** 0.7  # every run swells and fades: endless-ascent feel
    vel = (0.10 + 0.20 * u) * (0.25 + 0.75 * swell) * fade_gain(u)
    pan = 0.75 * np.sin(TWO_PI * j / 21)            # panning cycles every 21 notes
    pluck(s5, g_at + Tg * u, 5 + step, vel=vel, pan=pan, decay=5.0)
for j in range(90):                                                    # rising glitter
    x = j / 90
    u = 1.0 - (1.0 - x) ** 1.3
    sparkle(s5, g_at + Tg * u, 14 + int(5 * u), vel=0.06 * fade_gain(u))

# =============================================================
# 9. SPACE AND MASTERING
# =============================================================


def make_ir(seconds=2.8, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    noise = r.standard_normal(n)
    dark = lfilter([0.12], [1.0, -0.88], noise)                       # high frequencies die faster
    mix = np.clip(t / (seconds * 0.6), 0.0, 1.0)
    ir = ((1 - mix) * noise + mix * dark * 2.5) * np.exp(-t * 2.6)
    ir[: int(0.02 * SR)] = 0.0                                         # 20 ms pre-delay
    return ir / np.sqrt(np.sum(ir ** 2))


IR_L, IR_R = make_ir(seed=3), make_ir(seed=4)
delay = int(0.27 * SR)

master = np.zeros((TOTAL_SAMPLES, 2))
for name in SCENES:
    x = buses[name].astype(np.float64)
    x[delay:, 0] += x[:-delay, 1] * 0.25                               # ping-pong echo
    x[delay:, 1] += x[:-delay, 0] * 0.20
    wet = np.column_stack((
        fftconvolve(x[:, 0], IR_L)[:TOTAL_SAMPLES],
        fftconvolve(x[:, 1], IR_R)[:TOTAL_SAMPLES],
    ))
    x = x + REVERB_WET * wet
    buses[name] = x
    master += x

def finish(a):
    a = np.tanh(a * 1.1)                                               # soft ceiling
    fade_in = int(0.02 * SR)
    a[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    fade_out = min(int(TAIL * 0.9 * SR), len(a))
    a[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None] ** 2
    return a


master = finish(master)
peak_val = np.max(np.abs(master))
scale = LEVEL / peak_val if peak_val > 0 else 1.0
master *= scale

wavfile.write(str(OUTPUT_FILE), SR, (master * 32767).astype(np.int16))
print(f"Done! Saved to:\n{OUTPUT_FILE}")

if EXPORT_STEMS:
    for name in SCENES:
        stem = finish(buses[name].copy()) * scale
        path = OUTPUT_DIR / f"{SCRIPT_NAME}_{name}.wav"
        wavfile.write(str(path), SR, (np.clip(stem, -1, 1) * 32767).astype(np.int16))
        print(f"  stem: {path}")