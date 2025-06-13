"""Financial Dashboard Backend Package."""

__version__ = "1.0.0"
__title__ = "Financial Dashboard MCP"
__description__ = "A comprehensive financial dashboard system with AI integration"
__author__ = "Financial Dashboard Team"
__license__ = "MIT"

# Re-export common modules for convenience
from backend.database import get_db_session
from backend.models.base import Base

__all__ = [
    "__version__",
    "__title__",
    "__description__",
    "__author__",
    "__license__",
    "get_db_session",
    "Base",
]