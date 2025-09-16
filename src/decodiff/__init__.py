from importlib.metadata import PackageNotFoundError, version

from .decodiff import main

try:
    __version__ = version("decodiff")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = (
    "main",
    "__version__",
)
