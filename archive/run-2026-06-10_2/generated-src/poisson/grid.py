"""Grid class for the 2D Poisson solver."""

import numpy as np


class Grid:
    """Uniform 2D grid with solution array phi and RHS array f.

    The arrays have shape (nx+2, ny+2) to include boundary ghost cells.
    Boundary rows/columns hold the BC values (zero for Dirichlet by default).
    Interior points are indexed [1:nx+1, 1:ny+1].
    """

    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0,
                 neumann=None):
        self.nx = nx
        self.ny = ny
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.dx = (xmax - xmin) / (nx + 1)
        self.dy = (ymax - ymin) / (ny + 1)

        # Coordinate arrays for interior + boundary points
        self.x = np.linspace(xmin, xmax, nx + 2)
        self.y = np.linspace(ymin, ymax, ny + 2)

        # Solution and RHS arrays (including boundary)
        self.phi = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        self.f = np.zeros((nx + 2, ny + 2), dtype=np.float64)

        # Neumann boundary edges — subset of {'left','right','top','bottom'}
        self.neumann = set(neumann) if neumann else set()

    def apply_bc(self):
        """Apply boundary conditions.

        For Neumann (zero-flux) edges, set the ghost cell value equal to the
        adjacent interior value.  Dirichlet edges are left untouched (they
        keep whatever value is stored — typically zero).
        """
        if 'left' in self.neumann:
            self.phi[0, :] = self.phi[1, :]
        if 'right' in self.neumann:
            self.phi[-1, :] = self.phi[-2, :]
        if 'bottom' in self.neumann:
            self.phi[:, 0] = self.phi[:, 1]
        if 'top' in self.neumann:
            self.phi[:, -1] = self.phi[:, -2]
