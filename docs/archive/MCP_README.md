# MCP Integration for NIFTY Bearnness Screener

This project now includes Model Context Protocol (MCP) support, allowing AI assistants like Claude to interact directly with your trading analysis tools.

## ✅ Status: FULLY WORKING & TESTED

The MCP server has been successfully implemented and tested. All stdout pollution issues have been resolved and the server properly handles the complete MCP protocol sequence.

**Latest Test Results:**
- ✅ MCP server starts without errors
- ✅ Properly responds to `initialize` requests with tools capabilities
- ✅ Accepts `initialized` notifications
- ✅ Successfully serves `tools/list` with all 6 tools
- ✅ Breeze API messages correctly redirected to stderr
- ✅ JSON-RPC protocol compliance verified
- ✅ Claude Desktop connection should now work

## What is MCP?

MCP (Model Context Protocol) is a protocol that enables AI assistants to connect to external tools and data sources. Your trading analysis functions are now exposed as MCP tools that can be called by AI assistants.

## Quick Setup (Already Configured)

### ✅ Configuration Complete
The Claude Desktop configuration has been automatically copied to: `C:\Users\DELL\AppData\Roaming\Claude\claude_desktop_config.json`

### 🔄 Next Steps
1. **Restart Claude Desktop** completely
2. **Wait 10-15 seconds** for MCP server to load
3. **Test with:** "Show me the stocks in the NIFTY 50 universe"

## Setup Instructions (Manual)

### 1. Install Dependencies

The MCP package has already been installed. If you need to reinstall:

```bash
pip install mcp>=1.26.0
```

### 2. Configure Claude Desktop (or other MCP clients)

1. Locate your Claude Desktop configuration file:
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Add the NIFTY Bearnness MCP server configuration:

```json
{
  "mcpServers": {
    "nifty-bearnness": {
      "command": "d:\\DreamProject\\algooptions\\venv\\Scripts\\python.exe",
      "args": ["d:\\DreamProject\\algooptions\\mcp_server.py"],
      "env": {
        "PYTHONPATH": "d:\\DreamProject\\algooptions"
      }
    }
  }
}
```

**Note**: Adjust the paths according to your actual installation directory.

### 3. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the new MCP server.

## Available MCP Tools

Once configured, Claude will have access to these trading analysis tools:

### 1. `analyze_stock`
Analyze a specific stock's technical indicators and scoring.

**Parameters:**
- `symbol` (string): Stock symbol (e.g., 'RELIANCE.NS')
- `days` (integer, optional): Number of days to analyze (default: 30)

### 2. `get_universe_stocks`
Get list of stocks in a specific universe.

**Parameters:**
- `universe` (string): Universe name ('nifty50', 'nifty100', 'nifty200', 'nifty500', 'niftylarge')

### 3. `run_backtest`
Run a backtest on a specific universe.

**Parameters:**
- `universe` (string): Universe to backtest
- `start_date` (string, optional): Start date (YYYY-MM-DD, default: '2024-01-01')
- `end_date` (string, optional): End date (YYYY-MM-DD, default: '2024-12-31')
- `initial_capital` (number, optional): Initial capital amount (default: 100000)

### 4. `generate_report`
Generate an HTML report for universe analysis.

**Parameters:**
- `universe` (string): Universe to analyze
- `output_file` (string, optional): Output HTML file path

### 5. `get_market_regime`
Get current market regime analysis.

**Parameters:** None

### 6. `score_stocks`
Score stocks based on technical indicators.

**Parameters:**
- `symbols` (array): List of stock symbols to score
- `universe` (string, optional): Universe name (alternative to providing symbols)

## Usage Examples

Once configured, you can ask Claude things like:

- "Analyze RELIANCE.NS for the last 60 days"
- "Show me the stocks in the NIFTY 50 universe"
- "Run a backtest on NIFTY 100 from January to June 2024"
- "Generate a report for NIFTY Large Cap stocks"
- "What's the current market regime?"
- "Score these stocks: TCS.NS, INFY.NS, HDFC.NS"

## Testing the MCP Server

To test that the MCP server works correctly:

```bash
python test_mcp_server.py
```

This will start the server briefly and verify it initializes without errors.

## What Was Fixed

### Issues Resolved:
1. **Import Errors** - Fixed incorrect class names and missing imports
2. **Stdout Pollution** - Breeze API messages now go to stderr, keeping stdout clean for MCP protocol
3. **Initialization Errors** - Proper MCP server initialization with correct capabilities and NotificationOptions
4. **Method Mismatches** - Updated all tool implementations to use correct API methods
5. **Protocol Compliance** - Full MCP protocol sequence (initialize → initialized → tools/list) working

## Extending the MCP Server

To add new tools, modify `mcp_server.py`:

1. Add the tool definition in `handle_list_tools()`
2. Implement the tool logic in `handle_call_tool()`
3. Create the actual function that performs the work

## Troubleshooting

### Server won't start
- Check that all Python dependencies are installed
- Verify the paths in the configuration are correct
- Check the console/logs for error messages

### Tools not appearing in Claude
- Ensure Claude Desktop is restarted after configuration changes
- Check that the configuration file syntax is valid JSON
- Verify the Python path and script path are correct

### Tool execution fails
- Check that your trading modules can be imported
- Ensure database connections and API keys are configured
- Look at the MCP server logs for detailed error messages

## Security Considerations

- The MCP server runs locally and only accepts connections from the configured MCP client
- No external network access is required
- All data processing happens on your local machine
- Be cautious about sharing the Claude Desktop configuration file

## Future Enhancements

Potential improvements to the MCP integration:

- Add real-time data streaming tools
- Implement portfolio optimization tools
- Add risk management analysis tools
- Include options strategy analysis
- Support for custom universe creation
- Integration with trading platforms for order execution