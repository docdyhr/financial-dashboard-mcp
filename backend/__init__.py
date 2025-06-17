"""Financial Dashboard Backend Package."""

__version__ = "2.0.2"
__title__ = "Financial Dashboard MCP"
__description__ = "A comprehensive financial dashboard system with AI integration"
__author__ = "Financial Dashboard Team"
__license__ = "MIT"

# Re-export common modules for convenience
from backend.database import get_db_session
from backend.models.base import Base

__all__ = [
    "Base",
    "__author__",
    "__description__",
    "__license__",
    "__title__",
    "__version__",
    "get_db_session",
]
