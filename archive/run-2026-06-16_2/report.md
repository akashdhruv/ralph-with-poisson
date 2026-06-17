# Experiment Report — run-2026-06-16_2

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-16 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `Spec.toml`) |
| Mode | Fresh-session loop (max 30 iterations/loop, max 5 loops) |
| Loops completed | 1 of 5 |
| Total wall duration | 4m 26s |

*Second caching-enabled CodeScribe run, same day as `run-2026-06-16`. Confirms the caching result is repeatable.*

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 36,756 |
| Output tokens | 15,462 |
| Cache read tokens | 140,173 |
| Cache write tokens | 32,758 |
| Reasoning tokens | not reported separately |
| Total wall duration | 4m 26s |

*Billed input of 37k against 140k cache reads — the same caching profile as `run-2026-06-16`, and the fastest CodeScribe run recorded (4m 26s).*

## Result

All 8 tasks completed in a single loop. 4/4 tests pass.

```
tests/test_poisson.py::test_jacobi_manufactured PASSED
tests/test_poisson.py::test_cg_manufactured PASSED
tests/test_poisson.py::test_direct_manufactured PASSED
tests/test_poisson.py::test_neumann_basic PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `Grid` class, Neumann flags, and `apply_neumann()`
- [x] Jacobi iterative solver — `solvers.jacobi()` with L2 residual convergence
- [x] Conjugate gradient solver (numpy only) — `solvers.conjugate_gradient()` on the flattened interior
- [x] Manufactured solution test — all three solvers achieve L2 ≈ 1.1e-5 on 32×32
- [x] Direct solver — `solvers.direct()` builds the sparse Laplacian and solves with `scipy`
- [x] Neumann BC support — `Grid.neumann` dict + `apply_neumann()`; covered by `test_neumann_basic`
- [x] `demo.py` convergence plot — text-based log residual vs iteration chart for Jacobi and CG
- [x] Performance benchmark — wall-clock table for all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
Solver       Grid         Time (s)    Iters     Residual
--------------------------------------------------------
Jacobi       64x64         1.1326    17356    9.997e-07
CG           64x64         0.0001        1    6.332e-11
Direct       64x64         0.0531        1    7.609e-11
Jacobi       128x128       3.3630    20000    3.380e+00  (capped — did not converge)
CG           128x128       0.0003        1    4.706e-10
Direct       128x128       0.1376        1    5.957e-10
```

## Files Generated

```
generated-src/
  poisson/
    __init__.py
    grid.py
    solvers.py
    demo.py
  tests/
    test_poisson.py
```

## Notes

- Second caching-enabled run; billed input (37k) and cache reads (140k) mirror `run-2026-06-16`, showing the caching behaviour is stable across runs.
- Fastest CodeScribe run in the archive at 4m 26s, all 8 tasks in one loop.
- `demo.py` here renders a text-based (ASCII) convergence chart rather than saving a `convergence.png`.
- Jacobi on 128×128 is capped at 20,000 iterations and does not reach `tol`; CG and the direct solver converge immediately (CG in 1 iteration on the eigenmode RHS).
