from importlib.metadata import version, PackageNotFoundError

from .markdiff import main

try:
    __version__ = version("markdiff")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = (
    "main",
    "__version__",
)
