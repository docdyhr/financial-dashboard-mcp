#!/usr/bin/env python3
"""Safe Claude Desktop MCP Server Configuration Updater
Adds or updates the financial-dashboard MCP server while preserving all other existing servers.
"""

import json
import sys
from pathlib import Path
from typing import Any


# Colors for output
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def log_info(message: str) -> None:
    """Log info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")


def log_success(message: str) -> None:
    """Log success message."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")


def log_warning(message: str) -> None:
    """Log warning message."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")


def log_error(message: str) -> None:
    """Log error message."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


class ClaudeConfigUpdater:
    """Safely updates Claude Desktop configuration while preserving existing MCP servers."""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.claude_config_dir = (
            Path.home() / "Library" / "Application Support" / "Claude"
        )
        self.claude_config_file = self.claude_config_dir / "claude_desktop_config.json"
        self.backup_file = self.claude_config_dir / "claude_desktop_config.json.backup"

    def validate_project(self) -> bool:
        """Validate that the project structure is correct."""
        log_info("Validating project structure...")

        # Check virtual environment
        venv_python = self.project_root / ".venv" / "bin" / "python"
        if not venv_python.exists():
            log_error(f"Virtual environment Python not found: {venv_python}")
            return False

        # Check MCP server module
        mcp_main = self.project_root / "mcp_server" / "__main__.py"
        if not mcp_main.exists():
            log_error(f"MCP server module not found: {mcp_main}")
            return False

        log_success("Project structure validated")
        return True

    def test_mcp_server(self) -> bool:
        """Test that the MCP server can be loaded."""
        log_info("Testing MCP server functionality...")

        try:
            # Add project root to Python path for testing
            sys.path.insert(0, str(self.project_root))

            from mcp_server.main import FinancialDashboardMCP

            mcp = FinancialDashboardMCP()
            tool_count = len(mcp.all_tools)

            log_success(f"MCP server test passed - {tool_count} tools loaded")
            return True

        except Exception as e:
            log_error(f"MCP server test failed: {e}")
            return False

    def load_existing_config(self) -> dict[str, Any]:
        """Load existing Claude Desktop configuration."""
        if not self.claude_config_file.exists():
            log_info("No existing configuration found, will create new one")
            return {}

        try:
            with open(self.claude_config_file) as f:
                config = json.load(f)
            log_info("Loaded existing configuration")
            return config
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON in configuration file: {e}")
            raise
        except Exception as e:
            log_error(f"Error reading configuration file: {e}")
            raise

    def backup_config(self) -> None:
        """Create backup of existing configuration."""
        if self.claude_config_file.exists():
            try:
                with open(self.claude_config_file) as src:
                    config = json.load(src)

                with open(self.backup_file, "w") as dst:
                    json.dump(config, dst, indent=2)

                log_success(f"Backup created: {self.backup_file}")

                # Show existing servers
                servers = config.get("mcpServers", {})
                if servers:
                    log_info("Existing MCP servers that will be preserved:")
                    for server_name in servers.keys():
                        status = (
                            "🔄 Will update"
                            if server_name == "financial-dashboard"
                            else "✅ Will preserve"
                        )
                        log_info(f"  • {server_name}: {status}")
                else:
                    log_info("No existing MCP servers found")

            except Exception as e:
                log_error(f"Failed to create backup: {e}")
                raise
        else:
            log_info("No existing configuration to backup")

    def create_financial_dashboard_config(self) -> dict[str, Any]:
        """Create the financial-dashboard MCP server configuration."""
        return {
            "command": str(self.project_root / ".venv" / "bin" / "python"),
            "args": ["-m", "mcp_server"],
            "cwd": str(self.project_root),
            "env": {
                "BACKEND_URL": "http://localhost:8000",
                "PYTHONPATH": str(self.project_root),
            },
        }

    def update_config(self) -> None:
        """Update Claude Desktop configuration safely."""
        log_info("Updating Claude Desktop configuration...")

        # Ensure directory exists
        self.claude_config_dir.mkdir(parents=True, exist_ok=True)

        # Load existing configuration
        config = self.load_existing_config()

        # Ensure mcpServers section exists
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add or update financial-dashboard server
        financial_config = self.create_financial_dashboard_config()

        was_existing = "financial-dashboard" in config["mcpServers"]
        config["mcpServers"]["financial-dashboard"] = financial_config

        # Write updated configuration
        try:
            with open(self.claude_config_file, "w") as f:
                json.dump(config, f, indent=2)

            action = "Updated" if was_existing else "Added"
            log_success(f"{action} financial-dashboard MCP server configuration")

        except Exception as e:
            log_error(f"Failed to write configuration: {e}")
            raise

    def validate_config(self) -> bool:
        """Validate the updated configuration."""
        log_info("Validating updated configuration...")

        try:
            with open(self.claude_config_file) as f:
                config = json.load(f)

            # Check structure
            if "mcpServers" not in config:
                log_error("Missing mcpServers section")
                return False

            if "financial-dashboard" not in config["mcpServers"]:
                log_error("Missing financial-dashboard server configuration")
                return False

            # Check financial-dashboard configuration
            fd_config = config["mcpServers"]["financial-dashboard"]
            required_fields = ["command", "args", "cwd", "env"]

            for field in required_fields:
                if field not in fd_config:
                    log_error(f"Missing required field: {field}")
                    return False

            log_success("Configuration validation passed")
            return True

        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON in updated configuration: {e}")
            return False
        except Exception as e:
            log_error(f"Error validating configuration: {e}")
            return False

    def show_summary(self) -> None:
        """Show summary of the configuration update."""
        try:
            with open(self.claude_config_file) as f:
                config = json.load(f)

            servers = config.get("mcpServers", {})

            log_info("Configuration update summary:")
            print("=" * 50)
            print(f"Total MCP servers: {len(servers)}")

            for server_name in sorted(servers.keys()):
                if server_name == "financial-dashboard":
                    print(f"  • {server_name}: ✅ Financial Dashboard (updated)")
                else:
                    print(f"  • {server_name}: ✅ Preserved")

            print("=" * 50)

            # Show financial-dashboard details
            fd_config = servers.get("financial-dashboard", {})
            if fd_config:
                print("\nFinancial Dashboard MCP Server Configuration:")
                print(f"  Command: {fd_config.get('command', 'N/A')}")
                print(f"  Working Directory: {fd_config.get('cwd', 'N/A')}")
                print(
                    f"  Backend URL: {fd_config.get('env', {}).get('BACKEND_URL', 'N/A')}"
                )

        except Exception as e:
            log_warning(f"Could not show summary: {e}")

    def restore_backup(self) -> bool:
        """Restore configuration from backup."""
        if not self.backup_file.exists():
            log_error("No backup file found to restore")
            return False

        try:
            with open(self.backup_file) as src:
                config = json.load(src)

            with open(self.claude_config_file, "w") as dst:
                json.dump(config, dst, indent=2)

            log_success("Configuration restored from backup")
            return True

        except Exception as e:
            log_error(f"Failed to restore backup: {e}")
            return False

    def run(self, restore_mode: bool = False) -> bool:
        """Run the configuration update process."""
        print("Financial Dashboard - Claude Desktop Configuration Updater")
        print("=" * 60)

        if restore_mode:
            return self.restore_backup()

        try:
            # Validate project
            if not self.validate_project():
                return False

            # Test MCP server
            if not self.test_mcp_server():
                log_warning(
                    "MCP server test failed, but continuing with configuration update"
                )

            # Create backup
            self.backup_config()

            # Update configuration
            self.update_config()

            # Validate updated configuration
            if not self.validate_config():
                log_error("Configuration validation failed, restoring backup...")
                self.restore_backup()
                return False

            # Show summary
            self.show_summary()

            # Show next steps
            print("\n" + "=" * 60)
            log_success("Claude Desktop configuration updated successfully!")
            print()
            log_warning("IMPORTANT: Restart Claude Desktop for changes to take effect")
            print()
            log_info("Next steps:")
            log_info("1. Quit Claude Desktop completely (Cmd+Q)")
            log_info("2. Wait 5 seconds")
            log_info("3. Restart Claude Desktop")
            log_info("4. Ask Claude: 'What financial tools do you have available?'")
            print()

            return True

        except Exception as e:
            log_error(f"Configuration update failed: {e}")
            log_info("Attempting to restore backup...")
            self.restore_backup()
            return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Safely add or update Financial Dashboard MCP server in Claude Desktop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add_to_claude_config.py           # Update configuration
  python scripts/add_to_claude_config.py --restore # Restore from backup
  python scripts/add_to_claude_config.py --test    # Test only, don't update
        """,
    )

    parser.add_argument(
        "--restore", action="store_true", help="Restore configuration from backup"
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test MCP server only, do not update configuration",
    )

    args = parser.parse_args()

    updater = ClaudeConfigUpdater()

    if args.test:
        # Test mode - just validate project and MCP server
        if updater.validate_project() and updater.test_mcp_server():
            log_success("All tests passed - ready for Claude Desktop integration")
            sys.exit(0)
        else:
            log_error("Tests failed")
            sys.exit(1)
    elif args.restore:
        # Restore mode
        if updater.restore_backup():
            sys.exit(0)
        else:
            sys.exit(1)
    # Update mode
    elif updater.run():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
