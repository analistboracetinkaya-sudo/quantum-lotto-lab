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
    profile["profile"] = name
    profile["requested_qubits"] = profile["qubits"]
    profile["qubits"] = min(profile["qubits"], int(backend_qubits))
    profile["total_requested_shots"] = profile["shots"] * profile["batch_circuits"] * profile["repeat_jobs"]
    return profile
