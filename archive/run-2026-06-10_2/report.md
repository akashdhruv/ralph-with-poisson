# Experiment Report — run-2026-06-10_2

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-10 |
| Model | claude-opus-4-6 + extended thinking (`--reason`) |
| Prompt | `code-scribe loop Spec.toml -m anthropic-claude-opus-4-6 -v --reason` |
| Harness | CodeScribe loop (fresh session per loop, `Spec.toml`) |
| Mode | Fresh-session loop (max 12 iterations/loop, max 5 loops) |
| Loops completed | 5 of 5 |
| Total wall duration | 16m 47s |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 974,751 |
| Output tokens | 54,368 |
| Cache read tokens | 0 |
| Cache write tokens | 0 |
| Total wall duration | 16m 47s |

## Result

All 8 tasks completed. 12/12 tests pass.

```
poisson/tests/test_poisson.py::TestJacobi::test_convergence_32 PASSED
poisson/tests/test_poisson.py::TestJacobi::test_accuracy_fine PASSED
poisson/tests/test_poisson.py::TestCG::test_convergence_32 PASSED
poisson/tests/test_poisson.py::TestCG::test_accuracy_fine PASSED
poisson/tests/test_poisson.py::TestDirect::test_convergence_32 PASSED
poisson/tests/test_poisson.py::TestDirect::test_accuracy_fine PASSED
poisson/tests/test_poisson.py::TestConvergenceRate::test_h2_convergence PASSED
poisson/tests/test_poisson.py::TestNeumann::test_apply_bc_mirrors_ghost PASSED
poisson/tests/test_poisson.py::TestNeumann::test_neumann_right_direct PASSED
poisson/tests/test_poisson.py::TestNeumann::test_neumann_cg PASSED
poisson/tests/test_poisson.py::TestSolveDispatch::test_jacobi_dispatch PASSED
poisson/tests/test_poisson.py::TestSolveDispatch::test_unknown_method PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `Grid(nx,ny)`, `phi`/`f` arrays of shape `(nx+2, ny+2)`, `apply_bc()`
- [x] Jacobi iterative solver — `jacobi()` with L2 residual convergence check
- [x] Conjugate gradient solver (numpy only) — CG on flattened interior system
- [x] Manufactured solution test — L2 error < 1e-3 on 32×32, < 1e-4 on 64×64; O(h²) convergence rate verified
- [x] Direct solver — sparse Laplacian assembly + `scipy.sparse.linalg.spsolve`; Neumann edges modify sparse matrix
- [x] Neumann BC support — `Grid.apply_bc()` mirrors ghost cells; all solvers apply it; 3 Neumann tests added
- [x] `demo.py` convergence plot — ASCII log-residual table for Jacobi and CG
- [x] Performance benchmark — wall-clock table for all three solvers on 64×64 and 128×128 grids

## Benchmark Output

```
--- Wall-clock benchmark (seconds) ---
      Grid      Jacobi          CG      Direct
   64×64        1.38        0.0002      0.057
  128×128       9.66        0.009       0.111
```

Note: Jacobi does not converge at 128×128 within the iteration cap. CG and direct are dramatically faster.

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

- Most comprehensive test suite of the four CodeScribe runs: 12 tests covering Jacobi/CG/Direct accuracy, O(h²) convergence rate, Neumann ghost-cell mirroring, and solver dispatch.
- The direct solver modifies the sparse matrix itself for Neumann edges rather than applying ghost-cell correction post-solve.
- Some bash commands were blocked by sandbox restrictions (pipes, `||`, `$()`); the agent worked around them cleanly.
- The agent hit its max_iterations limit on loop 5 without emitting a final summary; all substantive work was already complete.
