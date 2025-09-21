#!/bin/bash

# Travel Chatbot Deployment Script
# This script sets up and runs the travel chatbot API server

set -e  # Exit on any error

echo "🚀 Starting Travel Chatbot Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📍 Working directory: $SCRIPT_DIR${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if .env file exists
if [ ! -f "config/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    cp config/.env.example config/.env
    echo -e "${RED}❗ Please edit config/.env with your API keys before running the chatbot${NC}"
    echo -e "${YELLOW}   Required: API_KEY (OpenRouter/OpenAI)${NC}"
    echo -e "${YELLOW}   Optional: Google Vision API credentials, Langfuse keys${NC}"
    exit 1
fi

# Install/upgrade dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r reqironments.txt
pip install streamlit fastapi uvicorn langfuse google-cloud-vision flask flask-cors

# Check if database file exists, if not create it
if [ ! -f "travel_chats.db" ]; then
    echo -e "${YELLOW}🗄️  Database not found. It will be created automatically on first use.${NC}"
fi

# Get port from environment or use default
PORT=${PORT:-5001}

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}🌐 Starting Travel Chatbot API Server on port $PORT...${NC}"
echo -e "${BLUE}📡 The API will be available at: http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}🔗 Integration endpoints for your website:${NC}"
echo -e "${YELLOW}   POST http://localhost:$PORT/chat           - Main chat endpoint${NC}"
echo -e "${YELLOW}   GET  http://localhost:$PORT/health         - Health check${NC}"
echo -e "${YELLOW}   GET  http://localhost:$PORT/info           - Chatbot info${NC}"
echo -e "${YELLOW}   POST http://localhost:$PORT/sessions       - Create session${NC}"
echo ""
echo -e "${GREEN}🎯 Press Ctrl+C to stop the server${NC}"
echo ""

# Run the web application
python web_app.py