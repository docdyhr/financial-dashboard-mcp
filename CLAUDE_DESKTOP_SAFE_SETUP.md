# Safe Claude Desktop Setup - Financial Dashboard

## ⚠️ Important: Safe Configuration

The previous JSON config may have crashed Claude Desktop. Here are safer approaches:

## Option 1: Simple API Helper Script (Recommended)

Use the provided Python script to safely access your Financial Dashboard:

### Usage Examples:

```bash
# Check health
python claude_desktop_api_helper.py health

# Get assets
python claude_desktop_api_helper.py assets

# Get positions
python claude_desktop_api_helper.py positions

# Get transactions
python claude_desktop_api_helper.py transactions

# Get portfolio overview
python claude_desktop_api_helper.py overview

# Get user info
python claude_desktop_api_helper.py me
```

## Option 2: Direct API Calls (Manual)

Use these safe curl commands in Claude Desktop:

### Authentication Token
```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4
```

### Safe API Endpoints:

#### Health Check
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4" \
http://localhost:8000/health
```

#### Get Portfolio Positions
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4" \
"http://localhost:8000/api/v1/positions/?user_id=3"
```

#### Get Assets
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4" \
http://localhost:8000/api/v1/assets/
```

#### Get Transactions
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4" \
"http://localhost:8000/api/v1/transactions/?user_id=3"
```

## Option 3: Minimal MCP Configuration (Advanced)

If you want to try MCP again, use this minimal config:

```json
{
  "mcpServers": {}
}
```

Then gradually add servers one by one.

## Troubleshooting

### If Claude Desktop Crashed:
1. **Restart Claude Desktop** completely
2. **Clear any cached configurations**
3. **Use the safe Python helper script first**
4. **Test with direct curl commands**

### Safe Testing:
```bash
# Test the helper script
python claude_desktop_api_helper.py health

# Should return:
{
  "status": "healthy",
  "service": "backend",
  "version": "0.1.0",
  "environment": "development"
}
```

## What Caused the Crash?

Likely issues with the previous config:
- **Invalid JSON structure** for Claude Desktop
- **Custom configuration format** not recognized
- **Token length** or special characters
- **Endpoint definitions** in wrong format

## Current Status

✅ **Financial Dashboard API**: Running on http://localhost:8000
✅ **Authentication**: Working with Bearer token
✅ **CORS**: Configured for Claude Desktop access
✅ **Safe Helper Script**: Available for testing

Use the Python helper script or direct curl commands until we can safely configure MCP integration.
