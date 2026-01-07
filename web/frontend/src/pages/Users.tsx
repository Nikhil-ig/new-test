import { useEffect, useState } from 'react'
import { Trash2, Plus, Edit2 } from 'lucide-react'
import { Card, Button, Input, LoadingSpinner, Alert } from '../components/ui'
import { apiClient } from '../api/client'
import type { User } from '../types'

export function Users() {
    const [users, setUsers] = useState<User[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [success, setSuccess] = useState<string | null>(null)
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({ username: '', email: '', role: '' })

    useEffect(() => {
        fetchUsers()
    }, [])

    const fetchUsers = async () => {
        try {
            setLoading(true)
            const data = await apiClient.getUsers()
            setUsers(data)
            setError(null)
        } catch (err) {
            setError('Failed to load users')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleCreate = async () => {
        try {
            if (!formData.username || !formData.email) {
                setError('Please fill in all fields')
                return
            }
            await apiClient.createUser(formData)
            setSuccess('User created successfully')
            setFormData({ username: '', email: '', role: '' })
            setShowForm(false)
            fetchUsers()
        } catch (err) {
            setError('Failed to create user')
            console.error(err)
        }
    }

    const handleDelete = async (id: number) => {
        if (!window.confirm('Are you sure?')) return
        try {
            await apiClient.deleteUser(id)
            setSuccess('User deleted successfully')
            fetchUsers()
        } catch (err) {
            setError('Failed to delete user')
            console.error(err)
        }
    }

    if (loading) {
        return (
            <div className="flex justify-center items-center h-96">
                <LoadingSpinner size="lg" />
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold text-white">Users</h1>
                    <p className="text-dark-400 mt-1">Manage system users and permissions</p>
                </div>
                <Button onClick={() => setShowForm(!showForm)} variant="primary" size="lg">
                    <Plus className="inline mr-2 w-5 h-5" /> Add User
                </Button>
            </div>

            {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
            {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

            {showForm && (
                <Card className="bg-dark-700 border border-dark-600">
                    <h2 className="text-xl font-bold text-white mb-4">Create New User</h2>
                    <div className="space-y-4">
                        <Input label="Username" value={formData.username} onChange={(v) => setFormData({ ...formData, username: String(v) })} placeholder="john_doe" />
                        <Input label="Email" type="email" value={formData.email} onChange={(v) => setFormData({ ...formData, email: String(v) })} placeholder="john@example.com" />
                        <Input label="Role" value={formData.role} onChange={(v) => setFormData({ ...formData, role: String(v) })} placeholder="admin" />
                        <div className="flex gap-2">
                            <Button onClick={handleCreate} variant="success">Create</Button>
                            <Button onClick={() => setShowForm(false)} variant="secondary">Cancel</Button>
                        </div>
                    </div>
                </Card>
            )}

            <Card>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-dark-700">
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Username</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Email</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Role</th>
                                <th className="text-left py-3 px-4 font-semibold text-dark-200">Created</th>
                                <th className="text-center py-3 px-4 font-semibold text-dark-200">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user) => (
                                <tr key={user.id} className="border-b border-dark-700 hover:bg-dark-700 transition">
                                    <td className="py-3 px-4 font-semibold text-dark-100">{user.username}</td>
                                    <td className="py-3 px-4 text-dark-300">{user.email}</td>
                                    <td className="py-3 px-4">
                                        <span className="px-3 py-1 bg-primary-100 text-primary-800 rounded-full text-sm font-semibold">
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-dark-300 text-sm">{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</td>
                                    <td className="py-3 px-4">
                                        <div className="flex justify-center gap-2">
                                            <Button onClick={() => { }} variant="secondary" size="sm">
                                                <Edit2 className="w-4 h-4" />
                                            </Button>
                                            <Button onClick={() => handleDelete(user.id)} variant="danger" size="sm">
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        </div>
    )
}
