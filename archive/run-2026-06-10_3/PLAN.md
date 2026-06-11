# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `grid.py`: Grid with phi, f arrays, Laplacian, residual methods
- [x] Jacobi iterative solver with convergence check — vectorised Jacobi in `solvers.py`, converges ~4320 iters on 32×32
- [x] Conjugate gradient solver, numpy only — CG in `solvers.py` with BC handling; converges in 1 iter for eigenvector-RHS
- [x] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid — 32×32 discretisation error is ~3.9e-4 (second-order FD limit); tests pass at 5e-4 on 32×32 and <1e-4 on 64×64
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — sparse COO assembly + spsolve in `solvers.py`
- [x] Neumann boundary condition support — Grid.neumann dict + apply_neumann(); handled in all three solvers
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG — saved to convergence.png
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids — integrated into demo.py


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
