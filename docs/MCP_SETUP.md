# MCP Server Setup for Claude Desktop

## Installation

1. **Install the Financial Dashboard MCP Server:**
   ```bash
   cd /path/to/financial-dashboard-mcp
   pip install -e .
   ```

2. **Start the backend services:**
   ```bash
   ./scripts/start_dashboard.sh
   ```

3. **Configure Claude Desktop:**
   
   Add the following to your Claude Desktop configuration file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "financial-dashboard": {
         "command": "python",
         "args": [
           "/full/path/to/financial-dashboard-mcp/scripts/start_mcp_server.py"
         ],
         "env": {
           "BACKEND_URL": "http://localhost:8000"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop** to load the MCP server.

## Available Tools

### Portfolio Management
- `get_positions` - Retrieve current portfolio positions
- `get_portfolio_summary` - Get comprehensive portfolio overview
- `get_allocation` - Get current portfolio allocation breakdown
- `add_position` - Add a new position to the portfolio
- `update_position` - Update an existing portfolio position

### Market Data
- `get_asset_price` - Get current price and basic info for an asset
- `calculate_performance` - Calculate portfolio performance for specific periods
- `analyze_portfolio_risk` - Analyze portfolio risk metrics and volatility
- `get_market_trends` - Get current market trends and sector performance

### AI Analytics
- `recommend_allocation` - Get AI-powered portfolio allocation recommendations
- `analyze_opportunity` - Find investment opportunities based on criteria
- `rebalance_portfolio` - Generate portfolio rebalancing recommendations
- `generate_insights` - Generate AI-powered portfolio insights and recommendations

## Example Usage

Once configured, you can ask Claude questions like:

- "Show me my current portfolio positions"
- "What's my portfolio performance this year?"
- "Recommend an allocation for moderate risk tolerance"
- "Analyze opportunities in growth stocks"
- "Should I rebalance my portfolio?"
- "Give me insights on my portfolio risk"

## Troubleshooting

- Ensure the backend is running on `http://localhost:8000`
- Check that the MCP server script path is correct
- Look at Claude Desktop logs for any connection issues
- Test the MCP server independently: `python scripts/test_mcp_server.py`
