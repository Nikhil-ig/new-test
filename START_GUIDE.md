# 🚀 V3 Microservices - Complete Start Guide

## Quick Start (All Services at Once)

```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
./start_all_services.sh
```

---

## Manual Startup (One Service at a Time)

### Terminal 1: Start MongoDB
```bash
mkdir -p /tmp/mongo_data
mongod --port 27018 --dbpath /tmp/mongo_data
```

### Terminal 2: Start Centralized API
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
/Users/apple/.pyenv/versions/3.10.11/bin/python -m uvicorn centralized_api.app:app --reload --port 8000
```

### Terminal 3: Start Web Service
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
/Users/apple/.pyenv/versions/3.10.11/bin/python -m uvicorn web.app:app --reload --port 8002
```

### Terminal 4: Start Telegram Bot
```bash
export TELEGRAM_BOT_TOKEN="8366781443:AAHIXgGD1UXvPWw9EIDBlMk5Ktuhj2qQ8WU"
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
/Users/apple/.pyenv/versions/3.10.11/bin/python bot/main.py
```

---

## Verification Checklist

### Check MongoDB is Running
```bash
curl -v mongodb://localhost:27018
# Or check logs
tail -f /tmp/mongod.log
```

### Check Centralized API is Healthy
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"healthy","service":"centralized_api","version":"1.0.0","database":"connected"}
```

### Check Web Service is Running
```bash
curl http://localhost:8002
# Expected: {"service":"Web Service","version":"1.0.0","status":"running","documentation":"/docs"}
```

### Check Bot Logs
```bash
tail -f /tmp/bot.log
# Look for: "Bot is polling for updates..."
```

---

## Service URLs

| Service | URL | Documentation |
|---------|-----|----------------|
| Centralized API | http://localhost:8000 | http://localhost:8000/docs |
| Web Service | http://localhost:8002 | http://localhost:8002/docs |
| Health Check | http://localhost:8000/api/health | - |

---

## Stop All Services

### Using the stop script:
```bash
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
./stop_all_services.sh
```

### Manual stop (run in any terminal):
```bash
# Stop Telegram Bot
pkill -f "python bot/main.py"

# Stop Web Service
pkill -f "uvicorn web.app"

# Stop Centralized API
pkill -f "uvicorn centralized_api.app"

# Stop MongoDB
pkill mongod
```

---

## Common Issues & Solutions

### "Port already in use" error

```bash
# Find what's using the port
lsof -i :8000    # Centralized API
lsof -i :8002    # Web Service
lsof -i :27018   # MongoDB

# Kill the process
kill -9 <PID>
```

### MongoDB won't start

```bash
# Check if another instance is running
ps aux | grep mongod

# Remove lock file if it exists
rm -f /tmp/mongo_data/mongod.lock

# Start fresh
mongod --port 27018 --dbpath /tmp/mongo_data
```

### API returns "database connection failed"

```bash
# Verify MongoDB is running first
ps aux | grep mongod

# Check MongoDB logs
tail -f /tmp/mongod.log

# Restart API
pkill -f "uvicorn centralized_api"
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
/Users/apple/.pyenv/versions/3.10.11/bin/python -m uvicorn centralized_api.app:app --reload --port 8000
```

### Bot not responding to commands

```bash
# Check if bot is running
ps aux | grep "python bot/main.py"

# Verify token is set
echo $TELEGRAM_BOT_TOKEN

# Check bot logs
tail -f /tmp/bot.log

# Restart bot
pkill -f "python bot/main.py"
export TELEGRAM_BOT_TOKEN="8366781443:AAHIXgGD1UXvPWw9EIDBlMk5Ktuhj2qQ8WU"
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
/Users/apple/.pyenv/versions/3.10.11/bin/python bot/main.py
```

---

## Log Locations

```bash
# View MongoDB logs
tail -f /tmp/mongod.log

# View API logs
tail -f /tmp/api.log

# View Web Service logs
tail -f /tmp/web.log

# View Bot logs
tail -f /tmp/bot.log
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  CLIENTS                                 │
│  (Telegram Users, Web Browsers, Mobile Apps)            │
└────────┬───────────────────────────────┬────────────────┘
         │                               │
    ┌────▼────┐                  ┌──────▼───────┐
    │  BOT    │                  │  WEB SERVICE │
    │ Polling │                  │  REST API    │
    └────┬────┘                  └──────┬───────┘
         │                              │
         └──────────────┬───────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  CENTRALIZED API (8000)     │
         │  • RBAC Engine              │
         │  • User Management          │
         │  • Group Management         │
         │  • Audit Logging            │
         └──────────┬──────────┬───────┘
                    │          │
              ┌─────▼─┐    ┌───▼──┐
              │MongoDB│    │Redis │
              │27018  │    │Cache │
              └───────┘    └──────┘
```

---

## Environment Variables

```bash
# Bot Token (REQUIRED)
export TELEGRAM_BOT_TOKEN="8366781443:AAHIXgGD1UXvPWw9EIDBlMk5Ktuhj2qQ8WU"

# API Configuration
export CENTRALIZED_API_URL="http://localhost:8000"
export CENTRALIZED_API_KEY="shared-api-key"

# Database
export MONGODB_HOST="localhost"
export MONGODB_PORT="27018"
export MONGODB_DATABASE="telegram_bot"

# Logging
export LOG_LEVEL="INFO"
```

---

## Troubleshooting Checklist

- [ ] MongoDB is running on port 27018
- [ ] Centralized API is responding at http://localhost:8000/api/health
- [ ] Web Service is running at http://localhost:8002
- [ ] Bot has TELEGRAM_BOT_TOKEN set
- [ ] Bot logs show "Bot is polling for updates"
- [ ] All required ports (8000, 8002, 27018) are available
- [ ] Python executable is correct: `/Users/apple/.pyenv/versions/3.10.11/bin/python`

---

## Quick Commands

```bash
# Start all services in background
cd "/Users/apple/Documents/Personal/startup/bots/telegram bot/python/main_bot_v2/v3"
./start_all_services.sh

# Check status
curl http://localhost:8000/api/health
curl http://localhost:8002

# View all logs
tail -f /tmp/{mongod,api,web,bot}.log

# Stop everything
./stop_all_services.sh
```

Good luck! 🚀
