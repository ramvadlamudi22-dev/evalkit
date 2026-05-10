"""EvalKit — a pytest-shaped LLM evaluation toolkit.

Public surface in Phase 0:
    __version__: the installed version string.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("evalkit")
except PackageNotFoundError:  # pragma: no cover - editable install before metadata exists
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
