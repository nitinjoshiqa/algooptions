#!/usr/bin/env python3
"""
Test MCP server with protocol messages to simulate Claude Desktop connection
"""

import subprocess
import json
import sys
import time

def test_mcp_protocol():
    """Test MCP server with actual protocol messages."""
    print("Testing MCP server with protocol messages...")

    # Start the MCP server
    cmd = [
        "d:\\DreamProject\\algooptions\\venv\\Scripts\\python.exe",
        "d:\\DreamProject\\algooptions\\mcp_server.py"
    ]

    print(f"Starting MCP server: {' '.join(cmd)}")

    try:
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="d:\\DreamProject\\algooptions"
        )

        # Give it a moment to start
        time.sleep(2)

        # Send MCP initialize message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }

        print("Sending initialize message...")
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline().strip()
        if response_line:
            try:
                response = json.loads(response_line)
                print(f"✓ Received response: {response.get('result', {}).get('serverInfo', {}).get('name', 'unknown')}")
            except json.JSONDecodeError as e:
                print(f"✗ Invalid JSON response: {e}")
                print(f"Raw response: {response_line}")
        else:
            print("✗ No response received")

        # Send tools/list message
        tools_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }

        print("Sending tools/list message...")
        process.stdin.write(json.dumps(tools_message) + "\n")
        process.stdin.flush()

        # Read response
        response_line = process.stdout.readline().strip()
        if response_line:
            try:
                response = json.loads(response_line)
                tools = response.get('result', {}).get('tools', [])
                print(f"✓ Server exposes {len(tools)} tools")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"  - {tool.get('name')}: {tool.get('description', '')[:50]}...")
            except json.JSONDecodeError as e:
                print(f"✗ Invalid JSON response: {e}")
        else:
            print("✗ No response received")

        # Clean shutdown
        process.terminate()
        process.wait(timeout=5)

        print("✅ MCP protocol test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Error during MCP protocol test: {e}")
        if 'process' in locals():
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                pass
        return False

if __name__ == "__main__":
    success = test_mcp_protocol()
    sys.exit(0 if success else 1)