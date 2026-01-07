# Web Service

Independent web API and dashboard service that communicates with centralized_api.

## 🌐 What This Service Does

- **REST API** - HTTP endpoints for web clients
- **Web Dashboard** (upcoming) - Beautiful admin interface
- **Real-time Updates** - WebSocket support for live data
- **Admin Panel** - Manage groups, users, permissions
- **Statistics & Analytics** - Group and system-wide stats
- **Can be Deployed Independently** - On different server than centralized_api

## 🏗️ Folder Structure

```
web/
├── app.py                   # FastAPI application setup
├── client.py                # HTTP client for centralized_api
├── config.py                # Configuration
├── endpoints/               # API endpoints
│   ├── __init__.py
│   ├── rbac.py             # RBAC endpoints
│   ├── groups.py           # Group endpoints
│   ├── users.py            # User endpoints
│   └── analytics.py        # Analytics endpoints
├── middleware/              # Middleware
│   ├── __init__.py
│   └── auth.py             # JWT authentication
├── dashboard/               # Web dashboard (upcoming)
│   ├── __init__.py
│   ├── static/             # CSS, JS, images
│   ├── templates/          # HTML templates
│   └── components/         # Reusable UI components
├── utils/                   # Utilities
│   ├── __init__.py
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
# - CENTRALIZED_API_URL (where centralized_api is running)
# - JWT_SECRET (for web authentication)
```

### 3. Run the Service

```bash
python app.py
```

Or with uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

### 4. Test

```bash
curl http://localhost:8002/api/health
```

## 📡 API Endpoints

### Health & Status
- `GET /api/health` - Service health
- `GET /api/status` - Service status

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout
- `POST /api/auth/refresh` - Refresh JWT token

### Groups
- `GET /api/groups` - List all groups (with pagination)
- `GET /api/groups/{group_id}` - Get group details
- `POST /api/groups` - Create group
- `PUT /api/groups/{group_id}` - Update group
- `DELETE /api/groups/{group_id}` - Delete group
- `GET /api/groups/{group_id}/members` - List members
- `POST /api/groups/{group_id}/members/{user_id}` - Add member
- `DELETE /api/groups/{group_id}/members/{user_id}` - Remove member
- `POST /api/groups/{group_id}/actions` - Execute action on group

### Users
- `GET /api/users` - List users
- `GET /api/users/{user_id}` - Get user details
- `POST /api/users` - Create user
- `PUT /api/users/{user_id}` - Update user
- `DELETE /api/users/{user_id}` - Delete user
- `GET /api/users/{user_id}/groups` - User's groups
- `POST /api/users/{user_id}/role` - Change user role

### RBAC
- `GET /api/rbac/permissions` - List all permissions
- `GET /api/rbac/roles` - List all roles
- `GET /api/rbac/user/{user_id}/permissions` - User's permissions

### Analytics
- `GET /api/analytics/system` - System-wide stats
- `GET /api/analytics/groups/{group_id}` - Group statistics
- `GET /api/analytics/users/{user_id}` - User statistics
- `GET /api/analytics/audit` - Audit log analytics

### WebSocket (Real-time)
- `WS /ws/groups/{group_id}` - Real-time group updates
- `WS /ws/dashboard` - Real-time dashboard updates
- `WS /ws/audit` - Real-time audit log stream

## 🔧 Configuration

Edit `config.py` or `.env`:

```python
# API
CENTRALIZED_API_URL = "http://localhost:8000"
CENTRALIZED_API_KEY = "shared-api-key"

# JWT
JWT_SECRET = "your-secret-key-here"
JWT_EXPIRATION = 3600

# Web
DEBUG = False
CORS_ORIGINS = ["http://localhost:3000", "https://yourdomain.com"]
```

## 📦 Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
httpx==0.25.0            # Async HTTP client
python-jose==3.3.0       # JWT tokens
python-dotenv==1.0.0     # Environment variables
```

## 🌟 Key Features

### 1. REST API
- Full REST API with pagination
- JSON request/response
- Proper HTTP status codes
- Comprehensive error messages

### 2. JWT Authentication
- Login with credentials
- Token-based authentication
- Automatic token refresh
- Secure session management

### 3. Real-time Updates (WebSocket)
- Live group updates
- Real-time audit log
- Dashboard refresh
- Event notifications

### 4. Dashboard (Upcoming)
- Beautiful admin interface
- Group management
- User management
- Statistics and analytics
- Real-time updates

## 🔐 Security

### Authentication Flow
```
User Login
    ↓
Web API receives credentials
    ↓
Validate with centralized_api
    ↓
Generate JWT token
    ↓
Return token to client
    ↓
Client uses token in Authorization header for subsequent requests
```

### Permission Checking
```
Authenticated Request
    ↓
