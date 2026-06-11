"""Grid class for the 2D Poisson solver."""

import numpy as np


class Grid:
    """Uniform 2D grid with solution array phi and RHS array f.

    Parameters
    ----------
    nx, ny : int
        Number of *interior* grid points in the x and y directions.
    xmin, xmax, ymin, ymax : float
        Domain boundaries (default unit square [0,1]x[0,1]).

    Attributes
    ----------
    phi : ndarray, shape (nx+2, ny+2)
        Solution array (includes boundary ghost layer).
    f : ndarray, shape (nx+2, ny+2)
        Right-hand-side source term.
    dx, dy : float
        Grid spacings.
    x, y : ndarray
        1-D coordinate arrays including boundary points.
    """

    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0,
                 bc_type=None):
        self.nx = nx
        self.ny = ny
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax

        # Boundary condition types per edge: 'dirichlet' (default) or 'neumann'
        # Keys: 'left', 'right', 'bottom', 'top'
        self.bc_type = {
            'left': 'dirichlet', 'right': 'dirichlet',
            'bottom': 'dirichlet', 'top': 'dirichlet',
        }
        if bc_type is not None:
            self.bc_type.update(bc_type)

        # Grid spacing (nx interior points => nx+1 intervals)
        self.dx = (xmax - xmin) / (nx + 1)
        self.dy = (ymax - ymin) / (ny + 1)

        # Coordinate vectors (including boundary)
        self.x = np.linspace(xmin, xmax, nx + 2)
        self.y = np.linspace(ymin, ymax, ny + 2)

        # Solution and RHS arrays (boundary + interior)
        self.phi = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        self.f = np.zeros((nx + 2, ny + 2), dtype=np.float64)

    def apply_neumann_bc(self):
        """Apply Neumann (zero-flux) BCs by copying adjacent interior values
        to ghost cells on the Neumann edges."""
        if self.bc_type['left'] == 'neumann':
            self.phi[0, :] = self.phi[1, :]
        if self.bc_type['right'] == 'neumann':
            self.phi[-1, :] = self.phi[-2, :]
        if self.bc_type['bottom'] == 'neumann':
            self.phi[:, 0] = self.phi[:, 1]
        if self.bc_type['top'] == 'neumann':
            self.phi[:, -1] = self.phi[:, -2]

    def interior_meshgrid(self):
        """Return meshgrid arrays for interior points only."""
        X, Y = np.meshgrid(self.x[1:-1], self.y[1:-1], indexing="ij")
        return X, Y

    def full_meshgrid(self):
        """Return meshgrid arrays for all points including boundary."""
        X, Y = np.meshgrid(self.x, self.y, indexing="ij")
        return X, Y
