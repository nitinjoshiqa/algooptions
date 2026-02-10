#!/usr/bin/env python3
"""
Test script for MCP Server functionality
Run this to verify the MCP server is working correctly.
"""

import subprocess
import sys
import time
import json

def test_mcp_server():
    """Test the MCP server by running it and checking basic functionality."""
    print("Testing MCP Server...")

    # Start the MCP server as a subprocess
    try:
        cmd = [
            "d:\\DreamProject\\algooptions\\venv\\Scripts\\python.exe",
            "d:\\DreamProject\\algooptions\\mcp_server.py"
        ]

        print(f"Starting MCP server with command: {' '.join(cmd)}")

        # For testing, we'll just check if the server starts without errors
        # In a real test, you'd send MCP protocol messages
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

        # Check if process is still running
        if process.poll() is None:
            print("✅ MCP server started successfully")
            process.terminate()
            process.wait()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ MCP server failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return False

    except Exception as e:
        print(f"❌ Error testing MCP server: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)