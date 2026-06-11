"""Solvers for the 2D Poisson equation: Jacobi, CG, and Direct."""

import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _laplacian(phi, dx, dy):
    """Apply the discrete Laplacian to phi, returning an array of the same shape.

    Only interior values are meaningful; boundary values are set to zero.
    """
    L = np.zeros_like(phi)
    dx2 = dx * dx
    dy2 = dy * dy
    L[1:-1, 1:-1] = (
        (phi[2:, 1:-1] - 2.0 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) / dx2
        + (phi[1:-1, 2:] - 2.0 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) / dy2
    )
    return L


def _residual(grid):
    """Compute residual r = f - L(phi) at interior points.

    Applies Neumann ghost-cell update before evaluating the Laplacian.
    """
    grid.apply_bc()
    L = _laplacian(grid.phi, grid.dx, grid.dy)
    r = np.zeros_like(grid.phi)
    r[1:-1, 1:-1] = grid.f[1:-1, 1:-1] - L[1:-1, 1:-1]
    return r


def _residual_l2(grid):
    """L2 norm of the residual over interior points."""
    r = _residual(grid)
    return np.sqrt(np.sum(r[1:-1, 1:-1] ** 2))


# ---------------------------------------------------------------------------
# Jacobi solver
# ---------------------------------------------------------------------------

def jacobi(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve nabla^2 phi = f in-place on grid.phi using Jacobi iteration.

    Returns
    -------
    (iterations, final_residual)
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2

    for it in range(1, maxiter + 1):
        grid.apply_bc()
        phi = grid.phi
        phi_new = phi.copy()
        phi_new[1:-1, 1:-1] = (
            (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
            + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
            - grid.f[1:-1, 1:-1]
        ) / denom
        grid.phi = phi_new

        res = _residual_l2(grid)
        if verbose and it % 500 == 0:
            print(f"Jacobi iter {it}: residual = {res:.6e}")
        if res < tol:
            if verbose:
                print(f"Jacobi converged at iter {it}: residual = {res:.6e}")
            return it, res

    res = _residual_l2(grid)
    if verbose:
        print(f"Jacobi did NOT converge after {maxiter} iters: residual = {res:.6e}")
    return maxiter, res


# ---------------------------------------------------------------------------
# Conjugate Gradient solver
# ---------------------------------------------------------------------------

def cg(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve nabla^2 phi = f in-place using Conjugate Gradient on the interior.

    The operator A(p) is the discrete Laplacian applied to p (interior only).

    Returns
    -------
    (iterations, final_residual)
    """
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy

    neumann = grid.neumann

    def apply_A(v_interior):
        """Apply discrete Laplacian to an interior-sized vector."""
        full = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        full[1:-1, 1:-1] = v_interior.reshape(nx, ny)
        # Apply Neumann ghost-cell mirroring
        if 'left' in neumann:
            full[0, :] = full[1, :]
        if 'right' in neumann:
            full[-1, :] = full[-2, :]
        if 'bottom' in neumann:
            full[:, 0] = full[:, 1]
        if 'top' in neumann:
            full[:, -1] = full[:, -2]
        L = _laplacian(full, dx, dy)
        return L[1:-1, 1:-1].ravel()

    # RHS for interior
    b = grid.f[1:-1, 1:-1].ravel().copy()

    # Initial guess from current phi
    x = grid.phi[1:-1, 1:-1].ravel().copy()

    # r = b - A x
    r = b - apply_A(x)
    p = r.copy()
    rs_old = np.dot(r, r)

    for it in range(1, maxiter + 1):
        Ap = apply_A(p)
        pAp = np.dot(p, Ap)
        if pAp == 0.0:
            break
        alpha = rs_old / pAp
        x += alpha * p
        r -= alpha * Ap
        rs_new = np.dot(r, r)
        res_norm = np.sqrt(rs_new)

        if verbose and it % 100 == 0:
            print(f"CG iter {it}: residual = {res_norm:.6e}")
        if res_norm < tol:
            grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
            if verbose:
                print(f"CG converged at iter {it}: residual = {res_norm:.6e}")
            return it, res_norm

        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
    res = _residual_l2(grid)
    if verbose:
        print(f"CG did NOT converge after {maxiter} iters: residual = {res:.6e}")
    return maxiter, res


# ---------------------------------------------------------------------------
# Direct solver
# ---------------------------------------------------------------------------

def direct(grid, maxiter=None, tol=None, verbose=False):
    """Solve nabla^2 phi = f using a sparse direct solver (spsolve).

    maxiter and tol are accepted for API compatibility but ignored.

    Returns
    -------
    (1, final_residual)
    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve

    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    N = nx * ny  # number of interior unknowns

    def idx(i, j):
        """Map interior (i,j) with 0-based interior indices to flat index."""
        return i * ny + j

    neumann = grid.neumann

    # Build sparse Laplacian matrix (with Neumann ghost-cell mirroring)
    rows, cols, vals = [], [], []

    for i in range(nx):
        for j in range(ny):
            k = idx(i, j)
            diag = -2.0 / dx2 - 2.0 / dy2

            # x-neighbours
            if i > 0:
                rows.append(k); cols.append(idx(i - 1, j)); vals.append(1.0 / dx2)
            else:
                # i==0 : left boundary ghost
                if 'left' in neumann:
                    # ghost = interior  =>  phi[0] = phi[1]  =>  contributes 1/dx2 to diag
                    diag += 1.0 / dx2
                # else Dirichlet: ghost = 0, no contribution

            if i < nx - 1:
                rows.append(k); cols.append(idx(i + 1, j)); vals.append(1.0 / dx2)
            else:
                if 'right' in neumann:
                    diag += 1.0 / dx2

            # y-neighbours
            if j > 0:
                rows.append(k); cols.append(idx(i, j - 1)); vals.append(1.0 / dy2)
            else:
                if 'bottom' in neumann:
                    diag += 1.0 / dy2

            if j < ny - 1:
                rows.append(k); cols.append(idx(i, j + 1)); vals.append(1.0 / dy2)
            else:
                if 'top' in neumann:
                    diag += 1.0 / dy2

            rows.append(k); cols.append(k); vals.append(diag)

    A = sparse.csr_matrix((vals, (rows, cols)), shape=(N, N))
    b = grid.f[1:-1, 1:-1].ravel().copy()

    x = spsolve(A, b)
    grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)

    res = _residual_l2(grid)
    if verbose:
        print(f"Direct solve: residual = {res:.6e}")
    return 1, res


# ---------------------------------------------------------------------------
# Unified interface
# ---------------------------------------------------------------------------

def solve(grid, method="jacobi", **kwargs):
    """Dispatch to the chosen solver.

    Parameters
    ----------
    method : str
        One of 'jacobi', 'cg', 'direct'.
    **kwargs : forwarded to the solver function.
    """
    solvers = {"jacobi": jacobi, "cg": cg, "direct": direct}
    if method not in solvers:
        raise ValueError(f"Unknown method '{method}'. Choose from {list(solvers)}")
    return solvers[method](grid, **kwargs)
