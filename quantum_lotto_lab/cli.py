from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .calibration import calibrated_randomness_fingerprint
from .data import load_custom_spec, load_draws
from .data_quality import validate_draw_history
from .ibm import run_profiled_sampling, save_ibm_account
from .lotteries import get_lottery, list_lotteries
from .math_model import (
    backtest_summary,
    hit_distribution,
    number_scores,
    optimize_tickets,
    optimize_tickets_with_metadata,
    ticket_set_metrics,
)
from .randomness import audit_pool_randomness, score_vector, walk_forward_models
from .quantum_profiles import resolve_quantum_profile
from .validation import nested_ticket_backtest


def prompt(value: str | None, label: str) -> str:
    if value:
        return value
    answer = input(f"{label}: ").strip()
    if not answer:
        raise SystemExit(f"{label} is required.")
    return answer


def cmd_list(_: argparse.Namespace) -> None:
    for spec in list_lotteries():
        bonus = f" + {spec.bonus.pick}/{spec.bonus.maximum}" if spec.bonus else ""
        print(f"{spec.slug:16} {spec.name:28} {spec.main.pick}/{spec.main.maximum}{bonus}  {spec.region}")


def cmd_ibm_login(args: argparse.Namespace) -> None:
    save_ibm_account(args.channel)


def cmd_predict(args: argparse.Namespace) -> None:
    spec = load_custom_spec(args.spec) if args.spec else get_lottery(prompt(args.lottery, "Which lottery"))
    target_date = prompt(args.date, "Draw date YYYY-MM-DD")
    try:
        date.fromisoformat(target_date)
    except ValueError as exc:
        raise SystemExit("--date must be YYYY-MM-DD") from exc

    draws = load_draws(spec, args.csv)
    if len(draws) < 30:
        raise SystemExit(f"Need at least 30 historical draws. Loaded {len(draws)}.")

    main_scores = number_scores(draws, spec.main, "main")
    seed_bits: list[int] | None = None
    quantum_job = None
    if args.ibm:
        weights = main_scores.tolist()
        output_counts = Path(args.output).with_suffix(".counts.json") if args.output else None
        profile = resolve_quantum_profile(args.quantum_profile, args.qubits or 10_000)
        seed_bits, quantum_job = run_profiled_sampling(
            backend_name=args.backend,
            qubits=args.qubits or profile["qubits"],
            layers=args.layers or profile["layers"],
            batch_circuits=args.batch_circuits or profile["batch_circuits"],
            shots=args.shots or profile["shots"],
            seed_weights=weights,
            output_counts=output_counts,
            repeat_jobs=args.repeat_jobs or profile["repeat_jobs"],
            profile=args.quantum_profile,
        )

    tickets = optimize_tickets(spec, draws, columns=args.columns, seed_bits=seed_bits, seed=args.seed)
    history = backtest_summary(tickets, draws[-min(len(draws), args.backtest_draws) :])
    set_metrics = ticket_set_metrics(tickets, spec.main)
    baseline = hit_distribution(spec.main.maximum - spec.main.minimum + 1, spec.main.pick, args.columns)
    jackpot_note = f"1 / {baseline['jackpot_one_in']:,}".replace(",", ".")

    payload = {
        "warning": "Research/entertainment only. Lottery outcomes are random; no guarantee is made.",
        "lottery": spec.name,
        "lottery_slug": spec.slug,
        "draw_date": target_date,
        "columns": args.columns,
        "tickets": [ticket.as_dict() for ticket in tickets],
        "ticket_set_metrics": set_metrics,
        "history": history,
        "theoretical": {
            "main_jackpot_approx": baseline["jackpot_approx"],
            "main_jackpot_one_in": jackpot_note,
            "random_any_2_plus": baseline["any_2_plus"],
            "random_any_3_plus": baseline["any_3_plus"],
        },
        "source": {
            "draws_loaded": len(draws),
            "first_draw": str(draws[0].date),
            "last_draw": str(draws[-1].date),
            "note": spec.source_note,
        },
        "ibm_quantum": quantum_job,
    }

    text = human_report(payload)
    print(text)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out.with_suffix(".md").write_text(text, encoding="utf-8")
        print(f"\nWrote {out}")
        print(f"Wrote {out.with_suffix('.md')}")


