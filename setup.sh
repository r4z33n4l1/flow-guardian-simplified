#!/bin/bash
# Flow Guardian Setup Script

set -e

echo "🚀 Setting up Flow Guardian..."

# Check Python version
PYTHON_CMD=""
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$PYTHON_VERSION >= 3.10" | bc -l) -eq 1 ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python 3.10+ required"
    echo "Install with: brew install python@3.10"
    exit 1
fi

echo "✓ Found Python: $($PYTHON_CMD --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Get FREE API keys (required):"
echo "   • Cerebras (LLM): https://cloud.cerebras.ai/ → API Keys"
echo "   • Gemini (Embeddings): https://ai.google.dev/ → Get API Key"
echo ""
echo "3. Configure environment variables:"
echo "   cp .env.example .env"
echo "   nano .env  # Add your API keys"
echo ""
echo "   Required in .env:"
echo "   CEREBRAS_API_KEY=csk-...  # For extracting insights"
echo "   GEMINI_API_KEY=...        # For semantic search"
echo ""
echo "   💡 Want to use different providers? See PROVIDERS.md"
echo ""
echo "4. Start Flow Guardian (daemon + API):"
echo "   python server.py all --foreground"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 MCP Integration (for Claude Code)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Add this to your ~/.claude/.mcp.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "flow-guardian": {'
echo "      \"command\": \"$(pwd)/venv/bin/python\","
echo '      "args": ["server.py", "mcp"],'
echo "      \"cwd\": \"$(pwd)\","
echo '      "env": {'
echo '        "CEREBRAS_API_KEY": "csk-...",'
echo '        "GEMINI_API_KEY": "..."'
echo '      }'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Then restart Claude Code to load the MCP tools."
