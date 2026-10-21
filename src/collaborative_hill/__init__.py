"""Collaborative Hill Lab.

A reproducible laboratory for whether LLM agents can build shared truth
under mixed incentives.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("collaborative-hill")
except PackageNotFoundError:
    # A source-only checkout has no installed distribution metadata.
    __version__ = "0+unknown"
