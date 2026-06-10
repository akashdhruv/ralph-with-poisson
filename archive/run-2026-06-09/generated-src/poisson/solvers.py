"""Iterative and direct solvers for the 2-D Poisson equation."""

import numpy as np


# ── helpers ──────────────────────────────────────────────────────────

def _residual(grid, neumann_edges=None):
    """Compute r = rhs - L(phi) at interior points and return L2 norm."""
    grid.apply_neumann(neumann_edges)
    phi = grid.phi
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    s = slice(1, -1)

    lap = (phi[2:, s] - 2.0 * phi[1:-1, s] + phi[:-2, s]) / dx2 \
        + (phi[s, 2:] - 2.0 * phi[s, 1:-1] + phi[s, :-2]) / dy2

    r = grid.rhs[s, s] - lap
    return np.sqrt(np.sum(r ** 2))


# ── Jacobi solver ───────────────────────────────────────────────────

def jacobi_solve(grid, maxiter=10000, tol=1e-6, verbose=False,
                 neumann_edges=None):
    """Solve ∇²φ = f in-place on *grid* using Jacobi iteration.

    Returns ``(iterations, final_residual)``.
    """
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    denom = 2.0 / dx2 + 2.0 / dy2
    s = slice(1, -1)

    for it in range(1, maxiter + 1):
        grid.apply_neumann(neumann_edges)
        phi = grid.phi

        phi_new = phi.copy()
        phi_new[s, s] = (
            (phi[2:, s] + phi[:-2, s]) / dx2
            + (phi[s, 2:] + phi[s, :-2]) / dy2
            - grid.rhs[s, s]
        ) / denom

        grid.phi = phi_new

        res = _residual(grid, neumann_edges)
        if verbose and it % 500 == 0:
            print(f"Jacobi iter {it:6d}  residual = {res:.6e}")
        if res < tol:
            return it, res

    return maxiter, _residual(grid, neumann_edges)


# ── Conjugate-Gradient solver ───────────────────────────────────────

def cg_solve(grid, maxiter=10000, tol=1e-6, verbose=False,
             neumann_edges=None):
    """Solve ∇²φ = f in-place on *grid* using Conjugate Gradient.

    Operates on the flattened interior system  A x = b  where A is the
    discrete Laplacian restricted to interior points.

    Returns ``(iterations, final_residual)``.
    """
    nx, ny = grid.nx, grid.ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    s = slice(1, -1)

    def apply_A(v):
        """Apply the discrete Laplacian to vector *v* (interior only).

        *v* has length ``nx * ny``; returns a vector of the same length.
        """
        # Embed v into a full (nx+2, ny+2) array with zero boundaries
        full = np.zeros((nx + 2, ny + 2))
        full[s, s] = v.reshape((nx, ny))
        # Apply Neumann if needed
        if neumann_edges:
            # Temporarily put full into grid to reuse apply_neumann
            saved = grid.phi
            grid.phi = full
            grid.apply_neumann(neumann_edges)
            full = grid.phi
            grid.phi = saved
        lap = (full[2:, s] - 2.0 * full[1:-1, s] + full[:-2, s]) / dx2 \
            + (full[s, 2:] - 2.0 * full[s, 1:-1] + full[s, :-2]) / dy2
        return lap.ravel()

    # RHS for the interior system (includes contribution from BCs)
    b = grid.rhs[s, s].ravel().copy()

    # Subtract boundary contributions so that A x = b_modified
    # boundary contribution comes from the known phi on boundaries
    bc_contrib = np.zeros((nx + 2, ny + 2))
    bc_contrib[s, s] = 0.0
    # left/right/bottom/top boundary values
    bc_full = np.zeros_like(grid.phi)
    bc_full[0, :] = grid.phi[0, :]
    bc_full[-1, :] = grid.phi[-1, :]
    bc_full[:, 0] = grid.phi[:, 0]
    bc_full[:, -1] = grid.phi[:, -1]
    bc_lap = (bc_full[2:, s] + bc_full[:-2, s]) / dx2 \
           + (bc_full[s, 2:] + bc_full[s, :-2]) / dy2
    b = b - bc_lap.ravel()

    # Initial guess: current interior values
    x = grid.phi[s, s].ravel().copy()

    r = b - apply_A(x)
    p = r.copy()
    rs_old = np.dot(r, r)

    for it in range(1, maxiter + 1):
        Ap = apply_A(p)
        alpha = rs_old / (np.dot(p, Ap) + 1e-300)
        x += alpha * p
        r -= alpha * Ap
        rs_new = np.dot(r, r)
        res_norm = np.sqrt(rs_new)
        if verbose and it % 100 == 0:
            print(f"CG iter {it:6d}  residual = {res_norm:.6e}")
        if res_norm < tol:
            grid.phi[s, s] = x.reshape((nx, ny))
            grid.apply_neumann(neumann_edges)
            return it, res_norm
        p = r + (rs_new / (rs_old + 1e-300)) * p
        rs_old = rs_new

    grid.phi[s, s] = x.reshape((nx, ny))
    grid.apply_neumann(neumann_edges)
    return maxiter, np.sqrt(rs_old)


