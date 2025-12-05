import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface BusinessConfig {
  name?: string
  location?: string
  phone?: string
  email?: string
  hours?: Record<string, { open?: string; close?: string; closed?: boolean }>
  services?: Array<{ id: string; name: string; duration_minutes: number; price: number; description: string }>
  policies?: { cancellation?: string; deposit?: boolean; deposit_amount?: number; walk_ins?: string }
  faqs?: Array<{ question: string; answer: string }>
}

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

export default function BusinessSetup() {
  const { business } = useAuth()
  const [config, setConfig] = useState<BusinessConfig>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  
  // Form state
  const [basicInfo, setBasicInfo] = useState({
    name: '',
    location: '',
    phone: '',
    email: '',
  })
  
  const [hours, setHours] = useState<Record<string, { open: string; close: string; closed: boolean }>>({})
  
  const [policies, setPolicies] = useState({
    cancellation: '',
    deposit: false,
    deposit_amount: 0,
    walk_ins: '',
  })
  
  const [services, setServices] = useState<Array<{ id: string; name: string; duration_minutes: number; price: number; description: string }>>([])
  const [editingServiceId, setEditingServiceId] = useState<string | null>(null)
  
  useEffect(() => {
    if (business?.id) {
      loadConfig()
    }
  }, [business?.id])
  
  const loadConfig = async () => {
    try {
      const data = await api.get<{ config: BusinessConfig }>(`/business/${business!.id}/config`)
      const cfg = data.config || {}
      setConfig(cfg)
      
      // Populate form state
      setBasicInfo({
        name: cfg.name || business!.name || '',
        location: cfg.location || '',
        phone: cfg.phone || '',
        email: cfg.email || '',
      })
      
      // Populate hours
      const defaultHours: Record<string, { open: string; close: string; closed: boolean }> = {}
      DAYS.forEach(day => {
        const h = cfg.hours?.[day]
        defaultHours[day] = {
          open: h?.open || '09:00',
          close: h?.close || '18:00',
          closed: h?.closed || false,
        }
      })
      setHours(defaultHours)
      
      // Populate policies
      setPolicies({
        cancellation: cfg.policies?.cancellation || '',
        deposit: cfg.policies?.deposit || false,
        deposit_amount: cfg.policies?.deposit_amount || 0,
        walk_ins: cfg.policies?.walk_ins || '',
      })
      
      // Populate services
      setServices(cfg.services || [])
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSave = async () => {
    if (!business?.id) return
    setSaving(true)
    setMessage('')
    
    try {
      // Build the config object
      const updatedConfig: BusinessConfig = {
        ...config,
        name: basicInfo.name,
        location: basicInfo.location,
        phone: basicInfo.phone,
        email: basicInfo.email,
        hours: hours,
        policies: policies,
        services: services,
      }
      
      await api.put(`/business/${business.id}/config`, updatedConfig)
      setMessage('Configuration saved successfully!')
      setConfig(updatedConfig)
    } catch (error: any) {
      setMessage(`Error: ${error.message}`)
    } finally {
      setSaving(false)
    }
  }
  
  const handleHoursChange = (day: string, field: 'open' | 'close' | 'closed', value: string | boolean) => {
    setHours(prev => ({
      ...prev,
      [day]: {
        ...prev[day],
        [field]: value,
      }
    }))
  }
  
  const handleAddService = () => {
    const newService = {
      id: `service_${Date.now()}`,
      name: 'New Service',
      duration_minutes: 30,
      price: 0,
      description: '',
    }
    setServices([...services, newService])
    setEditingServiceId(newService.id)
  }
  
  const handleUpdateService = (id: string, field: string, value: string | number) => {
    setServices(services.map(s => 
      s.id === id ? { ...s, [field]: value } : s
    ))
  }
  
  const handleDeleteService = (id: string) => {
    setServices(services.filter(s => s.id !== id))
    if (editingServiceId === id) {
      setEditingServiceId(null)
    }
  }
  
  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }
  
  if (!business) {
    return (
      <div className="p-8">
        <div className="card text-center py-12">
          <p className="text-muted-foreground">No business configured. Please sign up as a business owner.</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Business Setup</h1>
          <p className="text-muted-foreground mt-1">Configure your business information for the AI receptionist</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
      
      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.startsWith('Error') ? 'bg-destructive/10 text-destructive' : 'bg-green-500/10 text-green-700'
        }`}>
          {message}
        </div>
      )}
      
      <div className="space-y-6">
        {/* Basic Information */}
        <div className="card">
          <h2 className="text-lg font-semibold text-card-foreground mb-4">Basic Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Business Name</label>
              <input
                type="text"
                value={basicInfo.name}
                onChange={(e) => setBasicInfo({ ...basicInfo, name: e.target.value })}
                className="input-field"
                placeholder="Your business name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Location / Address</label>
              <input
                type="text"
                value={basicInfo.location}
                onChange={(e) => setBasicInfo({ ...basicInfo, location: e.target.value })}
                className="input-field"
                placeholder="123 Main St, City, State"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Phone</label>
              <input
                type="tel"
                value={basicInfo.phone}
                onChange={(e) => setBasicInfo({ ...basicInfo, phone: e.target.value })}
                className="input-field"
                placeholder="(555) 123-4567"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Email</label>
              <input
                type="email"
                value={basicInfo.email}
                onChange={(e) => setBasicInfo({ ...basicInfo, email: e.target.value })}
                className="input-field"
                placeholder="contact@yourbusiness.com"
              />
            </div>
          </div>
        </div>
        
        {/* Business Hours */}
        <div className="card">
          <h2 className="text-lg font-semibold text-card-foreground mb-4">Business Hours</h2>
          <div className="space-y-3">
            {DAYS.map((day) => (
              <div key={day} className="flex items-center gap-4 p-3 bg-secondary/30 rounded-lg">
                <div className="w-28">
                  <span className="font-medium text-card-foreground capitalize">{day}</span>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hours[day]?.closed || false}
                    onChange={(e) => handleHoursChange(day, 'closed', e.target.checked)}
                    className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="text-sm text-muted-foreground">Closed</span>
                </label>
                {!hours[day]?.closed && (
                  <>
                    <div className="flex items-center gap-2">
                      <input
                        type="time"
                        value={hours[day]?.open || '09:00'}
                        onChange={(e) => handleHoursChange(day, 'open', e.target.value)}
                        className="input-field w-32 py-1.5"
                      />
                      <span className="text-muted-foreground">to</span>
                      <input
                        type="time"
                        value={hours[day]?.close || '18:00'}
                        onChange={(e) => handleHoursChange(day, 'close', e.target.value)}
                        className="input-field w-32 py-1.5"
                      />
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Policies */}
        <div className="card">
          <h2 className="text-lg font-semibold text-card-foreground mb-4">Policies</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Cancellation Policy</label>
              <input
                type="text"
                value={policies.cancellation}
                onChange={(e) => setPolicies({ ...policies, cancellation: e.target.value })}
                className="input-field"
                placeholder="e.g., 24 hours notice required for cancellations"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1.5">Walk-in Policy</label>
              <input
                type="text"
                value={policies.walk_ins}
                onChange={(e) => setPolicies({ ...policies, walk_ins: e.target.value })}
                className="input-field"
                placeholder="e.g., Walk-ins welcome, appointments preferred"
              />
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={policies.deposit}
                  onChange={(e) => setPolicies({ ...policies, deposit: e.target.checked })}
                  className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
                />
                <span className="text-sm font-medium text-card-foreground">Require deposit</span>
              </label>
              {policies.deposit && (
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">$</span>
                  <input
                    type="number"
                    value={policies.deposit_amount}
                    onChange={(e) => setPolicies({ ...policies, deposit_amount: Number(e.target.value) })}
                    className="input-field w-24 py-1.5"
                    min="0"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Services */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-card-foreground">Services</h2>
            <button
              onClick={handleAddService}
              className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              + Add Service
            </button>
          </div>
          {services.length > 0 ? (
            <div className="space-y-3">
              {services.map((service) => (
                <div key={service.id} className="p-4 bg-secondary/30 rounded-lg">
                  {editingServiceId === service.id ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Service Name</label>
                          <input
                            type="text"
                            value={service.name}
                            onChange={(e) => handleUpdateService(service.id, 'name', e.target.value)}
                            className="input-field"
                            placeholder="Service name"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
                          <input
                            type="text"
                            value={service.description}
                            onChange={(e) => handleUpdateService(service.id, 'description', e.target.value)}
                            className="input-field"
                            placeholder="Brief description"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Duration (min)</label>
                          <input
                            type="number"
                            value={service.duration_minutes}
                            onChange={(e) => handleUpdateService(service.id, 'duration_minutes', Number(e.target.value))}
                            className="input-field"
                            min="5"
                            step="5"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-muted-foreground mb-1">Price ($)</label>
                          <input
                            type="number"
                            value={service.price}
                            onChange={(e) => handleUpdateService(service.id, 'price', Number(e.target.value))}
                            className="input-field"
                            min="0"
                            step="0.01"
                          />
                        </div>
                      </div>
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={() => setEditingServiceId(null)}
                          className="px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                        >
                          Done
                        </button>
                        <button
                          onClick={() => handleDeleteService(service.id)}
                          className="px-3 py-1.5 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium text-card-foreground">{service.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {service.duration_minutes} min {service.description && `• ${service.description}`}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <p className="font-semibold text-primary">${service.price}</p>
                        <button
                          onClick={() => setEditingServiceId(service.id)}
                          className="px-2 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No services configured. Click "Add Service" to create your first service.</p>
          )}
        </div>
      </div>
    </div>
  )
}
