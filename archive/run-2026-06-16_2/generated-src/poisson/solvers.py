"""Poisson solvers: Jacobi, Conjugate-Gradient, and Direct (sparse)."""

import numpy as np


# ====================================================================== #
# Shared helpers                                                          #
# ====================================================================== #

def _residual(grid):
    """Return the residual r = f - L(phi) on the interior."""
    phi = grid.phi
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    Lphi = (
        (phi[2:, 1:-1] - 2.0 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) / dx2
        + (phi[1:-1, 2:] - 2.0 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) / dy2
    )
    return grid.rhs[1:-1, 1:-1] - Lphi


def _l2norm(r):
    return np.sqrt(np.sum(r * r))


# ====================================================================== #
# Jacobi iterative solver                                                 #
# ====================================================================== #

def jacobi(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve ∇²φ = f using the Jacobi method.

    Updates ``grid.phi`` in-place.
    Returns ``(iterations, final_residual)``.
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2

    for it in range(1, maxiter + 1):
        grid.apply_neumann()

        phi = grid.phi
        phi_new = phi.copy()

        phi_new[1:-1, 1:-1] = (
            (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
            + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
            - grid.rhs[1:-1, 1:-1]
        ) / denom

        grid.phi = phi_new
        grid.apply_neumann()

        res = _residual(grid)
        rnorm = _l2norm(res)
        if verbose and it % 500 == 0:
            print(f"  Jacobi iter {it:6d}  |r| = {rnorm:.6e}")
        if rnorm < tol:
            return it, rnorm

    return maxiter, rnorm


# ====================================================================== #
# Conjugate-Gradient solver (numpy only)                                  #
# ====================================================================== #

def _apply_laplacian_interior(grid, p_full):
    """Apply the discrete Laplacian to p_full (which has boundary ring).
    Returns result on interior only."""
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    Lp = (
        (p_full[2:, 1:-1] - 2.0 * p_full[1:-1, 1:-1] + p_full[:-2, 1:-1]) / dx2
        + (p_full[1:-1, 2:] - 2.0 * p_full[1:-1, 1:-1] + p_full[1:-1, :-2]) / dy2
    )
    return Lp


def conjugate_gradient(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve ∇²φ = f using the Conjugate-Gradient method.

    Updates ``grid.phi`` in-place.
    Returns ``(iterations, final_residual)``.
    """
    nx, ny = grid.nx, grid.ny

    grid.apply_neumann()
    # Initial residual  r = f - L(phi)
    r = _residual(grid).copy()
    p = r.copy()  # search direction (interior-sized)

    rs_old = np.sum(r * r)
    r0norm = np.sqrt(rs_old)
    if r0norm < tol:
        return 0, r0norm

    for it in range(1, maxiter + 1):
        # Embed p into a full-sized array with zero (Dirichlet) or Neumann BCs
        p_full = np.zeros_like(grid.phi)
        p_full[1:-1, 1:-1] = p
        # Apply Neumann BCs to p_full
        if grid.neumann["left"]:
            p_full[0, :] = p_full[1, :]
        if grid.neumann["right"]:
            p_full[-1, :] = p_full[-2, :]
        if grid.neumann["bottom"]:
            p_full[:, 0] = p_full[:, 1]
        if grid.neumann["top"]:
            p_full[:, -1] = p_full[:, -2]

        Ap = _apply_laplacian_interior(grid, p_full)

        pAp = np.sum(p * Ap)
        if abs(pAp) < 1e-30:
            break
        alpha = rs_old / pAp

        grid.phi[1:-1, 1:-1] += alpha * p
        grid.apply_neumann()

        r -= alpha * Ap

        rs_new = np.sum(r * r)
        rnorm = np.sqrt(rs_new)
        if verbose and it % 100 == 0:
            print(f"  CG iter {it:6d}  |r| = {rnorm:.6e}")
        if rnorm < tol:
            return it, rnorm

        p = r + (rs_new / rs_old) * p
        rs_old = rs_new

    return it, rnorm


# ====================================================================== #
# Direct solver via scipy.sparse                                          #
# ====================================================================== #

def direct(grid, maxiter=None, tol=None, verbose=False):
    """Solve ∇²φ = f directly with scipy.sparse.linalg.spsolve.

    ``maxiter`` and ``tol`` are accepted but ignored (for API compat).
    Updates ``grid.phi`` in-place.
    Returns ``(1, final_residual)``.
    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve

    nx, ny = grid.nx, grid.ny
    N = nx * ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2

    # Build sparse matrix for interior Laplacian
    diag_main = (-2.0 / dx2 - 2.0 / dy2) * np.ones(N)
    diag_x = np.ones(N - ny) / dx2   # coupling in x (stride = ny)
    diag_y = np.ones(N - 1) / dy2    # coupling in y (stride = 1)

    # Zero out y-couplings that cross row boundaries
    for i in range(1, nx):
        diag_y[i * ny - 1] = 0.0

    diags = [diag_main, diag_x, diag_x, diag_y, diag_y]
    offsets = [0, ny, -ny, 1, -1]
    A = sparse.diags(diags, offsets, shape=(N, N), format="csc")

    # Handle Neumann BCs by adjusting matrix rows on boundaries
    # For Neumann: ghost = interior neighbour → effectively the boundary
    # Laplacian stencil gets +1/dx2 or +1/dy2 on the relevant side.
    A = A.tolil()
    for i in range(nx):
        for j in range(ny):
            idx = i * ny + j
            if i == 0 and grid.neumann["left"]:
                A[idx, idx] += 1.0 / dx2
            if i == nx - 1 and grid.neumann["right"]:
                A[idx, idx] += 1.0 / dx2
            if j == 0 and grid.neumann["bottom"]:
                A[idx, idx] += 1.0 / dy2
            if j == ny - 1 and grid.neumann["top"]:
                A[idx, idx] += 1.0 / dy2
    A = A.tocsc()

    # RHS vector — subtract known BC contributions
    b = grid.rhs[1:-1, 1:-1].copy()
    phi_bc = grid.phi.copy()
    # Zero interior so we only pick up boundary contributions
    phi_bc[1:-1, 1:-1] = 0.0

    bc_contrib = (
        (phi_bc[2:, 1:-1] + phi_bc[:-2, 1:-1]) / dx2
        + (phi_bc[1:-1, 2:] + phi_bc[1:-1, :-2]) / dy2
    )
    b -= bc_contrib

    b_flat = b.ravel()
    x = spsolve(A, b_flat)

    grid.phi[1:-1, 1:-1] = x.reshape((nx, ny))
    grid.apply_neumann()

    res = _residual(grid)
    rnorm = _l2norm(res)
    if verbose:
        print(f"  Direct solve  |r| = {rnorm:.6e}")
    return 1, rnorm


# ====================================================================== #
# Convenience wrapper                                                     #
# ====================================================================== #

def solve(grid, method="jacobi", **kwargs):
    """Dispatch to the chosen solver.  ``method`` is one of
    'jacobi', 'cg', 'direct'."""
    dispatch = {
        "jacobi": jacobi,
        "cg": conjugate_gradient,
        "direct": direct,
    }
    return dispatch[method](grid, **kwargs)
