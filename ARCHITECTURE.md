# V3 Microservices Architecture - Detailed Design

## Table of Contents
1. [Overview](#overview)
2. [Service Architecture](#service-architecture)
3. [Communication Protocol](#communication-protocol)
4. [Deployment Models](#deployment-models)
5. [Data Flow](#data-flow)
6. [Security](#security)
7. [Scaling](#scaling)
8. [Development Workflow](#development-workflow)

## Overview

V3 is a **production-grade microservices architecture** designed for:
- Independent deployment of services on different servers
- Horizontal scaling of any component
- Clear separation of concerns
- Fault isolation and resilience
- Easy maintenance and updates

### Key Principles

1. **Decoupling** - Services communicate via HTTP REST API
2. **Independence** - Each service can be deployed separately
3. **Resilience** - Failure in one service doesn't crash others
4. **Scalability** - Each service can be scaled independently
5. **Observability** - Health checks and logs for monitoring

## Service Architecture

### Three Core Services

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│  (Telegram Users, Web Browsers, Mobile Apps, Third-parties)  │
└──────────┬──────────────────────────────┬────────────────────┘
           │                              │
     ┌─────▼────────┐          ┌──────────▼───────┐
     │  BOT SERVICE │          │  WEB SERVICE     │
     │  (Port 8001) │          │  (Port 8002)     │
     │              │          │                  │
     │ - Commands   │          │ - REST API       │
     │ - Handlers   │          │ - Dashboard      │
     │ - Telegram   │          │ - Analytics      │
     └─────┬────────┘          └──────────┬───────┘
           │                              │
           │  HTTP Requests              │
           │  ┌──────────────────────────┘
           │  │
     ┌─────▼──────────────────────────┐
     │  CENTRALIZED API SERVICE       │
     │  (Port 8000)                   │
     │                                │
     │  ✅ RBAC Engine               │
     │  ✅ User Management           │
     │  ✅ Group Management          │
     │  ✅ Audit Logging             │
     │  ✅ Permission Checking       │
     │  ✅ Data Persistence          │
     │  ✅ Business Logic            │
     │                                │
     └─────┬────────────────┬─────────┘
           │                │
     ┌─────▼─────┐    ┌─────▼──────┐
     │ MongoDB   │    │ Redis      │
     │ (Data)    │    │ (Cache)    │
     └───────────┘    └────────────┘
```

### Service Responsibilities

#### Centralized API (Port 8000)
**Purpose:** Core business logic and data management

**Responsibilities:**
- RBAC (Role-Based Access Control)
- User and group management
- Permission checking
- Audit logging
- Moderation actions
- Data persistence to MongoDB
- API endpoints for other services

**Never does:**
- Telegram specific operations (delegated to bot)
- Web UI rendering (delegated to web)
- Client-facing operations

**Database:** MongoDB (single source of truth)

---

#### Bot Service (Port 8001)
**Purpose:** Telegram bot interactions

**Responsibilities:**
- Handle Telegram updates
- Parse bot commands
- Execute permission checks (via centralized_api)
- Send moderation commands to Telegram API
- Stream events to centralized_api for logging
- Provide bot-specific logic

**Never does:**
- Direct database access (goes through centralized_api)
- Store user data (stored in centralized_api)
- Business rule enforcement (delegated to centralized_api)

**Dependencies:**
- centralized_api (for permissions, data, business logic)
- Telegram Bot API (for Telegram operations)

---

#### Web Service (Port 8002)
**Purpose:** Web API and dashboard interface

**Responsibilities:**
- REST API endpoints for web clients
- JWT authentication
- Web dashboard (React/Vue)
- WebSocket for real-time updates
- Analytics and statistics
- User-friendly interface

**Never does:**
- Direct database access (goes through centralized_api)
- Store user data (stored in centralized_api)
- Business rule enforcement (delegated to centralized_api)

**Dependencies:**
- centralized_api (for permissions, data, business logic)
- Frontend assets (HTML, CSS, JS)

## Communication Protocol

### HTTP Communication

All inter-service communication uses **HTTP REST**:

```
Service A              Service B
   │                      │
   ├─── HTTP POST ─────────>
   │   Content-Type: application/json
   │   X-API-Key: shared-api-key
   │   {
   │     "user_id": "123",
   │     "action": "promote"
   │   }
   │                      │
   │   <──── 200 OK ──────┤
   │   Content-Type: application/json
   │   {
   │     "success": true,
   │     "data": {...}
   │   }
   │                      │
```

### Request Headers

All requests include:

```
GET /api/endpoint HTTP/1.1
Host: centralized-api:8000
Content-Type: application/json
X-API-Key: shared-api-key
Authorization: Bearer eyJ... (if needed)
```

### Error Responses

```json
{
  "success": false,
  "error": "permission_denied",
  "message": "User does not have permission for this action",
  "status_code": 403
}
```

## Deployment Models

### Model 1: Single Machine (Development)

```
Single Server:
  ├─ centralized_api (8000)
  ├─ bot (8001)
  ├─ web (8002)
  ├─ MongoDB (27017)
  └─ Redis (6379)

Start: docker-compose up
```

**Pros:**
- Simple setup
- Easy debugging
- Minimal resources

**Cons:**
- No isolation
- Single point of failure
- Can't scale services independently

---

### Model 2: Multi-Server (Production)

```
Server 1 (Core):
  ├─ centralized_api (8000)
  ├─ MongoDB (27017)
  └─ Redis (6379)

Server 2 (Bot):
  └─ bot (8001) → connects to Server 1:8000

Server 3 (Web):
  └─ web (8002) → connects to Server 1:8000

Server 4 (Load Balancer):
  └─ Nginx/HAProxy → routes to servers
```

**Pros:**
- Service isolation
- Independent scaling
- Hardware specialization
- Better resilience

**Cons:**
- Network latency
- More complex setup
- More servers to manage

---

### Model 3: Kubernetes (Enterprise)

```
Kubernetes Cluster:
  ├─ centralized-api-deployment (2-5 replicas)
  ├─ bot-deployment (3-10 replicas)
  ├─ web-deployment (2-5 replicas)
  ├─ mongodb-statefulset
  ├─ redis-deployment
  ├─ ingress-controller
  └─ service-mesh (optional)
```

**Pros:**
- Auto-scaling
- Self-healing
- Rolling updates
- Full automation

**Cons:**
- Complex setup
- Requires expertise
- Higher resource consumption

## Data Flow

### Bot Command Flow

```
1. User sends command
   /admin_dashboard

2. Bot receives update
   - Message from Telegram
   - Contains user_id, command, parameters

3. Bot creates HTTP client
   client = BotClient("http://centralized-api:8000")

4. Bot checks permission
   allowed = await client.check_permission(
       user_id="123",
       permission="ADMIN_DASHBOARD"
   )
   → Call: POST /api/rbac/check-permission
   → Response: {"allowed": true}

5. If allowed, bot fetches data
   stats = await client.get_system_stats()
   → Call: GET /api/rbac/system/stats
   → Response: {"groups": 5, "users": 42, ...}

6. Bot formats response
   message = format_dashboard(stats)

7. Bot sends to Telegram
   await message.reply(message)

8. Centralized API logs action
   - Automatic audit logging
   - Stored in MongoDB
```

### Web Request Flow

```
1. User opens web dashboard
   GET http://web.example.com/dashboard

2. Web service authenticates
   POST /api/auth/login
   {
     "username": "admin",
     "password": "secret"
   }
   → Validate with centralized_api
   → Return JWT token

3. User clicks "View Groups"
   GET /api/groups
   Header: Authorization: Bearer eyJ...

4. Web service validates token
   - Verify JWT signature
   - Extract user_id from token
   - Check if token expired

5. Web service checks permission
   allowed = await client.check_permission(
       user_id="user_from_token",
       permission="VIEW_GROUPS"
   )

6. If allowed, web fetches data
   groups = await client.list_groups()
   → Call: GET /api/groups
   → Response: [{group_data}]

7. Web transforms data
   - Format for frontend
   - Apply pagination
   - Sort and filter

8. Web returns JSON to browser
   {
     "data": [{...groups}],
     "total": 10,
     "page": 1,
     "limit": 20
   }

9. Browser renders UI
   - JavaScript processes JSON
   - React/Vue renders components
   - User sees group list
```

## Security

### Authentication Methods

#### 1. Service-to-Service (API Key)
```
Bot → centralized_api

Headers:
  X-API-Key: shared-api-key
```

#### 2. User Authentication (JWT)
```
User → web service

Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR...
```

#### 3. Telegram Authentication
```
Bot → Telegram API

Headers:
  Authorization: Bearer TELEGRAM_BOT_TOKEN
```

### Permission Checking Flow

```
Request arrives at endpoint
    ↓
Extract user_id from token/request
    ↓
Call centralized_api/api/rbac/check-permission
    ├─ user_id: "123"
    ├─ permission: "MANAGE_GROUPS"
    └─ group_id: "group_456" (optional)
    ↓
centralized_api checks:
    ├─ User exists?
    ├─ User has permission?
    ├─ For group permission, user is member?
    └─ Permission not revoked?
    ↓
Return response:
    ├─ {"allowed": true}  → Proceed with operation
    └─ {"allowed": false} → Return 403 Forbidden
    ↓
Log to audit trail
    ├─ User ID
    ├─ Action
    ├─ Result (allowed/denied)
    └─ Timestamp
```

## Scaling

### Scaling Strategies

#### Horizontal Scaling (Add more instances)

**Bot Service**
```
Current Load: 10,000 messages/sec
Current Capacity: 5,000 messages/sec per instance
Action: Increase from 2 to 4 instances

Result:
  - Load balancer distributes traffic
  - Each instance handles 2,500 messages/sec
  - Total capacity: 10,000 messages/sec
  - Handles peak loads
```

**Web Service**
```
Current Load: 1,000 requests/sec
Current Capacity: 500 requests/sec per instance
Action: Increase from 2 to 6 instances

Result:
  - Nginx load balancer distributes requests
  - Each instance handles ~166 requests/sec
  - Total capacity: 1,000 requests/sec
  - No 502 Bad Gateway errors
```

**Centralized API**
```
Current Load: 15,000 requests/sec
Current Capacity: 5,000 requests/sec per instance
Action: Increase from 3 to 9 instances

Result:
  - Load balancer distributes to all instances
  - Each instance handles 1,666 requests/sec
  - Total capacity: 15,000 requests/sec
  - Database becomes bottleneck (use sharding)
```

#### Vertical Scaling (More powerful servers)

```
Current Server:
  - CPU: 2 cores
  - RAM: 4 GB
  - Network: 100 Mbps

Upgrade to:
  - CPU: 8 cores
  - RAM: 32 GB
  - Network: 1 Gbps

Result:
  - 4x more CPU capacity
  - 8x more memory
  - 10x more network
```

#### Database Scaling

**MongoDB Sharding**
```
Single MongoDB instance
  └─ Handles 10,000 ops/sec
  └─ Storage: 500 GB
  └─ Single point of failure

Sharded MongoDB (3 shards)
  ├─ Shard 1: ops by user_id % 3 == 0
  ├─ Shard 2: ops by user_id % 3 == 1
  └─ Shard 3: ops by user_id % 3 == 2
  
Result:
  - 30,000 ops/sec total
  - 1.5 TB total storage
  - No single point of failure
  - Query router handles distribution
```

## Development Workflow

### Local Development

1. **Start Services**
```bash
cd v3
docker-compose up
```

2. **Make Changes**
```bash
# Edit bot/handlers/admin.py
# Changes auto-reload in container
```

3. **Test Changes**
```bash
curl http://localhost:8000/api/health
curl http://localhost:8002/api/health
```

4. **View Logs**
```bash
docker-compose logs -f bot
docker-compose logs -f web
docker-compose logs -f centralized-api
```

5. **Stop Services**
```bash
docker-compose down
```

### Production Deployment

1. **Build Images**
```bash
docker build -t company/centralized-api:1.0.0 ./centralized_api
docker build -t company/bot:1.0.0 ./bot
docker build -t company/web:1.0.0 ./web
```

2. **Push to Registry**
```bash
docker push company/centralized-api:1.0.0
docker push company/bot:1.0.0
docker push company/web:1.0.0
```

3. **Deploy with Kubernetes**
```bash
kubectl apply -f k8s/centralized-api-deployment.yaml
kubectl apply -f k8s/bot-deployment.yaml
kubectl apply -f k8s/web-deployment.yaml
```

4. **Monitor**
```bash
kubectl logs -f deployment/centralized-api
kubectl logs -f deployment/bot
kubectl logs -f deployment/web
```

### CI/CD Pipeline

```
Developer pushes code
    ↓
GitHub/GitLab webhook triggered
    ↓
CI Pipeline starts:
    1. Run tests
    2. Check code quality
    3. Build Docker images
    4. Push to registry
    ↓
CD Pipeline (if tests pass):
    1. Deploy to staging
    2. Run integration tests
    3. If staging OK → deploy to production
    4. Monitor for errors
    ↓
Rollback if issues detected
```

## Monitoring & Observability

### Health Checks

Each service has a health endpoint:

```
GET /api/health
Response: {
  "status": "healthy",
  "service": "centralized-api",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### Metrics

Services expose Prometheus metrics:

```
GET /metrics

# HELP bot_commands_total Total bot commands executed
# TYPE bot_commands_total counter
bot_commands_total{command="admin_dashboard"} 1523
bot_commands_total{command="promote_user"} 342

# HELP api_request_duration_seconds API request duration
# TYPE api_request_duration_seconds histogram
api_request_duration_seconds_bucket{endpoint="/api/groups",le="0.1"} 542
api_request_duration_seconds_bucket{endpoint="/api/groups",le="0.5"} 1023
```

### Logging

Structured JSON logging:

```json
{
  "timestamp": "2024-01-15T12:34:56.789Z",
  "service": "centralized-api",
  "level": "INFO",
  "event": "permission_check",
  "user_id": "user_123",
  "permission": "MANAGE_ADMINS",
  "result": "allowed",
  "group_id": "group_456",
  "duration_ms": 15
}
```

---

**Version:** 3.0.0 | **Last Updated:** 2024 | **Status:** Architecture Complete
