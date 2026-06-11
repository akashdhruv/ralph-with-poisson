"""Iterative and direct solvers for the 2D Poisson equation."""

import numpy as np
import scipy.sparse
import scipy.sparse.linalg


# ---------------------------------------------------------------------------
# Jacobi iterative solver
# ---------------------------------------------------------------------------

def jacobi(grid, maxiter: int = 10000, tol: float = 1e-6, verbose: bool = False):
    """Solve ∇²φ = f in-place on grid.phi using Jacobi iteration.

    Parameters
    ----------
    grid    : Grid object (phi and rhs arrays live here)
    maxiter : maximum number of iterations
    tol     : convergence tolerance on L2 norm of residual
    verbose : if True, print residual every 100 iterations

    Returns
    -------
    (iterations, final_residual)
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2
    rhs_int = grid.rhs[1:-1, 1:-1]

    for it in range(1, maxiter + 1):
        grid.apply_neumann()

        phi = grid.phi
        phi_new = ((phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
                   + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
                   - rhs_int) / denom

        grid.phi[1:-1, 1:-1] = phi_new

        # Residual
        res = np.linalg.norm(grid.residual()) * grid.dx * grid.dy
        if verbose and it % 100 == 0:
            print(f"  Jacobi iter {it:5d}  residual = {res:.3e}")
        if res < tol:
            return it, res

    return maxiter, np.linalg.norm(grid.residual()) * grid.dx * grid.dy


# ---------------------------------------------------------------------------
# Conjugate Gradient solver (numpy only)
# ---------------------------------------------------------------------------

def cg(grid, maxiter: int = 10000, tol: float = 1e-6, verbose: bool = False):
    """Solve ∇²φ = f in-place on grid.phi using the conjugate gradient method.

    Works on the flattened interior system.  A(p) is the application of the
    negative discrete Laplacian (positive definite) to a vector p.

    Returns
    -------
    (iterations, final_residual)
    """
    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2

    # Build A(p) operator — applies -L to interior vector p (shape nx*ny)
    # We work with -L because L is negative definite; CG needs SPD.
    def matvec(p):
        P = p.reshape(nx, ny)
        # Zero-pad with boundary contributions (Dirichlet = 0 by default).
        # For Neumann edges the ghost contribution cancels, so we treat boundary
        # as zero for the matrix-vector product here; BCs are absorbed into rhs.
        P_full = np.zeros((nx + 2, ny + 2))
        P_full[1:-1, 1:-1] = P
        lap = ((P_full[2:, 1:-1] - 2 * P_full[1:-1, 1:-1] + P_full[:-2, 1:-1]) / dx2
               + (P_full[1:-1, 2:] - 2 * P_full[1:-1, 1:-1] + P_full[1:-1, :-2]) / dy2)
        return -lap.ravel()

    # RHS: b = -f + boundary contributions (absorbed; boundaries are 0 here)
    # Sign convention: solve -L phi = -f  →  Ax = b with A = -L, b = -rhs
    b = -grid.rhs[1:-1, 1:-1].ravel()

    # Initial guess from current phi
    x = grid.phi[1:-1, 1:-1].ravel().copy()

    r = b - matvec(x)
    p = r.copy()
    rs_old = r @ r

    res_norm = np.sqrt(rs_old) * grid.dx * grid.dy

    for it in range(1, maxiter + 1):
        Ap = matvec(p)
        alpha = rs_old / (p @ Ap)
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = r @ r
        res_norm = np.sqrt(rs_new) * grid.dx * grid.dy

        if verbose and it % 50 == 0:
            print(f"  CG iter {it:5d}  residual = {res_norm:.3e}")

        if res_norm < tol:
            grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
            return it, res_norm

        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
    return maxiter, res_norm


# ---------------------------------------------------------------------------
# Direct sparse solver via scipy
# ---------------------------------------------------------------------------

def direct(grid, maxiter: int = 1, tol: float = 1e-6, verbose: bool = False):
    """Solve ∇²φ = f in-place on grid.phi using scipy sparse direct solver.

    Assembles the (nx*ny) × (nx*ny) sparse Laplacian matrix and calls
    scipy.sparse.linalg.spsolve.

    maxiter and tol are accepted for API compatibility but are not used.

    Returns
    -------
    (1, final_residual)   — direct solver needs only one 'iteration'
    """
    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    N = nx * ny

    diag_val = -(2.0 / dx2 + 2.0 / dy2)
    off_x = 1.0 / dx2
    off_y = 1.0 / dy2

    # Build 1-D index: point (i, j) → i * ny + j
    rows, cols, data = [], [], []

    for i in range(nx):
        for j in range(ny):
            idx = i * ny + j

            # Diagonal
            rows.append(idx); cols.append(idx); data.append(diag_val)

            # x-neighbours
            if i > 0:
                rows.append(idx); cols.append((i - 1) * ny + j); data.append(off_x)
            if i < nx - 1:
                rows.append(idx); cols.append((i + 1) * ny + j); data.append(off_x)

            # y-neighbours
            if j > 0:
                rows.append(idx); cols.append(i * ny + j - 1); data.append(off_y)
            if j < ny - 1:
                rows.append(idx); cols.append(i * ny + j + 1); data.append(off_y)

    A = scipy.sparse.csr_matrix((data, (rows, cols)), shape=(N, N))

    # RHS: subtract boundary contributions (already zero for Dirichlet)
    rhs_flat = grid.rhs[1:-1, 1:-1].ravel().copy()

    # Subtract boundary phi contributions
    phi = grid.phi
    rhs_vec = rhs_flat.copy()
    for i in range(nx):
        j_idx = i * ny
        # left boundary (i==0)
        if i == 0:
            rhs_vec[j_idx:j_idx + ny] -= off_x * phi[0, 1:-1]
        # right boundary (i==nx-1)
        if i == nx - 1:
            rhs_vec[j_idx:j_idx + ny] -= off_x * phi[nx + 1, 1:-1]
        # bottom boundary (j==0) and top boundary (j==ny-1)
        rhs_vec[i * ny + 0] -= off_y * phi[i + 1, 0]
        rhs_vec[i * ny + ny - 1] -= off_y * phi[i + 1, ny + 1]

    sol = scipy.sparse.linalg.spsolve(A, rhs_vec)
    grid.phi[1:-1, 1:-1] = sol.reshape(nx, ny)

    res = np.linalg.norm(grid.residual()) * grid.dx * grid.dy
    if verbose:
        print(f"  Direct solver  residual = {res:.3e}")

    return 1, res


# ---------------------------------------------------------------------------
# Unified interface
# ---------------------------------------------------------------------------

def solve(grid, method: str = "jacobi", maxiter: int = 10000,
          tol: float = 1e-6, verbose: bool = False):
    """Dispatch to the requested solver.

    Parameters
    ----------
    method : 'jacobi', 'cg', or 'direct'

    Returns
    -------
    (iterations, final_residual)
    """
    methods = {"jacobi": jacobi, "cg": cg, "direct": direct}
    if method not in methods:
        raise ValueError(f"Unknown method '{method}'. Choose from {list(methods)}")
    return methods[method](grid, maxiter=maxiter, tol=tol, verbose=verbose)
