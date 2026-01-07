#!/bin/bash

# V3 Microservices Stop Script
# Cleanly stops all services

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     V3 Microservices Shutdown - Stopping All Services       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop Telegram Bot
echo -e "${YELLOW}Stopping Telegram Bot...${NC}"
pkill -f "python bot/main.py" 2>/dev/null && echo -e "${GREEN}✅ Bot stopped${NC}" || echo -e "${RED}ℹ️  Bot not running${NC}"

# Stop Web Service
echo -e "${YELLOW}Stopping Web Service...${NC}"
pkill -f "uvicorn web.app" 2>/dev/null && echo -e "${GREEN}✅ Web Service stopped${NC}" || echo -e "${RED}ℹ️  Web Service not running${NC}"

# Stop Centralized API
echo -e "${YELLOW}Stopping Centralized API...${NC}"
pkill -f "uvicorn centralized_api.app" 2>/dev/null && echo -e "${GREEN}✅ Centralized API stopped${NC}" || echo -e "${RED}ℹ️  Centralized API not running${NC}"

# Stop MongoDB
echo -e "${YELLOW}Stopping MongoDB...${NC}"
pkill mongod 2>/dev/null && echo -e "${GREEN}✅ MongoDB stopped${NC}" || echo -e "${RED}ℹ️  MongoDB not running${NC}"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 ✅ ALL SERVICES STOPPED                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
