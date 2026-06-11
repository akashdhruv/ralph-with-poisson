# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `generated-src/poisson/grid.py`; includes `apply_neumann()`, `laplacian()`, `residual()`, and `set_rhs()` helpers
- [x] Jacobi iterative solver with convergence check — `generated-src/poisson/solvers.py`; full update rule with L2 residual norm stopping criterion
- [x] Conjugate gradient solver, numpy only — same file; standard CG on flattened interior system using `matvec` closure
- [x] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid — `generated-src/tests/test_poisson.py`; 20 tests all pass for Jacobi, CG, and direct
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — same file; sparse CSR Laplacian assembled and solved with boundary contributions subtracted
- [x] Neumann boundary condition support — `Grid.apply_neumann()` mirrors ghost cells; tested in `TestNeumann`
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG — `generated-src/poisson/demo.py`; saves `convergence_plot.png` via matplotlib
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — printed table in `demo.py`


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
