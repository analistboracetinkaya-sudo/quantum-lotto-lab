# KuponIQ Mobile UX Flow

Status: implemented in the public Flutter prototype.

## Core Navigation

The mobile app should use five bottom tabs, not ten separate screens.

| Tab | Purpose | Merged Screens |
| --- | --- | --- |
| Ana | Current lottery, visual quantum scene, key metrics, next action. | Welcome, dashboard |
| Loto | Select lottery and switch product context. | Lottery picker |
| Analiz | Understand whether the data is usable and whether IBM is ready. | Data health, randomness fingerprint, IBM QPU setup, job monitor |
| Kupon | Configure columns and see the generated portfolio in one place. | Coupon builder, result portfolio, backtest summary |
| Ayarlar | IBM token status and gateway connection only. | IBM token/settings |

## Why

- The user wants to play one flow, not manage ten tool panels.
- Data health, randomness audit, QPU state, and job status are one mental task: "Is analysis ready?"
- Coupon tuning and coupon result are one mental task: "What will I play?"
- The public prototype has no account layer; Ayarlar is only for IBM token and gateway state.

## UX Rules

- Bottom navigation must be fixed and visible.
- No horizontally scrolling navigation for primary actions.
- Expensive IBM actions must remain explicit.
- The first screen should show the selected lottery and next useful action.
- The app should work in demo mode, but gateway/IBM status must be visible.
