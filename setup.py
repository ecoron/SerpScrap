"""Compatibility entry point for tools that still invoke setup.py directly.

Package metadata and dependencies are intentionally defined only in
``pyproject.toml``.
"""

from setuptools import setup

setup()
