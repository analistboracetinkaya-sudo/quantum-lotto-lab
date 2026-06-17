from __future__ import annotations

import itertools
import math
from collections import Counter
from statistics import NormalDist

import numpy as np

from .math_model import number_scores, pair_centrality, robust_z
from .models import Draw, LotterySpec, PoolSpec


def values_for(draw: Draw, field: str) -> tuple[int, ...]:
    return draw.main if field == "main" else draw.bonus


def normal_two_sided_p(z: float) -> float:
    return max(0.0, min(1.0, 2.0 * (1.0 - NormalDist().cdf(abs(z)))))


def audit_pool_randomness(draws: list[Draw], pool: PoolSpec, field: str = "main") -> dict:
    if not draws:
        raise ValueError("draws cannot be empty")
    values = pool.values
    total_slots = len(draws) * pool.pick
    expected = total_slots / len(values)
    counts = Counter(num for draw in draws for num in values_for(draw, field) if pool.minimum <= num <= pool.maximum)
    observed = np.array([counts[value] for value in values], dtype=float)
    chi_square = float(np.sum((observed - expected) ** 2 / max(expected, 1e-12)))
    z_scores = (observed - expected) / math.sqrt(max(expected, 1e-12))
    top_positive = sorted(
        ({"number": value, "count": int(counts[value]), "z": float(z_scores[idx])} for idx, value in enumerate(values)),
        key=lambda row: row["z"],
        reverse=True,
    )[:10]
    top_negative = sorted(
        ({"number": value, "count": int(counts[value]), "z": float(z_scores[idx])} for idx, value in enumerate(values)),
        key=lambda row: row["z"],
    )[:10]

    gaps: dict[int, list[int]] = {value: [] for value in values}
    last_seen: dict[int, int] = {}
    for idx, draw in enumerate(draws):
        present = set(values_for(draw, field))
        for value in values:
            if value in present:
                if value in last_seen:
                    gaps[value].append(idx - last_seen[value])
                last_seen[value] = idx
    gap_rows = []
    for value in values:
        row = gaps[value]
        gap_rows.append(
            {
                "number": value,
                "mean_gap": float(np.mean(row)) if row else None,
                "max_gap": int(max(row)) if row else None,
                "current_gap": len(draws) - 1 - last_seen[value] if value in last_seen else len(draws),
            }
        )
    most_overdue = sorted(gap_rows, key=lambda row: row["current_gap"], reverse=True)[:10]

    pair_counts = Counter()
    for draw in draws:
        nums = sorted(num for num in values_for(draw, field) if pool.minimum <= num <= pool.maximum)
        for pair in itertools.combinations(nums, 2):
            pair_counts[pair] += 1
    expected_pair = len(draws) * (pool.pick / len(values)) * ((pool.pick - 1) / max(1, len(values) - 1))
    pair_rows = [
        {"pair": list(pair), "count": count, "lift": float(count / max(expected_pair, 1e-12))}
        for pair, count in pair_counts.items()
    ]
    pair_rows.sort(key=lambda row: row["lift"], reverse=True)

    months = Counter(draw.date.month for draw in draws)
    weekdays = Counter(draw.date.weekday() for draw in draws)
    month_skew = max(months.values()) / max(1, min(months.values())) if months else 1.0
    weekday_skew = max(weekdays.values()) / max(1, min(weekdays.values())) if weekdays else 1.0

    max_abs_z = float(np.max(np.abs(z_scores))) if len(z_scores) else 0.0
    max_pair_lift = float(pair_rows[0]["lift"]) if pair_rows else 0.0
    signal_score = 0
    if max_abs_z >= 2.0:
        signal_score += 1
    if max_abs_z >= 3.0:
        signal_score += 1
    if max_pair_lift >= 1.5:
        signal_score += 1
    if month_skew >= 1.8 or weekday_skew >= 1.8:
        signal_score += 1
    strength = ("none", "weak", "moderate", "strong", "strong")[min(signal_score, 4)]
    plain = (
        "No obvious deviation from a simple random baseline was detected."
        if strength == "none"
        else "The history shows measurable deviations from a simple random baseline. This is a signal to backtest, not proof of predictability."
    )

    return {
        "draws": len(draws),
        "pool": {"min": pool.minimum, "max": pool.maximum, "pick": pool.pick},
        "frequency": {
            "expected_per_number": expected,
            "chi_square": chi_square,
            "max_abs_z": max_abs_z,
            "top_positive": top_positive,
            "top_negative": top_negative,
            "approx_strongest_p": normal_two_sided_p(max_abs_z),
        },
        "gap": {"most_overdue": most_overdue},
        "pair_lift": {"expected_pair_count": expected_pair, "max_lift": max_pair_lift, "top_pairs": pair_rows[:10]},
        "seasonality": {"month_skew": float(month_skew), "weekday_skew": float(weekday_skew)},
        "verdict": {"signal_strength": strength, "plain": plain},
    }


