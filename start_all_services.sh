#!/bin/bash

# V3 Microservices Startup Script
# Starts all services: MongoDB, Centralized API, Web Service, Bot Service

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="/Users/apple/.pyenv/versions/3.10.11/bin/python"
TELEGRAM_TOKEN="${TELEGRAM_BOT_TOKEN:-8366781443:AAHIXgGD1UXvPWw9EIDBlMk5Ktuhj2qQ8WU}"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Startup - Starting All Services        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Start MongoDB
echo -e "${BLUE}1️⃣  Starting MongoDB on port 27018...${NC}"
mkdir -p /tmp/mongo_data
mongod --port 27018 --dbpath /tmp/mongo_data > /tmp/mongod.log 2>&1 &
MONGO_PID=$!
sleep 2
echo -e "${GREEN}✅ MongoDB started (PID: $MONGO_PID)${NC}"
echo ""

# 2. Start Centralized API
echo -e "${BLUE}2️⃣  Starting Centralized API on port 8000...${NC}"
cd "$PROJECT_DIR"
export TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
$PYTHON_BIN -m uvicorn centralized_api.app:app --reload --port 8000 > /tmp/api.log 2>&1 &
API_PID=$!
sleep 3
echo -e "${GREEN}✅ Centralized API started (PID: $API_PID)${NC}"
echo ""

# 3. Start Web Service
echo -e "${BLUE}3️⃣  Starting Web Service on port 8003...${NC}"
cd "$PROJECT_DIR"
$PYTHON_BIN -m uvicorn web.app:app --reload --port 8003 > /tmp/web.log 2>&1 &
WEB_PID=$!
sleep 2
echo -e "${GREEN}✅ Web Service started (PID: $WEB_PID)${NC}"
echo ""

# 4. Start Telegram Bot
echo -e "${BLUE}4️⃣  Starting Telegram Bot (polling)...${NC}"
export TELEGRAM_BOT_TOKEN="$TELEGRAM_TOKEN"
cd "$PROJECT_DIR"
$PYTHON_BIN bot/main.py > /tmp/bot.log 2>&1 &
BOT_PID=$!
sleep 2
echo -e "${GREEN}✅ Telegram Bot started (PID: $BOT_PID)${NC}"
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ ALL SERVICES STARTED                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Service Status:"
echo ""
echo -e "  ${GREEN}MongoDB${NC}             PID: $MONGO_PID   (port 27018)"
echo -e "  ${GREEN}Centralized API${NC}     PID: $API_PID   (port 8000)"
echo -e "  ${GREEN}Web Service${NC}         PID: $WEB_PID   (port 8003)"
echo -e "  ${GREEN}Telegram Bot${NC}        PID: $BOT_PID   (polling)"
echo ""
echo "🔗 Access Points:"
echo "  • Centralized API: http://localhost:8000"
echo "  • Web Service:     http://localhost:8003"
echo "  • API Docs:        http://localhost:8000/docs"
echo "  • Web Docs:        http://localhost:8003/docs"
echo ""
echo "📝 Log Files:"
echo "  • MongoDB:  tail -f /tmp/mongod.log"
echo "  • API:      tail -f /tmp/api.log"
echo "  • Web:      tail -f /tmp/web.log"
echo "  • Bot:      tail -f /tmp/bot.log"
echo ""
echo "🛑 To stop all services, run: ./stop_all_services.sh"
echo ""
