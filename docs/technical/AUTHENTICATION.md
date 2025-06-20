# Authentication and Authorization Documentation

## Overview

This document provides comprehensive guidance for implementing authentication and authorization in the Financial Dashboard MCP system. While the current version (v1.1.2) operates as a single-user system, the foundation for multi-user authentication has been established and is ready for implementation.

## Current Authentication State

### Single-User System (v1.1.2)
- **Status**: Production-ready single-user system
- **Security**: MCP server uses token-based authentication
- **User Model**: Complete User model prepared for multi-user expansion
- **Database**: User table with authentication fields ready

### MCP Server Authentication
The MCP server currently uses a simple bearer token authentication:

```python
# Environment Configuration
MCP_AUTH_TOKEN = "development-token"  # Change in production

# Usage
headers = {"Authorization": "Bearer development-token"}
```

## Database Schema

### User Model Structure
The system includes a comprehensive User model ready for authentication:

```python
class User(Base):
    # Basic Information
    email: str                    # Unique, indexed
    username: str                 # Unique, indexed
    full_name: str | None         # Optional display name

    # Authentication
    hashed_password: str          # Bcrypt hashed password
    is_active: bool              # Account status
    is_verified: bool            # Email verification status
    is_superuser: bool           # Admin privileges

    # User Preferences
    preferred_currency: str       # Default: "USD"
    timezone: str                # Default: "UTC"

    # Tracking
    last_login: datetime | None   # Last login timestamp
    email_verified_at: datetime | None  # Email verification date
```

## Implementation Roadmap

### Phase 1: Core Authentication System

#### 1.1 JWT Authentication Service

Create `backend/services/auth.py`:

```python
from datetime import datetime, timedelta
from typing import Any, Union
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
```

#### 1.2 Authentication Dependencies

Create `backend/dependencies/auth.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.services.auth import AuthService
from backend.database import get_db

security = HTTPBearer()
auth_service = AuthService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    try:
        payload = auth_service.verify_token(credentials.credentials)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    return user

async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
```

#### 1.3 Authentication Schemas

Create `backend/schemas/auth.py`:

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    user_id: int | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    preferred_currency: str
    timezone: str
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerification(BaseModel):
    token: str
