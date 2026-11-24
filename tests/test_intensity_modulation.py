"""pixels.intensity_modulation: static cosine along world v; right wavelength/amplitude; off = unchanged."""
import numpy as np

from test_intensity_noise import per_pixel


def test_modulation(tmp_path):
    base = per_pixel(tmp_path, 1, 4)
    mod = "intensity_modulation = 0.05\nintensity_modulation_wavelength = 6.0"
    a, b = per_pixel(tmp_path, 1, 4, mod), per_pixel(tmp_path, 2, 16, mod)
    assert np.allclose(a, b)                                   # static across ray seed / rays_per_pixel
    f = (a / base).reshape(30, 30)                             # pixel order: u outer, v inner
    assert np.allclose(f, f[0])                                # depends on v only
    v = np.arange(30) - 14.5                                   # pixel centres, pitch 1, mask 30 wide centred at 0
    assert np.allclose(f[0], 1 + 0.05 * np.cos(2 * np.pi * v / 6.0))
    ph = per_pixel(tmp_path, 1, 4, mod + "\nintensity_modulation_phase_deg = 90")
    assert np.allclose((ph / base).reshape(30, 30)[0], 1 - 0.05 * np.sin(2 * np.pi * v / 6.0))