def score_vector(draws: list[Draw], spec: LotterySpec, field: str, model: str) -> np.ndarray:
    pool = spec.main if field == "main" else spec.bonus
    if pool is None:
        return np.array([])
    values = pool.values
    if model == "uniform":
        return np.zeros(len(values), dtype=float)
    mat_counts = Counter(num for draw in draws for num in values_for(draw, field))
    frequency = robust_z(np.array([mat_counts[value] for value in values], dtype=float))
    recent = draws[-min(52, len(draws)) :]
    recent_counts = Counter(num for draw in recent for num in values_for(draw, field))
    recent_frequency = robust_z(np.array([recent_counts[value] for value in values], dtype=float))
    last_seen = {}
    for idx, draw in enumerate(draws):
        for num in values_for(draw, field):
            last_seen[num] = idx
    gap = robust_z(np.array([len(draws) - 1 - last_seen.get(value, -1) for value in values], dtype=float))
    pair = pair_centrality(draws, pool, field)
    if model == "frequency_all":
        return frequency
    if model == "recent_frequency":
        return recent_frequency
    if model == "gap_overdue":
        return gap
    if model == "pair_centrality":
        return pair
    if model == "ensemble":
        return robust_z(0.30 * frequency + 0.25 * recent_frequency + 0.20 * gap + 0.25 * pair)
    if model == "legacy_weighted":
        return number_scores(draws, pool, field)
    raise ValueError(f"unknown model {model}")


def pick_top(scores: np.ndarray, pool: PoolSpec) -> set[int]:
    ranked = np.argsort(scores)[::-1]
    return set(pool.values[idx] for idx in ranked[: pool.pick])


def summarize_hits(hits: list[int], pick: int, uniform_hits: list[int] | None = None) -> dict:
    arr = np.array(hits, dtype=float)
    if len(arr) == 0:
        return {}
    distribution = {str(k): int(np.sum(arr == k)) for k in range(pick + 1)}
    mean_hits = float(arr.mean())
    uniform_mean = float(np.mean(uniform_hits)) if uniform_hits else mean_hits
    return {
        "mean_hits": mean_hits,
        "any_1_plus": float(np.mean(arr >= 1)),
        "any_2_plus": float(np.mean(arr >= 2)),
        "any_3_plus": float(np.mean(arr >= 3)),
        "hit_distribution": distribution,
        "lift_vs_uniform": float(mean_hits - uniform_mean),
    }


def walk_forward_models(
    draws: list[Draw],
    spec: LotterySpec,
    field: str = "main",
    train_min: int = 80,
    top_k: int | None = None,
) -> dict:
    pool = spec.main if field == "main" else spec.bonus
    if pool is None:
        return {}
    if top_k is None:
        top_k = pool.pick
    if len(draws) <= train_min:
        train_min = max(5, min(len(draws) - 1, train_min))
    models = ["uniform", "frequency_all", "recent_frequency", "gap_overdue", "pair_centrality", "ensemble", "legacy_weighted"]
    hits_by_model: dict[str, list[int]] = {model: [] for model in models}

    for idx in range(train_min, len(draws)):
        train = draws[:idx]
        actual = set(values_for(draws[idx], field))
        for model in models:
            scores = score_vector(train, spec, field, model)
            chosen = pick_top(scores, pool)
            hits_by_model[model].append(len(chosen & actual))

    uniform_hits = hits_by_model["uniform"]
    summaries = {model: summarize_hits(hits, top_k, uniform_hits) for model, hits in hits_by_model.items()}
    best_model = max(summaries, key=lambda model: (summaries[model]["mean_hits"], summaries[model]["any_3_plus"]))
    best = summaries[best_model]
    uniform = summaries["uniform"]
    useful = best["mean_hits"] > uniform["mean_hits"] and best["any_2_plus"] >= uniform["any_2_plus"]
    return {
        "field": field,
        "train_min": train_min,
        "test_draws": max(0, len(draws) - train_min),
        "best_model": best_model,
        "models": summaries,
        "verdict": {
            "useful_signal": bool(useful),
            "plain": (
                f"Best model '{best_model}' beat the uniform baseline in walk-forward mean hits."
                if useful
                else "No model beat the uniform baseline strongly enough to claim a reusable edge."
            ),
        },
    }

