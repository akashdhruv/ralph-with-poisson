"""Convergence plot: log residual vs iteration for Jacobi and CG solvers."""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from poisson import Grid
from poisson import solvers


def _setup_grid(n=32):
    g = Grid(n, n)
    X, Y = np.meshgrid(g.x, g.y, indexing="ij")
    g.f[:] = -2 * np.pi ** 2 * np.sin(np.pi * X) * np.sin(np.pi * Y)
    return g


def run_with_history(solver_fn, n=32, maxiter=500, tol=1e-10):
    """Run a solver and collect residual history."""
    g = _setup_grid(n)
    history = []

    orig = solvers._l2_residual

    def patched_residual(grid):
        r = orig(grid)
        history.append(r)
        return r

    solvers._l2_residual = patched_residual
    try:
        solver_fn(g, maxiter=maxiter, tol=tol)
    finally:
        solvers._l2_residual = orig

    return history


def plot_convergence():
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available — printing residuals instead")
        _print_convergence()
        return

    print("Running Jacobi (32×32)...")
    jac_hist = run_with_history(solvers.jacobi, n=32, maxiter=2000)

    print("Running CG (32×32)...")
    cg_hist = run_with_history(solvers.cg, n=32, maxiter=500, tol=1e-10)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(range(1, len(jac_hist) + 1), jac_hist, label="Jacobi")
    ax.semilogy(range(1, len(cg_hist) + 1), cg_hist, label="CG")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("L2 Residual")
    ax.set_title("Poisson solver convergence (32×32, manufactured solution)")
    ax.legend()
    ax.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    out = "convergence.png"
    plt.savefig(out, dpi=150)
    print(f"Saved {out}")
    plt.show()


def _print_convergence():
    g = _setup_grid(32)
    print("Jacobi residuals (every 50 iters):")
    solvers.jacobi(g, maxiter=500, tol=1e-12, verbose=True)


def benchmark():
    import time

    print("\n--- Performance benchmark ---")
    for n in (64, 128):
        print(f"\nGrid {n}×{n}:")
        for name, fn in [("jacobi", solvers.jacobi), ("cg", solvers.cg), ("direct", solvers.direct)]:
            g = _setup_grid(n)
            t0 = time.perf_counter()
            iters, res = fn(g, maxiter=50000, tol=1e-6)
            elapsed = time.perf_counter() - t0
            print(f"  {name:8s}  iters={iters:6}  res={res:.2e}  time={elapsed:.3f}s")


if __name__ == "__main__":
    plot_convergence()
    benchmark()
