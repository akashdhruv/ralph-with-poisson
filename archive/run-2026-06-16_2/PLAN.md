# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `SPEC.md`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `generated-src/poisson/grid.py` with Grid class, Neumann flags, and apply_neumann()
- [x] Jacobi iterative solver with convergence check — `solvers.jacobi()` with L2 residual convergence
- [x] Conjugate gradient solver, numpy only — `solvers.conjugate_gradient()` using flattened interior CG
- [x] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid — all 3 solvers achieve L2≈1.1e-5
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — `solvers.direct()` builds sparse Laplacian and solves
- [x] Neumann boundary condition support — Grid.neumann dict + apply_neumann(); tested in test_neumann_basic
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG — text-based chart
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — in demo.py benchmark()


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
