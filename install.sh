#!/bin/bash

# IPMA MCP Server Installation Script
# This script helps set up the IPMA weather MCP server for use with Open WebUI

set -e  # Exit on error

echo "=================================="
echo "IPMA MCP Server Installation"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠️  'uv' is not installed."
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo ""
    echo "✅ uv installed successfully!"
    echo "Please restart your terminal and run this script again."
    exit 0
fi

echo "✅ uv is installed"
echo ""

# Initialize project if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    uv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate 2>/dev/null || . .venv/Scripts/activate 2>/dev/null || true
echo ""

# Install dependencies
echo "📥 Installing dependencies..."
uv pip install -e .
echo "✅ Dependencies installed"
echo ""

# Test the installation
echo "🧪 Testing installation..."
if python -c "from mcp.server.fastmcp import FastMCP; import httpx; print('✅ All imports successful!')" 2>/dev/null; then
    echo ""
    echo "=================================="
    echo "✅ Installation Complete!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Test the server:"
    echo "   uv run python weather.py"
    echo ""
    echo "2. For Open WebUI integration, install mcpo:"
    echo "   uv tool install mcpo"
    echo ""
    echo "3. Run the server with mcpo proxy:"
    echo "   uvx mcpo --port 8000 --api-key \"your-secret-key\" -- uv run python weather.py"
    echo ""
    echo "4. Add to Open WebUI:"
    echo "   - URL: http://localhost:8000"
    echo "   - Auth: Bearer token with your API key"
    echo ""
    echo "See README.md for detailed integration instructions."
else
    echo "❌ Installation test failed. Please check the error messages above."
    exit 1
fi
