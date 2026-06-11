"""Tests for the Poisson solver.

Manufactured solution: φ_exact = sin(πx)sin(πy)
  ∇²φ_exact = -2π²φ_exact  →  f = -2π²sin(πx)sin(πy)

Each solver is tested on a 32×32 interior grid; the expected L2 error is < 1e-4.
"""

import sys
import os
import numpy as np
import pytest

# Allow imports from generated-src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from poisson.grid import Grid
from poisson import solvers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_manufactured_grid(nx: int = 32, ny: int = 32) -> Grid:
    """Return a fresh Grid with the manufactured-solution RHS loaded."""
    g = Grid(nx, ny)
    g.set_rhs(lambda x, y: -2.0 * np.pi ** 2 * np.sin(np.pi * x) * np.sin(np.pi * y))
    return g


def l2_error(grid) -> float:
    """L2 norm of (phi - phi_exact) on interior points, scaled by cell area."""
    X, Y = np.meshgrid(grid.x, grid.y, indexing='ij')
    phi_exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    diff = grid.phi[1:-1, 1:-1] - phi_exact
    return np.linalg.norm(diff) * grid.dx * grid.dy


# ---------------------------------------------------------------------------
# Grid tests
# ---------------------------------------------------------------------------

class TestGrid:
    def test_shape(self):
        g = Grid(8, 8)
        assert g.phi.shape == (10, 10)
        assert g.rhs.shape == (10, 10)

    def test_spacing(self):
        g = Grid(3, 3)
        assert abs(g.dx - 0.25) < 1e-12
        assert abs(g.dy - 0.25) < 1e-12

    def test_boundary_zero(self):
        g = Grid(4, 4)
        assert np.all(g.phi[0, :] == 0.0)
        assert np.all(g.phi[-1, :] == 0.0)
        assert np.all(g.phi[:, 0] == 0.0)
        assert np.all(g.phi[:, -1] == 0.0)

    def test_set_rhs(self):
        g = Grid(4, 4)
        g.set_rhs(lambda x, y: x + y)
        # Corner interior point (x=0.2, y=0.2)
        assert abs(g.rhs[1, 1] - (g.x[0] + g.y[0])) < 1e-12

    def test_residual_zero_phi(self):
        g = Grid(4, 4)
        g.set_rhs(lambda x, y: np.zeros_like(x))
        res = g.residual()
        assert np.allclose(res, 0.0)


# ---------------------------------------------------------------------------
# Manufactured solution: Jacobi
# ---------------------------------------------------------------------------

class TestJacobi:
    def test_converges(self):
        g = make_manufactured_grid(32, 32)
        iters, res = solvers.jacobi(g, maxiter=20000, tol=1e-6)
        assert res < 1e-6, f"Jacobi did not converge (residual={res:.2e})"

    def test_l2_error(self):
        g = make_manufactured_grid(32, 32)
        solvers.jacobi(g, maxiter=20000, tol=1e-7)
        err = l2_error(g)
        assert err < 1e-4, f"Jacobi L2 error {err:.2e} >= 1e-4"

    def test_returns_tuple(self):
        g = make_manufactured_grid(8, 8)
        result = solvers.jacobi(g, maxiter=1000, tol=1e-3)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Manufactured solution: Conjugate Gradient
# ---------------------------------------------------------------------------

class TestCG:
    def test_converges(self):
        g = make_manufactured_grid(32, 32)
        iters, res = solvers.cg(g, maxiter=5000, tol=1e-6)
        assert res < 1e-6, f"CG did not converge (residual={res:.2e})"

    def test_l2_error(self):
        g = make_manufactured_grid(32, 32)
        solvers.cg(g, maxiter=5000, tol=1e-7)
        err = l2_error(g)
        assert err < 1e-4, f"CG L2 error {err:.2e} >= 1e-4"

    def test_returns_tuple(self):
        g = make_manufactured_grid(8, 8)
        result = solvers.cg(g, maxiter=500, tol=1e-3)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Manufactured solution: Direct (sparse)
# ---------------------------------------------------------------------------

class TestDirect:
    def test_converges(self):
        g = make_manufactured_grid(32, 32)
        iters, res = solvers.direct(g)
        assert res < 1e-6, f"Direct solver residual {res:.2e} >= 1e-6"

    def test_l2_error(self):
        g = make_manufactured_grid(32, 32)
        solvers.direct(g)
        err = l2_error(g)
        assert err < 1e-4, f"Direct L2 error {err:.2e} >= 1e-4"

    def test_returns_tuple(self):
        g = make_manufactured_grid(8, 8)
        result = solvers.direct(g)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Neumann boundary condition test
# ---------------------------------------------------------------------------

class TestNeumann:
    def test_neumann_ghost_cell(self):
        """Zero-flux on left edge: phi[0,:] == phi[1,:]."""
        g = Grid(8, 8)
        g.neumann_left = True
        g.phi[1:-1, 1:-1] = np.random.default_rng(0).random((8, 8))
        g.apply_neumann()
        assert np.allclose(g.phi[0, :], g.phi[1, :])

    def test_neumann_top_ghost_cell(self):
        g = Grid(8, 8)
        g.neumann_top = True
        g.phi[1:-1, 1:-1] = np.random.default_rng(1).random((8, 8))
        g.apply_neumann()
        assert np.allclose(g.phi[:, -1], g.phi[:, -2])


# ---------------------------------------------------------------------------
# Unified solve() dispatcher
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_jacobi_dispatch(self):
        g = make_manufactured_grid(16, 16)
        it, res = solvers.solve(g, method='jacobi', tol=1e-4)
        assert res < 1e-4

    def test_cg_dispatch(self):
        g = make_manufactured_grid(16, 16)
        it, res = solvers.solve(g, method='cg', tol=1e-4)
        assert res < 1e-4

    def test_direct_dispatch(self):
        g = make_manufactured_grid(16, 16)
        it, res = solvers.solve(g, method='direct')
        assert res < 1e-4

    def test_unknown_method(self):
        g = make_manufactured_grid(4, 4)
        with pytest.raises(ValueError):
            solvers.solve(g, method='unknown')
