# Randomness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the "right question" system: test whether historical lottery draws show measurable non-random structure, validate whether any structure survives out-of-sample backtesting, and only then generate tickets.

**Architecture:** Add a focused randomness-audit module that is independent of IBM QPU sampling. The audit produces statistical evidence, model backtest scores, a plain-language verdict, and optional ticket generation based on the best validated model. IBM remains a final sampling layer, not the system that "understands" lottery data.

**Tech Stack:** Python, numpy, pandas, standard-library statistics/math, pytest, existing `quantum_lotto_lab` CLI.

---

### Task 1: Statistical Randomness Audit Core

**Files:**
- Create: `quantum_lotto_lab/randomness.py`
- Test: `tests/test_randomness.py`

- [ ] **Step 1: Write tests for frequency, gap, pair, and seasonality signals**

```python
from datetime import date, timedelta

from quantum_lotto_lab.models import Draw, PoolSpec
from quantum_lotto_lab.randomness import audit_pool_randomness


def make_draws():
    start = date(2024, 1, 1)
    draws = []
    for i in range(80):
        hot = 1 if i % 2 == 0 else 2
        draws.append(Draw(start + timedelta(days=i * 7), tuple(sorted([hot, 3, 4, 5, 6, 7]))))
    return draws


def test_audit_detects_obvious_frequency_bias():
    report = audit_pool_randomness(make_draws(), PoolSpec("numbers", 1, 10, 6), "main")
    assert report["draws"] == 80
    assert report["frequency"]["chi_square"] > 0
    assert report["frequency"]["max_abs_z"] > 2
    assert report["verdict"]["signal_strength"] in {"weak", "moderate", "strong"}
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `PYTHONPATH=. pytest tests/test_randomness.py -q`

Expected: FAIL because `quantum_lotto_lab.randomness` does not exist.

- [ ] **Step 3: Implement `randomness.py`**

Implement:
- `audit_pool_randomness(draws, pool, field)`
- frequency chi-square and z-scores
- gap distribution summary
- pair lift summary
- monthly/weekday seasonality summary
- plain verdict: `none`, `weak`, `moderate`, `strong`

- [ ] **Step 4: Run the randomness tests**

Run: `PYTHONPATH=. pytest tests/test_randomness.py -q`

Expected: PASS.

### Task 2: Out-of-Sample Model Backtest

**Files:**
- Modify: `quantum_lotto_lab/randomness.py`
- Test: `tests/test_randomness.py`

- [ ] **Step 1: Add tests for walk-forward backtest**

Test expected behavior:
- uniform baseline exists
- at least five candidate models are evaluated
- best model name and rates are returned

- [ ] **Step 2: Implement walk-forward model evaluation**

Implement:
- `walk_forward_models(draws, spec, field="main", train_min=30, top_k=None)`
- models:
  - `uniform`
  - `frequency_all`
  - `recent_frequency`
  - `gap_overdue`
  - `pair_centrality`
  - `ensemble`
- metrics:
  - `mean_hits`
  - `any_1_plus`
  - `any_2_plus`
  - `any_3_plus`
  - `hit_distribution`
  - `lift_vs_uniform`

- [ ] **Step 3: Run tests**

Run: `PYTHONPATH=. pytest tests/test_randomness.py tests/test_core.py -q`

Expected: PASS.

### Task 3: Human-Language Report and CLI

**Files:**
- Modify: `quantum_lotto_lab/cli.py`
- Modify: `README.md`
- Test: `tests/test_randomness.py`

- [ ] **Step 1: Add `audit` CLI command**

Command shape:

```bash
quantum-lotto-lab audit \
  --lottery super-loto-tr \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv \
  --columns 30 \
  --output outputs/audit.json
```

- [ ] **Step 2: Report must answer the correct question**

The report must say:
- whether there is measurable non-random structure
- whether it survives out-of-sample testing
- which model performed best
- whether the result is strong enough to use
- what the generated tickets are
- what IBM QPU can and cannot add

- [ ] **Step 3: Run CLI smoke test**

Run: `PYTHONPATH=. python -m quantum_lotto_lab.cli audit --lottery super-loto-tr --date 2026-06-23 --csv examples/sample_draws.csv --columns 5 --output /tmp/qll_audit.json`

Expected: command exits 0 and writes JSON/Markdown.

### Task 4: Documentation and Public Push

**Files:**
- Modify: `README.md`
- Modify: `docs/methodology.md`

- [ ] **Step 1: Document the locked workflow**

Document the exact order:
1. randomness tests
2. signal discovery
3. out-of-sample validation
4. model selection
5. ticket generation
6. optional IBM QPU sampling

- [ ] **Step 2: Verify no secrets**

Run:

```bash
rg -n "ApiKey|gho_|ghp_|ghs_|github_pat_|token\\s*=|QiskitRuntimeService\\(.*token" .
```

Expected: only safe local token input code, no real token values.

- [ ] **Step 3: Run full validation**

Run:

```bash
PYTHONPATH=. pytest -q
PYTHONPATH=. python -m quantum_lotto_lab.cli audit --lottery super-loto-tr --date 2026-06-23 --csv examples/sample_draws.csv --columns 5 --output /tmp/qll_audit.json
```

Expected: PASS and audit output exists.

- [ ] **Step 4: Commit and push**

Run:

```bash
git add .
git commit -m "Add randomness audit and walk-forward validation"
git push -u origin codex/randomness-audit
```

Then either open a PR or merge/push to `main` if explicitly desired.
