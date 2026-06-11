import numpy as np


class Grid:
    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        self.nx = nx
        self.ny = ny
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.dx = (xmax - xmin) / (nx - 1)
        self.dy = (ymax - ymin) / (ny - 1)
        self.x = np.linspace(xmin, xmax, nx)
        self.y = np.linspace(ymin, ymax, ny)
        # phi: solution array; boundary rows/cols hold BC values (zero = Dirichlet)
        self.phi = np.zeros((nx, ny))
        # f: right-hand side (source term)
        self.f = np.zeros((nx, ny))
        # neumann_edges: set of edges ('left','right','bottom','top') with zero-flux BC
        self.neumann_edges = set()
