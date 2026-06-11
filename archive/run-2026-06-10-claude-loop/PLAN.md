# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `grid.py` with phi/f/dx/dy/x/y/neumann_edges
- [x] Jacobi iterative solver with convergence check — `solvers.jacobi`, vectorised numpy update
- [x] Conjugate gradient solver, numpy only — `solvers.cg`, standard CG with matvec closure
- [x] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid — passes for all three solvers
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — `solvers.direct`, assembles CSR matrix
- [x] Neumann boundary condition support — ghost-cell rule in `_apply_neumann`, applied per Jacobi iteration
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG, saves convergence.png
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — in `demo.py:benchmark()`


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
