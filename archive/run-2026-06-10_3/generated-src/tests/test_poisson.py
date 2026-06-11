"""Tests for the Poisson solver using the manufactured solution.

Manufactured solution: phi_exact = sin(pi*x)*sin(pi*y)
RHS: f = -2*pi^2 * sin(pi*x)*sin(pi*y)
Dirichlet BC: phi = 0 on boundary.

On a 32x32 interior-point grid the second-order discretisation error is ~4e-4.
The spec asks for L2 error < 1e-4; we therefore also run on a 64x64 grid
where the discretisation error drops below 1e-4, and keep the 32x32 test
with a realistic 5e-4 threshold for a sanity check.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poisson.grid import Grid
from poisson.solvers import jacobi_solve, cg_solve, direct_solve


def make_manufactured_grid(n=32):
    """Create a grid with manufactured RHS."""
    grid = Grid(n, n)
    pi = np.pi
    grid.f[:] = -2.0 * pi ** 2 * np.sin(pi * grid.X) * np.sin(pi * grid.Y)
    return grid


def exact_solution(grid):
    return np.sin(np.pi * grid.X) * np.sin(np.pi * grid.Y)


def l2_error(grid):
    """Root-mean-square error at interior points."""
    phi_exact = exact_solution(grid)
    diff = grid.phi[1:-1, 1:-1] - phi_exact[1:-1, 1:-1]
    return np.sqrt(np.sum(diff ** 2) / diff.size)


# --------------- 32x32 tests (sanity, discretisation-limited) ---------------

def test_jacobi():
    grid = make_manufactured_grid(32)
    iters, res = jacobi_solve(grid, maxiter=20000, tol=1e-6)
    err = l2_error(grid)
    print(f"Jacobi 32x32: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 5e-4, f"Jacobi L2 error {err} >= 5e-4"


def test_cg():
    grid = make_manufactured_grid(32)
    iters, res = cg_solve(grid, maxiter=10000, tol=1e-6)
    err = l2_error(grid)
    print(f"CG     32x32: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 5e-4, f"CG L2 error {err} >= 5e-4"


def test_direct():
    grid = make_manufactured_grid(32)
    iters, res = direct_solve(grid, verbose=False)
    err = l2_error(grid)
    print(f"Direct 32x32: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 5e-4, f"Direct L2 error {err} >= 5e-4"


# ------------- 64x64 tests (verify L2 error < 1e-4 per spec) ---------------

def test_jacobi_fine():
    grid = make_manufactured_grid(64)
    iters, res = jacobi_solve(grid, maxiter=50000, tol=1e-7)
    err = l2_error(grid)
    print(f"Jacobi 64x64: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 1e-4, f"Jacobi (64x64) L2 error {err} >= 1e-4"


def test_cg_fine():
    grid = make_manufactured_grid(64)
    iters, res = cg_solve(grid, maxiter=10000, tol=1e-7)
    err = l2_error(grid)
    print(f"CG     64x64: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 1e-4, f"CG (64x64) L2 error {err} >= 1e-4"


def test_direct_fine():
    grid = make_manufactured_grid(64)
    iters, res = direct_solve(grid, verbose=False)
    err = l2_error(grid)
    print(f"Direct 64x64: iters={iters}, residual={res:.6e}, L2 err={err:.6e}")
    assert err < 1e-4, f"Direct (64x64) L2 error {err} >= 1e-4"


if __name__ == '__main__':
    test_jacobi()
    test_cg()
    test_direct()
    print()
    test_cg_fine()
    test_direct_fine()
    # Jacobi 64x64 takes many iterations; skip in quick runs.
    # test_jacobi_fine()
    print("\nAll tests passed!")
