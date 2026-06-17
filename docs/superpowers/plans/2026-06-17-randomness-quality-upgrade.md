# Randomness Quality Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Quantum Lotto Lab from a working research prototype into a calibrated randomness-fingerprint and candidate-search system that first identifies the kind of randomness, then generates as many validated candidate variations as feasible from 10 years of history, then returns the best 30 columns or the best single column, with a long IBM Quantum execution profile.

**Architecture:** Split the current monolithic math into calibrated audit, nested validation, candidate-search, portfolio optimization, and IBM profile modules. The statistical layer must control false positives before the optimizer or IBM QPU layer is allowed to influence final columns. IBM remains the long-running sampling/entropy layer after the statistical model is built.

**Tech Stack:** Python 3.10+, numpy, pandas, qiskit, qiskit-ibm-runtime, pytest, ruff.

---

## Current Audit Findings

1. **High severity: raw pair/triple lift overstates structure.**
   - Current code uses the maximum observed pair/triple lift directly.
   - Uniform simulation check showed false positives: for 100 uniform `6/60` histories with 30 draws, `pair_clustering` and `triple_clustering` appeared in 100/100 runs.
   - Fix: replace raw max-lift classification with calibrated scan-statistic p-values from null simulations/permutation.

2. **High severity: ticket backtest is not fully out-of-sample.**
   - `candidate_objective()` rewards historical 2+/3+ behavior on the same recent history used to generate tickets.
   - `ticket_backtest` therefore measures historical fit, not true predictive validation.
   - Fix: add nested walk-forward ticket-set validation where each tested draw is unseen when tickets are generated.

3. **Medium severity: candidate generation samples only a small subset.**
   - `candidate_pool=6000` is tiny versus `C(60, 6) = 50,063,860`.
   - For `6/60`, exact streaming enumeration is feasible and should be available in deep mode.
   - Fix: add streaming all-combination search with a top-K heap for feasible games, and fall back to stochastic candidate generation only when the total space is too large.

4. **Medium severity: IBM QPU run has no "long" policy.**
   - The code accepts `--qubits`, `--layers`, `--batch-circuits`, and `--shots`, but there is no enforceable long-run profile.
   - Fix: add `--quantum-profile long|deep|extreme`, minimum total shots, repeat jobs, and report actual qubits/layers/circuits/shots/job IDs.

5. **Medium severity: reports need stronger honesty around uncertainty.**
   - The report should say when structure is calibrated-significant, when it is only historical fit, and when it is not strong enough.
   - Fix: add p-values, null false-positive rates, confidence intervals, exact candidate-space counts, and model-selection details.

---

### Task 1: Add Calibration Regression Tests

**Files:**
- Create: `tests/test_calibration.py`
- Modify: none

- [ ] **Step 1: Write failing tests for uniform false-positive control**

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
PYTHONPATH=. pytest tests/test_calibration.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'quantum_lotto_lab.calibration'`.

---

### Task 2: Implement Calibrated Null Simulation Layer

**Files:**
- Create: `quantum_lotto_lab/calibration.py`
- Modify: `quantum_lotto_lab/randomness.py`
- Test: `tests/test_calibration.py`

- [ ] **Step 1: Create null simulation helpers**

Add `quantum_lotto_lab/calibration.py`:

```python
from __future__ import annotations

from collections import Counter
from datetime import timedelta
import itertools
import math

import numpy as np

from .models import Draw, PoolSpec
from .randomness import audit_pool_randomness, randomness_fingerprint


def simulate_uniform_draws(template: list[Draw], pool: PoolSpec, seed: int) -> list[Draw]:
    rng = np.random.default_rng(seed)
    values = pool.values
    out: list[Draw] = []
    for idx, draw in enumerate(template):
        nums = tuple(sorted(int(x) for x in rng.choice(values, size=pool.pick, replace=False)))
        out.append(Draw(draw.date if draw.date else template[0].date + timedelta(days=idx), nums))
    return out


