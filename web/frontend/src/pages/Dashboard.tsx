import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Users, BarChart3, Activity, TrendingUp } from 'lucide-react'
import { Card, LoadingSpinner } from '../components/ui'
import { apiClient } from '../api/client'
import type { DashboardStats } from '../types'

const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export function Dashboard() {
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchStats = async () => {
            try {
                setLoading(true)
                const data = await apiClient.getDashboardStats()
                setStats(data)
                setError(null)
            } catch (err) {
                setError('Failed to load dashboard statistics')
                console.error(err)
            } finally {
                setLoading(false)
            }
        }

        fetchStats()
        const interval = setInterval(fetchStats, 30000) // Refresh every 30 seconds

        return () => clearInterval(interval)
    }, [])

    if (loading) {
        return (
            <div className="flex justify-center items-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        )
    }

    if (error || !stats) {
        return (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded text-red-900">
                {error || 'No data available'}
            </div>
        )
    }

    const chartData = [
        { name: 'Users', value: stats.users_count },
        { name: 'Groups', value: stats.groups_count },
        { name: 'Actions', value: stats.total_actions || 0 },
    ]

    const pieData = [
        { name: 'Active', value: stats.active_groups || 0 },
        { name: 'Inactive', value: Math.max(0, (stats.groups_count || 0) - (stats.active_groups || 0)) },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
                <p className="text-dark-400">Real-time system overview and analytics</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="border-l-4 border-primary-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-dark-300 text-sm font-semibold">Total Users</p>
                            <p className="text-3xl font-bold text-white mt-2">{stats.users_count}</p>
                        </div>
                        <Users className="w-12 h-12 text-primary-500 opacity-20" />
                    </div>
                </Card>

                <Card className="border-l-4 border-green-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-dark-300 text-sm font-semibold">Total Groups</p>
                            <p className="text-3xl font-bold text-white mt-2">{stats.groups_count}</p>
                        </div>
                        <BarChart3 className="w-12 h-12 text-green-500 opacity-20" />
                    </div>
                </Card>

                <Card className="border-l-4 border-blue-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-dark-300 text-sm font-semibold">Active Groups</p>
                            <p className="text-3xl font-bold text-white mt-2">{stats.active_groups || 0}</p>
                        </div>
                        <Activity className="w-12 h-12 text-blue-500 opacity-20" />
                    </div>
                </Card>

                <Card className="border-l-4 border-purple-500">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-dark-300 text-sm font-semibold">Total Actions</p>
                            <p className="text-3xl font-bold text-white mt-2">{stats.total_actions || 0}</p>
                        </div>
                        <TrendingUp className="w-12 h-12 text-purple-500 opacity-20" />
                    </div>
                </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <Card className="lg:col-span-2">
                    <h2 className="text-xl font-bold text-white mb-4">System Overview</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="name" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#f3f4f6' }} />
                            <Bar dataKey="value" fill="#0ea5e9" radius={[8, 8, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>

                <Card>
                    <h2 className="text-xl font-bold text-white mb-4">Group Status</h2>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie data={pieData} cx="50%" cy="50%" labelLine={false} label={({ name, value }) => `${name}: ${value}`} outerRadius={80} fill="#8884d8" dataKey="value">
                                {COLORS.map((color, index) => (
                                    <Cell key={`cell-${index}`} fill={color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </Card>
            </div>

            {/* Recent Actions */}
            {stats.recent_actions && stats.recent_actions.length > 0 && (
                <Card>
                    <h2 className="text-xl font-bold text-white mb-4">Recent Actions</h2>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-dark-700">
                                    <th className="text-left py-2 px-4 font-semibold text-dark-200">Type</th>
                                    <th className="text-left py-2 px-4 font-semibold text-dark-200">User ID</th>
                                    <th className="text-left py-2 px-4 font-semibold text-dark-200">Group ID</th>
                                    <th className="text-left py-2 px-4 font-semibold text-dark-200">Status</th>
                                    <th className="text-left py-2 px-4 font-semibold text-dark-200">Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {stats.recent_actions.slice(0, 5).map((action, idx) => (
                                    <tr key={idx} className="border-b border-dark-700 hover:bg-dark-700 transition">
                                        <td className="py-3 px-4 text-dark-100 font-semibold">{action.action_type}</td>
                                        <td className="py-3 px-4 text-dark-300">{action.user_id}</td>
                                        <td className="py-3 px-4 text-dark-300">{action.group_id}</td>
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-1 rounded text-sm font-semibold ${action.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                                {action.status || 'pending'}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-dark-300 text-sm">{action.timestamp ? new Date(action.timestamp).toLocaleString() : 'N/A'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </Card>
            )}
        </div>
    )
}