Extract user_id from JWT
    ↓
Call centralized_api/api/rbac/check-permission
    ↓
If allowed: Execute endpoint
If denied: Return 403 Forbidden
```

## 🛠️ Key Classes

### WebClient
HTTP client for communicating with centralized_api:

```python
from web.client import WebClient

client = WebClient(base_url="http://localhost:8000")

# Get group details
group = await client.get_group("group_123")

# List all groups
groups = await client.list_groups(limit=10, offset=0)

# Execute action
result = await client.execute_action({
    "group_id": "group_123",
    "action": "ban",
    "user_id": "user_456",
    "reason": "Spam"
})
```

### Endpoints
API endpoint definitions:

```python
# web/endpoints/groups.py
from fastapi import APIRouter, Depends, HTTPException
from web.middleware.auth import get_current_user
from web.client import WebClient

router = APIRouter(prefix="/api/groups", tags=["groups"])

@router.get("/")
async def list_groups(
    current_user = Depends(get_current_user),
    client: WebClient = Depends()
):
    # Check permission
    if not await client.check_permission(
        current_user.id,
        "VIEW_GROUPS"
    ):
        raise HTTPException(status_code=403)
    
    # Get groups from centralized_api
    return await client.list_groups()
```

## 📊 Example Response

### Get Groups

```bash
curl http://localhost:8002/api/groups \
  -H "Authorization: Bearer eyJ..."
```

Response:
```json
{
  "data": [
    {
      "id": "group_123",
      "name": "Support Team",
      "telegram_id": -1001234567890,
      "owner_id": "user_123",
      "member_count": 42,
      "admin_count": 3,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

## 🎯 Communication Flow

```
Browser/Client
    ↓
HTTP Request to Web API (port 8002)
    ↓
Web Service
    ├─ Authenticate (JWT)
    ├─ Check permission (centralized_api)
    ├─ Fetch data (centralized_api)
    └─ Transform response
    ↓
HTTP Response (JSON)
```

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t web-service .

# Run container
docker run -p 8002:8002 \
  -e CENTRALIZED_API_URL=http://centralized-api:8000 \
  -e JWT_SECRET=your-secret-key \
  web-service
```

### Docker Compose (from v3/)

```bash
cd ..
docker-compose up web
```

### Kubernetes

```bash
kubectl apply -f k8s/web-deployment.yaml
kubectl apply -f k8s/web-service.yaml
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_endpoints.py

# Run with coverage
pytest tests/ --cov=.
```

## 🎨 Dashboard (Future)

The dashboard will include:

### Sections
- **Dashboard** - System overview, statistics
- **Groups** - View, create, edit, delete groups
- **Users** - Manage users and roles
- **Members** - Manage group members
- **Audit Log** - View all operations
- **Analytics** - Charts and statistics
- **Settings** - System configuration

### Technologies
- React/Vue.js - Frontend framework
- TypeScript - Type-safe JavaScript
- Tailwind CSS - Styling
- Chart.js - Analytics graphs
- Socket.io - Real-time updates

### Features
- Real-time data updates
- Role-based UI (different views for different roles)
- Search and filtering
- Pagination
- Export capabilities
- Mobile-responsive design

## 🔄 Integration with centralized_api

### 1. Create Client

```python
# web/client.py
import httpx

class WebClient:
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

### 2. Use in Endpoints

```python
# web/endpoints/groups.py
@router.get("/{group_id}")
async def get_group(
    group_id: str,
    current_user = Depends(get_current_user),
    client: WebClient = Depends()
):
    # Check permission
    allowed = await client.check_permission(
        current_user.id,
        "VIEW_GROUPS"
    )
    
    if not allowed:
        raise HTTPException(status_code=403)
    
    # Get group from centralized_api
    group = await client.get_group(group_id)
    
    if not group:
        raise HTTPException(status_code=404)
    
    return group
```

## 📈 Monitoring

- Health check: `GET /api/health`
- Metrics: `GET /metrics` (Prometheus format)
- Logs: Check stdout or log file

## 🆘 Troubleshooting

### Cannot Connect to centralized_api
```
Error: Connection refused to http://localhost:8000
```
Solution: Start centralized_api first, check CENTRALIZED_API_URL

### JWT Token Invalid
```
Error: Invalid token
```
Solution: Re-login to get new token

### Permission Denied
```
Error: 403 Forbidden
```
Solution: Check user permissions in centralized_api

## 🎯 Status

✅ REST API ready
✅ Authentication system ready
✅ centralized_api integration ready
🔜 WebSocket support
🔜 Beautiful dashboard
🔜 Analytics graphs
🔜 Mobile app

---

**Status:** Ready for development | **Version:** 3.0.0
