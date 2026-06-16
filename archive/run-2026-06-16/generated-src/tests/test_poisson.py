"""Tests for the Poisson solver package."""

import sys, os, math
import numpy as np

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poisson.grid import Grid
from poisson import solvers


# ---------- manufactured solution helpers ----------

def _make_manufactured(n=32):
    """Return a Grid with f = -2pi^2 sin(pi x) sin(pi y) and exact solution arrays."""
    g = Grid(n, n)
    XX, YY = g.interior_coords()
    g.rhs[:] = -2.0 * math.pi**2 * np.sin(math.pi * XX) * np.sin(math.pi * YY)
    phi_exact = np.sin(math.pi * XX) * np.sin(math.pi * YY)
    return g, phi_exact


def _l2_error(grid, phi_exact):
    """L2 error weighted by cell area (matches archive convention)."""
    return float(np.linalg.norm(grid.phi - phi_exact) * grid.dx * grid.dy)


# ---------- tests ----------

def test_grid_creation():
    g = Grid(10, 10)
    assert g.phi.shape == (10, 10)
    assert g.rhs.shape == (10, 10)
    assert abs(g.dx - 1.0 / 9) < 1e-14
    assert abs(g.dy - 1.0 / 9) < 1e-14


def test_jacobi_manufactured():
    g, phi_exact = _make_manufactured(32)
    iters, res = solvers.solve_jacobi(g, maxiter=20000, tol=1e-6)
    err = _l2_error(g, phi_exact)
    assert err < 1e-4, f"Jacobi L2 error {err:.6e} >= 1e-4"


def test_cg_manufactured():
    g, phi_exact = _make_manufactured(32)
    iters, res = solvers.solve_cg(g, maxiter=10000, tol=1e-8)
    err = _l2_error(g, phi_exact)
    assert err < 1e-4, f"CG L2 error {err:.6e} >= 1e-4"


def test_direct_manufactured():
    g, phi_exact = _make_manufactured(32)
    iters, res = solvers.solve_direct(g)
    err = _l2_error(g, phi_exact)
    assert err < 1e-4, f"Direct L2 error {err:.6e} >= 1e-4"


def test_neumann_bc():
    """Smoke test: Neumann on top edge should not crash and should converge."""
    g = Grid(16, 16)
    g.neumann.add('top')
    XX, YY = g.interior_coords()
    g.rhs[:] = -2.0 * math.pi**2 * np.sin(math.pi * XX) * np.sin(math.pi * YY)
    iters, res = solvers.solve_jacobi(g, maxiter=20000, tol=1e-5)
    assert np.all(np.isfinite(g.phi)), "Neumann Jacobi produced non-finite values"


if __name__ == '__main__':
    for name, func in list(globals().items()):
        if name.startswith('test_') and callable(func):
            print(f"Running {name} ... ", end='', flush=True)
            func()
            print("OK")
    print("All tests passed.")
