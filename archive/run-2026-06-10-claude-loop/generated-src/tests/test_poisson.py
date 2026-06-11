import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from poisson import Grid
from poisson import solvers


def _manufactured_grid(n=32):
    """Return a Grid set up for φ_exact = sin(πx)sin(πy), f = -2π²φ_exact."""
    g = Grid(n, n)
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    g.f[:] = -2 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    # Dirichlet BC: phi=0 on boundary (already zero by default)
    return g, X, Y


def _l2_error(g, X, Y):
    phi_exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    return float(np.linalg.norm(g.phi - phi_exact) * g.dx * g.dy)


class TestGrid:
    def test_shape(self):
        g = Grid(10, 12)
        assert g.phi.shape == (10, 12)
        assert g.f.shape == (10, 12)

    def test_spacing(self):
        g = Grid(5, 5)
        assert abs(g.dx - 0.25) < 1e-12
        assert abs(g.dy - 0.25) < 1e-12

    def test_coordinates(self):
        g = Grid(3, 3)
        np.testing.assert_allclose(g.x, [0.0, 0.5, 1.0])
        np.testing.assert_allclose(g.y, [0.0, 0.5, 1.0])


class TestJacobi:
    def test_manufactured(self):
        g, X, Y = _manufactured_grid(32)
        iters, res = solvers.jacobi(g, maxiter=20000, tol=1e-6)
        err = _l2_error(g, X, Y)
        assert err < 1e-4, f"Jacobi L2 error {err:.2e} >= 1e-4"

    def test_returns_tuple(self):
        g, _, _ = _manufactured_grid(8)
        result = solvers.jacobi(g, maxiter=100, tol=1e-6)
        assert len(result) == 2


class TestCG:
    def test_manufactured(self):
        g, X, Y = _manufactured_grid(32)
        iters, res = solvers.cg(g, maxiter=10000, tol=1e-8)
        err = _l2_error(g, X, Y)
        assert err < 1e-4, f"CG L2 error {err:.2e} >= 1e-4"

    def test_converges_fast(self):
        g, _, _ = _manufactured_grid(16)
        iters, _ = solvers.cg(g, maxiter=10000, tol=1e-8)
        assert iters < 2000


class TestDirect:
    def test_manufactured(self):
        g, X, Y = _manufactured_grid(32)
        solvers.direct(g)
        err = _l2_error(g, X, Y)
        assert err < 1e-4, f"Direct L2 error {err:.2e} >= 1e-4"


class TestNeumann:
    def test_neumann_left(self):
        """With Neumann on left and Dirichlet on other three edges, solution should be smooth."""
        g = Grid(16, 16)
        X, Y = np.meshgrid(g.x, g.y, indexing="ij")
        g.f[:] = -2 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
        g.neumann_edges.add("left")
        iters, res = solvers.jacobi(g, maxiter=20000, tol=1e-5)
        # just check it doesn't blow up
        assert np.all(np.isfinite(g.phi))