def cmd_audit(args: argparse.Namespace) -> None:
    spec = load_custom_spec(args.spec) if args.spec else get_lottery(prompt(args.lottery, "Which lottery"))
    target_date = prompt(args.date, "Draw date YYYY-MM-DD")
    try:
        date.fromisoformat(target_date)
    except ValueError as exc:
        raise SystemExit("--date must be YYYY-MM-DD") from exc

    draws = load_draws(spec, args.csv)
    if len(draws) < 30:
        raise SystemExit(f"Need at least 30 historical draws. Loaded {len(draws)}.")

    quality = validate_draw_history(draws, spec)
    columns = 1 if args.target == "single6" else args.columns
    null_trials = args.null_trials if args.null_trials is not None else (2000 if args.deep_calibration else 500)
    randomness = audit_pool_randomness(draws, spec.main, "main")
    fingerprint = calibrated_randomness_fingerprint(
        draws,
        spec.main,
        "main",
        null_trials=null_trials,
        seed=args.seed,
    )
    walk = walk_forward_models(draws, spec, field="main", train_min=args.train_min)
    baseline = hit_distribution(spec.main.maximum - spec.main.minimum + 1, spec.main.pick, columns)

    best_model_scores = score_vector(draws, spec, "main", walk["best_model"])
    seed_bits = None
    quantum_job = None
    if args.ibm:
        # Use the validated model as IBM input weights. If the walk-forward
        # signal is weak, this still produces an honest experiment, not a claim.
        weights = best_model_scores.tolist()
        output_counts = Path(args.output).with_suffix(".counts.json") if args.output else None
        profile = resolve_quantum_profile(args.quantum_profile, args.qubits or 10_000)
        seed_bits, quantum_job = run_profiled_sampling(
            backend_name=args.backend,
            qubits=args.qubits or profile["qubits"],
            layers=args.layers or profile["layers"],
            batch_circuits=args.batch_circuits or profile["batch_circuits"],
            shots=args.shots or profile["shots"],
            seed_weights=weights,
            output_counts=output_counts,
            repeat_jobs=args.repeat_jobs or profile["repeat_jobs"],
            profile=args.quantum_profile,
        )

    tickets, search_report = optimize_tickets_with_metadata(
        spec,
        draws,
        columns=columns,
        seed_bits=seed_bits,
        seed=args.seed,
        score_override=best_model_scores,
        candidate_mode=args.candidate_mode,
        exact_top_k=args.exact_top_k,
        max_exact_combinations=args.max_exact_combinations,
    )
    ticket_backtest = backtest_summary(tickets, draws[-min(len(draws), args.backtest_draws) :])
    nested_backtest = nested_ticket_backtest(
        spec,
        draws,
        columns=columns,
        train_min=args.train_min,
        seed=args.seed,
        candidate_pool=args.nested_candidate_pool,
        max_test_draws=args.nested_test_draws,
    )
    set_metrics = ticket_set_metrics(tickets, spec.main)
    payload = {
        "warning": "Research/entertainment only. Lottery outcomes are random; no guarantee is made.",
        "right_question": "Is there measurable non-random structure, and does it survive out-of-sample validation?",
        "lottery": spec.name,
        "lottery_slug": spec.slug,
        "draw_date": target_date,
        "target": args.target,
        "target_plain": "single highest-ranked 6/6 column"
        if args.target == "single6"
        else f"{columns}-column diversified 6/6 portfolio",
        "columns": columns,
        "randomness_audit": randomness,
        "randomness_fingerprint": fingerprint,
        "calibration": fingerprint.get("calibration"),
        "data_quality": quality,
        "null_trials": null_trials,
        "walk_forward": walk,
        "selected_generation_model": walk["best_model"],
        "candidate_search": search_report,
        "tickets": [ticket.as_dict() for ticket in tickets],
        "ticket_set_metrics": set_metrics,
        "ticket_backtest": ticket_backtest,
        "nested_ticket_backtest": nested_backtest,
        "theoretical": {
            "main_jackpot_approx": baseline["jackpot_approx"],
            "main_jackpot_one_in": f"1 / {baseline['jackpot_one_in']:,}".replace(",", "."),
            "random_any_2_plus": baseline["any_2_plus"],
            "random_any_3_plus": baseline["any_3_plus"],
        },
        "source": {
            "draws_loaded": len(draws),
            "first_draw": str(draws[0].date),
            "last_draw": str(draws[-1].date),
            "note": spec.source_note,
        },
        "ibm_quantum": quantum_job,
    }
    text = audit_report(payload)
    print(text)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        out.with_suffix(".md").write_text(text, encoding="utf-8")
        print(f"\nWrote {out}")
        print(f"Wrote {out.with_suffix('.md')}")


