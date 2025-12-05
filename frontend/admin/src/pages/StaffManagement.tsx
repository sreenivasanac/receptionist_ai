import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Staff {
  id: string
  business_id: string
  name: string
  role_title?: string
  services_offered: string[]
  is_active: boolean
}

export default function StaffManagement() {
  const { business } = useAuth()
  const [staff, setStaff] = useState<Staff[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null)
  const [formData, setFormData] = useState({ name: '', role_title: '' })
  const [saving, setSaving] = useState(false)
  
  useEffect(() => {
    if (business?.id) {
      loadStaff()
    }
  }, [business?.id])
  
  const loadStaff = async () => {
    try {
      const data = await api.get<Staff[]>(`/admin/${business!.id}/staff?active_only=false`)
      setStaff(data)
    } catch (error) {
      console.error('Failed to load staff:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!business?.id) return
    
    setSaving(true)
    try {
      if (editingStaff) {
        await api.put(`/admin/${business.id}/staff/${editingStaff.id}`, {
          name: formData.name,
          role_title: formData.role_title || null,
          services_offered: editingStaff.services_offered,
        })
      } else {
        await api.post(`/admin/${business.id}/staff`, {
          name: formData.name,
          role_title: formData.role_title || null,
          services_offered: [],
        })
      }
      await loadStaff()
      closeModal()
    } catch (error) {
      console.error('Failed to save staff:', error)
    } finally {
      setSaving(false)
    }
  }
  
  const handleDelete = async (staffId: string) => {
    if (!business?.id || !confirm('Are you sure you want to remove this staff member?')) return
    
    try {
      await api.delete(`/admin/${business.id}/staff/${staffId}`)
      await loadStaff()
    } catch (error) {
      console.error('Failed to delete staff:', error)
    }
  }
  
  const openModal = (staffMember?: Staff) => {
    if (staffMember) {
      setEditingStaff(staffMember)
      setFormData({ name: staffMember.name, role_title: staffMember.role_title || '' })
    } else {
      setEditingStaff(null)
      setFormData({ name: '', role_title: '' })
    }
    setShowModal(true)
  }
  
  const closeModal = () => {
    setShowModal(false)
    setEditingStaff(null)
    setFormData({ name: '', role_title: '' })
  }
  
  if (!business) {
    return (
      <div className="p-8">
        <div className="card text-center py-12">
          <p className="text-gray-500">No business configured.</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Staff Management</h1>
          <p className="text-gray-500 mt-1">Manage your team members</p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          Add Staff Member
        </button>
      </div>
      
      {loading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>
      ) : staff.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No staff members yet</p>
          <button onClick={() => openModal()} className="btn-primary">
            Add Your First Staff Member
          </button>
        </div>
      ) : (
        <div className="card">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-medium text-gray-700">Name</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Role</th>
                <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                <th className="text-right py-3 px-4 font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {staff.map((member) => (
                <tr key={member.id} className="border-b border-gray-100 last:border-0">
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                        <span className="text-primary-700 font-medium">
                          {member.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <span className="font-medium">{member.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-gray-600">{member.role_title || '-'}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                      member.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {member.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button onClick={() => openModal(member)} className="text-primary-600 hover:text-primary-800 mr-3">
                      Edit
                    </button>
                    <button onClick={() => handleDelete(member.id)} className="text-red-600 hover:text-red-800">
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-xl font-bold mb-4">
              {editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role/Title</label>
                <input
                  type="text"
                  value={formData.role_title}
                  onChange={(e) => setFormData({ ...formData, role_title: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Senior Stylist"
                />
              </div>
              <div className="flex gap-3 justify-end mt-6">
                <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
                  {saving ? 'Saving...' : editingStaff ? 'Update' : 'Add'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
