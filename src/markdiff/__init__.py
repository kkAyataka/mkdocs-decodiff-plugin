from importlib.metadata import PackageNotFoundError, version

from .markdiff import main

try:
    __version__ = version("markdiff")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = (
    "main",
    "__version__",
)
