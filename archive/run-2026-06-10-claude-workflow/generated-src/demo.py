"""demo.py — convergence plot and performance benchmark for the Poisson solver.

Running this script:
    python3 -m poisson.demo            # from generated-src/ directory
    python3 generated-src/poisson/demo.py

Produces:
  1. convergence_plot.png — log residual vs iteration for Jacobi and CG on 32x32
  2. Console table of wall-clock times for all three solvers on 64x64 and 128x128
"""

import sys
import os
import time
import numpy as np

# Allow running directly as a script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poisson.grid import Grid
from poisson import solvers


# ---------------------------------------------------------------------------
# Manufactured solution helpers
# ---------------------------------------------------------------------------

def make_grid(nx: int, ny: int) -> Grid:
    g = Grid(nx, ny)
    g.set_rhs(lambda x, y: -2.0 * np.pi ** 2 * np.sin(np.pi * x) * np.sin(np.pi * y))
    return g


# ---------------------------------------------------------------------------
# Solver wrappers that record per-iteration residual history
# ---------------------------------------------------------------------------

def _run_jacobi_record(g, maxiter=5000, tol=1e-8):
    """Run Jacobi, return list of (iter, residual) pairs."""
    dx2 = g.dx ** 2
    dy2 = g.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2
    rhs_int = g.rhs[1:-1, 1:-1]
    history = []
    for it in range(1, maxiter + 1):
        g.apply_neumann()
        phi = g.phi
        phi_new = ((phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                   + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                   - rhs_int) / denom
        g.phi[1:-1, 1:-1] = phi_new
        res = np.linalg.norm(g.residual()) * g.dx * g.dy
        history.append((it, res))
        if res < tol:
            break
    return history


def _run_cg_record(g, maxiter=5000, tol=1e-8):
    """Run CG, return list of (iter, residual) pairs."""
    nx, ny = g.nx, g.ny
    dx2 = g.dx ** 2
    dy2 = g.dy ** 2

    def matvec(p):
        P = p.reshape(nx, ny)
        P_full = np.zeros((nx + 2, ny + 2))
        P_full[1:-1, 1:-1] = P
        lap = ((P_full[2:, 1:-1] - 2 * P_full[1:-1, 1:-1] + P_full[:-2, 1:-1]) / dx2
               + (P_full[1:-1, 2:] - 2 * P_full[1:-1, 1:-1] + P_full[1:-1, :-2]) / dy2)
        return -lap.ravel()

    b = -g.rhs[1:-1, 1:-1].ravel()
    x = g.phi[1:-1, 1:-1].ravel().copy()
    r = b - matvec(x)
    p = r.copy()
    rs_old = r @ r

    history = []
    for it in range(1, maxiter + 1):
        Ap = matvec(p)
        alpha = rs_old / (p @ Ap)
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = r @ r
        res_norm = np.sqrt(rs_new) * g.dx * g.dy
        history.append((it, res_norm))
        if res_norm < tol:
            break
        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    g.phi[1:-1, 1:-1] = x.reshape(nx, ny)
    return history


# ---------------------------------------------------------------------------
# 1. Convergence plot
# ---------------------------------------------------------------------------

def plot_convergence():
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        has_mpl = True
    except ImportError:
        has_mpl = False

    print("=== Convergence plot (32x32 grid) ===")
    g_j = make_grid(32, 32)
    hist_j = _run_jacobi_record(g_j, maxiter=10000, tol=1e-8)

    g_c = make_grid(32, 32)
    hist_c = _run_cg_record(g_c, maxiter=5000, tol=1e-8)

    iters_j, res_j = zip(*hist_j)
    iters_c, res_c = zip(*hist_c)

    print(f"  Jacobi converged in {iters_j[-1]} iterations, "
          f"final residual = {res_j[-1]:.3e}")
    print(f"  CG     converged in {iters_c[-1]} iterations, "
          f"final residual = {res_c[-1]:.3e}")

    if has_mpl:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.semilogy(iters_j, res_j, label='Jacobi')
        ax.semilogy(iters_c, res_c, label='CG')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('L2 residual')
        ax.set_title('Convergence: log residual vs iteration (32×32 grid)')
        ax.legend()
        ax.grid(True, which='both', alpha=0.3)
        out = 'convergence_plot.png'
        fig.savefig(out, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved {out}")
    else:
        print("  (matplotlib not available — skipping plot)")


# ---------------------------------------------------------------------------
# 2. Performance benchmark
# ---------------------------------------------------------------------------

def benchmark():
    print("\n=== Performance benchmark ===")
    header = f"{'Solver':>10}  {'Grid':>10}  {'Time (s)':>10}  {'Iterations':>10}"
    print(header)
    print('-' * len(header))

    for size in (64, 128):
        for method in ('jacobi', 'cg', 'direct'):
            g = make_grid(size, size)
            t0 = time.perf_counter()
            iters, res = solvers.solve(g, method=method, maxiter=20000, tol=1e-6)
            elapsed = time.perf_counter() - t0
            print(f"{method:>10}  {size}x{size:>4}  {elapsed:>10.4f}  {iters:>10d}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    plot_convergence()
    benchmark()
