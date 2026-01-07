import { useEffect, useState } from 'react'
import { Plus, Trash2, Edit2 } from 'lucide-react'
import { Card, Button, Input, LoadingSpinner, Alert } from '../components/ui'
import { apiClient } from '../api/client'
import type { Group } from '../types'

export function Groups() {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '', description: '' })

  useEffect(() => {
    fetchGroups()
  }, [])

  const fetchGroups = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getGroups()
      setGroups(data)
      setError(null)
    } catch (err) {
      setError('Failed to load groups')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      if (!formData.name) {
        setError('Please fill in group name')
        return
      }
      await apiClient.createGroup(formData)
      setSuccess('Group created successfully')
      setFormData({ name: '', description: '' })
      setShowForm(false)
      fetchGroups()
    } catch (err) {
      setError('Failed to create group')
      console.error(err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure?')) return
    try {
      await apiClient.deleteGroup(id)
      setSuccess('Group deleted successfully')
      fetchGroups()
    } catch (err) {
      setError('Failed to delete group')
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
          <h1 className="text-4xl font-bold text-white">Groups</h1>
          <p className="text-dark-400 mt-1">Manage Telegram groups</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)} variant="primary" size="lg">
          <Plus className="inline mr-2 w-5 h-5" /> Add Group
        </Button>
      </div>

      {error && <Alert type="error" message={error} onClose={() => setError(null)} />}
      {success && <Alert type="success" message={success} onClose={() => setSuccess(null)} />}

      {showForm && (
        <Card className="bg-dark-700 border border-dark-600">
          <h2 className="text-xl font-bold text-white mb-4">Create New Group</h2>
          <div className="space-y-4">
            <Input label="Group Name" value={formData.name} onChange={(v) => setFormData({ ...formData, name: String(v) })} placeholder="Programming" />
            <Input label="Description" type="textarea" value={formData.description} onChange={(v) => setFormData({ ...formData, description: String(v) })} placeholder="Description" />
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
                <th className="text-left py-3 px-4 font-semibold text-dark-200">Name</th>
                <th className="text-left py-3 px-4 font-semibold text-dark-200">Description</th>
                <th className="text-left py-3 px-4 font-semibold text-dark-200">Members</th>
                <th className="text-left py-3 px-4 font-semibold text-dark-200">Created</th>
                <th className="text-center py-3 px-4 font-semibold text-dark-200">Actions</th>
              </tr>
            </thead>
            <tbody>
              {groups.map((group) => (
                <tr key={group.id} className="border-b border-dark-700 hover:bg-dark-700 transition">
                  <td className="py-3 px-4 font-semibold text-dark-100">{group.name}</td>
                  <td className="py-3 px-4 text-dark-300 truncate">{group.description}</td>
                  <td className="py-3 px-4">
                    <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                      {group.members_count}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-dark-300 text-sm">{group.created_at ? new Date(group.created_at).toLocaleDateString() : 'N/A'}</td>
                  <td className="py-3 px-4">
                    <div className="flex justify-center gap-2">
                      <Button onClick={() => { }} variant="secondary" size="sm">
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button onClick={() => handleDelete(group.id)} variant="danger" size="sm">
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
