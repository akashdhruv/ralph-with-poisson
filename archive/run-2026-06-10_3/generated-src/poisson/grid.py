"""Grid class for the 2D Poisson solver."""

import numpy as np


class Grid:
    """Uniform 2D grid with solution array phi and RHS array f.

    The grid has (nx+2) x (ny+2) total points including boundary rows/columns.
    Interior points are indexed [1:nx+1, 1:ny+1].
    Boundary rows/columns hold BC values (zero for Dirichlet by default).
    """

    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        self.nx = nx
        self.ny = ny
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        # Grid spacings
        self.dx = (xmax - xmin) / (nx + 1)
        self.dy = (ymax - ymin) / (ny + 1)

        # Coordinate arrays (including boundary points)
        self.x = np.linspace(xmin, xmax, nx + 2)
        self.y = np.linspace(ymin, ymax, ny + 2)

        # 2D coordinate meshes
        self.X, self.Y = np.meshgrid(self.x, self.y, indexing='ij')

        # Solution and RHS arrays — (nx+2) x (ny+2)
        self.phi = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        self.f = np.zeros((nx + 2, ny + 2), dtype=np.float64)

        # Neumann BC flags: dict mapping edge name to True/False
        # edges: 'left', 'right', 'bottom', 'top'
        self.neumann = {'left': False, 'right': False, 'bottom': False, 'top': False}

    def apply_neumann(self):
        """Apply Neumann (zero-flux) BCs by setting ghost values equal to
        adjacent interior values."""
        if self.neumann.get('left'):
            self.phi[0, :] = self.phi[1, :]
        if self.neumann.get('right'):
            self.phi[-1, :] = self.phi[-2, :]
        if self.neumann.get('bottom'):
            self.phi[:, 0] = self.phi[:, 1]
        if self.neumann.get('top'):
            self.phi[:, -1] = self.phi[:, -2]

    def laplacian(self, u=None):
        """Compute the discrete Laplacian of u (defaults to self.phi).
        Returns an array of shape (nx+2, ny+2); only interior values are meaningful."""
        if u is None:
            u = self.phi
        dx2 = self.dx ** 2
        dy2 = self.dy ** 2
        L = np.zeros_like(u)
        L[1:-1, 1:-1] = (
            (u[2:, 1:-1] - 2 * u[1:-1, 1:-1] + u[:-2, 1:-1]) / dx2
            + (u[1:-1, 2:] - 2 * u[1:-1, 1:-1] + u[1:-1, :-2]) / dy2
        )
        return L

    def residual(self):
        """Compute residual r = f - L(phi) at interior points.
        Returns full-sized array (only interior values are meaningful)."""
        return self.f - self.laplacian()

    def residual_l2(self):
        """L2 norm of the residual at interior points."""
        r = self.residual()
        return np.sqrt(np.sum(r[1:-1, 1:-1] ** 2))
