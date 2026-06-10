#!/usr/bin/env python
"""Demo: convergence plot and performance benchmark for the Poisson solvers."""

import time
import numpy as np

from poisson import Grid, jacobi_solve, cg_solve, direct_solve


# ── Convergence history ─────────────────────────────────────────────

def convergence_demo(nx=32, ny=32):
    """Print residual vs iteration for Jacobi and CG."""
    print("=" * 60)
    print(f"Convergence demo on {nx}x{ny} grid")
    print("=" * 60)

    for name, solver in [("Jacobi", jacobi_solve), ("CG", cg_solve)]:
        g = Grid(nx, ny)
        g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * g.X) * np.sin(np.pi * g.Y)
        print(f"\n--- {name} ---")
        iters, res = solver(g, maxiter=20000, tol=1e-6, verbose=True)
        exact = np.sin(np.pi * g.X) * np.sin(np.pi * g.Y)
        s = slice(1, -1)
        err = np.sqrt(np.mean((g.phi[s, s] - exact[s, s]) ** 2))
        print(f"Converged in {iters} iterations, residual = {res:.6e}, "
              f"L2 error = {err:.6e}")


# ── Benchmark ───────────────────────────────────────────────────────

def benchmark(sizes=None):
    """Compare wall-clock time of all three solvers."""
    if sizes is None:
        sizes = [(64, 64), (128, 128)]
    print("\n" + "=" * 60)
    print("Performance benchmark")
    print("=" * 60)

    solvers = [
        ("Jacobi", jacobi_solve),
        ("CG", cg_solve),
        ("Direct", direct_solve),
    ]

    for nx, ny in sizes:
        print(f"\nGrid {nx}x{ny}")
        print(f"{'Solver':<10s}  {'Iters':>6s}  {'Residual':>12s}  {'Time (s)':>10s}")
        for name, solver in solvers:
            g = Grid(nx, ny)
            g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * g.X) * np.sin(np.pi * g.Y)
            t0 = time.perf_counter()
            iters, res = solver(g, maxiter=20000, tol=1e-6)
            elapsed = time.perf_counter() - t0
            print(f"{name:<10s}  {iters:6d}  {res:12.4e}  {elapsed:10.4f}")


# ── main ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    convergence_demo()
    benchmark()
