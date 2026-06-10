"""Poisson solver package — 2D Poisson equation on a uniform grid."""

from .grid import Grid
from .solvers import jacobi_solve, cg_solve, direct_solve

__all__ = ["Grid", "jacobi_solve", "cg_solve", "direct_solve"]
