"""
Power Method Numerical Implementation for CompressX.
STRICT RESTRICTION: ABSOLUTELY NO EIGENVALUE DECOMPOSITION (EVD) IS USED.
No np.linalg.eig, np.linalg.eigh, scipy.linalg.eig, or any blackbox solver.
"""

from typing import Dict, Any, List, Optional
import numpy as np


def power_method(
    A: np.ndarray,
    x0: Optional[np.ndarray] = None,
    max_iter: int = 100,
    tol: float = 1e-6,
    normalization: str = "l2"
) -> Dict[str, Any]:
    """
    Computes the dominant eigenvalue and eigenvector of real square matrix A
    using pure iterative matrix-vector multiplication and Rayleigh quotient estimation.
    """
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"Matrix A must be square. Given: {A.shape}")

    n = A.shape[0]
    if n == 0:
        raise ValueError("Matrix is empty")

    if x0 is None:
        x = np.ones(n, dtype=float)
        x = x / np.linalg.norm(x)
    else:
        x = np.asarray(x0, dtype=float).ravel()
        norm_val = np.linalg.norm(x)
        if norm_val < 1e-12:
            x = np.ones(n, dtype=float) / np.sqrt(n)
        else:
            x = x / norm_val

    history = []
    converged = False
    current_lambda = float(np.dot(x, A @ x) / np.dot(x, x))
    final_error = float("inf")

    history.append({
        "iteration": 0,
        "eigenvalue": current_lambda,
        "error": 1.0,
        "vector": x.copy().tolist()
    })

    for k in range(1, max_iter + 1):
        y = A @ x
        norm_y = float(np.linalg.norm(y))

        if norm_y < 1e-15:
            return {
                "dominant_eigenvalue": 0.0,
                "dominant_eigenvector": x,
                "iterations": k,
                "converged": True,
                "history": history,
                "error": 0.0
            }

        if normalization == "max":
            max_idx = np.argmax(np.abs(y))
            scale = y[max_idx]
            x_next = y / scale
            x_unit = x_next / np.linalg.norm(x_next)
        else:
            x_unit = y / norm_y

        Ax_next = A @ x_unit
        rayleigh = float(np.dot(x_unit, Ax_next) / np.dot(x_unit, x_unit))
        residual_norm = float(np.linalg.norm(Ax_next - rayleigh * x_unit))

        final_error = residual_norm
        history.append({
            "iteration": k,
            "eigenvalue": rayleigh,
            "error": final_error,
            "vector": x_unit.copy().tolist()
        })

        if residual_norm < tol:
            converged = True
            current_lambda = rayleigh
            x = x_unit
            break

        x = x_unit
        current_lambda = rayleigh

    return {
        "dominant_eigenvalue": current_lambda,
        "dominant_eigenvector": x,
        "iterations": k,
        "converged": converged,
        "history": history,
        "error": final_error
    }
