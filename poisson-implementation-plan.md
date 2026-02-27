# Poisson Solver — Implementation Plan

See `poisson-spec.md` for technical details on each item.

## Tasks

- [ ] Stand up `Grid` class with numpy arrays for φ and f (see poisson-spec.md § Grid)
- [ ] Jacobi iterative solver with convergence check (see poisson-spec.md § Jacobi)
- [ ] Conjugate gradient solver, numpy only (see poisson-spec.md § Conjugate Gradient)
- [ ] Manufactured solution test: verify L2 error < 1e-4 on 32×32 grid (see poisson-spec.md § Testing)
- [ ] Direct solver via `scipy.sparse.linalg.spsolve` (see poisson-spec.md § Direct)
- [ ] Neumann boundary condition support (see poisson-spec.md § Neumann)
- [ ] `demo.py`: convergence plot — log residual vs iteration for Jacobi and CG
- [ ] Performance benchmark: compare wall-clock time of all three solvers on 64×64 and 128×128 grids


## Process Rule

When you complete a task, mark it done (change `[ ]` to `[x]`) and add a one-line note describing what was built.

## Notes
