# Experiment Report — run-2026-06-16

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-16 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `Spec.toml`) |
| Mode | Fresh-session loop (max 30 iterations/loop, max 5 loops) |
| Loops completed | 1 of 5 |
| Total wall duration | 8m 20s |

*First CodeScribe run with prompt caching enabled — the API integration now reports `cache_read`/`cache_write` token counts (previously always 0).*

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 42,129 |
| Output tokens | 19,077 |
| Cache read tokens | 151,178 |
| Cache write tokens | 37,929 |
| Reasoning tokens | not reported separately |
| Total wall duration | 8m 20s |

*Billed input dropped to 42k (vs 235k–975k for the pre-caching CodeScribe runs) because the bulk of the repeated context — `SPEC.md`, `AGENTS.md`, `PLAN.md`, and the growing source tree — is now served from cache (151k cache reads).*

## Result

All 8 tasks completed in a single loop. 5/5 tests pass.

```
tests/test_poisson.py::test_grid_creation PASSED
tests/test_poisson.py::test_jacobi_manufactured PASSED
tests/test_poisson.py::test_cg_manufactured PASSED
tests/test_poisson.py::test_direct_manufactured PASSED
tests/test_poisson.py::test_neumann_bc PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`/`rhs` arrays, `dx`/`dy`, Neumann set, `apply_neumann()`
- [x] Jacobi iterative solver — `solve_jacobi()` with L2 residual convergence check
- [x] Conjugate gradient solver (numpy only) — `solve_cg()`, matrix-free CG on the flattened interior
- [x] Manufactured solution test — `test_poisson.py` verifies all three solvers (L2 error < 1e-4 on 32×32)
- [x] Direct solver — `solve_direct()` assembles the sparse Laplacian and calls `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — `grid.neumann` set + `apply_neumann()` ghost-cell mirroring, used in all three solvers
- [x] `demo.py` convergence plot — log residual vs iteration for Jacobi and CG; saves `convergence.png`
- [x] Performance benchmark — wall-clock table for all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
--- Grid 64x64 ---
  jacobi  :   1.0394s  iters=16279  residual=9.994e-07
  cg      :   0.0002s  iters=1      residual=5.128e-11
  direct  :   0.0553s  iters=1      residual=6.779e-11

--- Grid 128x128 ---
  jacobi  :  11.8054s  iters=50000  residual=2.842e-04  (capped — did not converge)
  cg      :   0.0006s  iters=1      residual=5.520e-10
  direct  :   0.1262s  iters=1      residual=5.509e-10
```

## Files Generated

```
generated-src/
  convergence.png
  poisson/
    __init__.py
    grid.py
    solvers.py
    demo.py
  tests/
    test_poisson.py
```

## Notes

- First CodeScribe run to record non-zero cache tokens — prompt caching is now wired into the API integration. Billed input fell by roughly an order of magnitude versus the pre-caching runs.
- Completed all 8 tasks in one loop. The per-loop iteration cap was also raised from 12 to 30, giving the single execution session room to finish end-to-end before the review pass.
- CG converges in 1 iteration because `sin(πx)sin(πy)` is an exact eigenmode of the 5-point discrete Laplacian.
- Jacobi on 128×128 hits the iteration cap (50,000) without reaching `tol`; CG and the direct solver are unaffected.
- Saves a `convergence.png` (log residual vs iteration), matching `run-2026-06-10_3`.
