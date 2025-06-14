"""Financial Dashboard Backend Package."""

<<<<<<< HEAD
__version__ = "1.2.0"
=======
__version__ = "1.1.1"
>>>>>>> 78c7171 (feat: add comprehensive authentication documentation)
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
