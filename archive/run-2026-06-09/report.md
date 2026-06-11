# Experiment Report — run-2026-06-09

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-09 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop specification.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `specification.toml`) |
| Mode | Fresh-session loop (max 12 iterations/loop, max 5 loops) |
| Loops completed | 4 of 5 |
| Total wall duration | 11m 52s |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | not recorded (cumulative tracking not available for this run) |
| Output tokens | not recorded |
| Cache read tokens | 0 |
| Cache write tokens | 0 |
| Last-loop input tokens | 74,514 |
| Last-loop output tokens | 2,176 |
| Total wall duration | 11m 52s |

*Note: execution.toml captures only the last loop (loop 4 — cleanup). Cumulative token totals were not tracked for this run.*

## Result

All 8 tasks completed. 5/5 tests pass.

```
tests/test_poisson.py::test_jacobi_manufactured PASSED
tests/test_poisson.py::test_cg_manufactured PASSED
tests/test_poisson.py::test_direct_manufactured PASSED
tests/test_poisson.py::test_grid_shape PASSED
tests/test_poisson.py::test_dirichlet_boundary_zero PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`, `rhs`, coordinate arrays, `apply_neumann()`
- [x] Jacobi iterative solver — `jacobi_solve()` in `solvers.py`
- [x] Conjugate gradient solver (numpy only) — `cg_solve()` in `solvers.py`
- [x] Manufactured solution test — L2 error < 1e-4 on 64×64 for all three solvers
- [x] Direct solver — sparse Laplacian assembly + `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — `apply_neumann()` on Grid, all solvers accept `neumann_edges`
- [x] `demo.py` convergence plot — prints residual vs iteration for Jacobi and CG
- [x] Performance benchmark — all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
--- Grid 64x64 ---
Solver       Iters      Residual    Time (s)
Jacobi       17356    9.9970e-07      1.12
CG               1    6.3322e-11      0.0002
Direct           1    7.6091e-11      0.050

--- Grid 128x128 ---
Solver       Iters      Residual    Time (s)
Jacobi       20000    3.3797e+00      3.16   (capped — did not converge)
CG               1    4.7059e-10      0.009
Direct           1    5.9575e-10      0.121
```

Note: Jacobi caps at 20,000 iterations on 128×128 (residual 3.38) — this implementation used a lower iter cap than later runs.

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

- Earliest run; used `specification.toml` (pre-dates `Spec.toml` reformatting).
- Loop 4 was a cleanup pass: the agent removed extra files (`_check.py`, `verify_convergence.py`, `tests/__init__.py`) that violated the spec module layout, using a helper `_cleanup.py` script due to `rm` being blocked.
- The test suite uses a 64×64 grid to stay below the second-order FD discretisation error floor (~3.9e-4 on 32×32).
- Jacobi's 20k iteration cap (vs 50k in later runs) caused non-convergence at 128×128.
