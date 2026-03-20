"""Shared test fixtures and configuration."""

from __future__ import annotations

import sys
import os

# Fallback: add src/ to path if pyproject.toml pythonpath isn't picked up.
_src = os.path.join(os.path.dirname(__file__), "..", "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
