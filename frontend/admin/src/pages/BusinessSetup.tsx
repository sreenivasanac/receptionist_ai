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

const TIME_OPTIONS = [
  '06:00', '06:30', '07:00', '07:30', '08:00', '08:30', '09:00', '09:30',
  '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30',
  '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30',
  '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30', '22:00'
]

const formatTimeDisplay = (time: string) => {
  const [hours, minutes] = time.split(':')
  const hour = parseInt(hours)
  const ampm = hour >= 12 ? 'PM' : 'AM'
  const hour12 = hour % 12 || 12
  return `${hour12}:${minutes} ${ampm}`
}

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
  const [newService, setNewService] = useState<{ id: string; name: string; duration_minutes: number; price: number; description: string } | null>(null)
  
  // Website Import state
  const [websiteUrls, setWebsiteUrls] = useState<string[]>([''])
  const [scraping, setScraping] = useState(false)
  const [scrapeResults, setScrapeResults] = useState<{
    results: Array<{ url: string; success: boolean; error?: string; title?: string }>
    current_config: Record<string, unknown>
    extracted_config: Record<string, unknown>
    field_diffs: Array<{ field: string; field_label: string; current_value?: string; extracted_value?: string }>
    new_services: Array<{ name: string; description?: string; duration_minutes?: number; price?: number; is_new: boolean }>
    new_faqs: Array<{ question: string; answer: string; is_new: boolean }>
    extracted_hours: Array<{ day: string; open?: string; close?: string; closed: boolean }>
    extraction_error?: string
  } | null>(null)
  const [selectedFields, setSelectedFields] = useState<Record<string, 'current' | 'extracted'>>({})
  const [selectedServices, setSelectedServices] = useState<Set<number>>(new Set())
  const [selectedFaqs, setSelectedFaqs] = useState<Set<number>>(new Set())
  const [applyHours, setApplyHours] = useState(false)
  const [applying, setApplying] = useState(false)
  
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
    setNewService({
      id: `service_${Date.now()}`,
      name: '',
      duration_minutes: 30,
      price: 0,
      description: '',
    })
  }
  
  const handleSaveNewService = () => {
    if (newService && newService.name.trim()) {
      setServices([...services, newService])
      setNewService(null)
    }
  }
  
  const handleCancelNewService = () => {
    setNewService(null)
  }
  
  const handleUpdateNewService = (field: string, value: string | number) => {
    if (newService) {
      setNewService({ ...newService, [field]: value })
    }
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
  
  // Website Import functions
  const addUrlField = () => {
    if (websiteUrls.length < 10) {
      setWebsiteUrls([...websiteUrls, ''])
    }
  }
  
  const removeUrlField = (index: number) => {
    setWebsiteUrls(websiteUrls.filter((_, i) => i !== index))
  }
  
  const updateUrl = (index: number, value: string) => {
    const newUrls = [...websiteUrls]
    newUrls[index] = value
    setWebsiteUrls(newUrls)
  }
  
  const handleScrapeWebsites = async () => {
    if (!business?.id) return
    
    const validUrls = websiteUrls.filter(url => url.trim())
    if (validUrls.length === 0) {
      setMessage('Please enter at least one URL')
      return
    }
    
    setScraping(true)
    setScrapeResults(null)
    setSelectedFields({})
    setSelectedServices(new Set())
    setSelectedFaqs(new Set())
    setApplyHours(false)
    setMessage('')
    
    try {
      const response = await api.post<typeof scrapeResults>(`/business/${business.id}/scrape`, {
        urls: validUrls
      })
      setScrapeResults(response)
      
      // Auto-select extracted values for fields that are empty in current config
      const autoSelected: Record<string, 'current' | 'extracted'> = {}
      response?.field_diffs?.forEach(diff => {
        if (!diff.current_value && diff.extracted_value) {
          autoSelected[diff.field] = 'extracted'
        } else {
          autoSelected[diff.field] = 'current'
        }
      })
      setSelectedFields(autoSelected)
      
      // Auto-select new services and FAQs
      const newSvcIndices = new Set<number>()
      response?.new_services?.forEach((svc, idx) => {
        if (svc.is_new) newSvcIndices.add(idx)
      })
      setSelectedServices(newSvcIndices)
      
      const newFaqIndices = new Set<number>()
      response?.new_faqs?.forEach((faq, idx) => {
        if (faq.is_new) newFaqIndices.add(idx)
      })
      setSelectedFaqs(newFaqIndices)
      
      if (response?.extraction_error) {
        setMessage(`Warning: ${response.extraction_error}`)
      } else {
        setMessage('Website information extracted successfully! Review and apply below.')
      }
    } catch (error: unknown) {
      const err = error as { message?: string }
      setMessage(`Error: ${err.message || 'Failed to scrape websites'}`)
    } finally {
      setScraping(false)
    }
  }
  
  const handleApplyExtracted = async () => {
    if (!business?.id || !scrapeResults) return
    
    setApplying(true)
    setMessage('')
    
    try {
      // Build extracted values map
      const extractedValues: Record<string, string> = {}
      scrapeResults.field_diffs.forEach(diff => {
        if (diff.extracted_value) {
          extractedValues[diff.field] = diff.extracted_value
        }
      })
      
      // Build services and FAQs to add
      const servicesToAdd = scrapeResults.new_services
        .filter((_, idx) => selectedServices.has(idx))
        .map(svc => ({
          name: svc.name,
          description: svc.description,
          duration_minutes: svc.duration_minutes,
          price: svc.price
        }))
      
      const faqsToAdd = scrapeResults.new_faqs
        .filter((_, idx) => selectedFaqs.has(idx))
        .map(faq => ({
          question: faq.question,
          answer: faq.answer
        }))
      
      // Build hours object
      const hoursObj: Record<string, { open?: string; close?: string; closed: boolean }> = {}
      scrapeResults.extracted_hours.forEach(h => {
        hoursObj[h.day] = { open: h.open, close: h.close, closed: h.closed }
      })
      
      await api.post(`/business/${business.id}/scrape/apply`, {
        selected_fields: selectedFields,
        extracted_values: extractedValues,
        add_services: servicesToAdd,
        add_faqs: faqsToAdd,
        apply_hours: applyHours,
        extracted_hours: hoursObj
      })
      
      setMessage('Changes applied successfully!')
      setScrapeResults(null)
      loadConfig() // Reload config to reflect changes
    } catch (error: unknown) {
      const err = error as { message?: string }
      setMessage(`Error: ${err.message || 'Failed to apply changes'}`)
    } finally {
      setApplying(false)
    }
  }
  
  const toggleFieldSelection = (field: string, value: 'current' | 'extracted') => {
    setSelectedFields(prev => ({ ...prev, [field]: value }))
  }
  
  const toggleServiceSelection = (idx: number) => {
    setSelectedServices(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }
  
  const toggleFaqSelection = (idx: number) => {
    setSelectedFaqs(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
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
        
        {/* Website Import */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-card-foreground">Import from Website</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Extract business information from your website pages
              </p>
            </div>
          </div>
          
          <div className="space-y-3 mb-4">
            {websiteUrls.map((url, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateUrl(index, e.target.value)}
                  className="input-field flex-1"
                  placeholder="https://yourbusiness.com/about"
                />
                {websiteUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeUrlField(index)}
                    className="px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </div>
          
          <div className="flex gap-2 mb-4">
            {websiteUrls.length < 10 && (
              <button
                type="button"
                onClick={addUrlField}
                className="text-sm text-primary hover:underline flex items-center gap-1"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add another URL
              </button>
            )}
          </div>
          
          <button
            type="button"
            onClick={handleScrapeWebsites}
            disabled={scraping || websiteUrls.every(u => !u.trim())}
            className="btn-primary disabled:opacity-50"
          >
            {scraping ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Fetching...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                Fetch Information
              </>
            )}
          </button>
          
          {/* Scrape Results - Diff View */}
          {scrapeResults && (
            <div className="mt-4 pt-4 border-t border-border space-y-4">
              {/* URL Results */}
              <div>
                <h3 className="text-sm font-medium text-card-foreground mb-2">Scraped Pages</h3>
                <div className="space-y-1">
                  {scrapeResults.results.map((result, idx) => (
                    <div key={idx} className={`text-sm p-2 rounded ${result.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                      {result.success ? '✓' : '✗'} {result.url}
                      {result.title && <span className="ml-2 text-muted-foreground">- {result.title}</span>}
                      {result.error && <span className="ml-2">- {result.error}</span>}
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Field Diffs */}
              {scrapeResults.field_diffs.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-card-foreground mb-2">Business Information</h3>
                  <p className="text-xs text-muted-foreground mb-3">Select which value to use for each field:</p>
                  <div className="bg-secondary/30 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left p-3 font-medium">Field</th>
                          <th className="text-left p-3 font-medium">Current Value</th>
                          <th className="text-left p-3 font-medium">Extracted Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {scrapeResults.field_diffs.map((diff) => (
                          <tr key={diff.field} className="border-b border-border last:border-0">
                            <td className="p-3 font-medium">{diff.field_label}</td>
                            <td className="p-3">
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="radio"
                                  name={`field-${diff.field}`}
                                  checked={selectedFields[diff.field] === 'current'}
                                  onChange={() => toggleFieldSelection(diff.field, 'current')}
                                  className="w-4 h-4 text-primary"
                                  disabled={!diff.current_value}
                                />
                                <span className={!diff.current_value ? 'text-muted-foreground italic' : ''}>
                                  {diff.current_value || '(empty)'}
                                </span>
                              </label>
                            </td>
                            <td className="p-3">
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="radio"
                                  name={`field-${diff.field}`}
                                  checked={selectedFields[diff.field] === 'extracted'}
                                  onChange={() => toggleFieldSelection(diff.field, 'extracted')}
                                  className="w-4 h-4 text-primary"
                                  disabled={!diff.extracted_value}
                                />
                                <span className={`${!diff.extracted_value ? 'text-muted-foreground italic' : 'text-green-700'}`}>
                                  {diff.extracted_value || '(not found)'}
                                </span>
                              </label>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              
              {/* Extracted Hours */}
              {scrapeResults.extracted_hours.length > 0 && (
                <div>
                  <label className="flex items-center gap-2 cursor-pointer mb-2">
                    <input
                      type="checkbox"
                      checked={applyHours}
                      onChange={(e) => setApplyHours(e.target.checked)}
                      className="w-4 h-4 rounded border-border text-primary"
                    />
                    <span className="text-sm font-medium text-card-foreground">Apply Extracted Business Hours</span>
                  </label>
                  {applyHours && (
                    <div className="bg-secondary/30 rounded-lg p-3 space-y-1">
                      {scrapeResults.extracted_hours.map((h) => (
                        <div key={h.day} className="text-sm flex gap-2">
                          <span className="capitalize font-medium w-24">{h.day}:</span>
                          <span className={h.closed ? 'text-red-600' : 'text-green-700'}>
                            {h.closed ? 'Closed' : `${h.open || '?'} - ${h.close || '?'}`}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* New Services */}
              {scrapeResults.new_services.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-card-foreground mb-2">
                    Services Found ({scrapeResults.new_services.filter(s => s.is_new).length} new)
                  </h3>
                  <div className="space-y-2">
                    {scrapeResults.new_services.map((svc, idx) => (
                      <label
                        key={idx}
                        className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedServices.has(idx) ? 'bg-green-50 border border-green-200' : 'bg-secondary/30'
                        } ${!svc.is_new ? 'opacity-50' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedServices.has(idx)}
                          onChange={() => toggleServiceSelection(idx)}
                          className="w-4 h-4 mt-0.5 rounded border-border text-primary"
                          disabled={!svc.is_new}
                        />
                        <div className="flex-1">
                          <div className="flex justify-between items-start">
                            <span className="font-medium">{svc.name}</span>
                            <span className="text-primary font-semibold">
                              {svc.price != null ? `$${svc.price}` : ''}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {svc.duration_minutes && `${svc.duration_minutes} min`}
                            {svc.description && ` • ${svc.description}`}
                          </p>
                          {!svc.is_new && (
                            <span className="text-xs text-amber-600">Already exists</span>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              
              {/* New FAQs */}
              {scrapeResults.new_faqs.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-card-foreground mb-2">
                    FAQs Found ({scrapeResults.new_faqs.filter(f => f.is_new).length} new)
                  </h3>
                  <div className="space-y-2">
                    {scrapeResults.new_faqs.map((faq, idx) => (
                      <label
                        key={idx}
                        className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedFaqs.has(idx) ? 'bg-green-50 border border-green-200' : 'bg-secondary/30'
                        } ${!faq.is_new ? 'opacity-50' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedFaqs.has(idx)}
                          onChange={() => toggleFaqSelection(idx)}
                          className="w-4 h-4 mt-0.5 rounded border-border text-primary"
                          disabled={!faq.is_new}
                        />
                        <div className="flex-1">
                          <p className="font-medium">{faq.question}</p>
                          <p className="text-sm text-muted-foreground line-clamp-2">{faq.answer}</p>
                          {!faq.is_new && (
                            <span className="text-xs text-amber-600">Already exists</span>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Apply Button */}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleApplyExtracted}
                  disabled={applying}
                  className="btn-primary disabled:opacity-50"
                >
                  {applying ? 'Applying...' : 'Apply Selected Changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setScrapeResults(null)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
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
                  <div className="flex items-center gap-2">
                    <select
                      value={hours[day]?.open || '09:00'}
                      onChange={(e) => handleHoursChange(day, 'open', e.target.value)}
                      className="input-field w-32 py-1.5"
                    >
                      {TIME_OPTIONS.map((time) => (
                        <option key={time} value={time}>{formatTimeDisplay(time)}</option>
                      ))}
                    </select>
                    <span className="text-muted-foreground">to</span>
                    <select
                      value={hours[day]?.close || '18:00'}
                      onChange={(e) => handleHoursChange(day, 'close', e.target.value)}
                      className="input-field w-32 py-1.5"
                    >
                      {TIME_OPTIONS.map((time) => (
                        <option key={time} value={time}>{formatTimeDisplay(time)}</option>
                      ))}
                    </select>
                  </div>
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
              type="button"
              onClick={handleAddService}
              disabled={!!newService}
              className="px-3 py-1.5 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              + Add Service
            </button>
          </div>
          
          {/* New service form - shown at top */}
          {newService && (
            <div className="p-4 bg-primary/10 border border-primary/30 rounded-lg mb-3">
              <p className="text-sm font-medium text-primary mb-3">New Service</p>
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Service Name *</label>
                    <input
                      type="text"
                      value={newService.name}
                      onChange={(e) => handleUpdateNewService('name', e.target.value)}
                      className="input-field"
                      placeholder="e.g., Women's Haircut"
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Description</label>
                    <input
                      type="text"
                      value={newService.description}
                      onChange={(e) => handleUpdateNewService('description', e.target.value)}
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
                      value={newService.duration_minutes}
                      onChange={(e) => handleUpdateNewService('duration_minutes', Number(e.target.value))}
                      className="input-field"
                      min="5"
                      step="5"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">Price ($)</label>
                    <input
                      type="number"
                      value={newService.price}
                      onChange={(e) => handleUpdateNewService('price', Number(e.target.value))}
                      className="input-field"
                      min="0"
                      step="0.01"
                    />
                  </div>
                </div>
                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={handleSaveNewService}
                    disabled={!newService.name.trim()}
                    className="px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
                  >
                    Add Service
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelNewService}
                    className="px-3 py-1.5 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
          
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
          ) : !newService && (
            <p className="text-muted-foreground">No services configured. Click "Add Service" to create your first service.</p>
          )}
        </div>
      </div>
    </div>
  )
}
