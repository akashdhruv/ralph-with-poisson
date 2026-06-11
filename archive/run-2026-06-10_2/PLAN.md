# Poisson Solver — Implementation Plan

Technical details are in the specification embedded in `specification.toml`.

## Tasks

- [x] Stand up `Grid` class with numpy arrays for φ and f — `grid.py` with Grid(nx,ny) constructor, phi/f arrays of shape (nx+2,ny+2)
- [x] Jacobi iterative solver with convergence check — `solvers.py` jacobi() with L2 residual convergence
- [x] Conjugate gradient solver, numpy only — `solvers.py` cg() using flattened interior system
- [x] Manufactured solution test: verify L2 error — tests pass on 32×32 (< 1e-3) and finer grids (< 1e-4), plus O(h²) convergence rate test
- [x] Direct solver via `scipy.sparse.linalg.spsolve` — `solvers.py` direct() assembles sparse Laplacian and calls spsolve
- [x] Neumann boundary condition support — Grid.apply_bc() mirrors ghost cells; solvers call it before each residual eval; direct solver modifies sparse matrix for Neumann edges; 3 Neumann tests added
- [x] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG (ASCII table output)
- [x] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids (in demo.py main)


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Completion Condition

The loop is done when all tasks above are marked `[x]` and all tests pass.

## Notes
