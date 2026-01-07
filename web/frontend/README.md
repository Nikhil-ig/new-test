# Bot Manager - React/Vite Frontend

Beautiful, advanced, and responsive admin dashboard built with **React 18**, **Vite 5**, **TypeScript**, and **Tailwind CSS**.

## 🎨 Features

✨ **Modern UI Components**
- Beautiful button variations (primary, secondary, danger, success)
- Input fields with validation and error states
- Cards, alerts, badges, loading spinners
- All built with Tailwind CSS utility classes

📊 **Advanced Dashboard**
- Real-time statistics with animated cards
- Recharts integration for beautiful visualizations
- Bar charts and pie charts
- Auto-refresh every 30 seconds
- Recent actions history table

👥 **User Management**
- View all users in a responsive table
- Create new users with form validation
- Delete users with confirmation
- Edit functionality (scaffolded)
- Success/error alerts

👫 **Group Management**
- List all Telegram groups
- Create new groups
- Delete groups
- Member count display
- Descriptions and metadata

⚡ **Moderation Actions**
- Execute moderation actions (ban, kick, mute, promote, demote, warn, pin, unpin)
- Track action history
- Reason and duration tracking
- Real-time status updates
- Action type badges with color coding

🔐 **Authentication**
- Login page with email/password
- Token-based authentication (JWT)
- Protected routes with automatic redirect
- Demo login for testing
- Logout functionality

🚀 **Performance**
- Vite for lightning-fast development (< 100ms HMR)
- Code splitting for optimal bundle size
- Optimized production build
- TypeScript strict mode for type safety

🎯 **API Integration**
- Axios-based API client with interceptors
- Automatic token refresh
- Centralized error handling
- Full TypeScript typing for all API responses
- Proxy setup for development

## 🛠️ Tech Stack

- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.0
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.3.5
- **Routing**: React Router DOM 6.20.0
- **HTTP Client**: Axios 1.6.0
- **Charts**: Recharts 2.10.0
- **Icons**: Lucide React 0.292.0

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm/yarn

### Setup

```bash
# Navigate to frontend directory
cd v3/web/frontend

# Install dependencies
npm install

# Create .env file (optional, uses localhost:8002 by default)
cp .env.example .env

# Start development server
npm run dev
```

The frontend will be available at **http://localhost:5173**

## 🚀 Available Scripts

```bash
# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Type check TypeScript files
npm run type-check

# Lint code (with ESLint - optional)
npm run lint
```

## 🔗 API Integration

The frontend connects to the backend API at `http://localhost:8002/api`:

### Available Endpoints (via API Client)

**Dashboard**
- `GET /api/stats/dashboard` - Get dashboard statistics
- `GET /api/health` - Health check

**Users**
- `GET /api/users` - List all users
- `GET /api/users/{id}` - Get user by ID
- `POST /api/users` - Create new user
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Delete user

**Groups**
- `GET /api/groups` - List all groups
- `GET /api/groups/{id}` - Get group by ID
- `POST /api/groups` - Create new group
- `PUT /api/groups/{id}` - Update group
- `DELETE /api/groups/{id}` - Delete group

**Actions**
- `POST /api/actions/execute` - Execute moderation action
- `GET /api/actions` - Get action history

**Authentication**
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/logout` - Logout

## 🎯 Project Structure

```
src/
├── App.tsx                 # Main app with routes
├── main.tsx                # Entry point
├── index.css               # Global styles with Tailwind
├── api/
│   └── client.ts          # Axios API client (15+ methods)
├── components/
│   ├── ui.tsx             # Reusable UI library
│   │   └── Button, Input, Card, Alert, Badge, LoadingSpinner
│   └── Layout.tsx         # Main layout with sidebar/header
├── pages/
│   ├── Dashboard.tsx      # Analytics dashboard with charts
│   ├── Users.tsx          # User management CRUD
│   ├── Groups.tsx         # Group management CRUD
│   ├── Actions.tsx        # Moderation actions interface
│   └── Login.tsx          # Authentication page
└── types/
    └── index.ts           # TypeScript type definitions
```

## 🔐 Default Credentials

For demo login:
- **Email**: admin@example.com
- **Password**: password123

Or use the "Demo Login" button on the login page.

## 🌐 Environment Variables

Create `.env.local` file for custom configuration:

```env
VITE_API_URL=http://localhost:8002/api
VITE_APP_NAME=Bot Manager
```

Default values are already set in the code if not provided.

## 📱 Responsive Design

- ✅ Mobile-first approach
- ✅ Responsive tables with horizontal scroll
- ✅ Mobile sidebar navigation menu
- ✅ Adaptive layouts for all screen sizes
- ✅ Optimized for mobile, tablet, and desktop

## 🎨 Styling

All styling uses **Tailwind CSS** with:
- Custom color palette (primary blue, dark grays)
- Responsive utility classes
- Smooth transitions and animations
- Custom animations (fade-in, slide-in)
- No separate CSS files - everything inline

## 🔧 Customization

### Change Theme Colors

Edit `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        50: '#f0f9ff',
        600: '#0b63f8',  // Change these
        700: '#0951d8',
      },
    },
  },
}
```

### Add New Pages

1. Create component in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout.tsx`

### Add New API Methods

Edit `src/api/client.ts`:

```typescript
async newMethod(data: any) {
  const response = await this.instance.get('/endpoint', { data })
  return response.data
}
```

## 🐛 Troubleshooting

### Dependencies Not Installing
```bash
rm -rf node_modules package-lock.json
npm install
```

### Port 5173 Already in Use
```bash
npm run dev -- --port 3000
```

### TypeScript Errors After npm install
```bash
npm run type-check
```

### API Connection Issues
1. Ensure backend is running on port 8002
2. Check proxy settings in `vite.config.ts`
3. Verify token in browser DevTools → Storage → localStorage

## 📚 Documentation

See parent project documentation:
- `../../../docs/API_REFERENCE_FULL.md` - Complete API documentation
- `../../../docs/ARCHITECTURE_VISUAL.md` - System architecture
- `../../README.md` - Backend setup and configuration

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

Creates optimized build in `dist/` directory.

### Deploy to Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Deploy to Docker

```bash
docker build -t bot-manager-frontend .
docker run -p 3000:80 bot-manager-frontend
```

See `Dockerfile` in this directory.

## 📄 License

MIT

## 👨‍💻 Support

For issues or feature requests, contact the development team.

---

**Ready to run?**

```bash
npm install && npm run dev
```

Visit http://localhost:5173 and start managing your bot! 🚀
