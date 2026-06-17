from __future__ import annotations

import itertools
import math
from collections import Counter

import numpy as np

from .models import Draw, LotterySpec, PoolSpec, Ticket


def robust_z(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    std = float(values.std(ddof=0))
    if std < 1e-12:
        return np.zeros_like(values)
    return np.clip((values - float(values.mean())) / std, -3.0, 3.0)


def draw_matrix(draws: list[Draw], pool: PoolSpec, field: str) -> np.ndarray:
    values = pool.values
    index = {value: idx for idx, value in enumerate(values)}
    mat = np.zeros((len(values), len(draws)), dtype=np.int8)
    for col, draw in enumerate(draws):
        nums = draw.main if field == "main" else draw.bonus
        for num in nums:
            if num in index:
                mat[index[num], col] = 1
    return mat


def pair_centrality(draws: list[Draw], pool: PoolSpec, field: str) -> np.ndarray:
    counts = Counter()
    totals = Counter()
    for draw in draws:
        nums = draw.main if field == "main" else draw.bonus
        nums = tuple(num for num in nums if pool.minimum <= num <= pool.maximum)
        for num in nums:
            totals[num] += 1
        for pair in itertools.combinations(sorted(nums), 2):
            counts[pair] += 1
    score = []
    for value in pool.values:
        related = sum(count for pair, count in counts.items() if value in pair)
        score.append(related + 0.3 * totals[value])
    return robust_z(np.array(score, dtype=float))


def number_scores(draws: list[Draw], pool: PoolSpec, field: str) -> np.ndarray:
    mat = draw_matrix(draws, pool, field)
    if mat.shape[1] == 0:
        return np.zeros(len(pool.values), dtype=float)
    total_freq = robust_z(mat.mean(axis=1))
    recent_window = mat[:, -min(52, mat.shape[1]) :]
    recent_freq = robust_z(recent_window.mean(axis=1))
    weights = np.exp(np.linspace(-3.0, 0.0, mat.shape[1]))
    ewma = robust_z((mat * weights).sum(axis=1) / weights.sum())
    gaps = []
    for row in mat:
        hit_idx = np.where(row > 0)[0]
        gaps.append(mat.shape[1] if len(hit_idx) == 0 else mat.shape[1] - 1 - int(hit_idx[-1]))
    gap_score = robust_z(np.array(gaps, dtype=float))
    pair_score = pair_centrality(draws, pool, field)
    return robust_z(0.28 * total_freq + 0.26 * recent_freq + 0.18 * ewma + 0.14 * gap_score + 0.14 * pair_score)


def hit_distribution(pool_size: int, pick: int, columns: int) -> dict:
    total = math.comb(pool_size, pick)
    single = {}
    for k in range(pick + 1):
        if pool_size - pick < pick - k:
            single[k] = 0.0
        else:
            single[k] = math.comb(pick, k) * math.comb(pool_size - pick, pick - k) / total
    any_2 = 1.0 - sum(single[k] for k in range(min(2, pick + 1))) ** columns
    any_3 = 1.0 - sum(single[k] for k in range(min(3, pick + 1))) ** columns
    jackpot = columns / total
    return {
        "single": single,
        "any_2_plus": any_2,
        "any_3_plus": any_3,
        "jackpot_approx": min(1.0, jackpot),
        "jackpot_one_in": round(1.0 / jackpot) if jackpot > 0 else None,
    }


def sample_unique(rng: np.random.Generator, values: list[int], probs: np.ndarray, pick: int) -> tuple[int, ...]:
    probs = np.asarray(probs, dtype=float)
    probs = probs / probs.sum()
    return tuple(sorted(int(x) for x in rng.choice(values, size=pick, replace=False, p=probs)))


def make_tickets(
    spec: LotterySpec,
    draws: list[Draw],
    columns: int,
    seed_bits: list[int] | None = None,
    seed: int = 0,
) -> list[Ticket]:
    main_scores = number_scores(draws, spec.main, "main")
    main_probs = np.exp(main_scores / 1.4)
    main_probs = main_probs / main_probs.sum()

    bonus_probs = None
    if spec.bonus:
        bonus_scores = number_scores(draws, spec.bonus, "bonus")
        bonus_probs = np.exp(bonus_scores / 1.4)
        bonus_probs = bonus_probs / bonus_probs.sum()

    rng_seed = int(seed)
    if seed_bits:
        digest = 0
        for bit in seed_bits[:512]:
            digest = ((digest << 1) ^ int(bit)) & ((1 << 63) - 1)
        rng_seed ^= digest
    rng = np.random.default_rng(rng_seed)

    tickets: list[Ticket] = []
    seen: set[tuple[tuple[int, ...], tuple[int, ...]]] = set()
    attempts = 0
    while len(tickets) < columns and attempts < columns * 500:
        attempts += 1
        main = sample_unique(rng, spec.main.values, main_probs, spec.main.pick)
        bonus = ()
        if spec.bonus and bonus_probs is not None:
            bonus = sample_unique(rng, spec.bonus.values, bonus_probs, spec.bonus.pick)
        key = (main, bonus)
        if key in seen:
            continue
        tickets.append(Ticket(main, bonus, "quantum_weighted" if seed_bits else "classical_weighted"))
        seen.add(key)
    return tickets


def backtest_summary(tickets: list[Ticket], draws: list[Draw]) -> dict:
    if not draws:
        return {}
    best_main = []
    best_bonus = []
    for draw in draws:
        main_hits = [len(set(ticket.main) & set(draw.main)) for ticket in tickets]
        bonus_hits = [len(set(ticket.bonus) & set(draw.bonus)) if ticket.bonus else 0 for ticket in tickets]
        best_main.append(max(main_hits))
        best_bonus.append(max(bonus_hits) if bonus_hits else 0)
    arr = np.array(best_main)
    return {
        "draws": len(draws),
        "best_main_mean": float(arr.mean()),
        "best_main_sd": float(arr.std(ddof=0)),
        "any_1_plus": float(np.mean(arr >= 1)),
        "any_2_plus": float(np.mean(arr >= 2)),
        "any_3_plus": float(np.mean(arr >= 3)),
        "best_main_distribution": {str(k): int(np.sum(arr == k)) for k in sorted(set(arr.tolist()) | {0, 1, 2, 3})},
        "best_bonus_mean": float(np.mean(best_bonus)) if best_bonus else 0.0,
    }

