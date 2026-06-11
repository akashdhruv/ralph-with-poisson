import numpy as np


def jacobi(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve ∇²φ = f in-place on grid.phi using Jacobi iteration.

    Returns: (iterations, final_residual)
    """
    phi = grid.phi
    f = grid.f
    dx, dy = grid.dx, grid.dy
    dx2, dy2 = dx * dx, dy * dy
    denom = 2.0 / dx2 + 2.0 / dy2

    for it in range(1, maxiter + 1):
        _apply_neumann(grid)
        phi_new = phi.copy()
        phi_new[1:-1, 1:-1] = (
            (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
            + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
            - f[1:-1, 1:-1]
        ) / denom
        # preserve Dirichlet boundaries
        phi_new[0, :] = phi[0, :]
        phi_new[-1, :] = phi[-1, :]
        phi_new[:, 0] = phi[:, 0]
        phi_new[:, -1] = phi[:, -1]
        grid.phi = phi_new
        phi = grid.phi

        residual = _l2_residual(grid)
        if verbose:
            print(f"  jacobi iter {it:5d}  residual={residual:.3e}")
        if residual < tol:
            return it, residual

    return maxiter, _l2_residual(grid)


def cg(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Solve ∇²φ = f in-place on grid.phi using conjugate gradient (numpy only).

    Returns: (iterations, final_residual)
    """
    nx, ny = grid.nx, grid.ny
    dx2, dy2 = grid.dx ** 2, grid.dy ** 2
    ni, nj = nx - 2, ny - 2  # interior counts

    def matvec(v):
        """Apply discrete Laplacian to interior vector v reshaped to (ni, nj)."""
        p = v.reshape(ni, nj)
        out = np.zeros_like(p)
        # pad with zeros for boundary
        P = np.zeros((nx, ny))
        P[1:-1, 1:-1] = p
        out = (
            (P[2:, 1:-1] + P[:-2, 1:-1]) / dx2
            + (P[1:-1, 2:] + P[1:-1, :-2]) / dy2
            - 2.0 * p / dx2
            - 2.0 * p / dy2
        )
        return out.ravel()

    rhs = grid.f[1:-1, 1:-1].ravel()
    x = grid.phi[1:-1, 1:-1].ravel().copy()

    r = rhs - matvec(x)
    p = r.copy()
    rs_old = r @ r

    for it in range(1, maxiter + 1):
        ap = matvec(p)
        alpha = rs_old / (p @ ap)
        x = x + alpha * p
        r = r - alpha * ap
        rs_new = r @ r
        residual = np.sqrt(rs_new)
        if verbose:
            print(f"  cg iter {it:5d}  residual={residual:.3e}")
        if residual < tol:
            grid.phi[1:-1, 1:-1] = x.reshape(ni, nj)
            return it, residual
        p = r + (rs_new / rs_old) * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape(ni, nj)
    return maxiter, np.sqrt(rs_old)


def direct(grid, maxiter=None, tol=None, verbose=False):
    """Solve ∇²φ = f using scipy sparse direct solver.

    Returns: (1, 0.0)
    """
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla

    nx, ny = grid.nx, grid.ny
    dx2, dy2 = grid.dx ** 2, grid.dy ** 2
    ni, nj = nx - 2, ny - 2
    n = ni * nj

    def idx(i, j):
        return i * nj + j

    rows, cols, vals = [], [], []
    rhs = np.zeros(n)

    for i in range(ni):
        for j in range(nj):
            k = idx(i, j)
            diag = -(2.0 / dx2 + 2.0 / dy2)
            rows.append(k); cols.append(k); vals.append(diag)
            # i+1 (right in x)
            if i + 1 < ni:
                rows.append(k); cols.append(idx(i + 1, j)); vals.append(1.0 / dx2)
            if i - 1 >= 0:
                rows.append(k); cols.append(idx(i - 1, j)); vals.append(1.0 / dx2)
            if j + 1 < nj:
                rows.append(k); cols.append(idx(i, j + 1)); vals.append(1.0 / dy2)
            if j - 1 >= 0:
                rows.append(k); cols.append(idx(i, j - 1)); vals.append(1.0 / dy2)

            b = grid.f[i + 1, j + 1]
            # subtract boundary contributions
            if i == 0:
                b -= grid.phi[0, j + 1] / dx2
            if i == ni - 1:
                b -= grid.phi[-1, j + 1] / dx2
            if j == 0:
                b -= grid.phi[i + 1, 0] / dy2
            if j == nj - 1:
                b -= grid.phi[i + 1, -1] / dy2
            rhs[k] = b

    A = sp.csr_matrix((vals, (rows, cols)), shape=(n, n))
    sol = spla.spsolve(A, rhs)
    grid.phi[1:-1, 1:-1] = sol.reshape(ni, nj)
    return 1, 0.0


# ---- helpers ----------------------------------------------------------------

def _apply_neumann(grid):
    """Apply zero-flux ghost-cell rule for any Neumann edges."""
    if 'left' in grid.neumann_edges:
        grid.phi[0, :] = grid.phi[1, :]
    if 'right' in grid.neumann_edges:
        grid.phi[-1, :] = grid.phi[-2, :]
    if 'bottom' in grid.neumann_edges:
        grid.phi[:, 0] = grid.phi[:, 1]
    if 'top' in grid.neumann_edges:
        grid.phi[:, -1] = grid.phi[:, -2]


def _l2_residual(grid):
    phi = grid.phi
    f = grid.f
    dx2, dy2 = grid.dx ** 2, grid.dy ** 2
    lap = (
        (phi[2:, 1:-1] + phi[:-2, 1:-1]) / dx2
        + (phi[1:-1, 2:] + phi[1:-1, :-2]) / dy2
        - 2.0 * phi[1:-1, 1:-1] / dx2
        - 2.0 * phi[1:-1, 1:-1] / dy2
    )
    r = f[1:-1, 1:-1] - lap
    return float(np.linalg.norm(r))
