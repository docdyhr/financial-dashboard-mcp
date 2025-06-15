# Claude Desktop MCP Server Setup Guide

## 🎯 Current Issue

Your Claude Desktop is showing `spawn python ENOENT` errors because it's using an outdated configuration. This guide will fix the issue and get your MCP server working with Claude Desktop.

## 📍 Claude Desktop Configuration Location

Claude Desktop stores its configuration in:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## 🔧 Step-by-Step Fix

### Step 1: Backup Current Configuration

First, let's backup your current configuration:

```bash
# Create backup
cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json.backup

# View current config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Step 2: Update Configuration

Replace the contents of `~/Library/Application Support/Claude/claude_desktop_config.json` with:

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/Users/thomas/Programming/financial-dashboard-mcp/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/thomas/Programming/financial-dashboard-mcp",
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Step 3: Alternative Configuration (if above doesn't work)

If the direct Python path doesn't work, try using the startup script:

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/bin/bash",
      "args": ["/Users/thomas/Programming/financial-dashboard-mcp/scripts/start_mcp_server.sh"],
      "cwd": "/Users/thomas/Programming/financial-dashboard-mcp"
    }
  }
}
```

### Step 4: Quick Update Commands

You can update the configuration using these commands:

```bash
# Option 1: Direct copy (recommended)
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/Users/thomas/Programming/financial-dashboard-mcp/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/Users/thomas/Programming/financial-dashboard-mcp",
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
EOF

# Option 2: Copy from our generated config
cp /Users/thomas/Programming/financial-dashboard-mcp/docs/claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## 🔄 Restart Claude Desktop

After updating the configuration:

1. **Quit Claude Desktop completely** (Cmd+Q)
2. **Wait 5 seconds**
3. **Restart Claude Desktop**
4. **Wait for it to fully load**

## ✅ Verify the Fix

### Check the Logs

Monitor the Claude Desktop logs to see if the error is resolved:

```bash
# Watch logs in real-time
tail -f ~/Library/Logs/Claude/mcp-server-financial-dashboard.log

# Check recent entries
tail -20 ~/Library/Logs/Claude/mcp-server-financial-dashboard.log
```

### Expected Success Logs

You should see logs like:
```
[info] Initializing server...
[info] Starting Financial Dashboard MCP Server
[info] Loaded 13 MCP tools
[info] Starting financial-dashboard-mcp v1.0.0
```

### Test in Claude

Ask Claude:
```
"What financial tools do you have available?"
```

You should see a response mentioning the 13 financial dashboard tools.

## 🚨 Troubleshooting

### If Still Getting ENOENT Errors

1. **Verify Python path exists:**
   ```bash
   ls -la /Users/thomas/Programming/financial-dashboard-mcp/.venv/bin/python
   ```

2. **Test MCP server manually:**
   ```bash
   cd /Users/thomas/Programming/financial-dashboard-mcp
   .venv/bin/python -m mcp_server --test
   ```

3. **Check services are running:**
   ```bash
   cd /Users/thomas/Programming/financial-dashboard-mcp
   ./scripts/services.sh status
   ```

### Alternative Configuration Methods

#### Method A: Using Shell Script
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/bin/bash",
      "args": ["-c", "cd /Users/thomas/Programming/financial-dashboard-mcp && source .venv/bin/activate && python -m mcp_server"],
      "cwd": "/Users/thomas/Programming/financial-dashboard-mcp"
    }
  }
}
```

#### Method B: Using Full Environment
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/usr/bin/env",
      "args": ["bash", "-c", "cd /Users/thomas/Programming/financial-dashboard-mcp && .venv/bin/python -m mcp_server"],
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "PYTHONPATH": "/Users/thomas/Programming/financial-dashboard-mcp"
      }
    }
  }
}
```

## 📋 Configuration Validation

### Validate JSON Syntax

Before updating Claude Desktop, validate your JSON:

```bash
# Test JSON syntax
python3 -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Test MCP Server Connectivity

```bash
# Test the exact command Claude will use
cd /Users/thomas/Programming/financial-dashboard-mcp
/Users/thomas/Programming/financial-dashboard-mcp/.venv/bin/python -m mcp_server --test
```

## 🎯 Expected Results

After successful configuration:

### ✅ In Claude Desktop Logs
```
[info] Initializing server...
[info] MCP server started successfully
[info] Loaded 13 MCP tools
```

### ✅ In Claude Chat
- Claude will recognize financial dashboard tools
- You can ask about portfolio management
- AI analytics tools will be available

### ✅ Available Tools
1. **Portfolio Management** (5 tools)
   - get_positions, get_portfolio_summary, get_allocation
   - add_position, update_position

2. **Market Data** (4 tools)
   - get_asset_price, calculate_performance
   - analyze_portfolio_risk, get_market_trends

3. **AI Analytics** (4 tools)
   - recommend_allocation, analyze_opportunity
   - rebalance_portfolio, generate_insights

## 🔧 Maintenance

### Regular Checks

```bash
# Check MCP server status
cd /Users/thomas/Programming/financial-dashboard-mcp
python scripts/test_mcp_standalone.py

# Check all services
./scripts/services.sh health

# View recent Claude logs
tail -50 ~/Library/Logs/Claude/mcp-server-financial-dashboard.log
```

### Before Using MCP Tools

Always ensure the backend services are running:

```bash
cd /Users/thomas/Programming/financial-dashboard-mcp
./scripts/services.sh start all
```

## 📞 Support

If you continue experiencing issues:

1. **Check the troubleshooting section above**
2. **Review the logs for specific error messages**
3. **Test each component individually**
4. **Verify all file paths are correct**

The MCP server is fully functional and tested - the issue is just getting Claude Desktop to use the correct configuration!
