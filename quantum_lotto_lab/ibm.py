from __future__ import annotations

import getpass
from pathlib import Path


def save_ibm_account(channel: str = "ibm_quantum_platform") -> None:
    from qiskit_ibm_runtime import QiskitRuntimeService

    token = getpass.getpass("IBM Quantum API token: ").strip()
    if not token:
        raise SystemExit("No token entered.")
    QiskitRuntimeService.save_account(channel=channel, token=token, overwrite=True)
    print("IBM Quantum account saved locally by Qiskit. No token was written to this repository.")


def run_heavy_sampling(
    backend_name: str,
    qubits: int,
    layers: int,
    batch_circuits: int,
    shots: int,
    seed_weights: list[float],
    output_counts: Path | None = None,
) -> tuple[list[int], dict]:
    import math
    from qiskit import QuantumCircuit
    from qiskit.transpiler import generate_preset_pass_manager
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler

    service = QiskitRuntimeService()
    backend = service.backend(backend_name)
    qubits = min(int(qubits), int(backend.num_qubits))
    weights = list(seed_weights) or [1.0]

    circuits = []
    golden = (math.sqrt(5.0) - 1.0) / 2.0
    for batch in range(batch_circuits):
        qc = QuantumCircuit(qubits)
        for q in range(qubits):
            w = float(weights[q % len(weights)])
            qc.sx(q)
            qc.rz(2 * math.pi * ((q + 1) * golden + 0.037 * batch + 0.013 * w), q)
        for layer in range(layers):
            for q in range(qubits):
                w = float(weights[(q + layer) % len(weights)])
                qc.rz(2 * math.pi * math.sin((q + 1) * (layer + 1) * 0.017 + w), q)
                qc.sx(q)
                if (q + layer + batch) % 13 == 0:
                    qc.x(q)
            for q in range(layer % 2, qubits - 1, 2):
                qc.cz(q, q + 1)
        qc.measure_all()
        circuits.append(qc)

    pm = generate_preset_pass_manager(backend=backend, optimization_level=0)
    isa = [pm.run(qc) for qc in circuits]
    job = Sampler(backend).run(isa, shots=shots)
    print(f"IBM backend: {backend.name}")
    print(f"Job ID: {job.job_id()}")
    result = job.result()
    counts: dict[str, int] = {}
    for pub_result in result:
        for bitstring, count in pub_result.data.meas.get_counts().items():
            counts[str(bitstring)] = counts.get(str(bitstring), 0) + int(count)
    bits: list[int] = []
    for bitstring, count in sorted(counts.items(), key=lambda item: -item[1])[:128]:
        bits.extend(1 if ch == "1" else 0 for ch in bitstring[::-1])
    payload = {
        "backend": backend.name,
        "job_id": job.job_id(),
        "qubits": qubits,
        "layers": layers,
        "batch_circuits": batch_circuits,
        "shots_per_circuit": shots,
        "total_requested_shots": batch_circuits * shots,
        "counts": counts,
    }
    if output_counts:
        import json

        output_counts.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return bits, payload


def run_profiled_sampling(
    backend_name: str,
    qubits: int,
    layers: int,
    batch_circuits: int,
    shots: int,
    seed_weights: list[float],
    output_counts: Path | None = None,
    repeat_jobs: int = 1,
    profile: str = "custom",
) -> tuple[list[int], dict]:
    all_bits: list[int] = []
    jobs = []
    for repeat in range(max(1, int(repeat_jobs))):
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
    first = jobs[0] if jobs else {}
    return all_bits, {
        "profile": profile,
        "backend": first.get("backend", backend_name),
        "job_id": ",".join(job["job_id"] for job in jobs),
        "job_ids": [job["job_id"] for job in jobs],
        "qubits": first.get("qubits", qubits),
        "layers": layers,
        "batch_circuits": batch_circuits,
        "shots_per_circuit": shots,
        "repeat_jobs": repeat_jobs,
        "total_requested_shots": sum(job["total_requested_shots"] for job in jobs),
        "jobs": jobs,
    }
