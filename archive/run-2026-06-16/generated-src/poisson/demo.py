#!/usr/bin/env python
"""Demo script: convergence plot and performance benchmark."""

import math
import time
import numpy as np

from .grid import Grid
from . import solvers


# ---------------------------------------------------------------
# Convergence plot data: log residual vs iteration for Jacobi & CG
# ---------------------------------------------------------------

def convergence_data(n=32):
    """Run Jacobi and CG, recording residual at each iteration.

    Returns dict mapping solver name to list of (iteration, residual).
    """
    results = {}

    for label, solver_fn in [('jacobi', solvers.solve_jacobi),
                              ('cg', solvers.solve_cg)]:
        g = Grid(n, n)
        XX, YY = g.interior_coords()
        g.rhs[:] = -2.0 * math.pi**2 * np.sin(math.pi * XX) * np.sin(math.pi * YY)

        history = []

        if label == 'jacobi':
            dx2 = g.dx ** 2
            dy2 = g.dy ** 2
            denom = 2.0 / dx2 + 2.0 / dy2
            for it in range(1, 20001):
                g.apply_neumann()
                phi = g.phi
                phi_new = phi.copy()
                phi_new[1:-1, 1:-1] = (
                    (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                    + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                    - g.rhs[1:-1, 1:-1]
                ) / denom
                g.phi = phi_new
                res = solvers._residual_norm(g)
                if it % 100 == 0 or it == 1:
                    history.append((it, res))
                if res < 1e-8:
                    history.append((it, res))
                    break
        else:
            iters, res = solvers.solve_cg(g, maxiter=10000, tol=1e-8, verbose=False)
            history = [(0, float('nan')), (iters, res)]

        results[label] = history

    return results


# ---------------------------------------------------------------
# Performance benchmark
# ---------------------------------------------------------------

def benchmark():
    """Compare wall-clock time of all three solvers on 64x64 and 128x128."""
    solver_map = {
        'jacobi': solvers.solve_jacobi,
        'cg': solvers.solve_cg,
        'direct': solvers.solve_direct,
    }
    for n in [64, 128]:
        print(f"\n--- Grid {n}x{n} ---")
        for name, fn in solver_map.items():
            g = Grid(n, n)
            XX, YY = g.interior_coords()
            g.rhs[:] = -2.0 * math.pi**2 * np.sin(math.pi * XX) * np.sin(math.pi * YY)
            t0 = time.perf_counter()
            if name == 'direct':
                iters, res = fn(g)
            else:
                iters, res = fn(g, maxiter=50000, tol=1e-6)
            elapsed = time.perf_counter() - t0
            print(f"  {name:8s}: {elapsed:8.4f}s  iters={iters}  residual={res:.3e}")


# ---------------------------------------------------------------
# Convergence plot (saved to file if matplotlib available)
# ---------------------------------------------------------------

def plot_convergence():
    """Generate convergence plot and save to convergence.png."""
    data = convergence_data()
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        for label in ['jacobi', 'cg']:
            iters_list = [d[0] for d in data[label]]
            res_list = [d[1] for d in data[label]]
            ax.semilogy(iters_list, res_list, label=label)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Residual (log)')
        ax.set_title('Convergence: Jacobi vs CG')
        ax.legend()
        fig.savefig('convergence.png', dpi=100)
        print("Saved convergence.png")
    except ImportError:
        print("matplotlib not available -- printing data instead")
        for label in ['jacobi', 'cg']:
            print(f"\n{label}:")
            for it, r in data[label]:
                print(f"  iter {it}: residual = {r:.6e}")


if __name__ == '__main__':
    plot_convergence()
    benchmark()