def audit_report(payload: dict) -> str:
    audit = payload["randomness_audit"]
    fingerprint = payload["randomness_fingerprint"]
    walk = payload["walk_forward"]
    best = walk["models"][walk["best_model"]]
    uniform = walk["models"]["uniform"]
    calibration = fingerprint.get("calibration") or {}
    candidate_search = payload.get("candidate_search") or {}
    nested = payload.get("nested_ticket_backtest") or {}
    quality = payload.get("data_quality") or {}
    rows = [
        f"# {payload['lottery']} - Randomness Audit",
        "",
        f"Draw date: `{payload['draw_date']}`",
        f"Question: {payload['right_question']}",
        "",
        "## Short Answer",
        "",
        f"- Measured structure strength: `{audit['verdict']['signal_strength']}`.",
        f"- Randomness fingerprint: `{', '.join(fingerprint['randomness_type']['dominant_types'])}`.",
        f"- Randomness-test interpretation: {audit['verdict']['plain']}",
        f"- Out-of-sample verdict: {walk['verdict']['plain']}",
        f"- Best walk-forward model: `{walk['best_model']}`.",
        f"- Target: `{payload['target_plain']}`.",
        "",
        "## Evidence",
        "",
        f"- Draws loaded: `{payload['source']['draws_loaded']}` from `{payload['source']['first_draw']}` to `{payload['source']['last_draw']}`.",
        f"- Data quality usable: `{quality.get('usable', True)}`.",
        f"- Duplicate draw dates: `{len(quality.get('duplicate_dates', []))}`.",
        f"- Range/size/duplicate-number errors: `{len(quality.get('range_errors', []))}` / `{len(quality.get('size_errors', []))}` / `{len(quality.get('duplicate_number_errors', []))}`.",
        f"- Frequency max |z|: `{audit['frequency']['max_abs_z']:.2f}`.",
        f"- Normalized entropy: `{fingerprint['entropy']['normalized_entropy']:.4f}`.",
        f"- Top pair lift: `{audit['pair_lift']['max_lift']:.2f}`.",
        f"- Top triple lift: `{fingerprint['triple_lift']['max_lift']:.2f}`.",
        f"- Serial lag max delta: `{fingerprint['serial_dependence']['max_abs_lift_delta']:.2f}`.",
        f"- Distribution drift JS: `{fingerprint['drift']['js_divergence']:.4f}`.",
        f"- Best model mean hits: `{best['mean_hits']:.3f}` vs uniform `{uniform['mean_hits']:.3f}`.",
        f"- Best model 2+ rate: `{best['any_2_plus'] * 100:.2f}%` vs uniform `{uniform['any_2_plus'] * 100:.2f}%`.",
        f"- Best model 3+ rate: `{best['any_3_plus'] * 100:.2f}%` vs uniform `{uniform['any_3_plus'] * 100:.2f}%`.",
    ]
    if calibration:
        rows.extend(
            [
                f"- Calibration null trials: `{payload['null_trials']}`.",
                f"- Frequency chi-square calibrated p: `{calibration['frequency_chi_square']['empirical_p']:.4f}`.",
                f"- Pair max-lift calibrated p: `{calibration['pair_max_lift']['empirical_p']:.4f}`.",
                f"- Triple max-lift calibrated p: `{calibration['triple_max_lift']['empirical_p']:.4f}`.",
                f"- Temporal lag calibrated p: `{calibration['lag_max_delta']['empirical_p']:.4f}`.",
                f"- Drift JS calibrated p: `{calibration['drift_js']['empirical_p']:.4f}`.",
                f"- Runs max-z calibrated p: `{calibration['runs_max_abs_z']['empirical_p']:.4f}`.",
                f"- Gap anomaly calibrated p: `{calibration['gap_max_abs_lift']['empirical_p']:.4f}`.",
                f"- Calendar effect calibrated p: `{calibration['calendar_max_js']['empirical_p']:.4f}`.",
            ]
        )
    if candidate_search:
        rows.extend(
            [
                f"- Candidate mode: `{candidate_search['candidate_mode']}`.",
                f"- Exact search used: `{candidate_search['exact_used']}`.",
                f"- Total combination space: `{candidate_search['total_combinations']}`.",
                f"- Evaluated combinations: `{candidate_search['evaluated_combinations']}`.",
                f"- Candidate count used by optimizer: `{candidate_search['candidate_count']}`.",
            ]
        )
    rows.extend(
        [
            "",
            "## What This Means",
            "",
            "If a signal appears before calibration but fails calibrated null testing, it is probably random noise.",
            "If a calibrated signal appears but fails walk-forward validation, it is probably not reusable.",
            "If it also improves out-of-sample metrics, the system may use it as a weak weighting signal. It is still not a guarantee.",
            f"Plain fingerprint summary: {fingerprint['plain_language']['summary']}",
            "",
            "## Generated Tickets",
            "",
        ]
    )
    for idx, ticket in enumerate(payload["tickets"], start=1):
        bonus = f" | bonus {ticket['bonus']}" if ticket["bonus"] else ""
        rows.append(f"{idx:02d}. main {ticket['main']}{bonus}")
    rows.extend(
        [
            "",
            "## Ticket Set Historical Fit",
            "",
            f"- Union coverage: `{payload['ticket_set_metrics']['union_size']}/{payload['ticket_set_metrics']['pool_size']}`.",
            f"- Max pairwise overlap: `{payload['ticket_set_metrics']['max_pairwise_overlap']}`.",
            f"- Max number reuse: `{payload['ticket_set_metrics']['max_number_reuse']}`.",
            f"- Pair/triple coverage count: `{payload['ticket_set_metrics']['pair_coverage_count']}` / `{payload['ticket_set_metrics']['triple_coverage_count']}`.",
            f"- Best-main average: `{payload['ticket_backtest']['best_main_mean']:.2f}`.",
            f"- 2+ rate: `{payload['ticket_backtest']['any_2_plus'] * 100:.2f}%`.",
            f"- 3+ rate: `{payload['ticket_backtest']['any_3_plus'] * 100:.2f}%`.",
            f"- Theoretical main jackpot chance: `{payload['theoretical']['main_jackpot_one_in']}`.",
        ]
    )
    if nested:
        rows.extend(
            [
                "",
                "## Nested Predictive Validation",
                "",
                f"- Leakage guard: `{nested['leakage_guard']}`.",
                f"- Test draws: `{nested['test_draws']}`.",
                f"- Best-main average: `{nested.get('best_main_mean', 0.0):.2f}`.",
                f"- 2+ rate: `{nested.get('any_2_plus', 0.0) * 100:.2f}%`.",
                f"- 3+ rate: `{nested.get('any_3_plus', 0.0) * 100:.2f}%`.",
                f"- Selected models: `{nested.get('selected_models', {})}`.",
            ]
        )
    if payload.get("ibm_quantum"):
        q = payload["ibm_quantum"]
        rows.extend(
            [
                "",
                "## IBM Quantum Layer",
                "",
                f"- Profile: `{q.get('profile', 'custom')}`",
                f"- Backend: `{q['backend']}`",
                f"- Job id: `{q['job_id']}`",
                f"- Qubits/layers/batch/shots: `{q['qubits']}` / `{q['layers']}` / `{q['batch_circuits']}` / `{q['shots_per_circuit']}`",
                f"- Repeat jobs: `{q.get('repeat_jobs', 1)}`",
                f"- Total requested shots: `{q.get('total_requested_shots', q['batch_circuits'] * q['shots_per_circuit'])}`",
                "IBM does sampling. It does not understand the lottery by itself; the audit/backtest layer is the reasoning layer.",
            ]
        )
    rows.extend(
        [
            "",
            "## Plain Warning",
            "",
            "This is a statistical audit and risk-optimized ticket generator. It does not prove that lottery draws are predictable.",
        ]
    )
    return "\n".join(rows) + "\n"


