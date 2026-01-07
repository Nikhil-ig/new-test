import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState, Suspense } from 'react'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Users } from './pages/Users'
import { Groups } from './pages/Groups'
import { Actions } from './pages/Actions'
import { Login } from './pages/Login'

console.log('App.tsx loaded')

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const [isAuth, setIsAuth] = useState<boolean | null>(null)

  useEffect(() => {
    try {
      const token = localStorage.getItem('token')
      setIsAuth(!!token)
      console.log('Auth state:', !!token)
    } catch (err) {
      console.error('Error checking auth:', err)
      setIsAuth(false)
    }
  }, [])

  if (isAuth === null) {
    return <div style={{ backgroundColor: '#111827', color: '#f3f4f6', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>
  }

  if (!isAuth) {
    return <Navigate to="/login" replace />
  }

  return <Layout>{children as any}</Layout>
}

export function App() {
  console.log('App rendering')
  return (
    <Suspense fallback={<div style={{ backgroundColor: '#111827', color: '#f3f4f6', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <Users />
              </ProtectedRoute>
            }
          />
          <Route
            path="/groups"
            element={
              <ProtectedRoute>
                <Groups />
              </ProtectedRoute>
            }
          />
          <Route
            path="/actions"
            element={
              <ProtectedRoute>
                <Actions />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </Suspense>
  )
}
