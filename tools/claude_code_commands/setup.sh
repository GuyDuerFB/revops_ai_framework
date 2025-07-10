#!/bin/bash
# Setup script for RevOps Claude Code slash commands

echo "🔧 Setting up RevOps Claude Code slash commands..."

# Make the Python script executable
chmod +x revops_debug_agent.py

# Check if Claude Code configuration directory exists
CLAUDE_CONFIG_DIR="$HOME/.claude-code"
COMMANDS_DIR="$CLAUDE_CONFIG_DIR/commands"

if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "⚠️  Claude Code configuration directory not found at $CLAUDE_CONFIG_DIR"
    echo "💡 Please ensure Claude Code is installed and has been run at least once."
    exit 1
fi

# Create commands directory if it doesn't exist
mkdir -p "$COMMANDS_DIR"

# Copy command files to Claude Code configuration
cp revops_debug_agent.py "$COMMANDS_DIR/"
cp claude_code_commands.json "$COMMANDS_DIR/"

echo "✅ Copied command files to $COMMANDS_DIR"

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
python3 -c "import boto3, botocore" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install boto3 botocore
}

echo "🎉 Setup complete!"
echo ""
echo "📋 Usage:"
echo "  /revops debug_agent                    # Interactive debugging session"
echo "  /revops debug_agent --help             # Show all options"
echo ""
echo "🔍 Before using:"
echo "  1. Ensure AWS SSO is logged in:"
echo "     aws sso login --profile FireboltSystemAdministrator-740202120544"
echo ""
echo "  2. Test the command:"
echo "     /revops debug_agent"
echo ""
echo "📚 For help with Claude Code slash commands:"
echo "     https://docs.anthropic.com/en/docs/claude-code/slash-commands"