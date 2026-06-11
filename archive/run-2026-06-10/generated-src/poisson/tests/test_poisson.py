"""Tests for the 2D Poisson solver -- manufactured solution.

Manufactured solution: phi_exact = sin(pi*x) sin(pi*y)
gives f = -2 pi^2 sin(pi*x) sin(pi*y), with phi=0 on the boundary of [0,1]^2.

The 2nd-order finite-difference discretization error is O(h^2).
On a 32x32 interior grid h=1/33 the irreducible discretization error is ~3.9e-4.
Spec asks for L2 < 1e-4 on 32x32 but this is below the discretization floor;
we therefore verify L2 < 5e-4 on 32x32 (confirming the solver is correct) and
L2 < 1e-4 on 64x64 (confirming convergence to the requested tolerance).
"""

import sys
import os
import numpy as np

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from poisson.grid import Grid
from poisson import solvers


def _setup_manufactured(n=32):
    """Create a Grid with the manufactured RHS for phi_exact = sin(pi*x)*sin(pi*y)."""
    grid = Grid(n, n)
    X, Y = grid.full_meshgrid()
    grid.f[:] = -2.0 * np.pi**2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    return grid


def _l2_error(grid):
    """L2 error of grid.phi vs the manufactured exact solution (RMS over interior)."""
    X, Y = grid.full_meshgrid()
    exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    diff = grid.phi - exact
    return np.sqrt(np.mean(diff[1:-1, 1:-1] ** 2))


# ---- Grid tests -----------------------------------------------------------

def test_grid_basic():
    """Sanity check on Grid construction."""
    g = Grid(10, 20)
    assert g.phi.shape == (12, 22)
    assert g.f.shape == (12, 22)
    assert abs(g.dx - 1.0 / 11) < 1e-15
    assert abs(g.dy - 1.0 / 21) < 1e-15
    print("PASS: test_grid_basic")


# ---- Solver accuracy on 32x32 (per spec; threshold relaxed to 5e-4) -------

def test_jacobi_manufactured_32():
    grid = _setup_manufactured(32)
    iters, res = solvers.jacobi(grid, maxiter=20000, tol=1e-6, verbose=False)
    err = _l2_error(grid)
    print(f"Jacobi 32x32: iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 5e-4, f"Jacobi L2 error too large: {err}"
    print("PASS: test_jacobi_manufactured_32")


def test_cg_manufactured_32():
    grid = _setup_manufactured(32)
    iters, res = solvers.cg(grid, maxiter=10000, tol=1e-6, verbose=False)
    err = _l2_error(grid)
    print(f"CG 32x32:     iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 5e-4, f"CG L2 error too large: {err}"
    print("PASS: test_cg_manufactured_32")


def test_direct_manufactured_32():
    grid = _setup_manufactured(32)
    iters, res = solvers.direct(grid, verbose=False)
    err = _l2_error(grid)
    print(f"Direct 32x32: iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 5e-4, f"Direct L2 error too large: {err}"
    print("PASS: test_direct_manufactured_32")


# ---- Verify L2 < 1e-4 at finer resolution (64x64) -------------------------

def test_direct_manufactured_64():
    grid = _setup_manufactured(64)
    iters, res = solvers.direct(grid, verbose=False)
    err = _l2_error(grid)
    print(f"Direct 64x64: iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 1e-4, f"Direct L2 error too large: {err}"
    print("PASS: test_direct_manufactured_64")


# ---- Convergence order (compare 32 vs 64 to verify O(h^2)) ----------------

def test_convergence_order():
    """Verify second-order convergence by comparing 32x32 vs 64x64."""
    grid32 = _setup_manufactured(32)
    solvers.direct(grid32)
    e32 = _l2_error(grid32)

    grid64 = _setup_manufactured(64)
    solvers.direct(grid64)
    e64 = _l2_error(grid64)

    ratio = e32 / e64
    print(f"Convergence order test: e32={e32:.3e}, e64={e64:.3e}, ratio={ratio:.2f}")
    # ratio should be ~4 for 2nd-order scheme
    assert 3.0 < ratio < 5.0, f"Expected ratio ~4, got {ratio:.2f}"
    print("PASS: test_convergence_order")


if __name__ == "__main__":
    test_grid_basic()
    test_direct_manufactured_32()
    test_cg_manufactured_32()
    test_jacobi_manufactured_32()
    test_direct_manufactured_64()
    test_convergence_order()
    print("\nAll tests passed!")
