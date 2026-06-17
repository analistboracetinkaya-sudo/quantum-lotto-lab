from quantum_lotto_lab.quantum_profiles import resolve_quantum_profile


def test_long_profile_is_not_short():
    profile = resolve_quantum_profile("long", backend_qubits=127)
    assert profile["qubits"] >= 96
    assert profile["layers"] >= 64
    assert profile["batch_circuits"] >= 12
    assert profile["shots"] >= 8192
    assert profile["repeat_jobs"] >= 2
