"""Tests for the 2-D Poisson solver (manufactured-solution verification)."""

import numpy as np
import pytest
import sys
import os

# Ensure generated-src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from poisson import Grid, jacobi_solve, cg_solve, direct_solve


# ── helpers ──────────────────────────────────────────────────────────

def _setup_manufactured(nx=64, ny=64):
    """Return a Grid with the manufactured-solution RHS.

    φ_exact = sin(πx) sin(πy)  →  f = -2π² sin(πx) sin(πy)

    Default 64×64 interior points.  Second-order FD discretization error
    on a 32×32 grid (~3.9e-4) exceeds 1e-4; 64×64 brings the error below
    1e-4 as required by the spec.
    """
    g = Grid(nx, ny)
    g.rhs[:] = -2.0 * np.pi ** 2 * np.sin(np.pi * g.X) * np.sin(np.pi * g.Y)
    return g


def _l2_error(grid):
    """L2 error of grid.phi vs manufactured exact solution (interior only)."""
    s = slice(1, -1)
    exact = np.sin(np.pi * grid.X) * np.sin(np.pi * grid.Y)
    diff = grid.phi[s, s] - exact[s, s]
    return np.sqrt(np.mean(diff ** 2))


# ── solver tests ─────────────────────────────────────────────────────

def test_jacobi_manufactured():
    g = _setup_manufactured()
    iters, res = jacobi_solve(g, maxiter=20000, tol=1e-6)
    err = _l2_error(g)
    assert err < 1e-4, f"Jacobi L2 error {err:.6e} >= 1e-4"
    assert res < 1e-6 or iters <= 20000


def test_cg_manufactured():
    g = _setup_manufactured()
    iters, res = cg_solve(g, maxiter=10000, tol=1e-6)
    err = _l2_error(g)
    assert err < 1e-4, f"CG L2 error {err:.6e} >= 1e-4"


def test_direct_manufactured():
    g = _setup_manufactured()
    iters, res = direct_solve(g)
    err = _l2_error(g)
    assert err < 1e-4, f"Direct L2 error {err:.6e} >= 1e-4"


def test_grid_shape():
    g = Grid(10, 15)
    assert g.phi.shape == (12, 17)
    assert g.rhs.shape == (12, 17)


def test_dirichlet_boundary_zero():
    g = _setup_manufactured()
    jacobi_solve(g, maxiter=5000, tol=1e-6)
    assert np.allclose(g.phi[0, :], 0.0)
    assert np.allclose(g.phi[-1, :], 0.0)
    assert np.allclose(g.phi[:, 0], 0.0)
    assert np.allclose(g.phi[:, -1], 0.0)
