from pathlib import Path

from quantum_lotto_lab.data import parse_generic_csv
from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.math_model import hit_distribution, make_tickets


def test_generic_csv_and_ticket_generation():
    spec = get_lottery("super-loto-tr")
    draws = parse_generic_csv(Path("examples/sample_draws.csv"), spec)
    assert len(draws) == 30
    tickets = make_tickets(spec, draws, columns=5, seed=7)
    assert len(tickets) == 5
    assert all(len(ticket.main) == 6 for ticket in tickets)
    assert all(all(1 <= num <= 60 for num in ticket.main) for ticket in tickets)


def test_hit_distribution():
    dist = hit_distribution(60, 6, 30)
    assert 0 < dist["jackpot_approx"] < 1
    assert dist["any_2_plus"] > dist["any_3_plus"]
