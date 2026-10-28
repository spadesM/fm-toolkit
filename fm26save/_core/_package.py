"""The installed fmsave version."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fmsave")
except PackageNotFoundError:  # pragma: no cover - only in an uninstalled source tree
    __version__ = "0.0.0+unknown"
