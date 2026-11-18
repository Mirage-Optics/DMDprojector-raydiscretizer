"""pixels.intensity_noise: static per-pixel factor, independent of ray seed / rays_per_pixel; off = unchanged."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import projectionImageGen as pig  # noqa: E402

TOML = """
[output]
output_folder = "{out}"
output_filename = "t.ry"
rays_only = true
seed = {seed}
batch_count = 1
normalize_batch_energy_to_mask_power = false
[projection]
width = 40.0
height = 40.0
axis = "y"
direction = 1
focus_plane_position = 0
source_plane_position = -100
[emission]
origin_type = "pixelated"
base_intensity = 10.0
[focus]
mode = "collimated"
[mask]
type = "rectangle"
width = 30.0
height = 30.0
[pixels]
rays_per_pixel = {rpp}
pitch = [1.0, 1.0]
size = [1.0, 1.0]
activation_mode = "center"
intensity_mode = "flat"
{extra}
"""


def per_pixel(tmp, seed, rpp, extra=""):
    p = tmp / f"c_{seed}_{rpp}_{len(extra)}.toml"
    p.write_text(TOML.format(out=tmp, seed=seed, rpp=rpp, extra=extra))
    cfg = pig.load_config(p)
    mask = pig._build_mask(cfg)
    _, _, e, _ = pig._generate_pixelated_rays(cfg, mask, np.random.default_rng(seed))
    return e.reshape(-1, rpp).sum(axis=1)                 # flat mode: exact per-pixel power


def test_noise(tmp_path):
    base = per_pixel(tmp_path, 1, 4)
    assert np.allclose(base, base[0])                      # flat, fully lit: uniform without noise
    noisy = "intensity_noise = 0.02\nintensity_noise_seed = 7"
    a, b, c = per_pixel(tmp_path, 1, 4, noisy), per_pixel(tmp_path, 2, 4, noisy), per_pixel(tmp_path, 3, 16, noisy)
    assert np.allclose(a, b) and np.allclose(a, c)         # static: same per pixel for any ray seed / rpp
    f = a / base
    assert 0.015 < f.std() < 0.025 and abs(f.mean() - 1) < 0.01
    d = per_pixel(tmp_path, 1, 4, "intensity_noise = 0.02\nintensity_noise_seed = 8")
    assert not np.allclose(a, d)                           # the noise seed changes the pattern
