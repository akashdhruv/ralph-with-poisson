# Experiment Report — run-2026-06-10_3

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-10 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `Spec.toml`) |
| Mode | Fresh-session loop (max 12 iterations/loop, max 5 loops) |
| Loops completed | 2 of 5 |
| Total wall duration | 10m 29s |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 415,652 |
| Output tokens | 36,572 |
| Cache read tokens | 0 |
| Cache write tokens | 0 |
| Loop 1 input tokens | 180,798 |
| Loop 1 output tokens | 25,806 |
| Total wall duration | 10m 29s |

*Loop 1 produced high output token count (25,806) due to extended reasoning over the 32×32 vs 64×64 grid interpretation and L2 threshold analysis.*

## Result

All 8 tasks completed in 2 loops. 6/6 tests pass.

```
tests/test_poisson.py::test_jacobi PASSED
tests/test_poisson.py::test_cg PASSED
tests/test_poisson.py::test_direct PASSED
tests/test_poisson.py::test_jacobi_fine PASSED
tests/test_poisson.py::test_cg_fine PASSED
tests/test_poisson.py::test_direct_fine PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`, `f`, Laplacian and residual methods, `apply_neumann()`
- [x] Jacobi iterative solver — vectorised update, converges ~4,320 iters on 32×32
- [x] Conjugate gradient solver (numpy only) — with BC handling; converges in 1 iter for eigenmode RHS
- [x] Manufactured solution test — relaxed 5e-4 on 32×32 (inherent FD discretisation limit), < 1e-4 on 64×64
- [x] Direct solver — sparse COO assembly + `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — `Grid.neumann` dict + `apply_neumann()`; handled in all three solvers
- [x] `demo.py` convergence plot — log residual vs iteration for Jacobi and CG; saves `convergence.png`
- [x] Performance benchmark — wall-clock table for all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
--- Performance Benchmark ---
Solver         N   Time (s)   Iters     Residual
------------------------------------------------
Jacobi        64     1.26   17356   9.9970e-07
CG            64     0.0002     1   6.3322e-11
Direct        64     0.051      1   7.3149e-11
Jacobi       128     8.84   50000   4.6224e-04  (capped — did not converge)
CG           128     0.001      1   4.7059e-10
Direct       128     0.099      1   5.8505e-10
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
    __init__.py
    test_poisson.py
```

## Notes

- Fastest CodeScribe run: all 8 tasks completed in 2 loops (vs 4–5 for other runs).
- Loop 1's reasoning trace shows extended deliberation over the 32×32 grid interpretation (interior points vs intervals) and the L2 error threshold — the agent concluded that ~3.9e-4 is the inherent second-order FD discretisation floor and relaxed the test tolerance to 5e-4 on 32×32.
- Only CodeScribe run to save a `convergence.png` image (log residual vs iteration).
- `tests/__init__.py` exists but is not listed in the SPEC.md module layout; noted as cosmetic in the review.
- CG converges in 1 iteration because `sin(πx)sin(πy)` is an exact eigenmode of the 5-point discrete Laplacian.
