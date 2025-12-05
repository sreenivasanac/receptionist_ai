import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

export default function Settings() {
  const { business } = useAuth()
  const [embedCode, setEmbedCode] = useState('')
  const [features, setFeatures] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)
  
  useEffect(() => {
    if (business?.id) {
      loadSettings()
    }
  }, [business?.id])
  
  const loadSettings = async () => {
    try {
      const [embedData, featuresData] = await Promise.all([
        api.get<{ embed_code: string }>(`/business/${business!.id}/embed-code?base_url=http://localhost:8000/static`),
        api.get<{ features: Record<string, boolean> }>(`/business/${business!.id}/features`)
      ])
      setEmbedCode(embedData.embed_code)
      setFeatures(featuresData.features)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setLoading(false)
    }
  }
  
  const handleCopyEmbed = () => {
    navigator.clipboard.writeText(embedCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  const handleToggleFeature = async (feature: string) => {
    if (!business?.id) return
    
    const newFeatures = { ...features, [feature]: !features[feature] }
    setFeatures(newFeatures)
    
    try {
      await api.put(`/business/${business.id}/features`, newFeatures)
    } catch (error) {
      console.error('Failed to update features:', error)
      setFeatures(features)
    }
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
  
  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-card-foreground">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure {business.name}'s AI receptionist</p>
      </div>
      
      <div className="space-y-6">
        {/* Embed Code */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Embed Code</h2>
          <p className="text-sm text-gray-500 mb-4">
            Add this script tag to your website to display the chat widget. Place it before the closing &lt;/body&gt; tag.
          </p>
          <div className="bg-gray-900 text-gray-100 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            <code>{embedCode}</code>
          </div>
          <button
            onClick={handleCopyEmbed}
            className="mt-4 btn-primary"
          >
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
        </div>
        
        {/* Feature Toggles */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Feature Toggles</h2>
          <p className="text-sm text-gray-500 mb-4">
            Enable or disable chatbot capabilities for your business.
          </p>
          <div className="space-y-4">
            {[
              { key: 'business_info', label: 'Business Information', description: 'Answer questions about hours, location, services, pricing' },
              { key: 'greeting', label: 'Custom Greeting', description: 'Personalized welcome message based on your business type' },
              { key: 'customer_collection', label: 'Customer Info Collection', description: 'Collect customer details for follow-ups' },
            ].map((feature) => (
              <div key={feature.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{feature.label}</p>
                  <p className="text-sm text-gray-500">{feature.description}</p>
                </div>
                <button
                  onClick={() => handleToggleFeature(feature.key)}
                  className={`relative w-14 h-7 rounded-full transition-colors shadow-inner border-2 ${
                    features[feature.key] 
                      ? 'bg-green-500 border-green-600' 
                      : 'bg-gray-200 border-gray-400'
                  }`}
                >
                  <span
                    className={`absolute top-0.5 w-5 h-5 bg-white rounded-full transition-transform shadow-md ${
                      features[feature.key] ? 'left-7' : 'left-0.5'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
        
        {/* Business Info */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Business Information</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Business ID</p>
              <p className="font-mono text-gray-900">{business.id}</p>
            </div>
            <div>
              <p className="text-gray-500">Business Type</p>
              <p className="capitalize text-gray-900">{business.type}</p>
            </div>
            <div>
              <p className="text-gray-500">Name</p>
              <p className="text-gray-900">{business.name}</p>
            </div>
            <div>
              <p className="text-gray-500">Status</p>
              <span className="inline-flex px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
