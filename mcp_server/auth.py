"""Authentication utilities for MCP server."""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication for MCP server API calls."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """Initialize auth manager."""
        self.backend_url = backend_url
        self._auth_token: Optional[str] = None
        self._user_id: Optional[int] = None

        # Get demo credentials from environment or use defaults
        self.demo_username = os.getenv("DEMO_USERNAME", "demo")
        self.demo_password = os.getenv("DEMO_PASSWORD", "demo123")

    async def get_auth_token(self) -> Optional[str]:
        """Get current auth token, refreshing if needed."""
        if self._auth_token is None:
            await self._authenticate()
        return self._auth_token

    async def get_user_id(self) -> Optional[int]:
        """Get current user ID."""
        if self._user_id is None:
            await self._authenticate()
        return self._user_id

    async def get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authentication."""
        token = await self.get_auth_token()
        if not token:
            raise ValueError("Authentication failed - no valid token")

        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _authenticate(self) -> None:
        """Authenticate with the backend API."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to authenticate with demo credentials
                auth_data = {
                    "username": self.demo_username,
                    "password": self.demo_password,
                }

                response = await client.post(
                    f"{self.backend_url}/api/v1/auth/login",
                    data=auth_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    token_data = response.json()
                    self._auth_token = token_data.get("access_token")

                    # Get user info to extract user_id
                    if self._auth_token:
                        user_response = await client.get(
                            f"{self.backend_url}/api/v1/auth/me",
                            headers={"Authorization": f"Bearer {self._auth_token}"},
                        )
                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            self._user_id = user_data.get("id")
                            logger.info(f"Authenticated as user {self._user_id}")
                        else:
                            logger.warning(
                                "Could not fetch user info after authentication"
                            )

                    logger.info("Successfully authenticated with backend")
                else:
                    logger.error(
                        f"Authentication failed: {response.status_code} - {response.text}"
                    )
                    # Fall back to hardcoded user_id for demo purposes
                    self._user_id = 3
                    logger.warning("Using fallback user_id=3 for demo mode")

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            # Fall back to demo mode with hardcoded user_id
            self._user_id = 3
            logger.warning("Authentication failed, using demo mode with user_id=3")

    async def refresh_token(self) -> None:
        """Refresh the authentication token."""
        self._auth_token = None
        self._user_id = None
        await self._authenticate()


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager(backend_url: str = "http://localhost:8000") -> AuthManager:
    """Get the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(backend_url)
    return _auth_manager
