"""Solvers for the 2D Poisson equation."""

import numpy as np


def jacobi_solve(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Jacobi iterative solver.

    Solve nabla^2 phi = f in-place on grid.phi.
    Returns: (iterations, final_residual)
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
            - grid.f[1:-1, 1:-1]
        ) / denom

        grid.phi = phi_new
        grid.apply_neumann()

        res = grid.residual_l2()
        if verbose and it % 500 == 0:
            print(f"Jacobi iter {it}: residual = {res:.6e}")
        if res < tol:
            if verbose:
                print(f"Jacobi converged at iter {it}: residual = {res:.6e}")
            return it, res

    res = grid.residual_l2()
    if verbose:
        print(f"Jacobi did NOT converge after {maxiter} iters: residual = {res:.6e}")
    return maxiter, res


def _apply_laplacian_interior(grid, u_full):
    """Apply discrete Laplacian to u_full; return interior block (nx x ny)."""
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    L = (
        (u_full[2:, 1:-1] - 2 * u_full[1:-1, 1:-1] + u_full[:-2, 1:-1]) / dx2
        + (u_full[1:-1, 2:] - 2 * u_full[1:-1, 1:-1] + u_full[1:-1, :-2]) / dy2
    )
    return L


def cg_solve(grid, maxiter=10000, tol=1e-6, verbose=False):
    """Conjugate gradient solver (numpy only).

    Solve nabla^2 phi = f in-place on grid.phi.
    Returns: (iterations, final_residual)
    """
    nx, ny = grid.nx, grid.ny

    grid.apply_neumann()

    def A_times(v_flat):
        """Apply discrete Laplacian to an interior-only vector."""
        u_full = np.zeros((nx + 2, ny + 2), dtype=np.float64)
        u_full[1:-1, 1:-1] = v_flat.reshape(nx, ny)
        # Apply Neumann BCs on the full array
        if grid.neumann.get('left'):
            u_full[0, :] = u_full[1, :]
        if grid.neumann.get('right'):
            u_full[-1, :] = u_full[-2, :]
        if grid.neumann.get('bottom'):
            u_full[:, 0] = u_full[:, 1]
        if grid.neumann.get('top'):
            u_full[:, -1] = u_full[:, -2]
        return _apply_laplacian_interior(grid, u_full).ravel()

    # Build RHS accounting for boundary values.
    # L(phi) = f  =>  A * x_int = f_int - L_bc
    # where L_bc is the Laplacian contribution from boundary-only values.
    bc_full = np.zeros_like(grid.phi)
    bc_full[0, :] = grid.phi[0, :]
    bc_full[-1, :] = grid.phi[-1, :]
    bc_full[:, 0] = grid.phi[:, 0]
    bc_full[:, -1] = grid.phi[:, -1]
    bc_contrib = _apply_laplacian_interior(grid, bc_full).ravel()

    b = grid.f[1:-1, 1:-1].ravel() - bc_contrib

    # CG iteration
    x = grid.phi[1:-1, 1:-1].copy().ravel()
    r = b - A_times(x)
    p = r.copy()
    rs_old = np.dot(r, r)

    for it in range(1, maxiter + 1):
        Ap = A_times(p)
        pAp = np.dot(p, Ap)
        if abs(pAp) < 1e-30:
            break
        alpha = rs_old / pAp
        x = x + alpha * p
        r = r - alpha * Ap
        rs_new = np.dot(r, r)
        res_norm = np.sqrt(rs_new)

        if verbose and it % 500 == 0:
            print(f"CG iter {it}: residual = {res_norm:.6e}")
        if res_norm < tol:
            grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
            grid.apply_neumann()
            if verbose:
                print(f"CG converged at iter {it}: residual = {res_norm:.6e}")
            return it, res_norm

        beta = rs_new / rs_old
        p = r + beta * p
        rs_old = rs_new

    grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
    grid.apply_neumann()
    res_norm = np.sqrt(rs_old)
    if verbose:
        print(f"CG did NOT converge after {maxiter} iters: residual = {res_norm:.6e}")
    return maxiter, res_norm


def direct_solve(grid, maxiter=None, tol=None, verbose=False):
    """Direct solver using scipy.sparse.linalg.spsolve.

    Assemble the sparse (nx*ny) x (nx*ny) Laplacian matrix and solve directly.
    Solve nabla^2 phi = f in-place on grid.phi.
    Returns: (1, final_residual)
    """
    from scipy import sparse
    from scipy.sparse.linalg import spsolve

    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    N = nx * ny

    def idx(i, j):
        """Map 0-based interior indices to flat index."""
        return i * ny + j

    # Build sparse matrix in COO format and boundary RHS contribution
    rows = []
    cols = []
    vals = []
    bc_rhs = np.zeros(N, dtype=np.float64)

    for i in range(nx):
        gi = i + 1  # grid index (1-based in full array)
        for j in range(ny):
            gj = j + 1
            k = idx(i, j)

            # Centre coefficient: -2/dx^2 - 2/dy^2
            rows.append(k)
            cols.append(k)
            vals.append(-2.0 / dx2 - 2.0 / dy2)

            # --- x-direction neighbours ---
            # Left (i-1)
            if i > 0:
                rows.append(k)
                cols.append(idx(i - 1, j))
                vals.append(1.0 / dx2)
            else:
                if grid.neumann.get('left'):
                    # ghost = interior value => coefficient adds to diagonal
                    rows.append(k)
                    cols.append(k)
                    vals.append(1.0 / dx2)
                else:
                    # Dirichlet: move known boundary value to RHS
                    bc_rhs[k] -= grid.phi[0, gj] / dx2

            # Right (i+1)
            if i < nx - 1:
                rows.append(k)
                cols.append(idx(i + 1, j))
                vals.append(1.0 / dx2)
            else:
                if grid.neumann.get('right'):
                    rows.append(k)
                    cols.append(k)
                    vals.append(1.0 / dx2)
                else:
                    bc_rhs[k] -= grid.phi[-1, gj] / dx2

            # --- y-direction neighbours ---
            # Bottom (j-1)
            if j > 0:
                rows.append(k)
                cols.append(idx(i, j - 1))
                vals.append(1.0 / dy2)
            else:
                if grid.neumann.get('bottom'):
                    rows.append(k)
                    cols.append(k)
                    vals.append(1.0 / dy2)
                else:
                    bc_rhs[k] -= grid.phi[gi, 0] / dy2

            # Top (j+1)
            if j < ny - 1:
                rows.append(k)
                cols.append(idx(i, j + 1))
                vals.append(1.0 / dy2)
            else:
                if grid.neumann.get('top'):
                    rows.append(k)
                    cols.append(k)
                    vals.append(1.0 / dy2)
                else:
                    bc_rhs[k] -= grid.phi[gi, -1] / dy2

    A = sparse.csr_matrix(
        (np.array(vals),
         (np.array(rows, dtype=np.int32),
          np.array(cols, dtype=np.int32))),
        shape=(N, N),
    )

    # RHS: A * x = f_interior - bc_contribution
    # bc_rhs accumulated -phi_bc/h^2 terms (the known boundary neighbour
    # values that were moved from LHS to RHS).
    f_interior = grid.f[1:-1, 1:-1].ravel()
    total_rhs = f_interior - bc_rhs

    x = spsolve(A, total_rhs)
    grid.phi[1:-1, 1:-1] = x.reshape(nx, ny)
    grid.apply_neumann()

    res = grid.residual_l2()
    if verbose:
        print(f"Direct solve: residual = {res:.6e}")
    return 1, res
