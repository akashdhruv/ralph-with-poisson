"""Grid class for the 2D Poisson solver."""

import numpy as np


class Grid:
    """Uniform 2-D grid on [xmin, xmax] x [ymin, ymax].

    The arrays ``phi`` and ``rhs`` have shape ``(nx + 2, ny + 2)`` so that
    rows 0, nx+1 and columns 0, ny+1 hold boundary values.  Interior points
    are indexed ``[1:nx+1, 1:ny+1]``.

    Parameters
    ----------
    nx, ny : int
        Number of *interior* grid points in x and y.
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

        # x and y coordinates including boundaries
        self.x = np.linspace(xmin, xmax, nx + 2)
        self.y = np.linspace(ymin, ymax, ny + 2)

        # 2-D coordinate arrays (full grid including boundaries)
        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")

        # Solution and right-hand side (initialised to zero → Dirichlet BCs)
        self.phi = np.zeros((nx + 2, ny + 2))
        self.rhs = np.zeros((nx + 2, ny + 2))

    # ------------------------------------------------------------------
    # Neumann helpers
    # ------------------------------------------------------------------
    def apply_neumann(self, edges=None):
        """Apply zero-flux Neumann BCs on the specified edges.

        ``edges`` is an iterable of strings chosen from
        ``{"left", "right", "bottom", "top"}``.  For each edge the
        boundary row/column is set equal to the adjacent interior
        row/column (zero normal gradient).
        """
        if edges is None:
            return
        for edge in edges:
            if edge == "left":
                self.phi[0, :] = self.phi[1, :]
            elif edge == "right":
                self.phi[-1, :] = self.phi[-2, :]
            elif edge == "bottom":
                self.phi[:, 0] = self.phi[:, 1]
            elif edge == "top":
                self.phi[:, -1] = self.phi[:, -2]
            else:
                raise ValueError(f"Unknown edge: {edge!r}")
