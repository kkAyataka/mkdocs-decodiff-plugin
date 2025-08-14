from importlib.metadata import version, PackageNotFoundError

from .markdiff import hello

try:
    __version__ = version("markdiff")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = (
    "hello",
    "__version__",
)
