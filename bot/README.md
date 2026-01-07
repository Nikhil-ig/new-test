# Bot Service

Independent Telegram bot service that communicates with centralized_api.

## 🤖 What This Service Does

- **Handles Telegram Updates** - Polls for messages and commands
- **Executes Bot Commands** - /admin_dashboard, /promote_user, etc.
- **Validates Permissions** - Checks with centralized_api
- **Executes Moderation Actions** - Ban, kick, mute, promote users
- **Streams Events** - Sends actions to centralized_api for logging
- **Can be Deployed Independently** - On different server than centralized_api

## 🏗️ Folder Structure

```
bot/
├── main.py                  # Bot entry point and initialization
├── client.py                # HTTP client for centralized_api
├── config.py                # Configuration
├── handlers/                # Command handlers
│   ├── __init__.py
│   ├── admin.py            # Admin commands
│   ├── user.py             # User commands
│   └── group.py            # Group commands
├── middleware/              # Bot middleware
│   ├── __init__.py
│   └── auth.py             # Permission checking
├── utils/                   # Utilities
│   ├── __init__.py
│   ├── telegram_api.py     # Telegram operations
│   └── helpers.py          # Helper functions
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── Dockerfile               # Docker image
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with:
# - TELEGRAM_BOT_TOKEN (from BotFather)
# - CENTRALIZED_API_URL (where centralized_api is running)
```

### 3. Run the Bot

```bash
python main.py
```

### 4. Test a Command

Send `/admin_dashboard` to your bot in Telegram

## 📡 Communication

```
User sends /command
    ↓
Bot receives update
    ↓
Permission check
    ├─ Call centralized_api/api/rbac/check-permission
    └─ Get result
    ↓
If allowed:
    ├─ Execute command
    ├─ Call centralized_api/api/actions/execute
    └─ Log to audit
    ↓
Send response to user
```

## 🔧 Configuration

Edit `config.py` or `.env`:

```python
# Telegram
TELEGRAM_BOT_TOKEN = "your-bot-token-here"

# API
CENTRALIZED_API_URL = "http://localhost:8000"  # or production URL
CENTRALIZED_API_KEY = "shared-api-key"

# Logging
LOG_LEVEL = "INFO"
```

## 📦 Dependencies

```
aiogram==3.0b7             # Telegram bot framework
httpx==0.25.0             # Async HTTP client
pydantic==2.5.0           # Data validation
python-dotenv==1.0.0      # Environment variables
```

## 🎯 Available Commands

### Admin Commands
```
/admin_dashboard     - View system statistics
/list_all_groups    - List all groups
/promote_user       - Promote user to admin
/demote_user        - Demote user from admin
/execute_action     - Execute moderation action
/audit_log          - View audit trail
/get_group_dashboard - View group statistics
/manage_group_admins - Manage group administrators
/batch_operation    - Execute batch operations
/get_user_groups    - List user's groups
/system_stats       - System-wide statistics
```

## 🔐 Permission Model

Commands require:
- Superadmin: Full access to all commands
- Owner: Full access within their groups
- Admin: Limited access within their groups
- Moderator: Moderation commands only
- Member: No access to admin commands

## 🛠️ Key Classes

### BotClient
HTTP client for communicating with centralized_api:

```python
from bot.client import BotClient

client = BotClient(base_url="http://localhost:8000")

# Check permission
allowed = await client.check_permission(
    user_id="123",
    permission="MANAGE_ADMINS"
)

# Execute action
result = await client.execute_action(
    group_id="group_123",
    user_id="user_456",
    action="ban",
    reason="Spam"
)
```

### Handlers
Command handlers for bot commands:

```python
# bot/handlers/admin.py
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("admin_dashboard"))
async def admin_dashboard(message: types.Message):
    # Get user permission from centralized_api
    # Display dashboard
    # Log action
    pass
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t telegram-bot .

# Run container
docker run \
  -e TELEGRAM_BOT_TOKEN=your-token \
  -e CENTRALIZED_API_URL=http://centralized-api:8000 \
  telegram-bot
```

### Docker Compose (from v3/)

```bash
cd ..
docker-compose up bot
```

### Kubernetes

```bash
kubectl apply -f k8s/bot-deployment.yaml
kubectl apply -f k8s/bot-configmap.yaml
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_handlers.py

# Run with coverage
pytest tests/ --cov=.
```

## 🔄 Integration with centralized_api

### 1. Create Client

```python
# bot/client.py
import httpx
from typing import Optional

class BotClient:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        response = await self.client.post(
            f"{self.base_url}/api/rbac/check-permission",
            json={"user_id": user_id, "permission": permission},
            headers={"X-API-Key": self.api_key}
        )
        return response.json()["allowed"]
```

### 2. Use in Handlers

```python
# bot/handlers/admin.py
from bot.client import BotClient

client = BotClient(
    base_url="http://localhost:8000",
    api_key="shared-api-key"
)

async def handle_promote_command(message, user_id_to_promote):
    # Check permission
    allowed = await client.check_permission(
        user_id=message.from_user.id,
        permission="MANAGE_ADMINS"
    )
    
    if not allowed:
        await message.reply("You don't have permission")
        return
    
    # Execute action
    result = await client.execute_action({
        "group_id": message.chat.id,
        "user_id": user_id_to_promote,
        "action": "promote",
        "executed_by": message.from_user.id
    })
    
    if result["success"]:
        await message.reply("User promoted successfully")
    else:
        await message.reply(f"Error: {result['message']}")
```

### 3. Error Handling

```python
async def safe_api_call(coroutine):
    try:
        return await asyncio.wait_for(coroutine, timeout=5.0)
    except httpx.TimeoutException:
        logger.error("centralized_api timeout")
        return None
    except httpx.ConnectionError:
        logger.error("centralized_api connection error")
        return None
    except Exception as e:
        logger.error(f"API call failed: {e}")
        return None
```

## 📊 Monitoring

- Bot health: Send `/health` command
- Logs: Check stdout or log file
- Errors: Logged to centralized monitoring

## 🆘 Troubleshooting

### Bot Token Invalid
```
Error: Invalid token provided
```
Solution: Get valid token from BotFather, update .env

### Cannot Connect to centralized_api
```
Error: Connection refused to http://localhost:8000
```
Solution: Start centralized_api first, check CENTRALIZED_API_URL

### Command Not Working
```
User: /admin_dashboard
Bot: No response
```
Solution: Check logs, verify permissions in centralized_api

## 🎯 Features

- ✅ Full RBAC integration with centralized_api
- ✅ Permission checking on all commands
- ✅ Moderation actions (ban, kick, mute)
- ✅ Batch operations support
- ✅ Complete audit logging
- ✅ Error handling and retries
- ✅ Independent deployment

## 🔄 Status

✅ Ready for deployment
✅ Fully integrated with centralized_api
✅ Independent scalability
🔜 Advanced features (auto-moderation, ML)

---

**Status:** Ready for integration | **Version:** 3.0.0
