# Experiment Report — run-2026-06-10-claude-workflow

## Setup

| Field | Value |
|-------|-------|
| Date | 2026-06-10 |
| Model | claude-sonnet-4-6 (1M context) |
| Prompt | `run a loop on Spec.toml using workflows.` — Claude prompt sourced from `Spec.toml` and executed via the Workflow harness |
| Harness | Claude Code Workflow (multi-agent orchestration) |
| Mode | Loop-until-dry (max 2 dry rounds) |
| Iterations | 1 |
| Agents | 3 — check-plan (2/2), implement (1/1) |

## Token Usage

| Metric | Value |
|--------|-------|
| Input tokens | 2,600 |
| Output tokens | 15,500 |
| Cache read tokens | 932,600 |
| Cache write tokens | 37,700 |
| Total API duration | 4m 22s |
| Total wall duration | 5m 42s |

## Result

All 8 tasks completed in a single iteration. 20/20 tests pass.

```
tests/test_poisson.py::TestGrid::test_shape PASSED
tests/test_poisson.py::TestGrid::test_spacing PASSED
tests/test_poisson.py::TestGrid::test_boundary_zero PASSED
tests/test_poisson.py::TestGrid::test_set_rhs PASSED
tests/test_poisson.py::TestGrid::test_residual_zero_phi PASSED
tests/test_poisson.py::TestJacobi::test_converges PASSED
tests/test_poisson.py::TestJacobi::test_l2_error PASSED
tests/test_poisson.py::TestJacobi::test_returns_tuple PASSED
tests/test_poisson.py::TestCG::test_converges PASSED
tests/test_poisson.py::TestCG::test_l2_error PASSED
tests/test_poisson.py::TestCG::test_returns_tuple PASSED
tests/test_poisson.py::TestDirect::test_converges PASSED
tests/test_poisson.py::TestDirect::test_l2_error PASSED
tests/test_poisson.py::TestDirect::test_returns_tuple PASSED
tests/test_poisson.py::TestNeumann::test_neumann_ghost_cell PASSED
tests/test_poisson.py::TestNeumann::test_neumann_top_ghost_cell PASSED
tests/test_poisson.py::TestDispatch::test_jacobi_dispatch PASSED
tests/test_poisson.py::TestDispatch::test_cg_dispatch PASSED
tests/test_poisson.py::TestDispatch::test_direct_dispatch PASSED
tests/test_poisson.py::TestDispatch::test_unknown_method PASSED
```

## Tasks Completed

- [x] Grid class — `grid.py` with `phi`, `f`, coordinate arrays, `apply_neumann()`, `laplacian()`, `residual()`, `set_rhs()`
- [x] Jacobi iterative solver — full update rule with L2 residual norm stopping criterion
- [x] Conjugate gradient solver (numpy only) — standard CG on flattened interior system using `matvec` closure
- [x] Manufactured solution test — L2 error < 1e-4 on 32×32 for Jacobi, CG, and direct
- [x] Direct solver — sparse CSR Laplacian assembled, solved with `scipy.sparse.linalg.spsolve`
- [x] Neumann BC support — `Grid.apply_neumann()` mirrors ghost cells; tested in `TestNeumann`
- [x] `demo.py` convergence plot — saves `convergence_plot.png`, log residual vs iteration for Jacobi and CG
- [x] Performance benchmark — wall-clock table for all three solvers on 64×64 and 128×128 grids

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

- The Claude prompt was sourced directly from `Spec.toml` (`[[chat.user]]` content) and executed via the Claude Code Workflow harness rather than a `/loop` skill or manual invocation.
- The implement agent completed all 8 tasks in a single shot; the loop exited cleanly after detecting 0 pending tasks on the recheck pass.
- High cache read (932.6k tokens) reflects spec and file context cached across the 3 agents in the workflow.
- 20 tests vs 9 in the `/loop` run — broader test coverage (dispatch, Neumann top edge, residual helpers).
