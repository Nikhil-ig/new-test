# 🚀 Bot Manager - Complete Setup Guide

## Phase 1: Backend Setup (if not already done)

### Start MongoDB & Redis

```bash
# Navigate to project root
cd /path/to/main_bot_v2

# Start all services with Docker Compose
docker-compose up -d

# Verify services are running
docker-compose ps
```

You should see:
- ✅ MongoDB on port 27017
- ✅ Redis on port 6379

### Backend is automatically starting:
- 🤖 **Bot Service** (Aiogram) on port 8001
- 💻 **Web Service** (FastAPI) on port 8002
- 🔗 **Centralized API** on port 8000

---

## Phase 2: Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd v3/web/frontend
```

### 2. Install Dependencies

```bash
npm install
```

**This installs:**
- React 18.2.0
- Vite 5.0.0
- TypeScript 5.3
- Tailwind CSS 3.3.5
- React Router 6.20.0
- Axios 1.6.0
- Recharts 2.10.0
- Lucide React 0.292.0

### 3. Start Development Server

```bash
npm run dev
```

**You'll see:**
```
  VITE v5.0.0  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### 4. Open in Browser

Go to: **http://localhost:5173**

---

## Phase 3: Login & Explore

### Option A: Demo Login (Fastest)

1. Click **"Demo Login"** button
2. You'll be logged in with a demo token
3. Redirected to dashboard

### Option B: Real Login

Default credentials:
- **Email**: admin@example.com
- **Password**: password123

