# Life OS · Performance Visual Budgets

## Targets (mid-tier device)

| Metric | Budget |
|---|---|
| Frame time (UI scroll) | <16ms sustained |
| Jank frames | <2% of session |
| Simultaneous infinite animations | ≤2 visible |
| Full-screen blur | Prohibited |
| Shader surfaces | ≤1 per screen without fallback |

## Recomposition

- Stable list keys
- `remember` derived state
- Avoid animating large subtrees

## Battery

- Pause animations off-screen
- Reduce effects in battery saver

## Measurement

- JankStats when integrated
- Macrobenchmark for critical paths
- Compose Layout Inspector for recomposition counts

## Fallback

Every GPU-heavy effect needs static/lightweight fallback for low-end + Reduce Motion
