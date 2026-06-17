from __future__ import annotations

from datetime import date, timedelta

from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.models import Draw
from quantum_lotto_lab.validation import nested_ticket_backtest


def make_draws() -> list[Draw]:
    start = date(2020, 1, 1)
    draws = []
    for idx in range(64):
        hot = 1 if idx % 3 else 2
        draws.append(Draw(start + timedelta(days=7 * idx), tuple(sorted([hot, 3, 4, 5, 6, 7 + idx % 20]))))
    return draws


def test_nested_ticket_backtest_uses_unseen_draws():
    spec = get_lottery("super-loto-tr")
    report = nested_ticket_backtest(
        spec,
        make_draws(),
        columns=8,
        train_min=40,
        seed=123,
        candidate_pool=120,
        max_test_draws=8,
    )
    assert report["test_draws"] == 8
    assert report["leakage_guard"] == "tickets generated only from draws before the tested draw"
    assert "any_2_plus" in report
    assert "best_main_distribution" in report
