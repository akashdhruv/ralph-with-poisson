#!/usr/bin/env python3
"""Demo script: convergence plot — log residual vs iteration for Jacobi and CG.

Also benchmarks wall-clock time of all three solvers on 64×64 and 128×128 grids.

Run:  cd generated-src && python -m poisson.demo
"""

import os
import sys
import time
import numpy as np

# Ensure the package is importable even when invoked as a standalone script.
_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from poisson.grid import Grid
from poisson import solvers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_problem(nx, ny=None, multimode=False):
    """Create a problem on an nx×ny grid.

    With *multimode=False* (default) the RHS is the manufactured solution
    f = -2π² sin(πx)sin(πy).  With *multimode=True* a sum of several
    Fourier modes is used so that CG requires many iterations (useful for
    demonstrating convergence behaviour).
    """
    if ny is None:
        ny = nx
    g = Grid(nx, ny)
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    if multimode:
        # Sum of modes so the RHS is NOT a single eigenvector of the
        # discrete Laplacian — forces CG to take many steps.
        g.f[:] = 0.0
        for m in range(1, 6):
            for n in range(1, 6):
                g.f[:] += -(m**2 + n**2) * np.pi**2 * np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    else:
        g.f[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    return g


def _collect_residual_history(solver_fn, grid, **kwargs):
    """Run a solver while collecting residual at every iteration.

    Works by wrapping the solver with a small callback via verbose prints.
    Returns (iterations, final_residual, history_list).
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    maxiter = kwargs.get("maxiter", 10000)
    tol = kwargs.get("tol", 1e-6)

    history = []

    if solver_fn is solvers.jacobi:
        denom = 2.0 / dx2 + 2.0 / dy2
        for it in range(1, maxiter + 1):
            phi = grid.phi
            phi_new = phi.copy()
            phi_new[1:-1, 1:-1] = (
                (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                - grid.f[1:-1, 1:-1]
            ) / denom
            grid.phi = phi_new
            res = solvers._residual_l2(grid)
            history.append(res)
            if res < tol:
                return it, res, history
        return maxiter, history[-1], history

    elif solver_fn is solvers.cg:
        nx, ny = grid.nx, grid.ny
        dx, dy = grid.dx, grid.dy

        def apply_A(v):
            full = np.zeros((nx + 2, ny + 2))
            full[1:-1, 1:-1] = v.reshape(nx, ny)
            L = solvers._laplacian(full, dx, dy)
            return L[1:-1, 1:-1].ravel()

        b = grid.f[1:-1, 1:-1].ravel().copy()
        x = grid.phi[1:-1, 1:-1].ravel().copy()
        r = b - apply_A(x)
        p = r.copy()
        rs_old = np.dot(r, r)

        for it in range(1, maxiter + 1):
            Ap = apply_A(p)
            pAp = np.dot(p, Ap)
            if pAp == 0.0:
                break
            alpha = rs_old / pAp
            x += alpha * p
            r -= alpha * Ap
            rs_new = np.dot(r, r)
            res_norm = np.sqrt(rs_new)
            history.append(res_norm)
            if res_norm < tol:
                grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
                return it, res_norm, history
            beta = rs_new / rs_old
            p = r + beta * p
            rs_old = rs_new
        grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
        return maxiter, history[-1] if history else 0.0, history

    else:
        raise ValueError("History collection only for jacobi/cg")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Poisson Solver Demo")
    print("=" * 60)

    # --- Part 1: Convergence histories (32×32, multimode RHS) ---
    print("\n--- Residual convergence on 32×32 grid (multimode RHS) ---")

    g_j = _make_problem(32, multimode=True)
    _, _, hist_j = _collect_residual_history(solvers.jacobi, g_j, maxiter=20000, tol=1e-6)
    print(f"Jacobi : {len(hist_j)} iterations, final residual = {hist_j[-1]:.4e}")

    g_c = _make_problem(32, multimode=True)
    _, _, hist_c = _collect_residual_history(solvers.cg, g_c, maxiter=10000, tol=1e-6)
    print(f"CG     : {len(hist_c)} iterations, final residual = {hist_c[-1]:.4e}")

    # Print a simple ASCII log-residual table
    print("\niter     Jacobi-log10(res)   CG-log10(res)")
    steps = list(range(0, max(len(hist_j), len(hist_c)), max(1, len(hist_j) // 20)))
    if steps[-1] != len(hist_j) - 1:
        steps.append(len(hist_j) - 1)
    for s in steps:
        jval = np.log10(hist_j[s]) if s < len(hist_j) else None
        cval = np.log10(hist_c[s]) if s < len(hist_c) else None
        jstr = f"{jval:8.3f}" if jval is not None else "     N/A"
        cstr = f"{cval:8.3f}" if cval is not None else "     N/A"
        print(f"{s:6d}   {jstr}            {cstr}")

    # --- Part 2: Benchmark ---
    print("\n--- Wall-clock benchmark (seconds) ---")
    print(f"{'Grid':>10s}  {'Jacobi':>10s}  {'CG':>10s}  {'Direct':>10s}")

    for n in [64, 128]:
        times = {}
        for name, fn in [("Jacobi", solvers.jacobi), ("CG", solvers.cg), ("Direct", solvers.direct)]:
            g = _make_problem(n)
            kw = {"maxiter": 50000, "tol": 1e-6} if name != "Direct" else {}
            t0 = time.perf_counter()
            fn(g, **kw)
            elapsed = time.perf_counter() - t0
            times[name] = elapsed
        print(f"{n:>5d}×{n:<4d}  {times['Jacobi']:10.4f}  {times['CG']:10.4f}  {times['Direct']:10.4f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
