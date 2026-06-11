"""Poisson solver package — 2D Poisson equation on a uniform grid."""

from .grid import Grid
from . import solvers

__all__ = ["Grid", "solvers"]
