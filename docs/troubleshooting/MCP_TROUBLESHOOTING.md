# MCP Server Troubleshooting Guide

This guide helps resolve common issues with the Financial Dashboard MCP server startup and configuration.

## Common Error Messages and Solutions

### 1. `spawn python ENOENT`

**Error Message:**
```
[error] spawn python ENOENT
[error] Server disconnected. For troubleshooting guidance, please visit our debugging documentation
```

**Cause:** The MCP client cannot find the Python executable or the path is incorrect.

**Solutions:**

#### Option A: Use Full Python Path
Update your Claude Desktop configuration to use the full path to Python:

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/Users/yourusername/Programming/financial-dashboard-mcp/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### Option B: Use the Startup Script
Use the provided startup script which handles environment setup:

```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/bin/bash",
      "args": ["/full/path/to/financial-dashboard-mcp/scripts/start_mcp_server.sh"],
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### Option C: Check Python Installation
```bash
# Verify Python is installed and accessible
which python
python --version

# Activate virtual environment
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
which python
```

### 2. Module Import Errors

**Error Message:**
```
ImportError: No module named 'mcp'
ModuleNotFoundError: No module named 'mcp_server'
```

**Solution:**
Install the project in development mode:

```bash
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
pip install -e .
```

### 3. Dependencies Missing

**Error Message:**
```
Missing required modules: mcp, fastapi, sqlalchemy
```

**Solution:**
Install all dependencies:

```bash
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
```

### 4. Environment Configuration Issues

**Error Message:**
```
Environment variable not set: BACKEND_URL
.env file not found
```

**Solutions:**

#### Create .env file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### Set environment variables in Claude Desktop config:
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 5. Backend Connection Errors

**Error Message:**
```
Error retrieving positions: Client error '404 Not Found'
Connection refused: http://localhost:8000
```

**Solution:**
Start the backend services first:

```bash
cd /path/to/financial-dashboard-mcp
./scripts/start_dashboard.sh
```

Or manually:
```bash
# Terminal 1: Backend
make run-backend

# Terminal 2: Redis (if needed)
redis-server

# Terminal 3: Celery (if needed)
make run-celery
```

### 6. Port Conflicts

**Error Message:**
```
Address already in use: 8000
Port 8502 is already in use
```

**Solution:**
Check and kill processes using the ports:

```bash
# Check what's using the port
lsof -i :8000
lsof -i :8502

# Kill processes if needed
kill -9 <PID>

# Or use different ports in .env:
API_PORT=8001
MCP_SERVER_PORT=8503
```

## Diagnostic Commands

### 1. Test MCP Server Independently
```bash
cd /path/to/financial-dashboard-mcp
python scripts/test_mcp_server.py
```

### 2. Test Python Module Loading
```bash
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
python -c "import mcp_server; print('MCP server module loaded successfully')"
```

### 3. Test MCP Server Startup
```bash
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
python -m mcp_server
# Should show initialization logs, press Ctrl+C to stop
```

### 4. Check Dependencies
```bash
cd /path/to/financial-dashboard-mcp
source .venv/bin/activate
pip list | grep -E "(mcp|fastapi|streamlit|sqlalchemy)"
```

### 5. Verify Backend is Running
```bash
curl http://localhost:8000/docs
# Should return HTML or redirect to API docs
```

## Step-by-Step Debugging Process

### Step 1: Verify Python Environment
```bash
cd /path/to/financial-dashboard-mcp
ls .venv/  # Should exist
source .venv/bin/activate
python --version  # Should be 3.11.x
which python  # Note this path for Claude config
```

### Step 2: Test MCP Server Locally
```bash
python -m mcp_server
# Look for "Loaded X MCP tools" message
# Press Ctrl+C to stop
```

### Step 3: Check Claude Desktop Configuration
1. Open Claude Desktop
2. Go to Settings → Developer
3. Check MCP server configuration
4. Verify paths are absolute and correct

### Step 4: Test Backend Connection
```bash
# Start backend
make run-backend

# In another terminal, test API
curl http://localhost:8000/api/portfolio/positions
```

### Step 5: Full Integration Test
```bash
# Start all services
./scripts/start_dashboard.sh

# Test MCP server
python scripts/test_mcp_server.py

# Configure Claude Desktop and test
```

## Configuration Examples

### Minimal Claude Desktop Configuration
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/full/path/to/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/full/path/to/financial-dashboard-mcp"
    }
  }
}
```

### Full Configuration with Environment Variables
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/full/path/to/.venv/bin/python",
      "args": ["-m", "mcp_server"],
      "cwd": "/full/path/to/financial-dashboard-mcp",
      "env": {
        "BACKEND_URL": "http://localhost:8000",
        "ENVIRONMENT": "development",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "/full/path/to/financial-dashboard-mcp"
      }
    }
  }
}
```

### Using Startup Script (Recommended)
```json
{
  "mcpServers": {
    "financial-dashboard": {
      "command": "/bin/bash",
      "args": ["/full/path/to/financial-dashboard-mcp/scripts/start_mcp_server.sh"],
      "cwd": "/full/path/to/financial-dashboard-mcp"
    }
  }
}
```

## Logging and Debugging

### Enable Debug Logging
Add to your .env file:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

### Check Claude Desktop Logs
- **macOS:** `~/Library/Logs/Claude/claude.log`
- **Windows:** `%USERPROFILE%\AppData\Local\Claude\logs\claude.log`

### MCP Server Logs
The MCP server logs to stderr, which appears in Claude Desktop logs. Look for:
```
[financial-dashboard] [info] Starting Financial Dashboard MCP Server
[financial-dashboard] [info] Loaded 13 MCP tools
```

## Common Platform-Specific Issues

### macOS
- Use `/usr/bin/python3` if not using virtual environment
- Ensure Xcode command line tools are installed: `xcode-select --install`
- Check Python path: `which python3`

### Windows
- Use forward slashes or double backslashes in paths
- Ensure Python is in PATH or use full path
- Use `.exe` extension: `python.exe`

### Linux
- Install `python3-venv` if virtual environment creation fails
- Check systemd services if running as service
- Verify firewall settings for port access

## Getting Help

If you're still experiencing issues:

1. **Run the full diagnostic:**
   ```bash
   python scripts/test_mcp_server.py
   ```

2. **Check project status:**
   ```bash
   make test
   make lint
   ```

3. **Create a minimal test case:**
   ```bash
   python -c "from mcp_server.main import main; print('Import successful')"
   ```

4. **Check the GitHub issues** for similar problems and solutions.

5. **Gather information for support:**
   - Python version: `python --version`
   - MCP server test output
   - Claude Desktop configuration
   - Error messages from logs
   - Operating system and version

## Quick Fix Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Backend services running
- [ ] .env file exists and configured
- [ ] Claude Desktop config uses absolute paths
- [ ] Python executable path is correct
- [ ] Ports are not in use by other processes
- [ ] MCP server test passes
- [ ] Backend API responds to curl tests

## Preventive Measures

1. **Use the startup script** instead of direct Python commands
2. **Always use absolute paths** in Claude Desktop configuration
3. **Test locally first** before configuring Claude Desktop
4. **Keep dependencies updated** with `pip install -e . --upgrade`
5. **Monitor logs** for early warning signs
6. **Document any custom configuration** changes
