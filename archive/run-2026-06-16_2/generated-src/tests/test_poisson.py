"""Tests for the Poisson solver package.

Manufactured solution: φ_exact = sin(πx)sin(πy)  →  f = -2π² sin(πx)sin(πy).
Each solver must achieve L2 error < 1e-4 on a 32×32 grid.
"""

import sys, os
import numpy as np

# Ensure generated-src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from poisson.grid import Grid
from poisson import solvers


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _setup_manufactured(n=32):
    """Return a Grid with rhs set to the manufactured source and the
    exact solution array."""
    g = Grid(n, n)
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    phi_exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    # Dirichlet BCs: phi=0 on boundary (already zero)
    return g, phi_exact


def _l2_error(grid, phi_exact):
    """Area-weighted L2 error: ||e||_L2 = ||phi - phi_exact||_2 * dx * dy."""
    diff = grid.phi - phi_exact
    return float(np.linalg.norm(diff) * grid.dx * grid.dy)


# ------------------------------------------------------------------ #
# Solver tests                                                         #
# ------------------------------------------------------------------ #

def test_jacobi_manufactured():
    g, phi_exact = _setup_manufactured()
    iters, res = solvers.jacobi(g, maxiter=20000, tol=1e-6)
    err = _l2_error(g, phi_exact)
    print(f"Jacobi: iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 1e-4, f"Jacobi L2 error too large: {err}"


def test_cg_manufactured():
    g, phi_exact = _setup_manufactured()
    iters, res = solvers.conjugate_gradient(g, maxiter=10000, tol=1e-6)
    err = _l2_error(g, phi_exact)
    print(f"CG:     iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 1e-4, f"CG L2 error too large: {err}"


def test_direct_manufactured():
    g, phi_exact = _setup_manufactured()
    iters, res = solvers.direct(g)
    err = _l2_error(g, phi_exact)
    print(f"Direct: iters={iters}, residual={res:.3e}, L2 error={err:.3e}")
    assert err < 1e-4, f"Direct L2 error too large: {err}"


def test_neumann_basic():
    """Neumann on the right edge with a simple constant-gradient solution."""
    nx, ny = 16, 16
    g = Grid(nx, ny)
    g.neumann["right"] = True
    # f = 0 → φ is harmonic; set left-edge Dirichlet = sin(πy)
    Y_left = g.y
    g.phi[0, :] = np.sin(np.pi * Y_left)
    # Solve with CG (should converge quickly for this smooth problem)
    iters, res = solvers.conjugate_gradient(g, maxiter=5000, tol=1e-6)
    # The zero-flux condition means ∂φ/∂x = 0 at right edge.
    # Check ghost equals interior neighbour (within tolerance).
    np.testing.assert_allclose(g.phi[-1, :], g.phi[-2, :], atol=1e-5)


# ------------------------------------------------------------------ #
# Entry point (so we can run with plain `python`)                      #
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    passed = 0
    failed = 0
    for name, func in list(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)
