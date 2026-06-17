# Quantum Lotto Lab

High-qubit IBM Quantum lottery research toolkit for configurable lotteries.

This project builds lottery ticket sets from historical draw data, classical statistical features, and optional IBM Quantum sampling. It is designed for research, education, and experimentation.

**It does not guarantee winnings. Lottery outcomes are random.**

## What It Does

- Asks which lottery and which draw date you want.
- Loads historical draws from a built-in source or your own CSV.
- Supports lotteries with different formats, not only 6-number games.
- Builds mathematical features:
  - frequency and recent frequency
  - exponential recency
  - overdue/gap signal
  - pair co-occurrence centrality
  - historical backtest summary
  - theoretical jackpot and 2+/3+ baselines
- Optionally runs a real IBM Quantum job using 100-200 qubits when the selected backend supports it.
- Uses IBM QPU bitstrings as a high-qubit sampling signal for ticket generation.

## Built-In Lottery Specs

Run:

```bash
quantum-lotto-lab list
```

Current built-ins:

- `powerball` - US Powerball, `5/69 + 1/26`
- `mega-millions` - US Mega Millions, `5/70 + 1/25`
- `euromillions` - EuroMillions, `5/50 + 2/12`
- `eurojackpot` - EuroJackpot, `5/50 + 2/12`
- `super-loto-tr` - Turkey Super Loto, `6/60`
- `uk-lotto` - UK Lotto, `6/59 + bonus`
- `france-loto` - France Loto, `5/49 + 1/10`
- `germany-6aus49` - Germany Lotto 6aus49, `6/49 + superzahl`
- `superenalotto` - Italy SuperEnalotto, `6/90`

Some jurisdictions publish clean CSV/API data; others change websites frequently or have licensing constraints. For reliable runs, use `--csv` with a draw-history file.

## Install

```bash
git clone https://github.com/analistboracetinkaya-sudo/quantum-lotto-lab.git
cd quantum-lotto-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Quick Start Without IBM Quantum

Recommended workflow: audit first, generate second.

```bash
quantum-lotto-lab audit \
  --lottery powerball \
  --date 2026-06-23 \
  --columns 30 \
  --output outputs/powerball_audit.json
```

```bash
quantum-lotto-lab predict \
  --lottery powerball \
  --date 2026-06-23 \
  --columns 30 \
  --output outputs/powerball.json
```

With your own CSV:

```bash
quantum-lotto-lab predict \
  --lottery super-loto-tr \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv \
  --columns 30
```

## IBM Quantum Setup

The repository does **not** contain API keys.

Each user saves their own IBM Quantum token locally:

```bash
quantum-lotto-lab ibm-login
```

Then run:

```bash
quantum-lotto-lab audit \
  --lottery powerball \
  --date 2026-06-23 \
  --columns 30 \
  --ibm \
  --backend ibm_kingston \
  --qubits 120 \
  --layers 40 \
  --batch-circuits 4 \
  --shots 4096 \
  --output outputs/powerball_ibm.json
```

If the backend has fewer available qubits than requested, Qiskit/IBM constraints apply. Use `ibm_kingston`, `ibm_marrakesh`, or another backend available to your IBM account.

## CSV Format

Recommended:

```csv
date,numbers,bonus
2025-01-01,"1 5 9 21 33 44",7
```

For fixed-column games:

```csv
date,1,2,3,4,5,6
2025-01-01,1,5,9,21,33,44
```

## Custom Lotteries

Create a JSON spec:

```json
{
  "slug": "my-lottery",
  "name": "My Custom Lottery",
  "region": "Custom",
  "main": { "name": "numbers", "min": 1, "max": 60, "pick": 6 },
  "bonus": { "name": "bonus", "min": 1, "max": 12, "pick": 2 }
}
```

Run:

```bash
quantum-lotto-lab predict \
  --spec examples/custom_lottery.json \
  --date 2026-06-23 \
  --csv examples/sample_draws.csv
```

## What "Quantum" Means Here

The IBM mode submits a real high-qubit circuit to IBM Quantum hardware. Exact classical statevector simulation scales as `O(2^qubits)`, so a 100-200 qubit circuit is not something a normal computer can exactly simulate.

That does **not** mean it predicts lottery outcomes. It means the ticket-generation system can use a real quantum measurement distribution as part of the research workflow.

The locked workflow is:

1. Test whether historical draws deviate from a simple random baseline.
2. Measure candidate signals: frequency, recency, gap/overdue, pair centrality, seasonality.
3. Run walk-forward out-of-sample validation.
4. Select the model only if it beats the uniform baseline.
5. Generate ticket sets.
6. Optionally add IBM Quantum sampling as the final sampling layer.

See [docs/methodology.md](docs/methodology.md) for the plain-language math notes.

## Security Notes

- Do not commit IBM tokens.
- Do not put tokens in `.env` files inside public repositories.
- This tool uses Qiskit's local account storage through `quantum-lotto-lab ibm-login`.
- Generated output files and counts are ignored by `.gitignore`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

## License

MIT
