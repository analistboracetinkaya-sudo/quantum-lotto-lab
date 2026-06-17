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


def pairs(combo: tuple[int, ...]) -> set[tuple[int, int]]:
    return set(itertools.combinations(combo, 2))


def triples(combo: tuple[int, ...]) -> set[tuple[int, int, int]]:
    return set(itertools.combinations(combo, 3))


def ticket_history_hits(combo: tuple[int, ...], draws: list[Draw]) -> np.ndarray:
    combo_set = set(combo)
    return np.array([len(combo_set & set(draw.main)) for draw in draws], dtype=float)


def candidate_objective(combo: tuple[int, ...], scores: np.ndarray, values: list[int], draws: list[Draw]) -> float:
    index = {value: idx for idx, value in enumerate(values)}
    base = float(sum(scores[index[num]] for num in combo))
    hits = ticket_history_hits(combo, draws[-min(157, len(draws)) :])
    odd = sum(num % 2 for num in combo)
    low = sum(num <= (values[0] + values[-1]) / 2 for num in combo)
    span = max(combo) - min(combo)
    consecutive = sum(1 for a, b in zip(combo[:-1], combo[1:]) if b - a == 1)
    target_odd = len(combo) / 2
    target_low = len(combo) / 2
    target_span = (values[-1] - values[0]) * 0.72
    structure = (
        -0.18 * (odd - target_odd) ** 2
        -0.16 * (low - target_low) ** 2
        -0.06 * ((span - target_span) / max(1.0, target_span)) ** 2
        -0.12 * max(0, consecutive - 1) ** 2
    )
    if len(hits) == 0:
        return base + structure
    return base + structure + 2.8 * float(np.mean(hits >= 2)) + 4.2 * float(np.mean(hits >= 3))


