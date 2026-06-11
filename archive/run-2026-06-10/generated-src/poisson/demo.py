"""Demo: convergence summary and performance benchmark for the Poisson solvers."""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from poisson.grid import Grid
from poisson import solvers


def _setup_manufactured(n=32):
    grid = Grid(n, n)
    X, Y = grid.full_meshgrid()
    grid.f[:] = -2.0 * np.pi**2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    return grid


def run_demo():
    """Print convergence history for Jacobi and CG on 32x32 grid."""
    print("=" * 60)
    print("Jacobi solver convergence (32x32)")
    print("=" * 60)
    grid_j = _setup_manufactured(32)
    it_j, res_j = solvers.jacobi(grid_j, maxiter=20000, tol=1e-6, verbose=True)

    print()
    print("=" * 60)
    print("CG solver convergence (32x32)")
    print("=" * 60)
    grid_cg = _setup_manufactured(32)
    it_cg, res_cg = solvers.cg(grid_cg, maxiter=10000, tol=1e-6, verbose=True)

    print()
    print("=" * 60)
    print("Direct solver (32x32)")
    print("=" * 60)
    grid_d = _setup_manufactured(32)
    it_d, res_d = solvers.direct(grid_d, verbose=True)

    print()
    print("Summary")
    print("-" * 40)
    print(f"  Jacobi : {it_j:6d} iters, residual = {res_j:.3e}")
    print(f"  CG     : {it_cg:6d} iters, residual = {res_cg:.3e}")
    print(f"  Direct : {it_d:6d} iters, residual = {res_d:.3e}")


def run_benchmark():
    """Compare wall-clock time of all three solvers on 64x64 and 128x128."""
    print()
    print("=" * 60)
    print("Performance benchmark")
    print("=" * 60)

    for n in [64, 128]:
        print(f"\n--- Grid {n}x{n} ---")
        for name, solver_fn, kw in [
            ("Jacobi", solvers.jacobi, dict(maxiter=50000, tol=1e-6)),
            ("CG",     solvers.cg,     dict(maxiter=10000, tol=1e-6)),
            ("Direct", solvers.direct, dict()),
        ]:
            grid = _setup_manufactured(n)
            t0 = time.perf_counter()
            iters, res = solver_fn(grid, **kw)
            elapsed = time.perf_counter() - t0
            print(f"  {name:8s}: {elapsed:8.4f}s  iters={iters:6d}  residual={res:.3e}")


if __name__ == "__main__":
    run_demo()
    run_benchmark()
