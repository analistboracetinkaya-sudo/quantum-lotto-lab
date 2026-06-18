# KuponIQ Quantum Mobile Plan

## Product Goal

KuponIQ Quantum turns lottery draw history into a reproducible research workflow:

1. Select a Turkish lottery product and draw date.
2. Fetch or import draw history.
3. Validate data quality.
4. Analyze the type of randomness and measurable deviations.
5. Prepare an IBM Quantum sampling job when the user supplies their own token.
6. Convert the returned distribution into coupon recommendations.
7. Present coupons with responsible-play warnings and backtest metrics.

The app never presents recommendations as guaranteed winning numbers.

## Screen Flow

1. **Splash / Welcome** - App identity and short animated lottery-ball orbit.
2. **Ayarlar / IBM Connect** - IBM token entry only; tokens are not stored in the repository.
3. **Lottery Picker** - Çılgın Sayısal Loto, Süper Loto, Şans Topu, On Numara, Hızlı On, Milli Piyango.
4. **Data Sync** - Last 10-year archive status, source badges, quality warnings.
5. **Randomness Audit** - Fingerprint chart for frequency, gap, pair, triple, calendar, drift, runs.
6. **IBM Quantum Job** - Backend, qubits, layers, batch, shots, job ID, counts status.
7. **Coupon Builder** - Column count, risk balance, coverage constraints, overlap control.
8. **Coupon Portfolio** - Generated coupons, union coverage, reuse and overlap metrics.
9. **Backtest / Result** - 2+ and 3+ backtest rates versus random baseline.
10. **Ayarlar** - IBM token and gateway status only.

## Build Scope

- Flutter app scaffold under `app/`.
- Python data/model backend remains in `quantum_lotto_lab/`.
- Turkish lottery metadata lives in `quantum_lotto_lab/tr_lotteries.py`.
- Last-10-year data fetcher lives in `scripts/fetch_tr_lottery_data.py`.
- Mobile prototype uses local demo data and placeholders; production IBM execution should be proxied through a backend, not called directly from the phone.

## Security

- IBM API tokens are never committed.
- Public repo users run `quantum-lotto-lab ibm-login` or enter their own token in the app.
- Flutter prototype includes UI for token entry, but production storage should use platform secure storage.
- Generated IBM count files stay ignored by `.gitignore`.

## Turkish Lottery Coverage

- Çılgın Sayısal Loto: ready for dated archive ingestion.
- Süper Loto: ready for dated archive ingestion.
- Şans Topu: ready for dated archive ingestion.
- On Numara: raw public archive exists but LotoBil rows lack draw dates; coupon adapter is prepared separately from draw audit.
- Hızlı On: app adapter exists; 10-year archive does not exist because it is a new fast-draw product.
- Milli Piyango: separate serial-ticket draw product, not a number-pool lotto coupon.

## Implementation Order

1. Add product and data-source documentation.
2. Add Turkish lottery metadata.
3. Add data fetcher and generate current manifest/CSV files.
4. Add Flutter app shell and 10-screen prototype.
5. Keep IBM token handling API-safe.
6. Run Python and Flutter checks.
7. Commit and push to GitHub.
