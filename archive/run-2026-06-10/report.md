# Experiment Report — run-2026-06-10

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-10 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `Spec.toml`) |
| Mode | Fresh-session loop (max 12 iterations/loop, max 5 loops) |
| Loops completed | 5 of 5 |
| Total wall duration | 16m 45s |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | not recorded (cumulative tracking not available for this run) |
| Output tokens | not recorded |
| Cache read tokens | 0 |
| Cache write tokens | 0 |
| Last-loop input tokens | 100,488 |
| Last-loop output tokens | 2,161 |
| Total wall duration | 16m 45s |

*Note: execution.toml captures only the last loop (loop 5 — cleanup). Cumulative token totals were not tracked for this run.*

## Result

All 8 tasks completed. 6/6 tests pass.

```
poisson/tests/test_poisson.py::test_grid_basic PASSED
poisson/tests/test_poisson.py::test_jacobi_manufactured_32 PASSED
poisson/tests/test_poisson.py::test_cg_manufactured_32 PASSED
poisson/tests/test_poisson.py::test_direct_manufactured_32 PASSED
poisson/tests/test_poisson.py::test_direct_manufactured_64 PASSED
poisson/tests/test_poisson.py::test_convergence_order PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`, `f`, meshgrid coordinate helpers
- [x] Jacobi iterative solver — `jacobi()` with L2 residual convergence check
- [x] Conjugate gradient solver (numpy only) — matrix-free CG on interior system
- [x] Manufactured solution test — L2 error < 5e-4 on 32×32, < 1e-4 on 64×64; O(h²) convergence rate test
- [x] Direct solver — sparse Laplacian assembly + `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — `apply_neumann_bc()` on Grid, handled in all three solvers
- [x] `demo.py` convergence summary — solver comparison with iteration counts and residuals
- [x] Performance benchmark — all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
--- Grid 64x64 ---
  Jacobi  :   1.35s  iters= 17356  residual=9.997e-07
  CG      :   0.0002s  iters=     1  residual=6.332e-11
  Direct  :   0.015s   iters=     1  residual=7.315e-11

--- Grid 128x128 ---
  Jacobi  :   9.52s  iters= 50000  residual=4.622e-04  (capped — did not converge)
  CG      :   0.009s  iters=     1  residual=4.706e-10
  Direct  :   0.104s  iters=     1  residual=5.851e-10
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

- First run using `Spec.toml` (replaces `specification.toml` from run-2026-06-09).
- Loop 5 was a cleanup pass: the agent updated `test_poisson.py` (relaxed the 32×32 L2 threshold to 5e-4 and added a 64×64 test at 1e-4) and removed `tests/__init__.py` via a helper `_cleanup.py` script.
- A leftover `_cleanup.py` helper script remained at the project root after loop 5 (noted in `review_output.toml`).
- Test files landed under `poisson/tests/` rather than a top-level `tests/` directory.
- CG converges in 1 iteration because the manufactured source `sin(πx)sin(πy)` is an exact eigenmode of the discrete Laplacian.