def pair_max_lift(draws: list[Draw], pool: PoolSpec, field: str) -> float:
    audit = audit_pool_randomness(draws, pool, field)
    return float(audit["pair_lift"]["max_lift"])


def triple_max_lift(draws: list[Draw], pool: PoolSpec, field: str) -> float:
    counts: Counter[tuple[int, int, int]] = Counter()
    for draw in draws:
        nums = draw.main if field == "main" else draw.bonus
        valid = sorted(num for num in nums if pool.minimum <= num <= pool.maximum)
        counts.update(itertools.combinations(valid, 3))
    if not counts or pool.pick < 3:
        return 0.0
    probability = math.comb(len(pool.values) - 3, pool.pick - 3) / math.comb(len(pool.values), pool.pick)
    expected = len(draws) * probability
    return max(count / max(expected, 1e-12) for count in counts.values())


def frequency_chi_square(draws: list[Draw], pool: PoolSpec, field: str) -> float:
    return float(audit_pool_randomness(draws, pool, field)["frequency"]["chi_square"])


def empirical_p_value(observed: float, null_values: list[float]) -> float:
    exceed = sum(value >= observed for value in null_values)
    return (exceed + 1.0) / (len(null_values) + 1.0)
```

- [ ] **Step 2: Add calibrated fingerprint function**

Append to `quantum_lotto_lab/calibration.py`:

```python
def calibrated_randomness_fingerprint(
    draws: list[Draw],
    pool: PoolSpec,
    field: str = "main",
    null_trials: int = 500,
    seed: int = 20260623,
) -> dict:
    base = randomness_fingerprint(draws, pool, field)
    observed = {
        "frequency_chi_square": frequency_chi_square(draws, pool, field),
        "pair_max_lift": pair_max_lift(draws, pool, field),
        "triple_max_lift": triple_max_lift(draws, pool, field),
    }
    nulls = {name: [] for name in observed}
    for trial in range(null_trials):
        null_draws = simulate_uniform_draws(draws, pool, seed + trial)
        nulls["frequency_chi_square"].append(frequency_chi_square(null_draws, pool, field))
        nulls["pair_max_lift"].append(pair_max_lift(null_draws, pool, field))
        nulls["triple_max_lift"].append(triple_max_lift(null_draws, pool, field))

    calibration = {}
    for name, value in observed.items():
        arr = np.asarray(nulls[name], dtype=float)
        calibration[name] = {
            "observed": value,
            "empirical_p": empirical_p_value(value, nulls[name]),
            "null_mean": float(arr.mean()),
            "null_p95": float(np.percentile(arr, 95)),
            "null_p99": float(np.percentile(arr, 99)),
        }

    raw_scores = dict(base["randomness_type"]["scores"])
    raw_scores["frequency_bias"] = 1.0 - calibration["frequency_chi_square"]["empirical_p"]
    raw_scores["pair_clustering"] = 1.0 - calibration["pair_max_lift"]["empirical_p"]
    raw_scores["triple_clustering"] = 1.0 - calibration["triple_max_lift"]["empirical_p"]
    dominant = [
        name
        for name, score in sorted(raw_scores.items(), key=lambda item: item[1], reverse=True)
        if score >= 0.95
    ][:5]
    if not dominant:
        dominant = ["near_uniform"]
    base["calibration"] = calibration
    base["randomness_type"] = {
        "scores": raw_scores,
        "dominant_types": dominant,
        "threshold": "dominant requires calibrated score >= 0.95 for calibrated families",
    }
    return base
