"""Pluggable solver system for evaluation.

Solvers define how models approach benchmark problems.
- baseline: Standard single-model approach
- minds: Multi-model collaboration
- custom: User-defined solvers loaded from Python modules
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Any, Optional, Type
from .base import Solver


# Global solver registry
_SOLVER_REGISTRY: dict[str, Type[Solver]] = {}


def register_solver(name: str, solver_class: Type[Solver]):
    """Register a solver class by name."""
    _SOLVER_REGISTRY[name] = solver_class


def get_solver(name: str) -> Type[Solver]:
    """Get a solver class by name.

    Raises:
        KeyError: If solver not found
    """
    if name not in _SOLVER_REGISTRY:
        raise KeyError(f"Unknown solver: {name}. Available: {list(_SOLVER_REGISTRY.keys())}")
    return _SOLVER_REGISTRY[name]


def list_solvers() -> list[str]:
    """List all registered solver names."""
    return list(_SOLVER_REGISTRY.keys())


def load_custom_solver(path: str) -> Type[Solver]:
    """Load a custom solver from a Python file or module.

    Supports two formats:
    1. File path: "/path/to/my_solver.py" or "./solvers/my_solver.py"
    2. Module path: "mypackage.solvers.MyCustomSolver"

    The file/module must define a class that inherits from Solver
    and has a 'name' class attribute.

    Args:
        path: File path or module.class path

    Returns:
        Solver class

    Raises:
        ImportError: If module cannot be loaded
        ValueError: If no valid Solver class found
    """
    # Check if it's a file path
    if path.endswith(".py") or "/" in path or "\\" in path:
        return _load_solver_from_file(path)
    else:
        return _load_solver_from_module(path)


def _load_solver_from_file(file_path: str) -> Type[Solver]:
    """Load a solver from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        Solver class

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If no valid Solver class found
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Solver file not found: {file_path}")

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("custom_solver", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from: {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find Solver subclasses
    solver_classes = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and
            issubclass(attr, Solver) and
            attr is not Solver and
            hasattr(attr, 'name')):
            solver_classes.append(attr)

    if not solver_classes:
        raise ValueError(f"No Solver subclass found in {file_path}")

    if len(solver_classes) > 1:
        # Return the first one, but warn
        import warnings
        warnings.warn(f"Multiple Solver classes found in {file_path}, using {solver_classes[0].name}")

    solver_class = solver_classes[0]

    # Auto-register
    register_solver(solver_class.name, solver_class)

    return solver_class


def _load_solver_from_module(module_path: str) -> Type[Solver]:
    """Load a solver from a module.class path.

    Args:
        module_path: Module path like "mypackage.solvers.MySolver"

    Returns:
        Solver class

    Raises:
        ImportError: If module cannot be imported
        ValueError: If class is not a valid Solver
    """
    # Split into module and class
    if "." not in module_path:
        raise ValueError(f"Invalid module path: {module_path}. Expected format: module.ClassName")

    parts = module_path.rsplit(".", 1)
    module_name, class_name = parts[0], parts[1]

    # Import the module
    module = importlib.import_module(module_name)

    # Get the class
    if not hasattr(module, class_name):
        raise ValueError(f"Class {class_name} not found in module {module_name}")

    solver_class = getattr(module, class_name)

    # Validate
    if not isinstance(solver_class, type) or not issubclass(solver_class, Solver):
        raise ValueError(f"{class_name} is not a Solver subclass")

    # Auto-register
    if hasattr(solver_class, 'name'):
        register_solver(solver_class.name, solver_class)

    return solver_class


def create_solver_instance(
    name: str,
    custom_path: Optional[str] = None,
    **kwargs
) -> Solver:
    """Create a solver instance by name or custom path.

    Args:
        name: Solver name (for built-in solvers)
        custom_path: Optional path to custom solver file/module
        **kwargs: Arguments to pass to solver constructor

    Returns:
        Solver instance
    """
    if custom_path:
        solver_class = load_custom_solver(custom_path)
    else:
        solver_class = get_solver(name)

    return solver_class(**kwargs)


# Import and register built-in solvers
from .baseline import BaselineSolver
register_solver("baseline", BaselineSolver)

from .minds import MindsSolver
register_solver("minds", MindsSolver)
