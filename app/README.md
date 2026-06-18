# KuponIQ Quantum App

Flutter prototype for the Quantum Lotto Lab workflow.

## Current Prototype Screens

1. Welcome
2. Login and IBM token entry
3. Turkish lottery picker
4. Data sync status
5. Randomness audit
6. IBM Quantum job status
7. Coupon builder
8. Coupon portfolio
9. Backtest summary
10. Profile and settings

## Token Handling

The app does not hard-code IBM credentials. The prototype shows the UX for entering a token. A production build should store the token with platform secure storage or call a backend that owns the IBM runtime session.

## Run

```bash
cd app
flutter run
```

## Validate

```bash
cd app
dart format lib test
flutter analyze
flutter test
```