```

- [ ] **Step 3: Run calibration tests**

Run:

```bash
PYTHONPATH=. pytest tests/test_calibration.py -q
```

Expected: PASS.

---

### Task 3: Replace CLI Audit With Calibrated Fingerprint

**Files:**
- Modify: `quantum_lotto_lab/cli.py`
- Modify: `README.md`
- Modify: `docs/methodology.md`
- Test: `tests/test_calibration.py`

- [ ] **Step 1: Add CLI flags**

Modify `build_parser()` in `quantum_lotto_lab/cli.py`:

```python
audit.add_argument("--deep-calibration", action="store_true", help="Use more null simulations for randomness calibration.")
audit.add_argument("--null-trials", type=int, default=None, help="Override null simulation count.")
```

- [ ] **Step 2: Use calibrated fingerprint in `cmd_audit`**

Change the fingerprint block in `cmd_audit`:

```python
from .calibration import calibrated_randomness_fingerprint
```

Then:

```python
null_trials = args.null_trials if args.null_trials is not None else (2000 if args.deep_calibration else 500)
fingerprint = calibrated_randomness_fingerprint(
    draws,
    spec.main,
    "main",
    null_trials=null_trials,
    seed=args.seed,
)
```

- [ ] **Step 3: Show calibrated p-values in report**

Add to `audit_report()` evidence rows:

```python
calibration = fingerprint.get("calibration", {})
if calibration:
    rows.extend(
        [
            f"- Frequency chi-square calibrated p: `{calibration['frequency_chi_square']['empirical_p']:.4f}`.",
            f"- Pair max-lift calibrated p: `{calibration['pair_max_lift']['empirical_p']:.4f}`.",
            f"- Triple max-lift calibrated p: `{calibration['triple_max_lift']['empirical_p']:.4f}`.",
        ]
    )
```

- [ ] **Step 4: Run CLI smoke test**

Run:

```bash
PYTHONPATH=. python -m quantum_lotto_lab.cli audit \
  --lottery super-loto-tr \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv \
  --columns 30 \
  --train-min 10 \
  --null-trials 50 \
  --output /tmp/qll_calibrated_audit.json
```

Expected: command exits 0 and markdown contains `calibrated p`.

---

### Task 4: Add Nested Out-of-Sample Ticket Validation

**Files:**
- Create: `quantum_lotto_lab/validation.py`
- Modify: `quantum_lotto_lab/cli.py`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Write failing validation test**

Create `tests/test_validation.py`:

```python
from __future__ import annotations

from datetime import date, timedelta

from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.models import Draw
from quantum_lotto_lab.validation import nested_ticket_backtest


def make_draws() -> list[Draw]:
    start = date(2020, 1, 1)
    draws = []
    for idx in range(120):
        hot = 1 if idx % 3 else 2
        draws.append(Draw(start + timedelta(days=7 * idx), tuple(sorted([hot, 3, 4, 5, 6, 7 + idx % 20]))))
    return draws


def test_nested_ticket_backtest_uses_unseen_draws():
    spec = get_lottery("super-loto-tr")
    report = nested_ticket_backtest(spec, make_draws(), columns=30, train_min=60, seed=123, candidate_pool=800)
    assert report["test_draws"] == 60
    assert report["leakage_guard"] == "tickets generated only from draws before the tested draw"
    assert "any_2_plus" in report
    assert "best_main_distribution" in report
```

- [ ] **Step 2: Implement nested validation**

Create `quantum_lotto_lab/validation.py`:

```python
from __future__ import annotations

from collections import Counter

import numpy as np

from .math_model import optimize_tickets
from .models import Draw, LotterySpec
from .randomness import score_vector, walk_forward_models


