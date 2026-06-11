"""Solvers for the 2D Poisson equation: Jacobi, CG, and Direct (sparse)."""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _laplacian(phi, dx, dy):
    """Apply the discrete 2D Laplacian to *phi* (full array including BCs).

    Returns an array of the same shape; only interior values are meaningful.
    """
    Lp = np.zeros_like(phi)
    Lp[1:-1, 1:-1] = (
        (phi[2:, 1:-1] - 2.0 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) / dx**2
        + (phi[1:-1, 2:] - 2.0 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) / dy**2
    )
    return Lp


def _apply_neumann(grid):
    """Apply Neumann ghost-cell update if the grid has Neumann edges."""
    if hasattr(grid, 'apply_neumann_bc'):
        grid.apply_neumann_bc()


def _residual_norm(grid):
    """L2 norm of the residual r = f - L(phi) over interior points."""
    _apply_neumann(grid)
    Lp = _laplacian(grid.phi, grid.dx, grid.dy)
    r = grid.f[1:-1, 1:-1] - Lp[1:-1, 1:-1]
    return np.sqrt(np.sum(r**2))


# ---------------------------------------------------------------------------
# Jacobi iterative solver
# ---------------------------------------------------------------------------

def jacobi(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve nabla^2 phi = f using Jacobi iteration (in-place on grid.phi).

    Returns
    -------
    iterations : int
    final_residual : float
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2
    phi = grid.phi
    f = grid.f

    for it in range(1, maxiter + 1):
        _apply_neumann(grid)
        phi_new = phi.copy()
        phi_new[1:-1, 1:-1] = (
            (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
            + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
            - f[1:-1, 1:-1]
        ) / denom
        grid.phi = phi_new
        phi = phi_new

        res = _residual_norm(grid)
        if verbose and it % 500 == 0:
            print(f"  Jacobi iter {it:6d}  residual = {res:.6e}")
        if res < tol:
            if verbose:
                print(f"  Jacobi converged at iter {it}, residual = {res:.6e}")
            return it, res

    res = _residual_norm(grid)
    if verbose:
        print(f"  Jacobi did NOT converge after {maxiter} iters, residual = {res:.6e}")
    return maxiter, res


# ---------------------------------------------------------------------------
# Conjugate-gradient solver (matrix-free)
# ---------------------------------------------------------------------------

def cg(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve nabla^2 phi = f using CG on the flattened interior system.

    A(p) is the discrete Laplacian applied to the interior vector reshaped
    to (nx, ny).  Boundary values in grid.phi are honoured but held constant.

    Returns
    -------
    iterations : int
    final_residual : float
    """
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy
    dx2, dy2 = dx**2, dy**2

    bc = getattr(grid, 'bc_type', {})

    def Ap(p_flat):
        """Apply the Laplacian restricted to interior points,
        accounting for Neumann ghost copies."""
        p_full = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        p_full[1:-1, 1:-1] = p_flat.reshape((nx, ny))
        # Neumann ghost copies for the search direction
        if bc.get('left') == 'neumann':
            p_full[0, :] = p_full[1, :]
        if bc.get('right') == 'neumann':
            p_full[-1, :] = p_full[-2, :]
        if bc.get('bottom') == 'neumann':
            p_full[:, 0] = p_full[:, 1]
        if bc.get('top') == 'neumann':
            p_full[:, -1] = p_full[:, -2]
        Lp = _laplacian(p_full, dx, dy)
        return Lp[1:-1, 1:-1].ravel()

    # Apply Neumann BCs before computing boundary contributions
    _apply_neumann(grid)

    # initial residual:  r = f_interior - A(phi_interior)
    # The true system is:  A_int(phi_int) = f_int - boundary_contribution
    Lp_full = _laplacian(grid.phi, dx, dy)
    phi_int = grid.phi[1:-1, 1:-1].copy()
    tmp = np.zeros_like(grid.phi)
    tmp[1:-1, 1:-1] = phi_int
    # Copy Neumann ghosts for tmp too
    if bc.get('left') == 'neumann':
        tmp[0, :] = tmp[1, :]
    if bc.get('right') == 'neumann':
        tmp[-1, :] = tmp[-2, :]
    if bc.get('bottom') == 'neumann':
        tmp[:, 0] = tmp[:, 1]
    if bc.get('top') == 'neumann':
        tmp[:, -1] = tmp[:, -2]
    Lp_int_only = _laplacian(tmp, dx, dy)
    bc_contribution = Lp_full[1:-1, 1:-1] - Lp_int_only[1:-1, 1:-1]

    rhs = grid.f[1:-1, 1:-1].ravel() - bc_contribution.ravel()

    x = phi_int.ravel().copy()
    r = rhs - Ap(x)
    p = r.copy()
    rs_old = np.dot(r, r)

    for it in range(1, maxiter + 1):
        Ap_vec = Ap(p)
        alpha = rs_old / np.dot(p, Ap_vec)
        x += alpha * p
        r -= alpha * Ap_vec
        rs_new = np.dot(r, r)
        res = np.sqrt(rs_new)

        if verbose and it % 500 == 0:
            print(f"  CG iter {it:6d}  residual = {res:.6e}")
        if res < tol:
            grid.phi[1:-1, 1:-1] = x.reshape((nx, ny))
            if verbose:
                print(f"  CG converged at iter {it}, residual = {res:.6e}")
            return it, res

        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape((nx, ny))
    res = np.sqrt(rs_old)
    if verbose:
        print(f"  CG did NOT converge after {maxiter} iters, residual = {res:.6e}")
    return maxiter, res


# ---------------------------------------------------------------------------
# Direct solver using scipy sparse
# ---------------------------------------------------------------------------

def _build_laplacian_matrix(nx, ny, dx, dy, bc=None):
    """Assemble the sparse (nx*ny) x (nx*ny) Laplacian for interior points.

    *bc* is a dict with keys 'left','right','bottom','top' and values
    'dirichlet' or 'neumann'.  For Neumann edges the ghost-cell copy
    folds back into the diagonal.
    """
    if bc is None:
        bc = {}
    N = nx * ny
    dx2 = dx ** 2
    dy2 = dy ** 2
    diag_main = -2.0 / dx2 - 2.0 / dy2

    rows, cols, vals = [], [], []

    for i in range(nx):
        for j in range(ny):
            idx = i * ny + j
            diag = diag_main
            # x-neighbours
            if i > 0:
                rows.append(idx); cols.append((i - 1) * ny + j)
                vals.append(1.0 / dx2)
            else:  # i == 0 — left edge
                if bc.get('left') == 'neumann':
                    diag += 1.0 / dx2  # ghost folds into diagonal
                # Dirichlet: boundary value handled in RHS
            if i < nx - 1:
                rows.append(idx); cols.append((i + 1) * ny + j)
                vals.append(1.0 / dx2)
            else:  # i == nx-1 — right edge
                if bc.get('right') == 'neumann':
                    diag += 1.0 / dx2
            # y-neighbours
            if j > 0:
                rows.append(idx); cols.append(i * ny + (j - 1))
                vals.append(1.0 / dy2)
            else:  # j == 0 — bottom edge
                if bc.get('bottom') == 'neumann':
                    diag += 1.0 / dy2
            if j < ny - 1:
                rows.append(idx); cols.append(i * ny + (j + 1))
                vals.append(1.0 / dy2)
            else:  # j == ny-1 — top edge
                if bc.get('top') == 'neumann':
                    diag += 1.0 / dy2
            # diagonal
            rows.append(idx); cols.append(idx); vals.append(diag)

    A = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    return A


def direct(grid, maxiter=None, tol=None, verbose=False):
    """Solve nabla^2 phi = f using scipy.sparse.linalg.spsolve.

    Parameters *maxiter* and *tol* are accepted for API compatibility but
    are ignored (direct solver).

    Returns
    -------
    iterations : int  (always 1)
    final_residual : float
    """
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy
    dx2, dy2 = dx**2, dy**2
    bc = getattr(grid, 'bc_type', {})

    A = _build_laplacian_matrix(nx, ny, dx, dy, bc)

    # Build RHS vector accounting for boundary conditions
    rhs = grid.f[1:-1, 1:-1].copy()  # shape (nx, ny)

    # Subtract Dirichlet boundary contributions (Neumann handled in matrix)
    if bc.get('left', 'dirichlet') == 'dirichlet':
        rhs[0, :] -= grid.phi[0, 1:-1] / dx2
    if bc.get('right', 'dirichlet') == 'dirichlet':
        rhs[-1, :] -= grid.phi[-1, 1:-1] / dx2
    if bc.get('bottom', 'dirichlet') == 'dirichlet':
        rhs[:, 0] -= grid.phi[1:-1, 0] / dy2
    if bc.get('top', 'dirichlet') == 'dirichlet':
        rhs[:, -1] -= grid.phi[1:-1, -1] / dy2

    b = rhs.ravel()
    x = spla.spsolve(A, b)
    grid.phi[1:-1, 1:-1] = x.reshape((nx, ny))

    # Copy solution to ghost cells for Neumann edges
    _apply_neumann(grid)

    res = _residual_norm(grid)
    if verbose:
        print(f"  Direct solve residual = {res:.6e}")
    return 1, res
