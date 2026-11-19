import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import projectionImageGen as g  # noqa: E402

BASE = """
[projection]
width = {width}
height = {height}
axis = "y"
direction = 1
focus_plane_position = 0.0
source_plane_position = -100.0

[emission]
origin_type = "pixelated"
base_intensity = 2.0

[mask]
{mask}

[pixels]
rays_per_pixel = 50
pitch = [10.0, 10.0]
intensity_mode = "flat"

[output]
output_filename = "t.ry"
seed = 7
rays_only = true
"""


def _cfg(tmp_path, mask, width=200.0, height=200.0):
	p = tmp_path / "c.toml"
	p.write_text(BASE.format(mask=mask, width=width, height=height))
	return g.load_config(p)


def test_flat_energy_equals_intensity_times_area(tmp_path):
	cfg = _cfg(tmp_path, 'type = "rectangle"\nwidth = 100.0\nheight = 60.0')
	mask = g._build_mask(cfg)
	_, _, energies, _ = g._generate_pixelated_rays(cfg, mask, np.random.default_rng(0))
	assert math.isclose(energies.sum(), 2.0 * 100.0 * 60.0, rel_tol=1e-9)


def test_ry_metadata_contains_original_area_and_intensity(tmp_path):
	config_path = tmp_path / "c.toml"
	cfg = _cfg(tmp_path, 'type = "rectangle"\nwidth = 100.0\nheight = 60.0')
	g.run(config_path, cfg)

	metadata = (tmp_path / "t.ry").read_text().splitlines()
	assert "# original_area: 6.0000000000000000e+03" in metadata
	assert "# original_intensity: 2.0000000000000000e+00" in metadata


def test_gaussian_falls_to_e2_at_half_diameter():
	sigma = g._gaussian_sigma(10.0, "1/e2_diameter")
	assert math.isclose(math.exp(-((5.0 / sigma) ** 2) / 2.0), math.exp(-2.0), rel_tol=1e-6)


def test_png_folder_frames_get_different_random_streams(tmp_path):
	frames_dir = (ROOT / "examples/png2ry/frames").as_posix()
	cfg = _cfg(
		tmp_path,
		f'type = "png"\npng_folder = "{frames_dir}"\npixel_pitch = [40.0, 40.0]',
		width=1080.0,
		height=1920.0,
	)
	frames = g._collect_png_frames(cfg.mask.png_folder, 1)[:2]
	offsets = []
	for idx, frame in enumerate(frames):
		fcfg = g._config_for_png_frame(cfg, frame, idx)
		rng = np.random.default_rng(fcfg.output.seed)  # as run() does for batch 0
		_, _, _, uv = g._generate_pixelated_rays(fcfg, g._build_mask(fcfg), rng)
		offsets.append(uv[:200] % 40.0)
	assert not np.allclose(offsets[0], offsets[1])
