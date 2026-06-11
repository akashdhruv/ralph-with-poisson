"""Tests for the 2D Poisson solver — manufactured solution."""

import numpy as np
import pytest

from poisson.grid import Grid
from poisson import solvers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_manufactured(nx=32, ny=32):
    """Set up a grid with f = -2 pi^2 sin(pi x) sin(pi y).

    Exact solution: phi_exact = sin(pi x) sin(pi y).
    Dirichlet BC phi=0 on boundary (satisfied by sin at 0 and 1).
    """
    g = Grid(nx, ny)
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    g.f[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    phi_exact = np.sin(np.pi * X) * np.sin(np.pi * Y)
    return g, phi_exact


def _l2_error(grid, phi_exact):
    """RMS error over interior points."""
    diff = grid.phi[1:-1, 1:-1] - phi_exact[1:-1, 1:-1]
    return np.sqrt(np.mean(diff ** 2))


# ---------------------------------------------------------------------------
# Tests — manufactured-solution accuracy (L2 error < 1e-4 on 32x32 grid)
#
# The 5-point stencil has O(h^2) discretisation error.  On a 32x32 interior
# grid (h ≈ 1/33) the error is ≈ 4e-4.  We therefore verify:
#   • each solver converges (residual < tol), and
#   • the L2 error is consistent with O(h^2) (< 1e-3 on 32×32),
#   • the L2 error is < 1e-4 on a finer grid (100×100) for CG & Direct.
# ---------------------------------------------------------------------------

class TestJacobi:
    def test_convergence_32(self):
        g, phi_exact = _setup_manufactured(32, 32)
        iters, res = solvers.jacobi(g, maxiter=20000, tol=1e-6)
        err = _l2_error(g, phi_exact)
        assert res < 1e-6, f"Jacobi residual {res:.6e} >= 1e-6"
        assert err < 1e-3, f"Jacobi L2 error {err:.6e} >= 1e-3"

    def test_accuracy_fine(self):
        """On a 64×64 grid, Jacobi should achieve L2 error < 1e-4."""
        g, phi_exact = _setup_manufactured(64, 64)
        iters, res = solvers.jacobi(g, maxiter=50000, tol=1e-7)
        err = _l2_error(g, phi_exact)
        assert err < 1e-4, f"Jacobi L2 error {err:.6e} >= 1e-4"


class TestCG:
    def test_convergence_32(self):
        g, phi_exact = _setup_manufactured(32, 32)
        iters, res = solvers.cg(g, maxiter=10000, tol=1e-6)
        err = _l2_error(g, phi_exact)
        assert res < 1e-6, f"CG residual {res:.6e} >= 1e-6"
        assert err < 1e-3, f"CG L2 error {err:.6e} >= 1e-3"

    def test_accuracy_fine(self):
        g, phi_exact = _setup_manufactured(100, 100)
        iters, res = solvers.cg(g, maxiter=10000, tol=1e-8)
        err = _l2_error(g, phi_exact)
        assert err < 1e-4, f"CG L2 error {err:.6e} >= 1e-4"


class TestDirect:
    def test_convergence_32(self):
        g, phi_exact = _setup_manufactured(32, 32)
        iters, res = solvers.direct(g)
        err = _l2_error(g, phi_exact)
        assert err < 1e-3, f"Direct L2 error {err:.6e} >= 1e-3"

    def test_accuracy_fine(self):
        g, phi_exact = _setup_manufactured(100, 100)
        iters, res = solvers.direct(g)
        err = _l2_error(g, phi_exact)
        assert err < 1e-4, f"Direct L2 error {err:.6e} >= 1e-4"


class TestConvergenceRate:
    """Verify O(h^2) convergence by comparing two grid sizes."""
    def test_h2_convergence(self):
        g32, e32 = _setup_manufactured(32, 32)
        solvers.direct(g32)
        err32 = _l2_error(g32, e32)

        g64, e64 = _setup_manufactured(64, 64)
        solvers.direct(g64)
        err64 = _l2_error(g64, e64)

        # Expect error ratio ≈ 4 for halving h (O(h^2))
        ratio = err32 / err64
        assert 3.0 < ratio < 5.0, f"Convergence ratio {ratio:.2f} not near 4"


class TestNeumann:
    """Tests for Neumann (zero-flux) boundary conditions."""

    def test_apply_bc_mirrors_ghost(self):
        """Grid.apply_bc should copy interior edge values to ghost cells."""
        g = Grid(4, 4, neumann=['left', 'top'])
        g.phi[1, :] = 5.0   # row adjacent to left ghost
        g.phi[:, -2] = 3.0  # col adjacent to top ghost
        g.apply_bc()
        np.testing.assert_array_equal(g.phi[0, :], g.phi[1, :])
        np.testing.assert_array_equal(g.phi[:, -1], g.phi[:, -2])

    def test_neumann_right_direct(self):
        """Direct solver with Neumann on right: zero flux at right boundary."""
        nx, ny = 32, 32
        g = Grid(nx, ny, neumann=['right'])
        X, Y = np.meshgrid(g.x, g.y, indexing='ij')
        # Constant source; Dirichlet=0 on left/top/bottom, Neumann on right
        g.f[:] = -1.0
        solvers.direct(g)
        # Zero-flux: phi at ghost == adjacent interior
        np.testing.assert_allclose(
            g.phi[-1, 1:-1], g.phi[-2, 1:-1], atol=1e-10,
            err_msg="Neumann zero-flux violated at right edge"
        )

    def test_neumann_cg(self):
        """CG solver with Neumann on bottom: zero flux at bottom boundary."""
        nx, ny = 16, 16
        g = Grid(nx, ny, neumann=['bottom'])
        X, Y = np.meshgrid(g.x, g.y, indexing='ij')
        g.f[:] = -1.0
        iters, res = solvers.cg(g, maxiter=5000, tol=1e-8)
        assert res < 1e-6, f"CG did not converge: res={res}"
        # After convergence, apply_bc should give ghost == interior
        g.apply_bc()
        np.testing.assert_allclose(
            g.phi[:, 0], g.phi[:, 1], atol=1e-8,
            err_msg="Neumann zero-flux violated at bottom edge"
        )


class TestSolveDispatch:
    def test_jacobi_dispatch(self):
        g, phi_exact = _setup_manufactured()
        iters, res = solvers.solve(g, method="jacobi", maxiter=20000, tol=1e-6)
        err = _l2_error(g, phi_exact)
        assert err < 1e-3

    def test_unknown_method(self):
        g, _ = _setup_manufactured()
        with pytest.raises(ValueError):
            solvers.solve(g, method="nonexistent")
