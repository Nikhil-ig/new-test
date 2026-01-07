import { ReactNode, useState } from 'react'
import { Menu, X, LogOut, BarChart3, Users, Zap, Settings } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from './ui'

interface LayoutProps {
    children: ReactNode
}

export function Layout({ children }: LayoutProps) {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const navigate = useNavigate()
    const location = useLocation()

    const navItems = [
        { path: '/', label: 'Dashboard', icon: BarChart3 },
        { path: '/users', label: 'Users', icon: Users },
        { path: '/groups', label: 'Groups', icon: Zap },
        { path: '/actions', label: 'Actions', icon: Settings },
    ]

    const handleLogout = () => {
        localStorage.removeItem('token')
        navigate('/login')
    }

    const isActive = (path: string) => location.pathname === path

    return (
        <div className="min-h-screen bg-dark-900">
            {/* Header */}
            <header className="bg-dark-800 border-b border-dark-700 sticky top-0 z-40">
                <div className="flex items-center justify-between h-16 px-4">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setSidebarOpen(!sidebarOpen)}
                            className="lg:hidden p-2 hover:bg-dark-700 rounded-lg transition"
                        >
                            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                                <BarChart3 className="w-5 h-5 text-white" />
                            </div>
                            <h1 className="text-xl font-bold text-white hidden sm:block">Bot Manager</h1>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-dark-400 text-sm hidden sm:inline">Admin Dashboard</span>
                        <Button onClick={handleLogout} variant="danger" size="sm">
                            <LogOut className="w-4 h-4 mr-1" /> Logout
                        </Button>
                    </div>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <aside
                    className={`fixed lg:relative w-64 h-[calc(100vh-64px)] bg-dark-800 border-r border-dark-700 transform transition lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                        } z-30 overflow-y-auto`}
                >
                    <nav className="p-4 space-y-2">
                        {navItems.map((item) => {
                            const Icon = item.icon
                            const active = isActive(item.path)
                            return (
                                <button
                                    key={item.path}
                                    onClick={() => {
                                        navigate(item.path)
                                        setSidebarOpen(false)
                                    }}
                                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition ${active
                                            ? 'bg-primary-600 text-white font-semibold'
                                            : 'text-dark-300 hover:bg-dark-700'
                                        }`}
                                >
                                    <Icon className="w-5 h-5" />
                                    <span>{item.label}</span>
                                </button>
                            )
                        })}
                    </nav>

                    <div className="absolute bottom-4 left-4 right-4 p-4 bg-primary-900/30 border border-primary-700 rounded-lg">
                        <p className="text-xs text-dark-400 mb-3 font-semibold uppercase tracking-wide">System Info</p>
                        <div className="space-y-2 text-xs text-dark-300">
                            <div>
                                <span className="text-dark-400">Status:</span>
                                <span className="ml-2 text-green-400 font-semibold">Online</span>
                            </div>
                            <div>
                                <span className="text-dark-400">Version:</span>
                                <span className="ml-2">v1.0.0</span>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 w-full lg:w-auto">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                        {children}
                    </div>
                </main>
            </div>

            {/* Mobile Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 lg:hidden z-20"
                    onClick={() => setSidebarOpen(false)}
                ></div>
            )}
        </div>
    )
}
