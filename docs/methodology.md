# Methodology

Quantum Lotto Lab is a research tool. It separates three things that are often mixed together:

1. **The lottery rule**
   - Example: Powerball is `5/69 + 1/26`; Super Loto is `6/60`.
   - The theoretical jackpot probability comes from combinations, not from AI.

2. **Historical risk modeling**
   - The tool reads previous draws and scores each number with several statistical signals:
     - long-term frequency
     - recent frequency
     - exponential recency
     - Bayesian-smoothed frequency
     - overdue/gap signal
     - anti-frequency and anti-recent controls
     - pair co-occurrence centrality
   - These signals can shape tickets, but they do not prove that future draws are predictable.

3. **Optional IBM Quantum sampling**
   - IBM Quantum mode runs a real high-qubit circuit.
   - Exact classical statevector simulation scales as `2^qubits`.
   - A 100-200 qubit circuit is therefore a very large exact-simulation problem.
   - The quantum bitstrings are used as a sampling signal for ticket generation.

## Expectation

For a ticket set with `N` columns and a main pool of `M` numbers where `K` numbers are drawn:

```text
single-column jackpot probability = 1 / C(M, K)
N-column approximate jackpot probability = N / C(M, K)
```

For example, a `6/60` lottery with 30 columns has:

```text
C(60, 6) = 50,063,860
30-column chance ~= 30 / 50,063,860
                 ~= 1 / 1,668,795
```

## Error Margin

Backtest percentages are estimates from historical data. If the backtest window has `n` draws and a metric has observed rate `p`, an approximate 95% uncertainty band is:

```text
1.96 * sqrt(p * (1 - p) / n)
```

This is not a guarantee. It is just a way to avoid over-reading small backtest samples.

## Randomness Fingerprint

The audit does not only ask "is this random?" It tries to identify the **shape** of any deviation from a simple uniform baseline.

Current fingerprint families:

- `frequency_bias`: some numbers appear unusually often or rarely.
- `entropy_compression`: the observed distribution is more concentrated than a flat distribution.
- `pair_clustering`: pairs appear together more often than a simple random model expects.
- `triple_clustering`: triples appear together more often than expected.
- `temporal_memory`: nearby draws overlap more or less than expected.
- `runs_irregularity`: hit/miss sequences for numbers have unusual run patterns.
- `distribution_drift`: early-history and late-history number distributions differ.
- `calendar_effect`: month or weekday buckets differ from the global distribution.
- `gap_anomaly`: waiting times between appearances differ from the geometric baseline.
- `graph_concentration`: top pair relationships are concentrated around a small group of numbers.
- `near_uniform`: no tested fingerprint is strong enough to highlight.

These are hypotheses. A fingerprint is only useful if it survives walk-forward testing.

## Walk-Forward Model Suite

The tool evaluates 15 candidate models by repeatedly training on earlier draws, predicting the next draw, and moving forward one step.

```text
uniform
frequency_all
recent_frequency
ewma_recency
bayesian_dirichlet
gap_overdue
pair_centrality
anti_frequency
anti_recent
drift_recent_vs_old
stability
hybrid_gap_pair
hybrid_recency_pair
ensemble
legacy_weighted
```

The selected generation model is the best out-of-sample model, not simply the model that looks best on the full history.

## Ticket Optimizer

For multi-column runs, the optimizer balances several goals:

- higher score under the selected walk-forward model
- broad union coverage across the available number pool
- full union coverage when the ticket capacity can cover the full pool
- controlled overlap between columns
- pair and triple diversity
- historical 2+ and 3+ backtest behavior over the recent window
- penalties for extreme number reuse or unnatural structure

For a `6/60` lottery, 30 columns are still a tiny subset of the full `C(60, 6) = 50,063,860` jackpot space. Optimization can improve coverage and historical fit; it cannot remove the jackpot risk.

## Honest Interpretation

Good phrasing:

> "This run used a real IBM Quantum sampling job and a mathematical ticket optimizer. It improved some historical metrics, but it does not guarantee future lottery outcomes."

Bad phrasing:

> "The quantum computer solved the lottery."

The second sentence is not supported by the math.

## Locked Workflow

Do not start from "make IBM choose numbers." The correct order is:

1. **Randomness audit**
   - Ask: does the history deviate from a simple random baseline?
   - Measure frequency z-scores, entropy, runs, pair/triple lift, gap behavior, serial lag, distribution drift, and date effects.

2. **Signal discovery**
   - Candidate signals are only hypotheses.
   - A hot number, overdue number, or strong pair is not useful unless it predicts outside the training window.

3. **Walk-forward validation**
   - Train on earlier draws.
   - Predict the next draw.
   - Move forward one draw and repeat.
   - Compare against a uniform baseline.

4. **Model selection**
   - Use the model only if it beats uniform out-of-sample.
   - If no model wins, say so plainly.

5. **Ticket generation**
   - Generate columns from the validated weighting model.
   - Optimize coverage, overlap, pair/triple diversity, 2+/3+ backtest behavior, and number reuse.
   - Report jackpot probability, 2+/3+ rates, and backtest uncertainty.

6. **Optional IBM Quantum layer**
   - IBM QPU sampling can be used after the model has been built.
   - IBM does not understand the lottery by itself.
   - The reasoning layer is the statistical audit and walk-forward validation.

This order is intentional. Skipping directly to quantum sampling creates impressive-looking output without answering whether the historical data contains a reusable signal.