```

#### 1.4 Authentication API Endpoints

Create `backend/api/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.user import User
from backend.schemas.auth import *
from backend.services.auth import AuthService
from backend.dependencies.auth import get_current_user

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    # Create user
    hashed_password = auth_service.get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # TODO: Send verification email

    return db_user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token = auth_service.create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)."""
    return {"message": "Successfully logged out"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token."""
    access_token = auth_service.create_access_token(data={"sub": str(current_user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": auth_service.access_token_expire_minutes * 60
    }
```

### Phase 2: Email Verification and Password Reset

#### 2.1 Email Service

Create `backend/services/email.py`:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from backend.config import get_settings

settings = get_settings()

class EmailService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email

        # Setup Jinja2 for email templates
        self.env = Environment(loader=FileSystemLoader('backend/templates/email'))

    async def send_email(self, to_email: str, subject: str, html_content: str):
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise

    async def send_verification_email(self, user_email: str, verification_token: str):
        """Send email verification."""
        template = self.env.get_template('verification.html')
        verification_url = f"{settings.frontend_url}/verify-email?token={verification_token}"

        html_content = template.render(
            verification_url=verification_url,
            app_name="Financial Dashboard"
        )

        await self.send_email(
            to_email=user_email,
            subject="Verify Your Email Address",
            html_content=html_content
        )

    async def send_password_reset_email(self, user_email: str, reset_token: str):
        """Send password reset email."""
        template = self.env.get_template('password_reset.html')
        reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"

        html_content = template.render(
            reset_url=reset_url,
            app_name="Financial Dashboard"
        )

        await self.send_email(
            to_email=user_email,
            subject="Reset Your Password",
            html_content=html_content
        )
```

#### 2.2 Token Management

Create `backend/services/tokens.py`:

```python
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from backend.models.user import User

class TokenService:
    def __init__(self):
        self.verification_token_expire_hours = 24
        self.reset_token_expire_hours = 1

    def generate_verification_token(self) -> str:
        """Generate email verification token."""
        return secrets.token_urlsafe(32)

    def generate_reset_token(self) -> str:
        """Generate password reset token."""
        return secrets.token_urlsafe(32)

    def create_verification_token(self, db: Session, user_id: int) -> str:
        """Create and store verification token."""
        token = self.generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=self.verification_token_expire_hours)

        # Store token in database (you'd need a UserToken model)
        # user_token = UserToken(
        #     user_id=user_id,
        #     token=token,
        #     token_type="email_verification",
        #     expires_at=expires_at
        # )
        # db.add(user_token)
        # db.commit()

        return token

    def verify_verification_token(self, db: Session, token: str) -> User | None:
        """Verify email verification token."""
        # Implement token verification logic
        pass

    def create_reset_token(self, db: Session, user_id: int) -> str:
        """Create and store password reset token."""
        token = self.generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=self.reset_token_expire_hours)

        # Store token in database
        return token

    def verify_reset_token(self, db: Session, token: str) -> User | None:
        """Verify password reset token."""
        # Implement token verification logic
        pass
```

### Phase 3: Authorization and Permissions

#### 3.1 Portfolio Access Control

Create `backend/services/permissions.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.models.position import Position
from backend.models.portfolio_snapshot import PortfolioSnapshot

class PermissionService:
    @staticmethod
    def check_portfolio_access(user: User, user_id: int):
        """Check if user can access portfolio data."""
        if user.id != user_id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this portfolio"
            )

    @staticmethod
    def check_position_ownership(db: Session, user: User, position_id: int):
        """Check if user owns the position."""
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )

        if position.user_id != user.id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this position"
            )

        return position

    @staticmethod
    def check_admin_access(user: User):
        """Check if user has admin access."""
        if not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
```

#### 3.2 Updated API Endpoints with Authorization

Update existing API endpoints to include authorization:

```python
# Example: Updated portfolio endpoint
@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get portfolio summary for authenticated user."""
    portfolio_service = PortfolioService()
    return await portfolio_service.get_portfolio_summary(db, current_user.id)

# Example: Updated positions endpoint
@router.get("/", response_model=PaginatedResponse[PositionResponse])
async def get_positions(
    current_user: User = Depends(get_current_verified_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get user's positions."""
    position_service = PositionService()
    return await position_service.get_user_positions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
```

### Phase 4: Frontend Authentication Integration

#### 4.1 Streamlit Authentication

Create `frontend/auth.py`:

```python
import streamlit as st
import requests
from datetime import datetime, timedelta

class StreamlitAuth:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session_key = "auth_token"
        self.user_key = "current_user"

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        token = st.session_state.get(self.session_key)
        return token is not None

    def get_auth_headers(self) -> dict:
        """Get authentication headers."""
        token = st.session_state.get(self.session_key)
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def login(self, email: str, password: str) -> bool:
        """Login user."""
        try:
            response = requests.post(
                f"{self.backend_url}/api/auth/login",
                data={"username": email, "password": password}
            )

            if response.status_code == 200:
                token_data = response.json()
                st.session_state[self.session_key] = token_data["access_token"]

                # Get user profile
                user_response = requests.get(
                    f"{self.backend_url}/api/auth/me",
                    headers=self.get_auth_headers()
                )

                if user_response.status_code == 200:
                    st.session_state[self.user_key] = user_response.json()
                    return True

        except Exception as e:
            st.error(f"Login failed: {e}")

        return False

    def logout(self):
        """Logout user."""
        if self.session_key in st.session_state:
            del st.session_state[self.session_key]
        if self.user_key in st.session_state:
            del st.session_state[self.user_key]

    def require_auth(self):
        """Require authentication for page access."""
        if not self.is_authenticated():
            self.show_login_page()
            st.stop()

    def show_login_page(self):
        """Show login form."""
        st.title("🔐 Login Required")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                if self.login(email, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    def get_current_user(self) -> dict | None:
        """Get current user data."""
        return st.session_state.get(self.user_key)
```

#### 4.2 Protected Streamlit Pages

Update main app to include authentication:

```python
# frontend/app.py
import streamlit as st
from auth import StreamlitAuth

# Initialize authentication
auth = StreamlitAuth("http://localhost:8000")

# Require authentication
auth.require_auth()

# Get current user
current_user = auth.get_current_user()

st.title(f"📈 Financial Dashboard - Welcome {current_user['full_name'] or current_user['username']}")

# Add logout button in sidebar
with st.sidebar:
    if st.button("Logout"):
        auth.logout()
        st.rerun()

# Rest of your app...
```

### Phase 5: MCP Server Multi-User Support

#### 5.1 User Context in MCP Tools

Update MCP tools to accept user context:

```python
# mcp_server/tools/portfolio.py
async def get_positions(user_id: int = 1) -> dict[str, Any]:
    """Get portfolio positions for specific user."""
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/positions",
            headers=headers,
            params={"user_id": user_id}  # Add user context
        )

        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False, "error": "Failed to fetch positions"}
```

## Security Considerations

### Password Security
- Use bcrypt for password hashing
- Enforce strong password requirements
- Implement password history to prevent reuse
- Add account lockout after failed attempts

### Token Security
- Use secure JWT tokens with appropriate expiration
- Implement token refresh mechanism
- Store sensitive tokens securely
- Use HTTPS for all authentication endpoints

### Session Management
- Implement secure session handling
- Add session timeout
- Track concurrent sessions
- Provide session invalidation

### Rate Limiting
- Implement rate limiting on auth endpoints
- Add CAPTCHA for repeated failed attempts
- Monitor for suspicious activity
- Log authentication events

### Environment Security
```bash
# Production environment variables
SECRET_KEY="your-very-secure-secret-key-here"
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
SMTP_SERVER="smtp.yourdomain.com"
SMTP_PORT=587
SMTP_USERNAME="noreply@yourdomain.com"
SMTP_PASSWORD="your-smtp-password"
FROM_EMAIL="Financial Dashboard <noreply@yourdomain.com>"
FRONTEND_URL="https://yourdomain.com"
```

## Testing Authentication

### Unit Tests
```python
# tests/test_auth.py
def test_user_registration():
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepassword123"
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200

def test_user_login():
    """Test user login."""
    login_data = {
        "username": "test@example.com",
        "password": "securepassword123"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_protected_endpoint():
    """Test protected endpoint access."""
    # Without token
    response = client.get("/api/portfolio/summary")
    assert response.status_code == 401

    # With token
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/api/portfolio/summary", headers=headers)
    assert response.status_code == 200
```

## Migration from Single-User to Multi-User

### Database Migration
```python
# Database migration script
def migrate_to_multi_user():
    """Migrate existing data to multi-user format."""
    # Create default admin user
    admin_user = User(
        email="admin@yourdomain.com",
        username="admin",
        hashed_password=hash_password("secure_admin_password"),
        is_superuser=True,
        is_verified=True
    )
    db.add(admin_user)
    db.commit()

    # Assign all existing positions to admin user
    positions = db.query(Position).filter(Position.user_id == None).all()
    for position in positions:
        position.user_id = admin_user.id

    db.commit()
```

### Configuration Updates
```python
# Update settings for multi-user mode
MULTI_USER_MODE = True
REQUIRE_EMAIL_VERIFICATION = True
ALLOW_REGISTRATION = False  # Set to True to allow public registration
DEFAULT_USER_PERMISSIONS = ["read_portfolio", "manage_positions"]
```

## Deployment Checklist

### Pre-Deployment
- [ ] Generate secure SECRET_KEY for production
- [ ] Configure SMTP settings for email
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Review and test all authentication flows
- [ ] Prepare admin user creation script
- [ ] Update frontend authentication integration
- [ ] Test MCP server with user context

### Security Review
- [ ] Audit all authentication endpoints
- [ ] Verify token expiration settings
- [ ] Test authorization controls
- [ ] Review password requirements
- [ ] Validate email verification flow
- [ ] Test password reset functionality
- [ ] Verify admin access controls
- [ ] Check for common vulnerabilities (OWASP Top 10)

## Conclusion

This authentication system provides a comprehensive foundation for transitioning from single-user to multi-user operation while maintaining security best practices. The modular design allows for gradual implementation and testing of each component.

Key benefits:
- **Secure**: Industry-standard JWT authentication with bcrypt password hashing
- **Scalable**: Designed for multi-user operation from the ground up
- **Flexible**: Role-based permissions and user management
- **Integrated**: Works seamlessly with existing MCP server and frontend
- **Maintainable**: Clean separation of concerns and comprehensive testing

For implementation support and detailed technical guidance, refer to the individual component documentation and example code provided in this document.
