# VS Code Testing Panel Troubleshooting Guide

## Overview
This guide helps troubleshoot issues with the VS Code TESTING panel not showing tests or failing to run them properly.

## Quick Diagnostic Steps

### 1. Verify Test Discovery
```bash
# Run this in the terminal to verify pytest can discover tests
.venv/bin/pytest --collect-only tests/ --no-cov -q
```
**Expected result:** Should show 477+ tests collected

### 2. Check Python Interpreter
1. Open Command Palette (`Cmd+Shift+P`)
2. Type "Python: Select Interpreter"
3. Ensure you select: `./venv/bin/python` (Python 3.11.13)

### 3. Verify VS Code Settings
Check `.vscode/settings.json` contains:
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": ["tests", "--no-cov"],
    "python.testing.cwd": "${workspaceFolder}",
    "python.testing.pytestPath": "${workspaceFolder}/.venv/bin/pytest"
}
```

## Common Issues and Solutions

### Issue 1: Tests Not Showing in TESTING Panel

**Solution 1: Refresh Test Discovery**
1. Open Command Palette (`Cmd+Shift+P`)
2. Run "Test: Refresh Tests"
3. Wait for discovery to complete

**Solution 2: Reload VS Code Window**
1. Command Palette → "Developer: Reload Window"
2. Wait for extensions to reload
3. Check TESTING panel again

**Solution 3: Clear VS Code Caches**
```bash
# Close VS Code first, then run:
rm -rf .vscode/.ropeproject
rm -rf **/__pycache__
rm -rf **/.pytest_cache
```

### Issue 2: Python Extension Not Working

**Solution: Reinstall Python Extension**
1. Go to Extensions panel
2. Find "Python" extension by Microsoft
3. Disable and re-enable
4. Or uninstall and reinstall

### Issue 3: Import Errors in Tests

**Check these settings in `.vscode/settings.json`:**
```json
{
    "python.analysis.extraPaths": [
        "${workspaceFolder}",
        "${workspaceFolder}/backend",
        "${workspaceFolder}/frontend",
        "${workspaceFolder}/mcp_server"
    ],
    "python.envFile": "${workspaceFolder}/.env"
}
```

### Issue 4: Pytest Configuration Conflicts

**Verify minimal `pytest.ini`:**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
minversion = 7.4.0
addopts =
    --strict-markers
    --strict-config
    --ignore=archive
    --ignore=scripts
```

## Verification Commands

### Test Individual Files
```bash
# Test a single file
.venv/bin/pytest tests/test_basic.py -v --no-cov

# Test a specific test
.venv/bin/pytest tests/test_basic.py::test_basic_math -v --no-cov
```

### Debug Mode
```bash
# Run with maximum verbosity
.venv/bin/pytest tests/test_basic.py -vvv --no-cov --tb=long
```

## VS Code Command Palette Commands

### Essential Testing Commands
- `Test: Refresh Tests` - Refresh test discovery
- `Test: Run All Tests` - Run all tests
- `Test: Debug All Tests` - Debug all tests
- `Python: Select Interpreter` - Select Python interpreter
- `Python: Refresh IntelliSense` - Refresh code analysis

## Environment Verification

### Check Virtual Environment
```bash
# Verify Python version
.venv/bin/python --version  # Should show Python 3.11.13

# Verify pytest installation
.venv/bin/pytest --version  # Should show pytest 7.4.0+

# Check current working directory
pwd  # Should be project root

# Verify .env file exists
ls -la .env
```

### Check File Permissions
```bash
# Ensure pytest is executable
ls -la .venv/bin/pytest

# Ensure all test files are readable
find tests/ -name "*.py" -exec ls -la {} \;
```

## Advanced Troubleshooting

### Enable VS Code Logging
1. Open settings (`Cmd+,`)
2. Search for "python.logging"
3. Set "Python › Logging: Level" to "debug"
4. Check Output panel → Python

### Check Extension Conflicts
- Disable other Python-related extensions temporarily
- Common conflicts: Pylance, Python Docstring Generator, etc.

### Reset VS Code Workspace
```bash
# Backup and remove VS Code settings
mv .vscode .vscode.backup
# Restart VS Code and reconfigure
```

## File Structure Verification

Ensure your project has this structure:
```
financial-dashboard-mcp/
├── .vscode/
│   ├── settings.json
│   ├── tasks.json
│   └── launch.json
├── .venv/
│   └── bin/
│       ├── python
│       └── pytest
├── tests/
│   ├── test_basic.py
│   ├── api/
│   ├── auth/
│   └── ...
├── pytest.ini
└── .env
```

## Success Indicators

When everything works correctly:
- TESTING panel shows all test files and functions
- Tests can be run individually by clicking the play button
- Tests can be debugged by right-clicking → "Debug Test"
- Status bar shows test results
- Failed tests show in Problems panel

## Getting Help

If issues persist:
1. Check VS Code Python extension documentation
2. Verify pytest documentation
3. Check project-specific issues in CHANGELOG.md
4. Review logs in VS Code Output panel