# ── Direct solver ───────────────────────────────────────────────────

def direct_solve(grid, maxiter=None, tol=None, verbose=False,
                 neumann_edges=None):
    """Solve ∇²φ = f in-place on *grid* using scipy sparse direct solver.

    *maxiter* and *tol* are accepted for API compatibility but ignored.

    Returns ``(1, final_residual)``.
    """
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla

    nx, ny = grid.nx, grid.ny
    N = nx * ny
    dx2 = grid.dx ** 2
    dy2 = grid.dy ** 2
    s = slice(1, -1)

    # Build sparse Laplacian for interior points
    # Mapping: interior point (i, j) -> index k = (i-1)*ny + (j-1)
    diag_main = (-2.0 / dx2 - 2.0 / dy2) * np.ones(N)
    diag_x = np.ones(N) / dx2   # neighbours in x-direction (stride ny)
    diag_y = np.ones(N) / dy2   # neighbours in y-direction (stride 1)

    # Remove connections that cross row boundaries in y
    for k in range(N):
        j = k % ny
        if j == 0:
            pass  # no lower y neighbour inside interior (boundary)
        if j == ny - 1:
            pass  # no upper y neighbour inside interior (boundary)

    diags_vals = [diag_main]
    diags_offsets = [0]

    # y-neighbours (offset ±1), but mask row-boundary crossings
    off1 = np.ones(N - 1) / dy2
    for k in range(N - 1):
        if (k + 1) % ny == 0:
            off1[k] = 0.0
    diags_vals.extend([off1, off1.copy()])
    diags_offsets.extend([-1, 1])

    # x-neighbours (offset ±ny)
    if ny <= N:
        offny = np.ones(N - ny) / dx2
        diags_vals.extend([offny, offny.copy()])
        diags_offsets.extend([-ny, ny])

    A = sp.diags(diags_vals, diags_offsets, shape=(N, N), format="csc")

    # Handle Neumann BCs by modifying the matrix rows at boundary-adjacent
    # interior points.
    if neumann_edges:
        A = A.tolil()
        for edge in neumann_edges:
            if edge == "left":
                # Interior points with i-1 == 0 (i.e. i=1, row 0 in interior)
                for j in range(ny):
                    k = 0 * ny + j
                    # phi[0,j+1] = phi[1,j+1] -> add 1/dx2 to diagonal
                    A[k, k] += 1.0 / dx2
            elif edge == "right":
                for j in range(ny):
                    k = (nx - 1) * ny + j
                    A[k, k] += 1.0 / dx2
            elif edge == "bottom":
                for i in range(nx):
                    k = i * ny + 0
                    A[k, k] += 1.0 / dy2
            elif edge == "top":
                for i in range(nx):
                    k = i * ny + (ny - 1)
                    A[k, k] += 1.0 / dy2
        A = A.tocsc()

    # RHS vector: rhs values at interior points minus BC contributions
    b = grid.rhs[s, s].ravel().copy()

    # Subtract known boundary contributions (Dirichlet)
    bc_full = np.zeros_like(grid.phi)
    bc_full[0, :] = grid.phi[0, :]
    bc_full[-1, :] = grid.phi[-1, :]
    bc_full[:, 0] = grid.phi[:, 0]
    bc_full[:, -1] = grid.phi[:, -1]

    # Zero out edges that are Neumann (those BCs are already in matrix)
    if neumann_edges:
        for edge in neumann_edges:
            if edge == "left":
                bc_full[0, :] = 0.0
            elif edge == "right":
                bc_full[-1, :] = 0.0
            elif edge == "bottom":
                bc_full[:, 0] = 0.0
            elif edge == "top":
                bc_full[:, -1] = 0.0

    bc_lap = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            gi, gj = i + 1, j + 1
            bc_lap[i, j] = (bc_full[gi + 1, gj] + bc_full[gi - 1, gj]) / dx2 \
                         + (bc_full[gi, gj + 1] + bc_full[gi, gj - 1]) / dy2
    b -= bc_lap.ravel()

    x = spla.spsolve(A, b)
    grid.phi[s, s] = x.reshape((nx, ny))
    grid.apply_neumann(neumann_edges)

    res = _residual(grid, neumann_edges)
    if verbose:
        print(f"Direct solve  residual = {res:.6e}")
    return 1, res
