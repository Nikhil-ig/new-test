# V3 Microservices - Quick Start Guide

## ✅ What Was Created

All 9 critical files have been created and verified:

```
✅ centralized_api/app.py        (6.0K)  - FastAPI entry point
✅ centralized_api/requirements.txt       - 11 dependencies
✅ centralized_api/Dockerfile             - Container build

✅ bot/main.py                   (12K)   - Aiogram bot
✅ bot/requirements.txt                   - 5 dependencies  
✅ bot/Dockerfile                        - Container build

✅ web/app.py                    (12K)   - FastAPI API
✅ web/requirements.txt                   - 5 dependencies
✅ web/Dockerfile                        - Container build
```

## 🚀 Start Services NOW

### Option 1: Docker Compose (Recommended)

```bash
cd v3
docker-compose up
```

This starts:
- MongoDB (port 27017)
- Redis (port 6379)
- Centralized API (port 8000)
- Telegram Bot (port 8001)
- Web Service (port 8002)

### Option 2: Local Development

**Terminal 1 - Centralized API:**
```bash
cd v3/centralized_api
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

**Terminal 2 - Bot:**
```bash
cd v3/bot
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="your_token_here"
python main.py
```

**Terminal 3 - Web:**
```bash
cd v3/web
pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8002
```

## 🧪 Test Services

```bash
# Test Centralized API
curl http://localhost:8000/
curl http://localhost:8000/api/health

# Test Web Service
curl http://localhost:8002/
curl http://localhost:8002/api/health

# View API documentation
# Visit: http://localhost:8000/docs
# Visit: http://localhost:8002/docs
```

## 📊 Features

### Centralized API (Port 8000)
- ✅ MongoDB async connection
- ✅ Health checks
- ✅ RBAC routes
- ✅ Action execution
- ✅ Error handling

### Bot Service (Port 8001)
- ✅ 7 commands: /start, /help, /status, /ban, /kick, /mute, /unmute
- ✅ HTTP client to centralized_api
- ✅ Aiogram 3.0 async polling
- ✅ Telegram integration

### Web Service (Port 8002)
- ✅ REST API endpoints
- ✅ Users management
- ✅ Groups management
- ✅ Actions execution
- ✅ Dashboard statistics

## 📝 Environment Variables

Create `.env` file in `v3/` directory:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
CENTRALIZED_API_URL=http://localhost:8000
API_KEY=shared-api-key
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret
LOG_LEVEL=INFO
DEBUG=false
```

## 🛑 Stop Services

```bash
# Docker Compose
docker-compose down

# View logs
docker-compose logs -f
docker-compose logs -f centralized-api
docker-compose logs -f bot
docker-compose logs -f web
```

## 📊 Check Status

```bash
docker-compose ps
```

## 🎯 Next Steps

1. ✅ All services are ready to run
2. Set TELEGRAM_BOT_TOKEN in .env
3. Run: `docker-compose up`
4. Visit: http://localhost:8000/docs
5. Test endpoints

## 📚 Documentation

- `README.md` - Architecture overview
- `ARCHITECTURE.md` - Detailed technical design
- `centralized_api/README.md` - API service docs
- `bot/README.md` - Bot service docs
- `web/README.md` - Web service docs

## ✅ Status

**Structure:** ✅ Complete
**Code:** ✅ Complete  
**Docker:** ✅ Ready
**Deployment:** ✅ Ready

Your V3 microservices architecture is production-ready! 🚀

