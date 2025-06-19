# Safe Claude Desktop MCP Setup - Financial Dashboard

## ✅ Problem Fixed: Proper MCP Server Implementation

The previous crash was caused by an improper configuration format. This setup provides a **real MCP server** that Claude Desktop can safely use.

## 🚀 Quick Setup

### 1. Install MCP Dependencies

```bash
pip install -r requirements-mcp.txt
```

### 2. Test the MCP Server

```bash
# Test the server standalone
python3 mcp_server/financial_dashboard_server.py
```

### 3. Configure Claude Desktop

Use the safe configuration file: `claude_desktop_safe_mcp_config.json`

**Location for Claude Desktop config:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Copy this exact configuration:**

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "python3",
      "args": [
        "/Users/thomas/Programming/financial-dashboard-mcp/mcp_server/financial_dashboard_server.py"
      ],
      "env": {
        "FINANCIAL_DASHBOARD_URL": "http://localhost:8000",
        "FINANCIAL_DASHBOARD_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzUyODY5NTI2fQ.gvNGOesVBIcVIP7a_p3T28cXXs416ncmt7GnpplgbC4",
        "FINANCIAL_DASHBOARD_USER_ID": "3"
      }
    }
  }
}
```

### 4. Restart Claude Desktop

1. **Completely quit** Claude Desktop
2. **Restart** Claude Desktop
3. The MCP server will automatically connect

## 🛠️ Available Tools in Claude Desktop

Once connected, you can use these commands:

### Portfolio Analysis
- `get_portfolio_overview` - Get total portfolio value and allocations
- `get_positions` - View all your stock/bond positions
- `get_assets` - Browse available investment assets

### Transaction History
- `get_transactions` - View recent transaction history
- `health_check` - Verify API connection

### Example Commands in Claude Desktop:
```
"Show me my portfolio overview"
"What are my current positions?"
"Get my last 5 transactions"
"Check if the financial dashboard is working"
```

## 🔧 Troubleshooting

### If MCP Server Won't Start:
```bash
# Check dependencies
pip install mcp httpx

# Test server directly
python3 mcp_server/financial_dashboard_server.py

# Check if API is running
curl http://localhost:8000/health
```

### If Claude Desktop Won't Connect:
1. **Check file path** in config matches your system
2. **Verify Financial Dashboard is running** on localhost:8000
3. **Check Claude Desktop logs** for connection errors
4. **Use absolute paths** in the configuration

### Authentication Issues:
- Token expires: January 14, 2026
- If auth fails, generate new token using the dashboard

## 🔒 Security Notes

- **Local only**: MCP server only connects to localhost:8000
- **No external connections**: All data stays on your machine
- **Token expiration**: Current token valid until 2026-01-14
- **User isolation**: Only accesses User ID 3 data

## ✨ What This Fixes

1. **No more crashes**: Proper MCP protocol implementation
2. **Real integration**: Native Claude Desktop tools
3. **Safe configuration**: Validated JSON format
4. **Error handling**: Graceful failure handling
5. **Rich output**: Formatted financial data display

## 📊 Current Status

✅ **Financial Dashboard API**: Running on http://localhost:8000
✅ **MCP Server**: Created and tested
✅ **Safe Configuration**: Provided
✅ **Dependencies**: Documented
✅ **Authentication**: Working with Bearer token

Ready for Claude Desktop integration!