(You'll need these set up in your backend API)

---

## 🎯 Explore the Dashboard

### Dashboard (/)
- **Real-time statistics cards** - Users, Groups, Actions count
- **Bar chart** - Users/Groups/Actions visualization
- **Pie chart** - Active vs Inactive groups
- **Recent actions table** - Last 10 moderation actions
- ⚡ Auto-refreshes every 30 seconds

### Users (/users)
- **View all users** in a responsive table
- **Create new users** with validation form
- **Delete users** with confirmation
- **Edit functionality** (scaffolded)
- Color-coded roles (primary/secondary/danger badges)

### Groups (/groups)
- **List all groups** with descriptions
- **Create groups** with name and description
- **Delete groups** with confirmation
- **Member count** display
- **Created date** tracking

### Actions (/actions)
- **Execute moderation actions**:
  - Ban, Kick, Mute, Unmute
  - Promote, Demote, Warn
  - Pin, Unpin messages
- **Specify action details**:
  - Group ID & User ID
  - Reason for action
  - Duration (for timed actions)
- **Track action history** with status badges
- **Recent actions table** (last 10)

---

## 🔐 Authentication Flow

1. **Login Page** (`/login`)
   - Enter credentials or click "Demo Login"
   - Token stored in localStorage

2. **Protected Routes**
   - Automatic redirect to `/login` if no token
   - Token sent in all API requests

3. **Logout**
   - Click logout button in header
   - Token cleared, redirected to login

---

## 📊 API Connections

### All pages automatically connect to:

```
Backend API: http://localhost:8002/api
```

**API Client Methods**:

```typescript
// Dashboard
apiClient.getDashboardStats()

// Users
apiClient.getUsers()
apiClient.createUser(data)
apiClient.deleteUser(id)

// Groups
apiClient.getGroups()
apiClient.createGroup(data)
apiClient.deleteGroup(id)

// Actions
apiClient.executeAction(data)
apiClient.getActions()
```

All methods are fully typed with TypeScript! ✨

---

## 🎨 What You're Getting

### UI Components (src/components/ui.tsx)

```typescript
<Button variant="primary|secondary|danger|success" size="sm|md|lg" />
<Input label="Field" type="text|email|password|textarea" />
<Card>Content</Card>
<Alert type="success|error|warning|info" />
<Badge variant="primary" text="Badge" />
<LoadingSpinner size="sm|md|lg" />
```

### Pages (Pre-built & Fully Functional)

- ✅ **Dashboard** - Analytics with Recharts
- ✅ **Users** - Full CRUD management
- ✅ **Groups** - Full CRUD management
- ✅ **Actions** - Moderation interface
- ✅ **Login** - Authentication
- ✅ **Layout** - Sidebar + Header navigation

---

## 🚀 Development Workflow

### Hot Module Replacement (HMR)
Edit any file and see changes instantly:

```bash
npm run dev
```

Files in `src/` auto-reload in browser < 100ms!

### Type Checking
Ensure no TypeScript errors:

```bash
npm run type-check
```

### Production Build
Optimized build for deployment:

```bash
npm run build
```

Creates `dist/` directory ready to deploy.

---

## 📁 File Structure

```
v3/web/frontend/
├── src/
│   ├── App.tsx               # Routes & app setup
│   ├── main.tsx              # Entry point
│   ├── index.css             # Global styles
│   ├── api/
│   │   └── client.ts         # API client (15+ methods)
│   ├── components/
│   │   ├── ui.tsx            # Reusable components
│   │   └── Layout.tsx        # Sidebar + Header
│   ├── pages/
│   │   ├── Dashboard.tsx     # Analytics
│   │   ├── Users.tsx         # User management
│   │   ├── Groups.tsx        # Group management
│   │   ├── Actions.tsx       # Moderation
│   │   └── Login.tsx         # Authentication
│   └── types/
│       └── index.ts          # TypeScript definitions
├── index.html                # HTML shell
├── package.json              # Dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript config
├── tailwind.config.js        # Tailwind customization
├── postcss.config.cjs        # PostCSS config
└── README.md                 # Full documentation
```

---

## 🔧 Configuration Files

### vite.config.ts
- React plugin enabled
- Proxy: `/api` → `localhost:8002/api`
- Dev server: port 5173
- Fast refresh enabled

### tsconfig.json
- Target: ES2020
- Strict mode enabled
- JSX: react-jsx
- Path mapping: `@/*` imports

### tailwind.config.js
- Custom colors (primary, dark)
- Animation keyframes (fade-in, slide-in)
- Responsive design utilities

### postcss.config.cjs
- Tailwind CSS plugin
- Autoprefixer plugin

---

## ✨ Features Breakdown

### Real-Time Dashboard
- 4 animated statistic cards
- 2 interactive Recharts (bar + pie)
- Recent actions table
- Auto-refresh every 30 seconds
- Loading states & error handling

### User Management
- Fetch all users from API
- Create users with validation
- Delete with confirmation
- Table with columns: username, email, role, created date
- Success/error alerts
- Form toggling

### Group Management
- Fetch all groups from API
- Create groups with name & description
- Delete with confirmation
- Table with columns: name, description, members, created date
- Status badges

### Moderation Actions
- 9 action types (ban, kick, mute, promote, etc.)
- Specify group ID, user ID, reason, duration
- Execute actions via API
- Track action history
- Status badges (completed, pending, failed)
- Recent actions table

### Authentication
- Email/password login
- Token-based (stored in localStorage)
- Demo login for testing
- Protected routes (automatic redirect)
- Logout functionality

---

## 🐛 Common Issues & Solutions

### 1. "Cannot find module 'react'"
```bash
# Solution: Reinstall node_modules
rm -rf node_modules package-lock.json
npm install
```

### 2. Port 5173 already in use
```bash
# Solution: Use different port
npm run dev -- --port 3000
```

### 3. API requests failing (CORS)
```bash
# Solution: Ensure backend is running
docker-compose up -d
# And check proxy in vite.config.ts
```

### 4. TypeScript errors
```bash
# Solution: Type check and fix
npm run type-check
```

---

## 📚 Next Steps

1. **Customize Theme**
   - Edit `tailwind.config.js`
   - Change primary colors
   - Adjust spacing/sizing

2. **Add More Pages**
   - Create in `src/pages/`
   - Add routes in `src/App.tsx`
   - Add nav items in `src/components/Layout.tsx`

3. **Extend API Client**
   - Add methods in `src/api/client.ts`
   - Full TypeScript typing

4. **Deploy**
   ```bash
   npm run build
   # Deploy dist/ folder
   ```

---

## 🎯 Quick Commands Cheat Sheet

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview

# Check for TypeScript errors
npm run type-check

# View all available scripts
npm run
```

---

## 📞 Support

Need help?

1. Check `README.md` in this directory
2. Check `../../docs/` for API documentation
3. Review `../../docs/ARCHITECTURE_VISUAL.md` for system overview
4. Check browser DevTools → Console for errors

---

## ✅ You're All Set! 🎉

```
✅ Backend running (MongoDB, Redis, 3 services)
✅ Frontend ready (React, Vite, Tailwind)
✅ Dashboard with analytics & charts
✅ Full user/group/action management
✅ Beautiful responsive UI
✅ Type-safe TypeScript codebase
✅ Protected authentication
✅ API fully integrated
```

### Start developing:
```bash
npm run dev
```

### Visit dashboard:
```
http://localhost:5173
```

**Happy coding! 🚀**
