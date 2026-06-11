"""Grid class for the 2D Poisson solver."""

import numpy as np


class Grid:
    """Uniform 2D grid for solving ∇²φ = f on [xmin,xmax] × [ymin,ymax].

    The grid has (nx+2) × (ny+2) total nodes including boundary layers.
    Interior indices run from 1 to nx (x) and 1 to ny (y).
    Boundary rows/columns of phi hold the BC values (zero for Dirichlet by default).

    Parameters
    ----------
    nx, ny : int
        Number of interior grid points in x and y.
    xmin, xmax : float
        Domain extent in x.
    ymin, ymax : float
        Domain extent in y.
    """

    def __init__(self, nx: int, ny: int,
                 xmin: float = 0.0, xmax: float = 1.0,
                 ymin: float = 0.0, ymax: float = 1.0) -> None:
        self.nx = nx
        self.ny = ny
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

        self.dx = (xmax - xmin) / (nx + 1)
        self.dy = (ymax - ymin) / (ny + 1)

        # 1-D coordinate arrays for interior points
        self.x = np.linspace(xmin + self.dx, xmax - self.dx, nx)
        self.y = np.linspace(ymin + self.dy, ymax - self.dy, ny)

        # Full arrays including boundary: shape (nx+2, ny+2)
        # phi[0,:], phi[-1,:], phi[:,0], phi[:,-1] are boundary values (0 for Dirichlet)
        self.phi = np.zeros((nx + 2, ny + 2), dtype=float)
        self.rhs = np.zeros((nx + 2, ny + 2), dtype=float)

        # Neumann edge flags: set True to apply zero-flux ghost cell on that edge
        self.neumann_left = False    # i = 0  edge (x = xmin)
        self.neumann_right = False   # i = -1 edge (x = xmax)
        self.neumann_bottom = False  # j = 0  edge (y = ymin)
        self.neumann_top = False     # j = -1 edge (y = ymax)

    # ------------------------------------------------------------------
    # Convenience: set RHS on interior points via a callable f(x, y)
    # ------------------------------------------------------------------
    def set_rhs(self, func) -> None:
        """Set rhs on interior points from func(x_2d, y_2d)."""
        X, Y = np.meshgrid(self.x, self.y, indexing='ij')
        self.rhs[1:-1, 1:-1] = func(X, Y)

    # ------------------------------------------------------------------
    # Apply Neumann ghost-cell correction (zero normal flux)
    # ------------------------------------------------------------------
    def apply_neumann(self) -> None:
        """Mirror adjacent interior values into boundary rows/columns for
        active Neumann edges (zero-flux condition)."""
        if self.neumann_left:
            self.phi[0, :] = self.phi[1, :]
        if self.neumann_right:
            self.phi[-1, :] = self.phi[-2, :]
        if self.neumann_bottom:
            self.phi[:, 0] = self.phi[:, 1]
        if self.neumann_top:
            self.phi[:, -1] = self.phi[:, -2]

    # ------------------------------------------------------------------
    # Discrete Laplacian applied to phi (returns interior values only)
    # ------------------------------------------------------------------
    def laplacian(self) -> np.ndarray:
        """Compute L(φ) at all interior points. Returns array of shape (nx, ny)."""
        phi = self.phi
        dx2 = self.dx ** 2
        dy2 = self.dy ** 2
        lap = ((phi[2:, 1:-1] - 2 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) / dx2
               + (phi[1:-1, 2:] - 2 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) / dy2)
        return lap

    # ------------------------------------------------------------------
    # Residual r = f - L(φ) on interior points
    # ------------------------------------------------------------------
    def residual(self) -> np.ndarray:
        """Compute residual r = rhs - L(φ) on interior points. Shape (nx, ny)."""
        return self.rhs[1:-1, 1:-1] - self.laplacian()
