#!/bin/bash

# LangGraph Coding Agent - One-Command Startup Script
# Usage: ./start.sh

set -e  # Exit on error

echo "🚀 Starting LangGraph Coding Agent..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓${NC} Found Python ${PYTHON_VERSION}"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓${NC} Dependencies installed"

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${RED}⚠️  Missing .env file${NC}"
    echo ""
    echo "Creating .env file for you..."
    
    cat > .env << 'EOF'
# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone API Key (Optional - for semantic codebase search)
PINECONE_API_KEY=your_pinecone_api_key_here

# OpenAI Model (Optional - defaults to gpt-4o)
# OPENAI_MODEL=gpt-4o
EOF
    
    echo -e "${GREEN}✓${NC} Created .env file"
    echo ""
    echo -e "${YELLOW}📝 ACTION REQUIRED:${NC}"
    echo "1. Edit the .env file and add your OPENAI_API_KEY"
    echo "2. (Optional) Add PINECONE_API_KEY for semantic codebase search"
    echo ""
    echo "Get your OpenAI API key from: https://platform.openai.com/api-keys"
    echo "Get your Pinecone API key from: https://app.pinecone.io"
    echo ""
    echo -e "${BLUE}After adding your API keys, run this script again:${NC}"
    echo "  ./start.sh"
    echo ""
    exit 0
fi

# Source .env file
export $(grep -v '^#' .env | xargs)

# Verify OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo ""
    echo -e "${RED}❌ OPENAI_API_KEY not configured in .env file${NC}"
    echo ""
    echo "Please edit .env and add your OpenAI API key:"
    echo "  OPENAI_API_KEY=sk-..."
    echo ""
    echo "Get your API key from: https://platform.openai.com/api-keys"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓${NC} Environment configured"

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Setup complete! Starting agent...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo "  • Type '/help' to see available commands"
echo "  • Type 'exit' or press Ctrl+C to quit"
echo "  • Use '/list' to see conversation history"
echo ""
echo -e "${GREEN}Starting agent...${NC}"
echo ""

# Run the CLI
python3 -m cli.main

