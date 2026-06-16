import numpy as np


class Grid:
    """2D uniform grid for the Poisson equation on [xmin,xmax] x [ymin,ymax].

    The arrays ``phi`` and ``rhs`` have shape ``(nx+2, ny+2)`` so that
    rows/columns 0 and nx+1 (resp. ny+1) hold boundary values.
    Interior indices run from 1..nx, 1..ny.

    Parameters
    ----------
    nx, ny : int
        Number of *interior* points in the x- and y-directions.
    xmin, xmax, ymin, ymax : float
        Domain extents (default unit square).
    """

    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        self.nx = nx
        self.ny = ny
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

        self.dx = (xmax - xmin) / (nx + 1)
        self.dy = (ymax - ymin) / (ny + 1)

        # phi (solution) and rhs (source term f) including boundary ring
        self.phi = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        self.rhs = np.zeros((nx + 2, ny + 2), dtype=np.float64)

        # Coordinate arrays (including boundary points)
        self.x = xmin + np.arange(nx + 2) * self.dx
        self.y = ymin + np.arange(ny + 2) * self.dy

        # Neumann flags — one per edge.  False = Dirichlet (default).
        # When True the edge uses zero-flux (∂φ/∂n = 0).
        self.neumann = {
            "left": False,
            "right": False,
            "bottom": False,
            "top": False,
        }

    # ------------------------------------------------------------------ #
    # Neumann helpers                                                      #
    # ------------------------------------------------------------------ #
    def apply_neumann(self):
        """Copy adjacent interior values to boundary rows/columns that are
        flagged as Neumann (zero-flux: ghost = interior neighbour)."""
        if self.neumann["left"]:
            self.phi[0, :] = self.phi[1, :]
        if self.neumann["right"]:
            self.phi[-1, :] = self.phi[-2, :]
        if self.neumann["bottom"]:
            self.phi[:, 0] = self.phi[:, 1]
        if self.neumann["top"]:
            self.phi[:, -1] = self.phi[:, -2]
