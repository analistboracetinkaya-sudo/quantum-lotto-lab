from __future__ import annotations

import argparse
import json
import math
from datetime import date
from pathlib import Path

from .data import load_custom_spec, load_draws
from .ibm import run_heavy_sampling, save_ibm_account
from .lotteries import get_lottery, list_lotteries
from .math_model import backtest_summary, hit_distribution, make_tickets, number_scores
from .randomness import audit_pool_randomness, walk_forward_models


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
        seed_bits, quantum_job = run_heavy_sampling(
            backend_name=args.backend,
            qubits=args.qubits,
            layers=args.layers,
            batch_circuits=args.batch_circuits,
            shots=args.shots,
            seed_weights=weights,
            output_counts=output_counts,
        )

    tickets = make_tickets(spec, draws, columns=args.columns, seed_bits=seed_bits, seed=args.seed)
    history = backtest_summary(tickets, draws[-min(len(draws), args.backtest_draws) :])
    baseline = hit_distribution(spec.main.maximum - spec.main.minimum + 1, spec.main.pick, args.columns)
    jackpot_note = f"1 / {baseline['jackpot_one_in']:,}".replace(",", ".")

    payload = {
        "warning": "Research/entertainment only. Lottery outcomes are random; no guarantee is made.",
        "lottery": spec.name,
        "lottery_slug": spec.slug,
        "draw_date": target_date,
        "columns": args.columns,
        "tickets": [ticket.as_dict() for ticket in tickets],
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

    randomness = audit_pool_randomness(draws, spec.main, "main")
    walk = walk_forward_models(draws, spec, field="main", train_min=args.train_min)
    baseline = hit_distribution(spec.main.maximum - spec.main.minimum + 1, spec.main.pick, args.columns)

    seed_bits = None
    quantum_job = None
    if args.ibm:
        best_model = walk["best_model"]
        # Use the model verdict to choose the input weights. If the walk-forward
        # signal is weak, this still produces an honest experiment, not a claim.
        weights = number_scores(draws, spec.main, "main").tolist()
        output_counts = Path(args.output).with_suffix(".counts.json") if args.output else None
        seed_bits, quantum_job = run_heavy_sampling(
            backend_name=args.backend,
            qubits=args.qubits,
            layers=args.layers,
            batch_circuits=args.batch_circuits,
            shots=args.shots,
            seed_weights=weights,
            output_counts=output_counts,
        )

    tickets = make_tickets(spec, draws, columns=args.columns, seed_bits=seed_bits, seed=args.seed)
    ticket_backtest = backtest_summary(tickets, draws[-min(len(draws), args.backtest_draws) :])
    payload = {
        "warning": "Research/entertainment only. Lottery outcomes are random; no guarantee is made.",
        "right_question": "Is there measurable non-random structure, and does it survive out-of-sample validation?",
        "lottery": spec.name,
        "lottery_slug": spec.slug,
        "draw_date": target_date,
        "columns": args.columns,
        "randomness_audit": randomness,
        "walk_forward": walk,
        "tickets": [ticket.as_dict() for ticket in tickets],
        "ticket_backtest": ticket_backtest,
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
    walk = payload["walk_forward"]
    best = walk["models"][walk["best_model"]]
    uniform = walk["models"]["uniform"]
    rows = [
        f"# {payload['lottery']} - Randomness Audit",
        "",
        f"Draw date: `{payload['draw_date']}`",
        f"Question: {payload['right_question']}",
        "",
        "## Short Answer",
        "",
        f"- Measured structure strength: `{audit['verdict']['signal_strength']}`.",
        f"- Randomness-test interpretation: {audit['verdict']['plain']}",
        f"- Out-of-sample verdict: {walk['verdict']['plain']}",
        f"- Best walk-forward model: `{walk['best_model']}`.",
        "",
        "## Evidence",
        "",
        f"- Draws loaded: `{payload['source']['draws_loaded']}` from `{payload['source']['first_draw']}` to `{payload['source']['last_draw']}`.",
        f"- Frequency max |z|: `{audit['frequency']['max_abs_z']:.2f}`.",
        f"- Top pair lift: `{audit['pair_lift']['max_lift']:.2f}`.",
        f"- Best model mean hits: `{best['mean_hits']:.3f}` vs uniform `{uniform['mean_hits']:.3f}`.",
        f"- Best model 2+ rate: `{best['any_2_plus'] * 100:.2f}%` vs uniform `{uniform['any_2_plus'] * 100:.2f}%`.",
        f"- Best model 3+ rate: `{best['any_3_plus'] * 100:.2f}%` vs uniform `{uniform['any_3_plus'] * 100:.2f}%`.",
        "",
        "## What This Means",
        "",
        "If a signal appears in the randomness audit but fails walk-forward validation, it is probably just historical noise.",
        "If it also improves out-of-sample metrics, the system may use it as a weak weighting signal. It is still not a guarantee.",
        "",
        "## Generated Tickets",
        "",
    ]
    for idx, ticket in enumerate(payload["tickets"], start=1):
        bonus = f" | bonus {ticket['bonus']}" if ticket["bonus"] else ""
        rows.append(f"{idx:02d}. main {ticket['main']}{bonus}")
    rows.extend(
        [
            "",
            "## Ticket Set Backtest",
            "",
            f"- Best-main average: `{payload['ticket_backtest']['best_main_mean']:.2f}`.",
            f"- 2+ rate: `{payload['ticket_backtest']['any_2_plus'] * 100:.2f}%`.",
            f"- 3+ rate: `{payload['ticket_backtest']['any_3_plus'] * 100:.2f}%`.",
            f"- Theoretical main jackpot chance: `{payload['theoretical']['main_jackpot_one_in']}`.",
        ]
    )
    if payload.get("ibm_quantum"):
        q = payload["ibm_quantum"]
        rows.extend(
            [
                "",
                "## IBM Quantum Layer",
                "",
                f"- Backend: `{q['backend']}`",
                f"- Job id: `{q['job_id']}`",
                f"- Qubits/layers/batch/shots: `{q['qubits']}` / `{q['layers']}` / `{q['batch_circuits']}` / `{q['shots_per_circuit']}`",
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
    if history:
        rows.extend(
            [
                f"- Historical best-main average on the backtest window: `{history['best_main_mean']:.2f}`.",
                f"- Historical 2+ rate on the generated set: `{history['any_2_plus'] * 100:.2f}%`.",
                f"- Historical 3+ rate on the generated set: `{history['any_3_plus'] * 100:.2f}%`.",
            ]
        )
    if payload.get("ibm_quantum"):
        q = payload["ibm_quantum"]
        rows.extend(
            [
                "",
                "## IBM Quantum job",
                "",
                f"- Backend: `{q['backend']}`",
                f"- Job id: `{q['job_id']}`",
                f"- Qubits/layers/batch/shots: `{q['qubits']}` / `{q['layers']}` / `{q['batch_circuits']}` / `{q['shots_per_circuit']}`",
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

    audit = sub.add_parser("audit", help="Test randomness structure, run walk-forward validation, then generate tickets.")
    audit.add_argument("--lottery", help="Built-in lottery slug. Run `quantum-lotto-lab list`.")
    audit.add_argument("--spec", help="Custom lottery JSON spec.")
    audit.add_argument("--date", help="Draw date YYYY-MM-DD.")
    audit.add_argument("--csv", help="Historical draw CSV. Recommended for reproducible runs.")
    audit.add_argument("--columns", type=int, default=30)
    audit.add_argument("--train-min", type=int, default=80)
    audit.add_argument("--backtest-draws", type=int, default=157)
    audit.add_argument("--seed", type=int, default=20260623)
    audit.add_argument("--ibm", action="store_true", help="Add a real IBM Quantum sampling layer after audit.")
    audit.add_argument("--backend", default="ibm_kingston")
    audit.add_argument("--qubits", type=int, default=100)
    audit.add_argument("--layers", type=int, default=32)
    audit.add_argument("--batch-circuits", type=int, default=4)
    audit.add_argument("--shots", type=int, default=4096)
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
    predict.add_argument("--qubits", type=int, default=100)
    predict.add_argument("--layers", type=int, default=32)
    predict.add_argument("--batch-circuits", type=int, default=4)
    predict.add_argument("--shots", type=int, default=4096)
    predict.add_argument("--output", default="outputs/prediction.json")
    predict.set_defaults(func=cmd_predict)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
