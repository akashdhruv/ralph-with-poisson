# Experiment Report — run-2026-06-10-claude-loop

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-10 |
| Model | claude-sonnet-4-6 (1M context) |
| Harness | Claude Code `/loop` skill with `Spec.toml` |
| Mode | Self-paced (dynamic, no fixed interval) |
| Iterations | 1 |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 1,100 |
| Output tokens | 13,000 |
| Cache read tokens | 1,100,000 |
| Cache write tokens | 26,300 |
| Total API duration | 3m 47s |
| Total wall duration | 5m 51s |
| Cost | $0.63 |

## Result

All 8 tasks completed in a single iteration. 9/9 tests pass.

```
tests/test_poisson.py::TestGrid::test_shape PASSED
tests/test_poisson.py::TestGrid::test_spacing PASSED
tests/test_poisson.py::TestGrid::test_coordinates PASSED
tests/test_poisson.py::TestJacobi::test_manufactured PASSED
tests/test_poisson.py::TestJacobi::test_returns_tuple PASSED
tests/test_poisson.py::TestCG::test_manufactured PASSED
tests/test_poisson.py::TestCG::test_converges_fast PASSED
tests/test_poisson.py::TestDirect::test_manufactured PASSED
tests/test_poisson.py::TestNeumann::test_neumann_left PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`, `f`, coordinate arrays, `neumann_edges`
- [x] Jacobi iterative solver — vectorised numpy update, L2 residual convergence check
- [x] Conjugate gradient solver (numpy only) — matrix-free CG with interior matvec closure
- [x] Manufactured solution test — L2 error < 1e-4 on 32×32 for all three solvers
- [x] Direct solver — CSR sparse assembly + `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — ghost-cell rule in `_apply_neumann`, applied per Jacobi iteration
- [x] `demo.py` convergence plot — saves `convergence.png`, log residual vs iteration
- [x] Performance benchmark — Jacobi / CG / direct on 64×64 and 128×128 grids

## Benchmark Output

```
--- Performance benchmark ---
Grid 64x64:
  jacobi    iters= 16279  res=9.99e-07  time=1.098s
  cg        iters=     1  res=6.76e-11  time=0.000s
  direct    iters=     1  res=0.00e+00  time=0.080s
Grid 128x128:
  jacobi    iters= 50000  res=2.84e-04  time=12.240s
  cg        iters=     1  res=6.83e-10  time=0.000s
  direct    iters=     1  res=0.00e+00  time=0.118s
```

Note: CG converges in 1 iteration because the manufactured source `sin(πx)sin(πy)` is an exact eigenmode of the 5-point discrete Laplacian — single-eigenvalue systems terminate in exactly 1 CG step. Jacobi does not converge within 50k iterations on 128×128 (residual 2.84e-4), consistent with its O(1/h²) iteration count growth.

## Files Generated

```
generated-src/
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

- The model implemented all tasks in one shot rather than one per loop iteration, then scheduled a fallback wakeup; the user stopped the loop manually.
- High cache read (1.1M tokens) reflects the system prompt / context being cached across the single long turn.
- CG and direct solvers are dramatically faster than Jacobi; Jacobi is included as the baseline iterative reference.
