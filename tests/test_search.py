from __future__ import annotations

from datetime import date

import numpy as np

from quantum_lotto_lab.math_model import optimize_tickets_with_metadata
from quantum_lotto_lab.models import Draw, LotterySpec, PoolSpec
from quantum_lotto_lab.search import stream_top_combinations


def test_stream_top_combinations_evaluates_exact_space():
    values = list(range(1, 11))
    scores = np.asarray(values, dtype=float)
    result = stream_top_combinations(values, pick=3, scores=scores, top_k=5)
    assert result["total_combinations"] == 120
    assert result["evaluated_combinations"] == 120
    assert result["top"][0]["combo"] == [8, 9, 10]


def test_optimizer_exact_mode_reports_evaluated_space():
    spec = LotterySpec("mini", "Mini", "test", PoolSpec("numbers", 1, 10, 3))
    draws = [
        Draw(draw_date, tuple(sorted(combo)))
        for draw_date, combo in [
            (date(2024, 1, 1), (1, 2, 3)),
            (date(2024, 1, 8), (4, 5, 6)),
            (date(2024, 1, 15), (7, 8, 9)),
            (date(2024, 1, 22), (1, 5, 9)),
            (date(2024, 1, 29), (2, 6, 10)),
        ]
    ]
    tickets, meta = optimize_tickets_with_metadata(
        spec,
        draws,
        columns=2,
        seed=5,
        candidate_mode="exact",
        exact_top_k=20,
        max_exact_combinations=500,
    )
    assert len(tickets) == 2
    assert meta["exact_used"] is True
    assert meta["total_combinations"] == 120
    assert meta["evaluated_combinations"] == 120
