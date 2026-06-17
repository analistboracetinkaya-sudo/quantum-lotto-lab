from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from quantum_lotto_lab.calibration import calibrated_randomness_fingerprint
from quantum_lotto_lab.models import Draw, PoolSpec


def make_uniform_draws(seed: int, draws_count: int = 240) -> list[Draw]:
    rng = np.random.default_rng(seed)
    pool = list(range(1, 61))
    start = date(2020, 1, 1)
    draws: list[Draw] = []
    for idx in range(draws_count):
        nums = tuple(sorted(int(x) for x in rng.choice(pool, size=6, replace=False)))
        draws.append(Draw(start + timedelta(days=7 * idx), nums))
    return draws


def test_uniform_data_is_not_classified_as_pair_or_triple_clustered():
    report = calibrated_randomness_fingerprint(
        make_uniform_draws(seed=11),
        PoolSpec("numbers", 1, 60, 6),
        field="main",
        null_trials=120,
        seed=99,
    )
    dominant = set(report["randomness_type"]["dominant_types"])
    assert "pair_clustering" not in dominant
    assert "triple_clustering" not in dominant
    assert report["calibration"]["pair_max_lift"]["empirical_p"] >= 0.05
    assert report["calibration"]["triple_max_lift"]["empirical_p"] >= 0.05


def test_biased_data_is_classified_after_calibration():
    start = date(2020, 1, 1)
    draws = []
    for idx in range(240):
        hot = 1 if idx % 2 == 0 else 2
        draws.append(Draw(start + timedelta(days=7 * idx), tuple(sorted([hot, 3, 4, 5, 6, 7]))))
    report = calibrated_randomness_fingerprint(
        draws,
        PoolSpec("numbers", 1, 60, 6),
        field="main",
        null_trials=120,
        seed=101,
    )
    dominant = set(report["randomness_type"]["dominant_types"])
    assert "frequency_bias" in dominant
    assert report["calibration"]["frequency_chi_square"]["empirical_p"] <= 0.01
