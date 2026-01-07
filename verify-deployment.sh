#!/bin/bash

# Production Deployment Verification Script
# Run this after deployment to verify everything is working

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED=$((PASSED + 1))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED=$((FAILED + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Start checks
echo "=========================================="
echo "Telegram Bot - Production Verification"
echo "=========================================="
echo ""

# 1. Docker status
echo "1. Docker Status"
echo "   -----------"
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    check_pass "Docker services running"
else
    check_fail "Docker services not running"
fi
echo ""

# 2. Database connectivity
echo "2. Database Connectivity"
echo "   ---------------------"
if docker-compose -f docker-compose.prod.yml exec -T mongo mongosh --eval "db.adminCommand('ping')" &>/dev/null; then
    check_pass "MongoDB is responding"
else
    check_fail "MongoDB is not responding"
fi

if docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping &>/dev/null; then
    check_pass "Redis is responding"
else
    check_fail "Redis is not responding"
fi
echo ""

# 3. API Health
echo "3. API Health"
echo "   ----------"
API_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/health)
HTTP_CODE=$(echo "$API_RESPONSE" | tail -n1)
BODY=$(echo "$API_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    check_pass "API responding (HTTP 200)"
    check_info "Response: $BODY"
else
    check_fail "API not responding (HTTP $HTTP_CODE)"
fi
echo ""

# 4. Web Service Health
echo "4. Web Service Health"
echo "   ------------------"
WEB_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8003/api/health 2>/dev/null || echo "error\n000")
HTTP_CODE=$(echo "$WEB_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    check_pass "Web service responding (HTTP 200)"
else
    check_warn "Web service health check may not be available"
fi
echo ""

# 5. Bot Service
echo "5. Bot Service"
echo "   -----------"
BOT_LOG=$(docker-compose -f docker-compose.prod.yml logs bot 2>&1)
if echo "$BOT_LOG" | grep -q "polling"; then
    check_pass "Bot is polling for updates"
elif echo "$BOT_LOG" | grep -q "running"; then
    check_pass "Bot service is running"
else
    check_warn "Bot polling status unclear - check logs"
fi
echo ""

# 6. Environment Configuration
echo "6. Environment Configuration"
echo "   -------------------------"
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    source .env
    
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ "$TELEGRAM_BOT_TOKEN" != "YOUR_BOT_TOKEN_HERE" ]; then
        check_pass "TELEGRAM_BOT_TOKEN is set"
    else
        check_fail "TELEGRAM_BOT_TOKEN not configured"
    fi
    
    if [ -n "$SECRET_KEY" ] && [ ${#SECRET_KEY} -ge 32 ]; then
        check_pass "SECRET_KEY is configured (length: ${#SECRET_KEY})"
    else
        check_fail "SECRET_KEY not configured or too short"
    fi
    
    if [ -n "$MONGODB_URL" ]; then
        check_pass "MONGODB_URL is configured"
    else
        check_fail "MONGODB_URL not configured"
    fi
else
    check_fail ".env file not found"
fi
echo ""

# 7. Directory Structure
echo "7. Directory Structure"
echo "   -------------------"
if [ -d "logs" ]; then
    check_pass "logs directory exists"
else
    check_warn "logs directory missing"
fi

if [ -f "docker-compose.prod.yml" ]; then
    check_pass "docker-compose.prod.yml exists"
else
    check_fail "docker-compose.prod.yml missing"
fi

if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt missing"
fi
echo ""

# 8. Docker Image Information
echo "8. Docker Images"
echo "   ---------------"
API_IMAGE=$(docker-compose -f docker-compose.prod.yml images -q centralized-api)
BOT_IMAGE=$(docker-compose -f docker-compose.prod.yml images -q bot)
WEB_IMAGE=$(docker-compose -f docker-compose.prod.yml images -q web)

if [ -n "$API_IMAGE" ]; then
    check_pass "API image built ($(docker images --format '{{.ID}}' $API_IMAGE 2>/dev/null | cut -c1-12))"
else
    check_fail "API image not found"
fi

if [ -n "$BOT_IMAGE" ]; then
    check_pass "Bot image built"
else
    check_fail "Bot image not found"
fi

if [ -n "$WEB_IMAGE" ]; then
    check_pass "Web image built"
else
    check_fail "Web image not found"
fi
echo ""

# 9. Recent Logs
echo "9. Recent Logs"
echo "   -----------"
check_info "API Service (last 5 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=5 centralized-api 2>&1 | sed 's/^/      /'

echo ""
check_info "Bot Service (last 5 lines):"
docker-compose -f docker-compose.prod.yml logs --tail=5 bot 2>&1 | sed 's/^/      /'
echo ""

# 10. System Resources
echo "10. System Resources"
echo "    -----------------"
TOTAL_MEMORY=$(docker stats --no-stream --format "{{.MemUsage}}" 2>/dev/null | head -1)
check_info "Docker memory usage: $TOTAL_MEMORY"

DISK_USAGE=$(du -sh . 2>/dev/null | cut -f1)
check_info "Application disk usage: $DISK_USAGE"
echo ""

# Summary
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed:  $PASSED${NC}"
echo -e "${RED}Failed:  $FAILED${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Some warnings found - review above${NC}"
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Test /start command in Telegram"
    echo "  2. Test /help to list all commands"
    echo "  3. Test one action command (e.g., /ban)"
    echo "  4. Monitor logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Critical checks failed - see above${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  docker-compose -f docker-compose.prod.yml logs"
    echo "  docker-compose -f docker-compose.prod.yml ps"
    echo ""
    exit 1
fi
