"""
Initialize API module
"""

from .routes import router, set_executor, get_executor

__all__ = ["router", "set_executor", "get_executor"]
