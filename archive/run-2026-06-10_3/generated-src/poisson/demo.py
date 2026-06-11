"""Convergence plot and performance benchmark for the Poisson solver.

Generates:
  1. A convergence plot — log residual vs iteration for Jacobi and CG.
  2. A performance comparison — wall-clock time of all three solvers
     on 64×64 and 128×128 grids.
"""

import os
import sys
import time
import numpy as np

# Ensure the package is importable when run as a script.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poisson.grid import Grid
from poisson.solvers import jacobi_solve, cg_solve, direct_solve


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_grid(n):
    """Build a grid with the manufactured-solution RHS."""
    grid = Grid(n, n)
    pi = np.pi
    grid.f[:] = -2.0 * pi ** 2 * np.sin(pi * grid.X) * np.sin(pi * grid.Y)
    return grid


def _collect_residuals(solver_func, n, maxiter, tol, record_every=1):
    """Run a solver, recording the residual at regular intervals.

    Returns (iterations, residuals_list).
    """
    grid = _make_grid(n)

    residuals = []

    # We drive the solver one iteration at a time so we can record
    # the residual history.  To avoid patching the solver internals
    # we simply re-implement lightweight wrappers here.
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2

    if solver_func == 'jacobi':
        for it in range(1, maxiter + 1):
            grid.apply_neumann()
            phi = grid.phi
            phi_new = phi.copy()
            phi_new[1:-1, 1:-1] = (
                (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                - grid.f[1:-1, 1:-1]
            ) / denom
            grid.phi = phi_new
            grid.apply_neumann()
            if it % record_every == 0 or it == 1:
                res = grid.residual_l2()
                residuals.append((it, res))
                if res < tol:
                    break
        return residuals

    elif solver_func == 'cg':
        nx, ny = grid.nx, grid.ny

        def A_times(v_flat):
            u_full = np.zeros((nx + 2, ny + 2), dtype=np.float64)
            u_full[1:-1, 1:-1] = v_flat.reshape(nx, ny)
            Ld = (
                (u_full[2:, 1:-1] - 2 * u_full[1:-1, 1:-1] + u_full[:-2, 1:-1]) / dx2
                + (u_full[1:-1, 2:] - 2 * u_full[1:-1, 1:-1] + u_full[1:-1, :-2]) / dy2
            )
            return Ld.ravel()

        bc_full = np.zeros_like(grid.phi)
        bc_full[0, :] = grid.phi[0, :]
        bc_full[-1, :] = grid.phi[-1, :]
        bc_full[:, 0] = grid.phi[:, 0]
        bc_full[:, -1] = grid.phi[:, -1]
        bc_contrib = (
            (bc_full[2:, 1:-1] - 2 * bc_full[1:-1, 1:-1] + bc_full[:-2, 1:-1]) / dx2
            + (bc_full[1:-1, 2:] - 2 * bc_full[1:-1, 1:-1] + bc_full[1:-1, :-2]) / dy2
        ).ravel()

        b = grid.f[1:-1, 1:-1].ravel() - bc_contrib
        x = grid.phi[1:-1, 1:-1].copy().ravel()
        r = b - A_times(x)
        p = r.copy()
        rs_old = np.dot(r, r)

        residuals.append((0, np.sqrt(rs_old)))

        for it in range(1, maxiter + 1):
            Ap = A_times(p)
            pAp = np.dot(p, Ap)
            if abs(pAp) < 1e-30:
                break
            alpha = rs_old / pAp
            x = x + alpha * p
            r = r - alpha * Ap
            rs_new = np.dot(r, r)
            res_norm = np.sqrt(rs_new)
            if it % record_every == 0 or it == 1:
                residuals.append((it, res_norm))
            if res_norm < tol:
                break
            beta = rs_new / rs_old
            p = r + beta * p
            rs_old = rs_new

        return residuals

    raise ValueError(f"Unknown solver: {solver_func}")


# ---------------------------------------------------------------------------
# 1. Convergence plot
# ---------------------------------------------------------------------------

def convergence_plot(n=32, maxiter_jacobi=10000, maxiter_cg=10000, tol=1e-6):
    """Create a log-residual vs iteration plot for Jacobi and CG."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("[demo] matplotlib not available — printing residuals to stdout instead.")
        jac_res = _collect_residuals('jacobi', n, maxiter_jacobi, tol, record_every=200)
        cg_res = _collect_residuals('cg', n, maxiter_cg, tol, record_every=1)
        print("Jacobi residuals:")
        for it, r in jac_res:
            print(f"  iter {it:6d}  residual {r:.6e}")
        print("CG residuals:")
        for it, r in cg_res:
            print(f"  iter {it:6d}  residual {r:.6e}")
        return

    jac_res = _collect_residuals('jacobi', n, maxiter_jacobi, tol, record_every=50)
    cg_res = _collect_residuals('cg', n, maxiter_cg, tol, record_every=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy([r[0] for r in jac_res], [r[1] for r in jac_res], label='Jacobi')
    ax.semilogy([r[0] for r in cg_res], [r[1] for r in cg_res], label='CG')
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Residual (L2)')
    ax.set_title(f'Convergence on {n}×{n} grid')
    ax.legend()
    ax.grid(True, which='both', ls='--', alpha=0.5)
    fig.tight_layout()
    outpath = os.path.join(os.path.dirname(__file__), '..', 'convergence.png')
    fig.savefig(outpath, dpi=120)
    print(f"[demo] Convergence plot saved to {outpath}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Performance benchmark
# ---------------------------------------------------------------------------

def benchmark(sizes=None):
    """Compare wall-clock time of Jacobi, CG, and Direct on given grid sizes."""
    if sizes is None:
        sizes = [64, 128]

    header = f"{'Solver':<10} {'N':>5} {'Time (s)':>10} {'Iters':>7} {'Residual':>12}"
    print(header)
    print('-' * len(header))

    for n in sizes:
        for name, solver in [('Jacobi', jacobi_solve),
                              ('CG', cg_solve),
                              ('Direct', direct_solve)]:
            grid = _make_grid(n)
            t0 = time.time()
            iters, res = solver(grid, maxiter=50000, tol=1e-6)
            elapsed = time.time() - t0
            print(f"{name:<10} {n:5d} {elapsed:10.4f} {iters:7d} {res:12.4e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("  Convergence Plot")
    print("=" * 60)
    convergence_plot()

    print()
    print("=" * 60)
    print("  Performance Benchmark")
    print("=" * 60)
    benchmark()
