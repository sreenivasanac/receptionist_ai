import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Staff {
  id: string
  business_id: string
  name: string
  role_title?: string
  services_offered: string[]
  availability_type?: 'store_hours' | 'custom'
  is_active: boolean
}

interface Service {
  id: string
  name: string
  duration_minutes: number
  price: number
  description: string
}

interface BusinessConfig {
  services?: Service[]
}

export default function StaffManagement() {
  const { business } = useAuth()
  const [staff, setStaff] = useState<Staff[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    role_title: '',
    services_offered: [] as string[],
    availability_type: 'store_hours' as 'store_hours' | 'custom'
  })
  const [saving, setSaving] = useState(false)
  
  useEffect(() => {
    if (business?.id) {
      loadData()
    }
  }, [business?.id])
  
  const loadData = async () => {
    try {
      const [staffData, configData] = await Promise.all([
        api.get<Staff[]>(`/admin/${business!.id}/staff?active_only=false`),
        api.get<{ config: BusinessConfig }>(`/business/${business!.id}/config`)
      ])
      setStaff(staffData)
      setServices(configData.config?.services || [])
    } catch (error) {
      console.error('Failed to load data:', error)
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
          services_offered: formData.services_offered,
        })
      } else {
        await api.post(`/admin/${business.id}/staff`, {
          name: formData.name,
          role_title: formData.role_title || null,
          services_offered: formData.services_offered,
        })
      }
      await loadData()
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
      await loadData()
    } catch (error) {
      console.error('Failed to delete staff:', error)
    }
  }
  
  const toggleService = (serviceId: string) => {
    setFormData(prev => ({
      ...prev,
      services_offered: prev.services_offered.includes(serviceId)
        ? prev.services_offered.filter(id => id !== serviceId)
        : [...prev.services_offered, serviceId]
    }))
  }
  
  const openModal = (staffMember?: Staff) => {
    if (staffMember) {
      setEditingStaff(staffMember)
      setFormData({
        name: staffMember.name,
        role_title: staffMember.role_title || '',
        services_offered: staffMember.services_offered || [],
        availability_type: staffMember.availability_type || 'store_hours'
      })
    } else {
      setEditingStaff(null)
      setFormData({
        name: '',
        role_title: '',
        services_offered: [],
        availability_type: 'store_hours'
      })
    }
    setShowModal(true)
  }
  
  const closeModal = () => {
    setShowModal(false)
    setEditingStaff(null)
    setFormData({ name: '', role_title: '', services_offered: [], availability_type: 'store_hours' })
  }
  
  const getServiceNames = (serviceIds: string[]) => {
    return serviceIds
      .map(id => services.find(s => s.id === id)?.name)
      .filter(Boolean)
  }
  
  if (!business) {
    return (
      <div className="p-8">
        <div className="card text-center py-12">
          <p className="text-muted-foreground">No business configured.</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Staff Management</h1>
          <p className="text-muted-foreground mt-1">Manage your team members and their service assignments</p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Staff Member
        </button>
      </div>
      
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-medium text-blue-900">How staff information is used</h3>
            <p className="text-sm text-blue-700 mt-1">
              Staff members and their assigned services are used by the AI receptionist to help customers book appointments. 
              When a customer requests a service through chat, they can choose from available staff members who offer that service. 
              This enables personalized booking recommendations and accurate scheduling.
            </p>
          </div>
        </div>
      </div>
      
      {loading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : staff.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No staff members yet</h3>
          <p className="text-muted-foreground mb-4 max-w-md mx-auto">
            Add your team members so customers can book appointments with specific staff through the AI chat.
          </p>
          <button onClick={() => openModal()} className="btn-primary">
            Add Your First Staff Member
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {staff.map((member) => {
            const memberServices = getServiceNames(member.services_offered)
            return (
              <div key={member.id} className="card hover:border-primary/30 transition-colors">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                      <span className="text-primary font-semibold text-lg">
                        {member.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <h3 className="font-medium text-card-foreground">{member.name}</h3>
                      <p className="text-sm text-muted-foreground">{member.role_title || 'Team Member'}</p>
                    </div>
                  </div>
                  <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                    member.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {member.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                {/* Services */}
                <div className="mb-4">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2">Services</p>
                  {memberServices.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {memberServices.slice(0, 3).map((name, idx) => (
                        <span key={idx} className="inline-flex px-2 py-0.5 bg-secondary rounded text-xs text-card-foreground">
                          {name}
                        </span>
                      ))}
                      {memberServices.length > 3 && (
                        <span className="inline-flex px-2 py-0.5 bg-secondary rounded text-xs text-muted-foreground">
                          +{memberServices.length - 3} more
                        </span>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">No services assigned</p>
                  )}
                </div>
                
                {/* Availability */}
                <div className="mb-4">
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">Availability</p>
                  <p className="text-sm text-card-foreground">
                    {member.availability_type === 'custom' ? 'Custom Hours' : 'During Store Hours'}
                  </p>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-3 border-t border-border">
                  <button 
                    onClick={() => openModal(member)} 
                    className="flex-1 px-3 py-2 text-sm font-medium text-primary bg-primary/5 rounded-lg hover:bg-primary/10 transition-colors"
                  >
                    Edit
                  </button>
                  <button 
                    onClick={() => handleDelete(member.id)} 
                    className="px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
      
      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-semibold text-card-foreground">
                {editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {editingStaff ? 'Update staff details and service assignments' : 'Add a new team member to your staff'}
              </p>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-card-foreground mb-1.5">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input-field"
                    placeholder="Full name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-card-foreground mb-1.5">Role/Title</label>
                  <input
                    type="text"
                    value={formData.role_title}
                    onChange={(e) => setFormData({ ...formData, role_title: e.target.value })}
                    className="input-field"
                    placeholder="e.g., Senior Stylist"
                  />
                </div>
              </div>
              
              {/* Services */}
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">Services Offered</label>
                <p className="text-xs text-muted-foreground mb-3">
                  Select the services this staff member can perform. Customers can book these services with this team member.
                </p>
                {services.length > 0 ? (
                  <div className="border border-border rounded-lg divide-y divide-border max-h-48 overflow-y-auto">
                    {services.map((service) => (
                      <label 
                        key={service.id} 
                        className="flex items-center gap-3 p-3 hover:bg-secondary/50 cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={formData.services_offered.includes(service.id)}
                          onChange={() => toggleService(service.id)}
                          className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-card-foreground">{service.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {service.duration_minutes} min • ${service.price}
                          </p>
                        </div>
                      </label>
                    ))}
                  </div>
                ) : (
                  <div className="border border-dashed border-border rounded-lg p-4 text-center">
                    <p className="text-sm text-muted-foreground">
                      No services configured yet. Add services in{' '}
                      <a href="/business" className="text-primary hover:underline">Business Setup</a>
                      {' '}first.
                    </p>
                  </div>
                )}
              </div>
              
              {/* Availability */}
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">Availability</label>
                <p className="text-xs text-muted-foreground mb-3">
                  When is this staff member available for appointments?
                </p>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer transition-colors">
                    <input
                      type="radio"
                      name="availability"
                      value="store_hours"
                      checked={formData.availability_type === 'store_hours'}
                      onChange={() => setFormData({ ...formData, availability_type: 'store_hours' })}
                      className="w-4 h-4 border-border text-primary focus:ring-primary"
                    />
                    <div>
                      <p className="text-sm font-medium text-card-foreground">During Store Hours</p>
                      <p className="text-xs text-muted-foreground">Available during your business operating hours</p>
                    </div>
                  </label>
                  <label className="flex items-center gap-3 p-3 border border-border rounded-lg hover:bg-secondary/30 cursor-pointer transition-colors opacity-60">
                    <input
                      type="radio"
                      name="availability"
                      value="custom"
                      checked={formData.availability_type === 'custom'}
                      onChange={() => setFormData({ ...formData, availability_type: 'custom' })}
                      className="w-4 h-4 border-border text-primary focus:ring-primary"
                      disabled
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-card-foreground">Custom Hours</p>
                        <span className="px-1.5 py-0.5 bg-secondary text-xs text-muted-foreground rounded">Coming Soon</span>
                      </div>
                      <p className="text-xs text-muted-foreground">Set specific working hours for this staff member</p>
                    </div>
                  </label>
                </div>
              </div>
              
              {/* Actions */}
              <div className="flex gap-3 justify-end pt-4 border-t border-border">
                <button type="button" onClick={closeModal} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
                  {saving ? 'Saving...' : editingStaff ? 'Update Staff' : 'Add Staff'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
