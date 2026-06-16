"""Solvers for the 2-D Poisson equation on a Grid."""

import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _laplacian(phi, dx, dy):
    """Discrete Laplacian of *phi* at interior points (returns interior-sized array)."""
    idx2 = 1.0 / (dx * dx)
    idy2 = 1.0 / (dy * dy)
    L = (phi[2:, 1:-1] - 2.0 * phi[1:-1, 1:-1] + phi[:-2, 1:-1]) * idx2 \
      + (phi[1:-1, 2:] - 2.0 * phi[1:-1, 1:-1] + phi[1:-1, :-2]) * idy2
    return L


def _residual_norm(grid):
    """Compute L2 norm of r = f - L(phi) on interior points."""
    grid.apply_neumann()
    L = _laplacian(grid.phi, grid.dx, grid.dy)
    r = grid.rhs[1:-1, 1:-1] - L
    return float(np.linalg.norm(r))


# ---------------------------------------------------------------------------
# Jacobi solver
# ---------------------------------------------------------------------------

def solve_jacobi(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Jacobi iterative solver.  Solves nabla^2 phi = f in-place on grid.phi.

    Returns (iterations, final_residual).
    """
    dx2 = grid.dx * grid.dx
    dy2 = grid.dy * grid.dy
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

        res = _residual_norm(grid)
        if verbose and it % 500 == 0:
            print(f"Jacobi iter {it}: residual = {res:.6e}")
        if res < tol:
            return it, res
    return maxiter, _residual_norm(grid)


# ---------------------------------------------------------------------------
# Conjugate-gradient solver (matrix-free)
# ---------------------------------------------------------------------------

def solve_cg(grid, maxiter=10000, tol=1e-6, verbose=False):
    """CG solver on the flattened interior system.

    Returns (iterations, final_residual).
    """
    nx, ny = grid.nx, grid.ny
    dx, dy = grid.dx, grid.dy
    dx2, dy2 = dx * dx, dy * dy
    ni, nj = nx - 2, ny - 2  # interior dimensions

    def A_times(v):
        """Apply discrete Laplacian to vector v (interior only)."""
        full = np.zeros((nx, ny), dtype=np.float64)
        full[1:-1, 1:-1] = v.reshape(ni, nj)
        # Apply Neumann ghost-cell mirroring on the temp array
        if 'left' in grid.neumann:
            full[0, :] = full[1, :]
        if 'right' in grid.neumann:
            full[-1, :] = full[-2, :]
        if 'bottom' in grid.neumann:
            full[:, 0] = full[:, 1]
        if 'top' in grid.neumann:
            full[:, -1] = full[:, -2]
        return _laplacian(full, dx, dy).ravel()

    # Build effective RHS: rhs_interior - boundary contribution from fixed BCs
    bc_full = np.zeros_like(grid.phi)
    bc_full[0, :] = grid.phi[0, :]
    bc_full[-1, :] = grid.phi[-1, :]
    bc_full[:, 0] = grid.phi[:, 0]
    bc_full[:, -1] = grid.phi[:, -1]
    bc_contrib = _laplacian(bc_full, dx, dy).ravel()

    b = grid.rhs[1:-1, 1:-1].ravel() - bc_contrib

    x = grid.phi[1:-1, 1:-1].ravel().copy()
    r = b - A_times(x)
    p = r.copy()
    rs_old = np.dot(r, r)

    for it in range(1, maxiter + 1):
        Ap = A_times(p)
        pAp = np.dot(p, Ap)
        if abs(pAp) < 1e-30:
            break
        alpha = rs_old / pAp
        x += alpha * p
        r -= alpha * Ap
        rs_new = np.dot(r, r)
        res_norm = np.sqrt(rs_new)
        if verbose and it % 100 == 0:
            print(f"CG iter {it}: residual = {res_norm:.6e}")
        if res_norm < tol:
            grid.phi[1:-1, 1:-1] = x.reshape(ni, nj)
            grid.apply_neumann()
            return it, res_norm
        p = r + (rs_new / rs_old) * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape(ni, nj)
    grid.apply_neumann()
    return maxiter, np.sqrt(rs_old)


# ---------------------------------------------------------------------------
# Direct solver via scipy sparse
# ---------------------------------------------------------------------------

def solve_direct(grid, **_kwargs):
    """Assemble sparse Laplacian and solve with spsolve.

    Returns (1, final_residual).
    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve

    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx * grid.dx
    dy2 = grid.dy * grid.dy
    ni, nj = nx - 2, ny - 2
    N = ni * nj

    def idx(i, j):
        return i * nj + j

    rows, cols, vals = [], [], []
    rhs_vec = np.zeros(N, dtype=np.float64)

    for i in range(ni):
        for j in range(nj):
            k = idx(i, j)
            diag = -2.0 / dx2 - 2.0 / dy2

            # x-left neighbour
            if i > 0:
                rows.append(k); cols.append(idx(i - 1, j)); vals.append(1.0 / dx2)
            elif 'left' in grid.neumann:
                diag += 1.0 / dx2
            else:
                rhs_vec[k] -= grid.phi[0, j + 1] / dx2

            # x-right neighbour
            if i < ni - 1:
                rows.append(k); cols.append(idx(i + 1, j)); vals.append(1.0 / dx2)
            elif 'right' in grid.neumann:
                diag += 1.0 / dx2
            else:
                rhs_vec[k] -= grid.phi[-1, j + 1] / dx2

            # y-bottom neighbour
            if j > 0:
                rows.append(k); cols.append(idx(i, j - 1)); vals.append(1.0 / dy2)
            elif 'bottom' in grid.neumann:
                diag += 1.0 / dy2
            else:
                rhs_vec[k] -= grid.phi[i + 1, 0] / dy2

            # y-top neighbour
            if j < nj - 1:
                rows.append(k); cols.append(idx(i, j + 1)); vals.append(1.0 / dy2)
            elif 'top' in grid.neumann:
                diag += 1.0 / dy2
            else:
                rhs_vec[k] -= grid.phi[i + 1, -1] / dy2

            rows.append(k); cols.append(k); vals.append(diag)
            rhs_vec[k] += grid.rhs[i + 1, j + 1]

    A = sparse.csr_matrix((vals, (rows, cols)), shape=(N, N))
    sol = spsolve(A, rhs_vec)
    grid.phi[1:-1, 1:-1] = sol.reshape(ni, nj)
    grid.apply_neumann()
    res = _residual_norm(grid)
    return 1, res
