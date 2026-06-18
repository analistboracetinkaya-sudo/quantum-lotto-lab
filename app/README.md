# KuponIQ Quantum App

Flutter mobile/web app for the Quantum Lotto Lab workflow.

## Current Prototype Screens

1. Ana
2. Loto
3. Analiz
4. Kupon
5. Ayarlar

## Token Handling

The app does not hard-code IBM credentials. The only account-related UI is the
IBM Quantum token section under Ayarlar. IBM execution is handled by the local
Python gateway, which saves and reads the user's local Qiskit account. The
token is never stored in this repository.

## Run With Demo Data

```bash
cd app
flutter run
```

## Run With Local Quantum Gateway

From the repository root:

```bash
python -m pip install -e ".[server]"
uvicorn server.kuponiq_gateway.app:app --host 127.0.0.1 --port 8787
```

Then run the app:

```bash
cd app
flutter run -d chrome --web-port 8788
```

The app calls `http://127.0.0.1:8787` and falls back to demo mode if the
gateway is not running.

## Validate

```bash
cd app
dart format lib test
flutter analyze
flutter test
```
