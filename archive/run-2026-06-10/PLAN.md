# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `grid.py`: Grid with phi, f, meshgrid helpers
- [x] Jacobi iterative solver with convergence check — `solvers.py`: jacobi() with L2 residual convergence
- [x] Conjugate gradient solver, numpy only — `solvers.py`: cg() matrix-free CG on interior system
- [x] Manufactured solution test: verify L2 error < 1e-4 on 64×64 grid (32×32 gives ~4e-4 due to O(h²) discretization) — `test_poisson.py`
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — `solvers.py`: direct() with sparse Laplacian assembly
- [x] Neumann boundary condition support — grid.py: apply_neumann_bc(); solvers: Jacobi, CG, Direct all handle Neumann ghost cells
- [x] `demo.py`: convergence summary — runs all three solvers and prints iteration counts and residuals
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — added run_benchmark() to demo.py


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
