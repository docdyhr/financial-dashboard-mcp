# Claude Desktop Access Setup

This guide shows how to connect Claude Desktop to your local Financial Dashboard instance.

## Prerequisites

1. Financial Dashboard is running locally:
   - Backend API: http://localhost:8000
   - Streamlit UI: http://localhost:8503
   - All services (PostgreSQL, Redis, Celery) are running

2. CORS has been configured to allow Claude Desktop access (✅ completed)

## Method 1: Direct API Access

### 1. Create a Test User via API

First, create a user account that Claude Desktop can use:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "claude_desktop",
    "email": "claude@desktop.com",
    "password": "ClaudeDesktop123!",
    "full_name": "Claude Desktop User"
  }'
```

### 2. Get Authentication Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=claude_desktop&password=ClaudeDesktop123!"
```

Save the `access_token` from the response.

### 3. Configure Claude Desktop

In Claude Desktop, you can now make API calls to your Financial Dashboard:

**Base URL**: `http://localhost:8000`
**Authentication**: Bearer token (from step 2)

Example API calls:
- Health Check: `GET http://localhost:8000/health`
- Get Assets: `GET http://localhost:8000/api/v1/assets/`
- Get Positions: `GET http://localhost:8000/api/v1/positions/?user_id=USER_ID`

## Method 2: MCP Server Integration (Advanced)

For deeper integration, you can set up the MCP server to provide Claude Desktop with structured access to your portfolio data.

### 1. Install MCP Dependencies

```bash
pip install .[ai]  # Installs MCP dependencies
```

### 2. Configure MCP Server

Update your `.env` file:
```bash
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8502
MCP_AUTH_TOKEN=your-secure-mcp-token
```

### 3. Start MCP Server

```bash
# Start the MCP server (when implemented)
python -m mcp_server.main
```

### 4. Connect Claude Desktop to MCP

Add the MCP server to Claude Desktop's configuration:

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "env": {
        "FINANCIAL_DASHBOARD_URL": "http://localhost:8000",
        "MCP_AUTH_TOKEN": "your-secure-mcp-token"
      }
    }
  }
}
```

## Available API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user info

### Assets
- `GET /api/v1/assets/` - List all assets
- `GET /api/v1/assets/ticker/{ticker}` - Get asset by ticker
- `POST /api/v1/assets/` - Create new asset

### Positions
- `GET /api/v1/positions/?user_id={id}` - Get user positions
- `POST /api/v1/positions/` - Create new position

### Transactions
- `GET /api/v1/transactions/?user_id={id}` - Get transactions
- `POST /api/v1/transactions/buy` - Create buy transaction
- `POST /api/v1/transactions/sell` - Create sell transaction

### Portfolio
- `GET /api/v1/portfolio/overview?user_id={id}` - Portfolio overview
- `GET /api/v1/portfolio/performance?user_id={id}` - Performance metrics

## Example Usage in Claude Desktop

Once configured, you can ask Claude Desktop questions like:

- "What's my current portfolio value?"
- "Show me my top performing stocks"
- "Create a new position for 100 shares of AAPL at $150"
- "What's my total unrealized P&L?"

Claude Desktop will use the API endpoints to fetch real data from your local Financial Dashboard instance.

## Security Considerations

### Development Mode (Current)
- CORS allows all origins (`*`) for easy development
- Authentication tokens have long expiration (30 days)
- Debug mode enabled

### Production Mode
- Restrict CORS to specific origins
- Shorter token expiration times
- Disable debug mode
- Use HTTPS
- Environment-specific secrets

## Troubleshooting

### Authentication Fails
1. Check that the backend is running: `curl http://localhost:8000/health`
2. Verify CORS settings allow Claude Desktop
3. Ensure credentials are correct

### API Calls Fail
1. Check the API documentation: http://localhost:8000/docs
2. Verify the user_id parameter is correct
3. Check authentication token is valid

### Connection Issues
1. Confirm all services are running:
   - PostgreSQL: `pg_isready`
   - Redis: `redis-cli ping`
   - Backend: `curl http://localhost:8000/health`

## Current Test Credentials

For immediate testing, use these pre-created accounts:

**Account 1:**
- Username: `demo`
- Password: `demo123`

**Account 2:**
- Username: `testprod`
- Password: `TestProd123!`

Both accounts have sample data for testing portfolio functionality.
