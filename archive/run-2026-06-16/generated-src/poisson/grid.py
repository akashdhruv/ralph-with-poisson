"""Grid class for 2-D Poisson problems."""

import numpy as np


class Grid:
    """Uniform rectangular grid on [xmin,xmax] x [ymin,ymax].

    Parameters
    ----------
    nx, ny : int
        Total number of grid points in each direction (including boundary).
        Interior points are at indices 1 .. nx-2  (resp. ny-2).
    xmin, xmax, ymin, ymax : float
        Domain extents (default unit square).
    """

    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        self.nx = nx
        self.ny = ny
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

        self.dx = (xmax - xmin) / (nx - 1)
        self.dy = (ymax - ymin) / (ny - 1)

        self.x = np.linspace(xmin, xmax, nx)
        self.y = np.linspace(ymin, ymax, ny)

        # Solution and RHS arrays – boundary rows/cols hold BC values
        self.phi = np.zeros((nx, ny), dtype=np.float64)
        self.rhs = np.zeros((nx, ny), dtype=np.float64)

        # Neumann flags: which boundary edges use zero-flux Neumann BC
        self.neumann = set()

    def apply_neumann(self):
        """Apply zero-flux Neumann BCs by copying adjacent interior values
        into the ghost (boundary) cells."""
        if 'left' in self.neumann:
            self.phi[0, :] = self.phi[1, :]
        if 'right' in self.neumann:
            self.phi[-1, :] = self.phi[-2, :]
        if 'bottom' in self.neumann:
            self.phi[:, 0] = self.phi[:, 1]
        if 'top' in self.neumann:
            self.phi[:, -1] = self.phi[:, -2]

    def interior_coords(self):
        """Return 2-D arrays of interior x, y coordinates."""
        XX, YY = np.meshgrid(self.x, self.y, indexing='ij')
        return XX, YY