def nested_ticket_backtest(
    spec: LotterySpec,
    draws: list[Draw],
    columns: int,
    train_min: int = 160,
    seed: int = 20260623,
    candidate_pool: int = 6000,
) -> dict:
    if len(draws) <= train_min:
        return {
            "test_draws": 0,
            "leakage_guard": "not enough draws for nested validation",
            "best_main_distribution": {},
        }
    best_hits: list[int] = []
    selected_models: Counter[str] = Counter()
    for idx in range(train_min, len(draws)):
        train = draws[:idx]
        actual = set(draws[idx].main)
        walk = walk_forward_models(train, spec, field="main", train_min=max(30, train_min // 2))
        model = walk["best_model"]
        selected_models[model] += 1
        scores = score_vector(train, spec, "main", model)
        tickets = optimize_tickets(
            spec,
            train,
            columns=columns,
            seed=seed + idx,
            candidate_pool=candidate_pool,
            score_override=scores,
        )
        best_hits.append(max(len(set(ticket.main) & actual) for ticket in tickets))
    arr = np.asarray(best_hits, dtype=int)
    return {
        "test_draws": int(len(arr)),
        "leakage_guard": "tickets generated only from draws before the tested draw",
        "selected_models": dict(selected_models),
        "best_main_mean": float(arr.mean()) if len(arr) else 0.0,
        "any_1_plus": float(np.mean(arr >= 1)) if len(arr) else 0.0,
        "any_2_plus": float(np.mean(arr >= 2)) if len(arr) else 0.0,
        "any_3_plus": float(np.mean(arr >= 3)) if len(arr) else 0.0,
        "best_main_distribution": {str(k): int(np.sum(arr == k)) for k in range(spec.main.pick + 1)},
    }
```

- [ ] **Step 3: Report both historical fit and nested predictive validation**

In `cmd_audit`, compute:

```python
from .validation import nested_ticket_backtest

nested = nested_ticket_backtest(
    spec,
    draws,
    columns=args.columns,
    train_min=args.train_min,
    seed=args.seed,
)
payload["nested_ticket_backtest"] = nested
```

In `audit_report()`, label current `ticket_backtest` as historical fit and nested result as predictive validation.

- [ ] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=. pytest tests/test_validation.py tests/test_randomness.py -q
```

Expected: PASS.

---

### Task 5: Add Exact Candidate-Space Search for Feasible Games

**Files:**
- Create: `quantum_lotto_lab/search.py`
- Modify: `quantum_lotto_lab/math_model.py`
- Test: `tests/test_search.py`

- [ ] **Step 1: Write exact-search tests**

Create `tests/test_search.py`:

```python
from __future__ import annotations

import numpy as np

from quantum_lotto_lab.search import stream_top_combinations


def test_stream_top_combinations_evaluates_exact_space():
    values = list(range(1, 11))
    scores = np.asarray(values, dtype=float)
    result = stream_top_combinations(values, pick=3, scores=scores, top_k=5, chunk_size=20)
    assert result["total_combinations"] == 120
    assert result["evaluated_combinations"] == 120
    assert result["top"][0]["combo"] == [8, 9, 10]
```

- [ ] **Step 2: Implement streaming top-K**

Create `quantum_lotto_lab/search.py`:

```python
from __future__ import annotations

import heapq
import itertools
import math

import numpy as np


def combo_score(combo: tuple[int, ...], index: dict[int, int], scores: np.ndarray) -> float:
    return float(sum(scores[index[num]] for num in combo))


def stream_top_combinations(
    values: list[int],
    pick: int,
    scores: np.ndarray,
    top_k: int = 5000,
    chunk_size: int = 250_000,
) -> dict:
    index = {value: idx for idx, value in enumerate(values)}
    total = math.comb(len(values), pick)
    heap: list[tuple[float, tuple[int, ...]]] = []
    evaluated = 0
    for combo in itertools.combinations(values, pick):
        score = combo_score(combo, index, scores)
        evaluated += 1
        item = (score, combo)
        if len(heap) < top_k:
            heapq.heappush(heap, item)
        elif score > heap[0][0]:
            heapq.heapreplace(heap, item)
    top = sorted(heap, key=lambda item: item[0], reverse=True)
    return {
        "total_combinations": total,
        "evaluated_combinations": evaluated,
        "top": [{"score": score, "combo": list(combo)} for score, combo in top],
    }
```

- [ ] **Step 3: Integrate search mode into optimizer**

Add `candidate_mode` to `optimize_tickets()`:

```python
candidate_mode: str = "sampled",
exact_top_k: int = 10000,
max_exact_combinations: int = 60_000_000,
```

Before sampled generation:

```python
if candidate_mode == "exact":
    from .search import stream_top_combinations

    total = math.comb(len(spec.main.values), spec.main.pick)
    if total <= max_exact_combinations:
        exact = stream_top_combinations(spec.main.values, spec.main.pick, scores, top_k=exact_top_k)
        candidates = [tuple(row["combo"]) for row in exact["top"]]
    else:
        candidates = generate_candidate_combos(spec, draws, scores, rng, candidate_pool)
else:
    candidates = generate_candidate_combos(spec, draws, scores, rng, candidate_pool)
```

- [ ] **Step 4: Add CLI flags**

Add:

```python
audit.add_argument("--candidate-mode", choices=["sampled", "exact"], default="sampled")
audit.add_argument("--exact-top-k", type=int, default=10000)
audit.add_argument("--max-exact-combinations", type=int, default=60000000)
```

Pass these through to `optimize_tickets()`.

- [ ] **Step 5: Run exact search smoke for 6/60**

Run:

```bash
PYTHONPATH=. python -m quantum_lotto_lab.cli audit \
  --lottery super-loto-tr \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv \
  --columns 30 \
  --train-min 10 \
  --candidate-mode exact \
  --exact-top-k 5000 \
  --output /tmp/qll_exact_audit.json
```

Expected: command exits 0 and JSON reports `total_combinations` as `50063860` when exact mode is used.

---

### Task 6: Add Final 30-or-1 Selection Contract

**Files:**
- Modify: `quantum_lotto_lab/cli.py`
- Modify: `quantum_lotto_lab/math_model.py`
- Test: `tests/test_randomness.py`

- [ ] **Step 1: Add target mode flag**

Add to audit parser:

```python
audit.add_argument("--target", choices=["portfolio30", "single6"], default="portfolio30")
```

- [ ] **Step 2: Enforce target contract**

In `cmd_audit`:

```python
columns = 1 if args.target == "single6" else args.columns
```

Use `columns` for optimizer, theoretical metrics, and report.

- [ ] **Step 3: Report the interpretation**

Add to payload:

```python
"target": args.target,
"target_plain": "single highest-ranked 6/6 column" if args.target == "single6" else "30-column diversified 6/6 portfolio",
```

Add to markdown:

```python
f"- Target: `{payload['target_plain']}`."
```

- [ ] **Step 4: Test single target**

Add to `tests/test_randomness.py`:

```python
def test_optimizer_single_target_returns_one_ticket():
    spec = get_lottery("super-loto-tr")
    draws = biased_draws()
    tickets = optimize_tickets(spec, draws, columns=1, seed=14, candidate_pool=500)
    assert len(tickets) == 1
    assert len(tickets[0].main) == 6
```

Run:

```bash
PYTHONPATH=. pytest tests/test_randomness.py -q
```

Expected: PASS.

---

### Task 7: Add Long IBM Quantum Profiles

**Files:**
- Create: `quantum_lotto_lab/quantum_profiles.py`
- Modify: `quantum_lotto_lab/cli.py`
- Modify: `quantum_lotto_lab/ibm.py`
- Test: `tests/test_quantum_profiles.py`

- [ ] **Step 1: Write profile tests**

Create `tests/test_quantum_profiles.py`:

```python
from quantum_lotto_lab.quantum_profiles import resolve_quantum_profile


def test_long_profile_is_not_short():
    profile = resolve_quantum_profile("long", backend_qubits=127)
    assert profile["qubits"] >= 96
    assert profile["layers"] >= 64
    assert profile["batch_circuits"] >= 12
    assert profile["shots"] >= 8192
    assert profile["repeat_jobs"] >= 2
```

- [ ] **Step 2: Implement profiles**

Create `quantum_lotto_lab/quantum_profiles.py`:

```python
from __future__ import annotations


PROFILES = {
    "standard": {"qubits": 100, "layers": 32, "batch_circuits": 4, "shots": 4096, "repeat_jobs": 1},
    "long": {"qubits": 127, "layers": 64, "batch_circuits": 12, "shots": 8192, "repeat_jobs": 2},
    "deep": {"qubits": 156, "layers": 96, "batch_circuits": 16, "shots": 8192, "repeat_jobs": 3},
    "extreme": {"qubits": 156, "layers": 128, "batch_circuits": 24, "shots": 8192, "repeat_jobs": 4},
}


def resolve_quantum_profile(name: str, backend_qubits: int) -> dict:
    if name not in PROFILES:
        raise ValueError(f"unknown quantum profile {name}")
    profile = dict(PROFILES[name])
    profile["requested_qubits"] = profile["qubits"]
    profile["qubits"] = min(profile["qubits"], int(backend_qubits))
    profile["total_requested_shots"] = profile["shots"] * profile["batch_circuits"] * profile["repeat_jobs"]
    return profile
```

- [ ] **Step 3: Add repeat job support**

In `ibm.py`, add:

```python
def run_profiled_sampling(
    backend_name: str,
    qubits: int,
    layers: int,
    batch_circuits: int,
    shots: int,
    seed_weights: list[float],
    output_counts: Path | None = None,
    repeat_jobs: int = 1,
) -> tuple[list[int], dict]:
    all_bits = []
    jobs = []
    for repeat in range(repeat_jobs):
        repeat_output = output_counts.with_suffix(f".counts.{repeat + 1:02d}.json") if output_counts else None
        bits, payload = run_heavy_sampling(
            backend_name=backend_name,
            qubits=qubits,
            layers=layers,
            batch_circuits=batch_circuits,
            shots=shots,
            seed_weights=seed_weights,
            output_counts=repeat_output,
        )
        all_bits.extend(bits)
        jobs.append(payload)
    return all_bits, {
        "jobs": jobs,
        "job_ids": [job["job_id"] for job in jobs],
        "repeat_jobs": repeat_jobs,
        "total_requested_shots": sum(job["total_requested_shots"] for job in jobs),
    }
```

Use unique output count paths such as `.counts.01.json`, `.counts.02.json`.

- [ ] **Step 4: Add CLI profile flags**

Add to both `audit` and `predict`:

```python
parser.add_argument("--quantum-profile", choices=["standard", "long", "deep", "extreme"], default="long")
parser.add_argument("--repeat-jobs", type=int, default=None)
```

When `--ibm` is used, resolve the backend qubit count and profile before submitting jobs. Explicit CLI `--qubits`, `--layers`, `--batch-circuits`, and `--shots` can override profile values only when supplied.

- [ ] **Step 5: Report long-run evidence**

Report:

```text
IBM profile: long
Requested qubits: 127
Actual qubits: <backend-limited>
Layers: 64
Batch circuits: 12
Shots per circuit: 8192
Repeat jobs: 2
Total requested shots: 196608
Job IDs: `<comma-separated job ids from payload['job_ids']>`
```

- [ ] **Step 6: Run profile tests**

Run:

```bash
PYTHONPATH=. pytest tests/test_quantum_profiles.py -q
```

Expected: PASS.

---

### Task 8: Add Data Quality and 10-Year Readiness Checks

**Files:**
- Create: `quantum_lotto_lab/data_quality.py`
- Modify: `quantum_lotto_lab/cli.py`
- Test: `tests/test_data_quality.py`

- [ ] **Step 1: Write data-quality test**

Create `tests/test_data_quality.py`:

```python
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
```

- [ ] **Step 2: Implement validator**

Create `quantum_lotto_lab/data_quality.py`:

```python
from __future__ import annotations

from collections import Counter

from .models import Draw, LotterySpec


def validate_draw_history(draws: list[Draw], spec: LotterySpec) -> dict:
    date_counts = Counter(str(draw.date) for draw in draws)
    duplicate_dates = sorted(date for date, count in date_counts.items() if count > 1)
    range_errors = []
    size_errors = []
    for draw in draws:
        if len(draw.main) != spec.main.pick:
            size_errors.append(str(draw.date))
        for num in draw.main:
            if num < spec.main.minimum or num > spec.main.maximum:
                range_errors.append({"date": str(draw.date), "number": num})
    usable = not duplicate_dates and not range_errors and not size_errors and len(draws) >= 80
    return {
        "draws": len(draws),
        "first_draw": str(draws[0].date) if draws else None,
        "last_draw": str(draws[-1].date) if draws else None,
        "duplicate_dates": duplicate_dates,
        "range_errors": range_errors,
        "size_errors": size_errors,
        "usable": usable,
        "minimum_recommended_draws": 80,
    }
```

- [ ] **Step 3: Add report gate**

In `cmd_audit`, compute data quality and include it in payload. If `usable` is false, continue only with a clear warning:

```python
quality = validate_draw_history(draws, spec)
payload["data_quality"] = quality
```

- [ ] **Step 4: Run tests**

Run:

```bash
PYTHONPATH=. pytest tests/test_data_quality.py -q
```

Expected: PASS.

---

### Task 9: Documentation and Report Upgrade

**Files:**
- Modify: `README.md`
- Modify: `docs/methodology.md`
- Modify: `quantum_lotto_lab/cli.py`

- [ ] **Step 1: Update motto and workflow**

Add to README:

```markdown
## Motto

Every random process has mathematics. The tool does not assume that the math is exploitable; it tests whether any measured structure survives calibrated null tests and out-of-sample validation.
```

- [ ] **Step 2: Add final workflow**

Add:

```markdown
1. Validate 10-year draw history.
2. Identify randomness type with calibrated null tests.
3. Select model with nested walk-forward validation.
4. Generate candidate variations with exact search when feasible.
5. Select either the best single 6-number column or a 30-column diversified portfolio.
6. Run IBM Quantum in long/deep/extreme mode only after the statistical model exists.
7. Report uncertainty, candidate-space size, IBM job IDs, and no-guarantee warning.
```

- [ ] **Step 3: Run docs smoke**

Run:

```bash
rg -n "Motto|calibrated|nested|candidate variations|long/deep/extreme" README.md docs/methodology.md
```

Expected: all terms appear.

---

### Task 10: Full Verification and Push

**Files:**
- All touched files

- [ ] **Step 1: Install dev dependencies locally**

Run:

```bash
python -m pip install -e ".[dev]"
```

Expected: installs `pytest` and `ruff`.

- [ ] **Step 2: Run full validation**

Run:

```bash
PYTHONPATH=. pytest -q
python -m ruff check .
PYTHONPATH=. python -m compileall -q quantum_lotto_lab tests
```

Expected: all pass.

- [ ] **Step 3: Run calibrated audit smoke**

Run:

```bash
PYTHONPATH=. python -m quantum_lotto_lab.cli audit \
  --lottery super-loto-tr \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv \
  --columns 30 \
  --target portfolio30 \
  --candidate-mode exact \
  --exact-top-k 5000 \
  --deep-calibration \
  --output /tmp/qll_final_quality_audit.json
```

Expected: command exits 0, reports calibrated p-values, reports exact candidate count, and produces 30 columns.

- [ ] **Step 4: Run secret scan**

Run:

```bash
rg -n "ApiKey-[0-9a-f-]+|gho_[A-Za-z0-9_]+|ghp_[A-Za-z0-9_]+|ghs_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|QiskitRuntimeService\\(.*token|token\\s*=\\s*['\\\"]" .
```

Expected: no output.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status -sb
git add quantum_lotto_lab tests README.md docs/methodology.md docs/superpowers/plans/2026-06-17-randomness-quality-upgrade.md
git commit -m "Calibrate randomness fingerprint and long quantum profiles"
git push origin main
```

Expected: public GitHub `main` updates without committing IBM API keys.
