from __future__ import annotations

from datetime import date

from quantum_lotto_lab.data_quality import validate_draw_history
from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.models import Draw


def test_validate_draw_history_detects_duplicates_and_range_errors():
    spec = get_lottery("super-loto-tr")
    draws = [
        Draw(date(2025, 1, 1), (1, 2, 3, 4, 5, 6)),
        Draw(date(2025, 1, 1), (1, 2, 3, 4, 5, 61)),
    ]
    report = validate_draw_history(draws, spec)
    assert report["duplicate_dates"] == ["2025-01-01"]
    assert report["range_errors"]
    assert report["usable"] is False
