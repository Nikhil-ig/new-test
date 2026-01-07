# Centralized API Service

Core backend providing shared business logic, database access, and utilities for all other services.

## 📋 What This Service Provides

- **RBAC Management** - Role-based access control
- **User Management** - User creation, roles, permissions
- **Group Management** - Group creation, member management
- **Audit Logging** - Track all operations
- **Permission Checking** - Validate user permissions
- **Moderation Actions** - Execute bans, kicks, mutes, etc.
- **Database Access** - MongoDB operations
- **Shared Models** - Pydantic models for data validation

## 🏗️ Folder Structure

```
centralized_api/
├── app.py                   # FastAPI application setup
├── config.py                # Configuration (MongoDB URL, secrets, etc.)
├── models/                  # Pydantic data models
│   ├── __init__.py
│   ├── rbac.py             # RBAC models
│   ├── user.py             # User models
│   ├── group.py            # Group models
│   └── audit.py            # Audit log models
├── services/                # Business logic
│   ├── __init__.py
│   ├── rbac_service.py     # RBAC operations
│   ├── user_service.py     # User management
│   ├── group_service.py    # Group management
│   └── audit_service.py    # Audit logging
├── api/                     # API endpoints
│   ├── __init__.py
│   ├── rbac.py             # RBAC endpoints
│   ├── users.py            # User endpoints
│   ├── groups.py           # Group endpoints
│   └── audit.py            # Audit endpoints
├── db/                      # Database layer
│   ├── __init__.py
│   ├── mongodb.py          # MongoDB connection
│   └── migrations.py       # Database migrations
├── middleware/              # Middleware
│   ├── __init__.py
│   └── auth.py             # Authentication middleware
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
# Edit .env with your MongoDB URL and secrets
```

### 3. Run the Service

```bash
python app.py
```

Or with uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Test

```bash
curl http://localhost:8000/api/health
```

## 📡 API Endpoints

### Health Check
- `GET /api/health` - Service health

### RBAC
- `GET /api/rbac/permissions` - List all permissions
- `GET /api/rbac/roles` - List all roles
- `POST /api/rbac/check-permission` - Check user permission
- `GET /api/rbac/user/{user_id}/permissions` - User permissions

### Users
- `POST /api/users/` - Create user
- `GET /api/users/{user_id}` - Get user details
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user
- `POST /api/users/{user_id}/role` - Change user role

### Groups
- `POST /api/groups/` - Create group
- `GET /api/groups/` - List groups
- `GET /api/groups/{group_id}` - Get group details
- `PUT /api/groups/{group_id}` - Update group
- `DELETE /api/groups/{group_id}` - Delete group
- `POST /api/groups/{group_id}/members` - Add member
- `DELETE /api/groups/{group_id}/members/{user_id}` - Remove member

### Audit
- `GET /api/audit/logs` - Get audit logs
- `GET /api/audit/logs/user/{user_id}` - User's audit logs
- `GET /api/audit/logs/group/{group_id}` - Group's audit logs

## 🔧 Configuration

Edit `config.py` or `.env`:

```python
# Database
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "bot_rbac"

# Security
SECRET_KEY = "your-secret-key-here"
JWT_EXPIRATION = 3600  # seconds

# Services
DEBUG = False
LOG_LEVEL = "INFO"
```

## 📦 Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
motor==3.3.1            # Async MongoDB
python-jose==3.3.0      # JWT tokens
passlib==1.7.4          # Password hashing
python-dotenv==1.0.0    # Environment variables
```

## 🔐 Security

### Authentication
- JWT tokens for API access
- API keys for service-to-service communication
- Role-based access control (RBAC)

### Authorization
- Permission checking on all endpoints
- Group isolation (users can't access other groups)
- Audit logging of all operations

## 📡 Integration

### With Bot Service

```python
# bot/client.py
import httpx

class CentralizedAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        response = await self.client.post(
            f"{self.base_url}/api/rbac/check-permission",
            json={"user_id": user_id, "permission": permission}
        )
        return response.json()["allowed"]
    
    async def execute_action(self, action_data: dict) -> dict:
        response = await self.client.post(
            f"{self.base_url}/api/actions/execute",
            json=action_data
        )
        return response.json()
```

### With Web Service

Same as bot - use the CentralizedAPIClient to make HTTP calls.

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_rbac.py

# Run with coverage
pytest tests/ --cov=.
```

## 📊 Data Models

### Role
```python
class Role(str, Enum):
    SUPERADMIN = "superadmin"
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"
```

### Permission
```python
class Permission(str, Enum):
    # Global permissions
    MANAGE_USERS = "manage_users"
    MANAGE_GROUPS = "manage_groups"
    VIEW_AUDIT = "view_audit"
    
    # Group permissions
    MANAGE_GROUP_ADMINS = "manage_group_admins"
    MANAGE_GROUP_MEMBERS = "manage_group_members"
    EXECUTE_MODERATION = "execute_moderation"
    # ... more
```

### User
```python
class User(BaseModel):
    id: str
    username: str
    telegram_id: int
    role: Role
    groups: List[str]
    created_at: datetime
    updated_at: datetime
```

### Group
```python
class Group(BaseModel):
    id: str
    name: str
    telegram_id: int
    owner_id: str
    members: List[str]
    admins: List[str]
    settings: dict
    created_at: datetime
    updated_at: datetime
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t centralized-api .

# Run container
docker run -p 8000:8000 \
  -e MONGODB_URL=mongodb://mongo:27017 \
  -e SECRET_KEY=your-secret-key \
  centralized-api
```

### Docker Compose (from v3/)

```bash
cd ..
docker-compose up centralized-api
```

### Kubernetes

```bash
kubectl apply -f k8s/centralized-api-deployment.yaml
kubectl apply -f k8s/centralized-api-service.yaml
```

## 📈 Monitoring

- Health check: `GET /api/health`
- Metrics: `GET /metrics` (Prometheus format)
- Logs: Check stdout/stderr or log file

## 🔄 Integration Checklist

When integrating bot or web services:

- [ ] Configure `CENTRALIZED_API_URL` environment variable
- [ ] Install `httpx` for async HTTP calls
- [ ] Create API client in service
- [ ] Test health endpoint first
- [ ] Test permission checking
- [ ] Test action execution
- [ ] Set up error handling and retries

## 🆘 Troubleshooting

### MongoDB Connection Error
```
Error: connect ECONNREFUSED 127.0.0.1:27017
```
Solution: Start MongoDB or update `MONGODB_URL`

### Port Already in Use
```
Error: Address already in use
```
Solution: Change port in config or kill existing process

### Import Errors
```
Error: ModuleNotFoundError: No module named 'fastapi'
```
Solution: Run `pip install -r requirements.txt`

---

**Status:** Ready for integration | **Version:** 3.0.0
