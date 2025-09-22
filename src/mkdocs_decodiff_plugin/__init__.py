from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("mkdocs_decodiff_plugin")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ("__version__",)
