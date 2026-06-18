from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from quantum_lotto_lab.calibration import calibrated_randomness_fingerprint
from quantum_lotto_lab.data import load_draws
from quantum_lotto_lab.data_quality import validate_draw_history
from quantum_lotto_lab.ibm import run_profiled_sampling
from quantum_lotto_lab.lotteries import get_lottery
from quantum_lotto_lab.math_model import (
    backtest_summary,
    optimize_tickets_with_metadata,
    ticket_set_metrics,
)
from quantum_lotto_lab.quantum_profiles import resolve_quantum_profile
from quantum_lotto_lab.randomness import audit_pool_randomness, score_vector, walk_forward_models
from quantum_lotto_lab.tr_lotteries import tr_lottery_games


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "tr"
OUTPUT_DIR = ROOT / "outputs" / "mobile"

CSV_BY_SLUG = {
    "cilgin-sayisal-loto-tr": DATA_DIR / "cilgin_sayisal_loto_tr_10y.csv",
    "super-loto-tr": DATA_DIR / "super_loto_tr_10y.csv",
    "sans-topu-tr": DATA_DIR / "sans_topu_tr_10y.csv",
}

app = FastAPI(title="KuponIQ Quantum Gateway", version="0.1.0")


def _manifest() -> dict[str, Any]:
    path = DATA_DIR / "turkey_lottery_manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_slug_draws(slug: str):
    csv_path = CSV_BY_SLUG.get(slug)
    if csv_path is None or not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"No dated CSV is configured for {slug}.")
    return load_draws(get_lottery(slug), csv_path)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "kuponiq-gateway",
        "data_dir": str(DATA_DIR),
        "generated_at": date.today().isoformat(),
    }


@app.get("/lotteries")
def lotteries() -> dict[str, Any]:
    manifest = _manifest()
    manifest_games = manifest.get("games", {}) if isinstance(manifest, dict) else {}
    games = []
    for game in tr_lottery_games():
        item = game.as_dict()
        stats = manifest_games.get(game.slug, {})
        quality = stats.get("quality", {}) if isinstance(stats, dict) else {}
        item["rows"] = quality.get("rows", 0)
        item["excluded_rows"] = stats.get("excluded_rows", 0)
        item["dated_history_ready"] = game.slug in CSV_BY_SLUG
        games.append(item)
    return {"games": games}


@app.get("/lotteries/{slug}/data-health")
def data_health(slug: str) -> dict[str, Any]:
    if slug == "on-numara-tr":
        return {
            "slug": slug,
            "ready": False,
            "rows": 779,
            "issue": "Public archive is year/draw-number based, not fully dated.",
            "status": "coupon adapter ready; time-series audit needs dated rows",
        }
    draws = _load_slug_draws(slug)
    spec = get_lottery(slug)
    quality = validate_draw_history(draws, spec)
    return {
        "slug": slug,
        "ready": True,
        "rows": len(draws),
        "first_draw": draws[0].date.isoformat(),
        "last_draw": draws[-1].date.isoformat(),
        "quality": quality,
    }


@app.post("/audit")
def audit(payload: dict[str, Any]) -> dict[str, Any]:
    slug = str(payload.get("lottery_slug") or "super-loto-tr")
    null_trials = int(payload.get("null_trials") or 250)
    draws = _load_slug_draws(slug)
    spec = get_lottery(slug)
    audit_result = audit_pool_randomness(draws, spec.main, "main")
    fingerprint = calibrated_randomness_fingerprint(
        draws,
        spec.main,
        "main",
        null_trials=null_trials,
        seed=int(payload.get("seed") or 7),
    )
    walk = walk_forward_models(draws, spec, field="main", train_min=int(payload.get("train_min") or 120))
    return {
        "lottery_slug": slug,
        "draws": len(draws),
        "randomness_audit": audit_result,
        "randomness_fingerprint": fingerprint,
        "walk_forward": walk,
    }


@app.post("/portfolio")
def portfolio(payload: dict[str, Any]) -> dict[str, Any]:
    slug = str(payload.get("lottery_slug") or "super-loto-tr")
    columns = int(payload.get("columns") or 30)
    draws = _load_slug_draws(slug)
    spec = get_lottery(slug)
    walk = walk_forward_models(draws, spec, field="main", train_min=int(payload.get("train_min") or 120))
    scores = score_vector(draws, spec, "main", walk["best_model"])
    tickets, search = optimize_tickets_with_metadata(
        spec,
        draws,
        columns=columns,
        score_override=scores,
        seed=int(payload.get("seed") or 23),
        candidate_mode=str(payload.get("candidate_mode") or "sampled"),
        exact_top_k=int(payload.get("exact_top_k") or 0),
    )
    return {
        "lottery_slug": slug,
        "columns": columns,
        "selected_model": walk["best_model"],
        "tickets": [ticket.as_dict() for ticket in tickets],
        "ticket_set_metrics": ticket_set_metrics(tickets, spec.main),
        "backtest": backtest_summary(tickets, draws[-min(len(draws), 250) :]),
        "candidate_search": search,
    }


@app.get("/ibm/status")
def ibm_status() -> dict[str, Any]:
    return _ibm_status()


@app.post("/ibm/token")
def ibm_token(payload: dict[str, Any]) -> dict[str, Any]:
    token = str(payload.get("token") or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="IBM token is required.")
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        QiskitRuntimeService.save_account(
            channel="ibm_quantum_platform",
            token=token,
            overwrite=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"IBM token could not be saved: {exc}") from exc
    return _ibm_status()


def _ibm_status() -> dict[str, Any]:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService()
        backends = service.backends()
    except Exception as exc:
        return {
            "connected": False,
            "message": str(exc),
            "backends": [],
        }
    return {
        "connected": True,
        "backends": [
            {
                "name": backend.name,
                "num_qubits": int(getattr(backend, "num_qubits", 0)),
            }
            for backend in backends[:12]
        ],
    }


@app.post("/ibm/run")
def ibm_run(payload: dict[str, Any]) -> dict[str, Any]:
    slug = str(payload.get("lottery_slug") or "super-loto-tr")
    backend = str(payload.get("backend") or "ibm_kingston")
    profile_name = str(payload.get("profile") or "long")
    draws = _load_slug_draws(slug)
    spec = get_lottery(slug)
    scores = score_vector(draws, spec, "main", "ensemble").tolist()
    profile = resolve_quantum_profile(profile_name, int(payload.get("qubits") or 10_000))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_counts = OUTPUT_DIR / f"{slug}_{profile_name}_ibm_counts.json"
    _, job = run_profiled_sampling(
        backend_name=backend,
        qubits=int(payload.get("qubits") or profile["qubits"]),
        layers=int(payload.get("layers") or profile["layers"]),
        batch_circuits=int(payload.get("batch_circuits") or profile["batch_circuits"]),
        shots=int(payload.get("shots") or profile["shots"]),
        seed_weights=scores,
        output_counts=output_counts,
        repeat_jobs=int(payload.get("repeat_jobs") or profile["repeat_jobs"]),
        profile=profile_name,
    )
    return {
        "lottery_slug": slug,
        "backend": backend,
        "profile": profile_name,
        "job": job,
        "output_counts": str(output_counts),
    }
