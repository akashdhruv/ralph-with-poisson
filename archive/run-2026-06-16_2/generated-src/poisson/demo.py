"""Demo script — convergence plot and performance benchmark.

Usage:
    python -m poisson.demo          (from generated-src/)
    python generated-src/poisson/demo.py
"""

import sys, os, time
import numpy as np

# Ensure generated-src is importable when run as a script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from poisson.grid import Grid
from poisson import solvers


# ====================================================================== #
# Convergence history                                                     #
# ====================================================================== #

def convergence_history(solver_fn, grid, **kw):
    """Run a solver while recording residual after each iteration.

    We run the solver repeatedly with increasing maxiter to collect
    the residual trajectory (cheap for CG, acceptable for Jacobi on
    small grids).
    """
    from poisson.solvers import _residual, _l2norm

    # Reset phi
    grid.phi[:] = 0.0
    grid.apply_neumann()

    history = []
    max_total = kw.pop("maxiter", 5000)
    tol = kw.pop("tol", 1e-10)

    # For Jacobi we just run step-by-step
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2

    if solver_fn is solvers.jacobi:
        for it in range(1, max_total + 1):
            grid.apply_neumann()
            phi = grid.phi
            phi_new = phi.copy()
            phi_new[1:-1, 1:-1] = (
                (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                - grid.rhs[1:-1, 1:-1]
            ) / denom
            grid.phi = phi_new
            grid.apply_neumann()
            res = _l2norm(_residual(grid))
            history.append(res)
            if res < tol:
                break
    else:
        # For CG just run full solve (fast)
        grid.phi[:] = 0.0
        # Intercept residual via repeated short runs
        remaining = max_total
        while remaining > 0:
            chunk = min(1, remaining)
            iters, res = solver_fn(grid, maxiter=chunk, tol=tol)
            history.append(res)
            remaining -= chunk
            if res < tol:
                break

    return history


# ====================================================================== #
# Convergence plot                                                        #
# ====================================================================== #

def convergence_plot():
    """Print a text-based convergence plot (log residual vs iteration)."""
    nx, ny = 32, 32
    print("=" * 60)
    print("Convergence: log₁₀(residual) vs iteration")
    print("=" * 60)

    for label, solver_fn in [("Jacobi", solvers.jacobi),
                              ("CG", solvers.conjugate_gradient)]:
        g = Grid(nx, ny)
        X, Y = np.meshgrid(g.x, g.y, indexing="ij")
        g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)

        hist = convergence_history(solver_fn, g, maxiter=5000, tol=1e-8)

        print(f"\n--- {label} ({len(hist)} iterations) ---")
        # Sample ~20 points for display
        step = max(1, len(hist) // 20)
        for idx in range(0, len(hist), step):
            bar_len = max(0, int(60 + np.log10(hist[idx] + 1e-30) * 5))
            print(f"  {idx+1:5d} | {'#' * bar_len} {hist[idx]:.2e}")
        # Last point
        if (len(hist) - 1) % step != 0:
            idx = len(hist) - 1
            bar_len = max(0, int(60 + np.log10(hist[idx] + 1e-30) * 5))
            print(f"  {idx+1:5d} | {'#' * bar_len} {hist[idx]:.2e}")


# ====================================================================== #
# Performance benchmark                                                   #
# ====================================================================== #

def benchmark():
    """Compare wall-clock time of all three solvers on 64×64 and 128×128."""
    print("\n" + "=" * 60)
    print("Performance benchmark")
    print("=" * 60)
    print(f"{'Solver':<12} {'Grid':<10} {'Time (s)':>10} {'Iters':>8} {'Residual':>12}")
    print("-" * 56)

    for n in [64, 128]:
        for label, solver_fn in [("Jacobi", solvers.jacobi),
                                  ("CG", solvers.conjugate_gradient),
                                  ("Direct", solvers.direct)]:
            g = Grid(n, n)
            X, Y = np.meshgrid(g.x, g.y, indexing="ij")
            g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)

            t0 = time.perf_counter()
            iters, res = solver_fn(g, maxiter=20000, tol=1e-6)
            elapsed = time.perf_counter() - t0

            print(f"{label:<12} {n}x{n:<6} {elapsed:>10.4f} {iters:>8} {res:>12.3e}")


# ====================================================================== #
# Main                                                                    #
# ====================================================================== #

if __name__ == "__main__":
    convergence_plot()
    benchmark()