def human_report(payload: dict) -> str:
    rows = [
        f"# {payload['lottery']} - Quantum Lotto Lab",
        "",
        f"Draw date: `{payload['draw_date']}`",
        f"Columns: `{payload['columns']}`",
        "",
        "## Human-readable expectation",
        "",
        f"- Main jackpot chance for this ticket set is roughly `{payload['theoretical']['main_jackpot_one_in']}`.",
        f"- Random baseline for at least one 2+ main hit: `{payload['theoretical']['random_any_2_plus'] * 100:.2f}%`.",
        f"- Random baseline for at least one 3+ main hit: `{payload['theoretical']['random_any_3_plus'] * 100:.2f}%`.",
    ]
    history = payload.get("history") or {}
    set_metrics = payload.get("ticket_set_metrics") or {}
    if history:
        rows.extend(
            [
                f"- Historical best-main average on the backtest window: `{history['best_main_mean']:.2f}`.",
                f"- Historical 2+ rate on the generated set: `{history['any_2_plus'] * 100:.2f}%`.",
                f"- Historical 3+ rate on the generated set: `{history['any_3_plus'] * 100:.2f}%`.",
            ]
        )
    if set_metrics:
        rows.extend(
            [
                f"- Union coverage: `{set_metrics['union_size']}/{set_metrics['pool_size']}`.",
                f"- Max pairwise overlap: `{set_metrics['max_pairwise_overlap']}`.",
            ]
        )
    if payload.get("ibm_quantum"):
        q = payload["ibm_quantum"]
        rows.extend(
            [
                "",
                "## IBM Quantum job",
                "",
                f"- Profile: `{q.get('profile', 'custom')}`",
                f"- Backend: `{q['backend']}`",
                f"- Job id: `{q['job_id']}`",
                f"- Qubits/layers/batch/shots: `{q['qubits']}` / `{q['layers']}` / `{q['batch_circuits']}` / `{q['shots_per_circuit']}`",
                f"- Repeat jobs: `{q.get('repeat_jobs', 1)}`",
                f"- Total requested shots: `{q.get('total_requested_shots', q['batch_circuits'] * q['shots_per_circuit'])}`",
                f"- Exact state-space size: about `2^{q['qubits']}`.",
            ]
        )
    rows.extend(["", "## Tickets", ""])
    for idx, ticket in enumerate(payload["tickets"], start=1):
        bonus = f" | bonus {ticket['bonus']}" if ticket["bonus"] else ""
        rows.append(f"{idx:02d}. main {ticket['main']}{bonus}")
    rows.extend(
        [
            "",
            "## Plain warning",
            "",
            "This is mathematical risk optimization plus optional IBM Quantum sampling. It is not a lottery oracle and it does not guarantee winnings.",
        ]
    )
    return "\n".join(rows) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantum-lotto-lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_parser = sub.add_parser("list", help="List built-in lottery specs.")
    list_parser.set_defaults(func=cmd_list)

    login_parser = sub.add_parser("ibm-login", help="Save a local IBM Quantum token using Qiskit.")
    login_parser.add_argument("--channel", default="ibm_quantum_platform")
    login_parser.set_defaults(func=cmd_ibm_login)

    audit = sub.add_parser(
        "audit", help="Test randomness structure, run walk-forward validation, then generate tickets."
    )
    audit.add_argument("--lottery", help="Built-in lottery slug. Run `quantum-lotto-lab list`.")
    audit.add_argument("--spec", help="Custom lottery JSON spec.")
    audit.add_argument("--date", help="Draw date YYYY-MM-DD.")
    audit.add_argument("--csv", help="Historical draw CSV. Recommended for reproducible runs.")
    audit.add_argument("--columns", type=int, default=30)
    audit.add_argument("--target", choices=["portfolio30", "single6"], default="portfolio30")
    audit.add_argument("--train-min", type=int, default=80)
    audit.add_argument("--backtest-draws", type=int, default=157)
    audit.add_argument("--nested-test-draws", type=int, default=52)
    audit.add_argument("--nested-candidate-pool", type=int, default=800)
    audit.add_argument(
        "--deep-calibration", action="store_true", help="Use more null simulations for randomness calibration."
    )
    audit.add_argument("--null-trials", type=int, default=None, help="Override null simulation count.")
    audit.add_argument("--candidate-mode", choices=["sampled", "exact"], default="sampled")
    audit.add_argument("--exact-top-k", type=int, default=10000)
    audit.add_argument("--max-exact-combinations", type=int, default=60000000)
    audit.add_argument("--seed", type=int, default=20260623)
    audit.add_argument("--ibm", action="store_true", help="Add a real IBM Quantum sampling layer after audit.")
    audit.add_argument("--backend", default="ibm_kingston")
    audit.add_argument("--quantum-profile", choices=["standard", "long", "deep", "extreme"], default="long")
    audit.add_argument("--repeat-jobs", type=int, default=None)
    audit.add_argument("--qubits", type=int, default=None)
    audit.add_argument("--layers", type=int, default=None)
    audit.add_argument("--batch-circuits", type=int, default=None)
    audit.add_argument("--shots", type=int, default=None)
    audit.add_argument("--output", default="outputs/audit.json")
    audit.set_defaults(func=cmd_audit)

    predict = sub.add_parser("predict", help="Generate a lottery ticket set.")
    predict.add_argument("--lottery", help="Built-in lottery slug. Run `quantum-lotto-lab list`.")
    predict.add_argument("--spec", help="Custom lottery JSON spec.")
    predict.add_argument("--date", help="Draw date YYYY-MM-DD.")
    predict.add_argument("--csv", help="Historical draw CSV. Recommended for reproducible runs.")
    predict.add_argument("--columns", type=int, default=30)
    predict.add_argument("--backtest-draws", type=int, default=157)
    predict.add_argument("--seed", type=int, default=20260623)
    predict.add_argument("--ibm", action="store_true", help="Run a real IBM Quantum job.")
    predict.add_argument("--backend", default="ibm_kingston")
    predict.add_argument("--quantum-profile", choices=["standard", "long", "deep", "extreme"], default="long")
    predict.add_argument("--repeat-jobs", type=int, default=None)
    predict.add_argument("--qubits", type=int, default=None)
    predict.add_argument("--layers", type=int, default=None)
    predict.add_argument("--batch-circuits", type=int, default=None)
    predict.add_argument("--shots", type=int, default=None)
    predict.add_argument("--output", default="outputs/prediction.json")
    predict.set_defaults(func=cmd_predict)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
