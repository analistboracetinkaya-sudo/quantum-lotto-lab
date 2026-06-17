from __future__ import annotations

from datetime import date, timedelta

from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.models import Draw, PoolSpec
from quantum_lotto_lab.randomness import audit_pool_randomness, walk_forward_models


def biased_draws() -> list[Draw]:
    start = date(2024, 1, 1)
    draws = []
    for idx in range(80):
        hot = 1 if idx % 2 == 0 else 2
        tail = 8 + (idx % 3)
        draws.append(Draw(start + timedelta(days=idx * 7), tuple(sorted([hot, 3, 4, 5, 6, tail]))))
    return draws


def test_audit_detects_obvious_frequency_bias():
    report = audit_pool_randomness(biased_draws(), PoolSpec("numbers", 1, 10, 6), "main")
    assert report["draws"] == 80
    assert report["frequency"]["chi_square"] > 0
    assert report["frequency"]["max_abs_z"] > 2
    assert report["pair_lift"]["max_lift"] > 1
    assert report["verdict"]["signal_strength"] in {"weak", "moderate", "strong"}


def test_walk_forward_models_reports_model_lift():
    spec = get_lottery("super-loto-tr")
    draws = biased_draws()
    report = walk_forward_models(draws, spec, field="main", train_min=30)
    assert report["test_draws"] == 50
    assert "uniform" in report["models"]
    assert len(report["models"]) >= 6
    assert report["best_model"] in report["models"]
    assert "lift_vs_uniform" in report["models"][report["best_model"]]

