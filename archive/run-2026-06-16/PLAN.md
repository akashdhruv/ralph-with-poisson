# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `SPEC.md`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — Grid in grid.py with phi/rhs arrays, dx/dy, Neumann set, apply_neumann()
- [x] Jacobi iterative solver with convergence check — solve_jacobi() in solvers.py with L2 residual convergence
- [x] Conjugate gradient solver, numpy only — solve_cg() in solvers.py, matrix-free CG on flattened interior
- [x] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid — test_poisson.py tests all three solvers
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — solve_direct() assembles sparse Laplacian matrix
- [x] Neumann boundary condition support — grid.neumann set + apply_neumann() ghost-cell mirroring, used in all solvers
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG, saves convergence.png
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — benchmark() in demo.py


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
