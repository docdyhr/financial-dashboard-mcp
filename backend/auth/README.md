# Authentication System

This module implements JWT-based authentication for the Financial Dashboard API.

## Overview

The authentication system provides:
- User registration with email and username
- JWT token-based authentication
- Password hashing with bcrypt
- Protected API endpoints
- User session management

## Usage

### Registration

```bash
POST /api/v1/auth/register
{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123",
    "full_name": "John Doe",
    "preferred_currency": "USD",
    "timezone": "America/New_York"
}
```

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

Returns:
```json
{
    "access_token": "eyJ...",
    "token_type": "bearer"
}
```

### Using Protected Endpoints

Include the token in the Authorization header:
```bash
GET /api/v1/positions
Authorization: Bearer eyJ...
```

## Development

For development, a default user is created:
- Email: user@example.com
- Username: testuser
- Password: password123

## Security Notes

- Tokens expire after 30 days by default
- Passwords are hashed using bcrypt
- JWT secret must be set via SECRET_KEY environment variable
- In production, use strong passwords and rotate secrets regularly