def generate_candidate_combos(
    spec: LotterySpec,
    draws: list[Draw],
    scores: np.ndarray,
    rng: np.random.Generator,
    candidate_pool: int,
) -> list[tuple[int, ...]]:
    values = spec.main.values
    probs = np.exp(scores / 1.35)
    probs = probs / probs.sum()
    candidates: set[tuple[int, ...]] = set()
    ranked = [values[idx] for idx in np.argsort(scores)[::-1]]

    # Coverage skeleton: force the optimizer to consider all pool regions.
    for offset in range(max(1, len(values) // spec.main.pick)):
        combo = tuple(sorted(ranked[(offset + step * max(1, len(values) // spec.main.pick)) % len(values)] for step in range(spec.main.pick)))
        candidates.add(combo)

    attempts = 0
    while len(candidates) < candidate_pool and attempts < candidate_pool * 20:
        attempts += 1
        combo = sample_unique(rng, values, probs, spec.main.pick)
        candidates.add(combo)
    return sorted(candidates)


def repair_union_coverage(selected: list[tuple[int, ...]], values: list[int], scores: np.ndarray, pick: int) -> list[tuple[int, ...]]:
    if len(selected) * pick < len(values):
        return selected

    repaired = list(selected)
    index = {value: idx for idx, value in enumerate(values)}
    usage = Counter(num for combo in repaired for num in combo)
    selected_keys = set(repaired)
    missing = [value for value in values if usage[value] == 0]

    for missing_num in missing:
        best: tuple[tuple[float, float, float], int, int, tuple[int, ...]] | None = None
        for combo_idx, combo in enumerate(repaired):
            combo_set = set(combo)
            if missing_num in combo_set:
                continue
            for remove_num in combo:
                if usage[remove_num] <= 1:
                    continue
                next_combo = tuple(sorted((combo_set - {remove_num}) | {missing_num}))
                if len(next_combo) != pick:
                    continue
                if next_combo in selected_keys:
                    continue
                rank = (
                    float(usage[remove_num]),
                    -float(scores[index[remove_num]]),
                    float(scores[index[missing_num]]),
                )
                if best is None or rank > best[0]:
                    best = (rank, combo_idx, remove_num, next_combo)
        if best is None:
            continue
        _, combo_idx, remove_num, next_combo = best
        selected_keys.remove(repaired[combo_idx])
        repaired[combo_idx] = next_combo
        selected_keys.add(next_combo)
        usage[remove_num] -= 1
        usage[missing_num] += 1
    return repaired


def optimize_tickets(
    spec: LotterySpec,
    draws: list[Draw],
    columns: int,
    seed_bits: list[int] | None = None,
    seed: int = 0,
    candidate_pool: int = 6000,
    score_override: np.ndarray | None = None,
) -> list[Ticket]:
    scores = score_override if score_override is not None else number_scores(draws, spec.main, "main")
    scores = np.asarray(scores, dtype=float)
    rng_seed = int(seed)
    if seed_bits:
        digest = 0
        for bit in seed_bits[:1024]:
            digest = ((digest << 1) ^ int(bit)) & ((1 << 63) - 1)
        rng_seed ^= digest
    rng = np.random.default_rng(rng_seed)
    candidates = generate_candidate_combos(spec, draws, scores, rng, candidate_pool)
    values = spec.main.values
    ranked = sorted(candidates, key=lambda combo: candidate_objective(combo, scores, values, draws), reverse=True)

    selected: list[tuple[int, ...]] = []
    usage: Counter[int] = Counter()
    seen_pairs: set[tuple[int, int]] = set()
    seen_triples: set[tuple[int, int, int]] = set()
    best_hits = np.zeros(min(157, len(draws)), dtype=float)
    recent_draws = draws[-min(157, len(draws)) :]

    while len(selected) < columns and ranked:
        best: tuple[float, tuple[int, ...]] | None = None
        for combo in ranked[: min(len(ranked), 1200)]:
            if combo in selected:
                continue
            overlap = max((len(set(combo) & set(chosen)) for chosen in selected), default=0)
            if overlap > max(2, spec.main.pick // 2 + 1):
                continue
            hits = ticket_history_hits(combo, recent_draws)
            new_best = np.maximum(best_hits, hits)
            union_gain = len(set(combo) - set(usage.keys())) / spec.main.pick
            pair_gain = len(pairs(combo) - seen_pairs) / max(1, len(pairs(combo)))
            triple_gain = len(triples(combo) - seen_triples) / max(1, len(triples(combo)))
            reuse_penalty = sum(max(0, usage[num] + 1 - max(3, columns // 5 + 1)) for num in combo)
            score = (
                candidate_objective(combo, scores, values, draws)
                + 12.0 * float(np.mean(new_best >= 2) - np.mean(best_hits >= 2))
                + 18.0 * float(np.mean(new_best >= 3) - np.mean(best_hits >= 3))
                + 4.0 * float(new_best.mean() - best_hits.mean())
                + 2.5 * union_gain
                + 1.4 * pair_gain
                + 1.0 * triple_gain
                - 2.0 * max(0, overlap - max(1, spec.main.pick // 2))
                - 3.0 * reuse_penalty
            )
            if best is None or score > best[0]:
                best = (score, combo)
        if best is None:
            break
        chosen = best[1]
        selected.append(chosen)
        usage.update(chosen)
        seen_pairs.update(pairs(chosen))
        seen_triples.update(triples(chosen))
        best_hits = np.maximum(best_hits, ticket_history_hits(chosen, recent_draws))
        ranked = [combo for combo in ranked if combo != chosen]

    if len(selected) < columns:
        for combo in ranked:
            if len(selected) >= columns:
                break
            selected.append(combo)

    selected = repair_union_coverage(selected, values, scores, spec.main.pick)

    tickets: list[Ticket] = []
    bonus_probs = None
    if spec.bonus:
        bonus_scores = number_scores(draws, spec.bonus, "bonus")
        bonus_probs = np.exp(bonus_scores / 1.4)
        bonus_probs = bonus_probs / bonus_probs.sum()
    for combo in selected[:columns]:
        bonus = ()
        if spec.bonus and bonus_probs is not None:
            bonus = sample_unique(rng, spec.bonus.values, bonus_probs, spec.bonus.pick)
        tickets.append(Ticket(combo, bonus, "optimized_quantum_weighted" if seed_bits else "optimized_classical"))
    return tickets


def ticket_set_metrics(tickets: list[Ticket], pool: PoolSpec) -> dict:
    combos = [ticket.main for ticket in tickets]
    union = set(num for combo in combos for num in combo)
    usage = Counter(num for combo in combos for num in combo)
    max_overlap = 0
    for left, right in itertools.combinations(combos, 2):
        max_overlap = max(max_overlap, len(set(left) & set(right)))
    pair_union = set()
    triple_union = set()
    for combo in combos:
        pair_union.update(pairs(combo))
        triple_union.update(triples(combo))
    return {
        "union_size": len(union),
        "pool_size": len(pool.values),
        "union_coverage": len(union) / max(1, len(pool.values)),
        "missing_numbers": [value for value in pool.values if value not in union],
        "max_pairwise_overlap": max_overlap,
        "max_number_reuse": max(usage.values()) if usage else 0,
        "pair_coverage_count": len(pair_union),
        "triple_coverage_count": len(triple_union),
    }


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
