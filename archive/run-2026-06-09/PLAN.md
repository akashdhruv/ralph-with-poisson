# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `grid.py` with `Grid(nx, ny, …)`, coordinate arrays, `phi`, `rhs`, and `apply_neumann()`
- [x] Jacobi iterative solver with convergence check — `jacobi_solve()` in `solvers.py`
- [x] Conjugate gradient solver, numpy only — `cg_solve()` in `solvers.py`
- [x] Manufactured solution test: verify L2 error < 1e-4 — tests in `test_poisson.py` (64×64 grid to stay within discretisation error)
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — `direct_solve()` in `solvers.py`
- [x] Neumann boundary condition support — `apply_neumann()` on Grid, all solvers accept `neumann_edges`
- [x] `demo.py`: convergence plot — prints residual vs iteration for Jacobi and CG
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — `benchmark()` in `demo.py`


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
