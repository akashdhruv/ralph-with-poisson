# Poisson Solver — Technical Specification

## Problem

Solve the 2D Poisson equation on a uniform grid:

```
∇²φ = f    on Ω = [0,1] × [0,1]
```

with Dirichlet boundary conditions φ = 0 on ∂Ω (default), or Neumann where specified.

## Module Layout

IMPORTANT: All code lives under `generated-src/`:

```
generated-src/
  poisson/
    __init__.py
    grid.py       # Grid class
    solvers.py    # Solver implementations
  demo.py         # Convergence demo
  tests/
    test_poisson.py
```

## Grid (`poisson/grid.py`)

```python
class Grid:
    def __init__(self, nx, ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0):
        ...
    # Attributes:
    #   nx, ny        : number of interior cells in x and y
    #   dx, dy        : cell spacings
    #   x, y          : 1D coordinate arrays (cell centers)
    #   phi           : 2D numpy array (nx, ny), solution φ — initialise to zeros
    #   rhs           : 2D numpy array (nx, ny), right-hand side f
```

The discrete Laplacian at interior point (i, j) using second-order finite differences:

```
L(φ)[i,j] = (φ[i+1,j] - 2φ[i,j] + φ[i-1,j]) / dx²
           + (φ[i,j+1] - 2φ[i,j] + φ[i,j-1]) / dy²
```

Boundary rows/columns of `phi` hold the BC values (zero for Dirichlet).

## Solvers (`poisson/solvers.py`)

All solvers share this signature:

```python
def solve(grid, maxiter=10000, tol=1e-6, verbose=False):
    """
    Solve ∇²φ = f in-place on grid.phi.
    Returns: (iterations, final_residual)
    """
```

### Jacobi

Update rule for interior points:

```
φ_new[i,j] = ( (φ[i+1,j] + φ[i-1,j]) / dx²
              + (φ[i,j+1] + φ[i,j-1]) / dy²
              - rhs[i,j] ) / (2/dx² + 2/dy²)
```

Convergence: L2 norm of residual `r = f - L(φ)` < `tol`.

### Conjugate Gradient (numpy only, no scipy)

Standard CG on the flattened interior system. Define `A(p)` as the application of the discrete Laplacian to a vector `p` reshaped to `(nx, ny)`. Convergence on `‖r‖₂ < tol`.

### Direct (scipy)

Assemble the sparse `(nx*ny) × (nx*ny)` Laplacian matrix and solve with `scipy.sparse.linalg.spsolve`.

### Neumann Boundary Conditions

For a Neumann edge, zero-flux means ghost cell value equals the adjacent interior value. Apply before each residual evaluation.

## Testing (`tests/test_poisson.py`)

**Manufactured solution**: choose φ_exact = sin(πx)sin(πy), which gives f = −2π²φ_exact.

Check that each solver achieves L2 error < 1e-4 on a 32×32 grid.
