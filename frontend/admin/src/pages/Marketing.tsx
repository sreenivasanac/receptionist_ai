import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Campaign {
  id: string
  name?: string
  message: string
  recipient_filter: Record<string, unknown>
  recipient_count: number
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed'
  scheduled_at?: string
  sent_at?: string
  created_at?: string
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  scheduled: 'bg-blue-100 text-blue-800',
  sending: 'bg-yellow-100 text-yellow-800',
  sent: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

export default function Marketing() {
  const { business } = useAuth()
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newCampaign, setNewCampaign] = useState({ name: '', message: '', all_customers: true })
  const [sending, setSending] = useState<string | null>(null)

  useEffect(() => {
    if (business?.id) {
      loadCampaigns()
    }
  }, [business?.id])

  const loadCampaigns = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      const data = await api.get<Campaign[]>(`/admin/${business.id}/campaigns?limit=50`)
      setCampaigns(data)
    } catch (error) {
      console.error('Failed to load campaigns:', error)
    } finally {
      setLoading(false)
    }
  }

  const createCampaign = async () => {
    if (!business?.id || !newCampaign.message) return
    try {
      await api.post(`/admin/${business.id}/campaigns`, {
        name: newCampaign.name || `Campaign ${new Date().toLocaleDateString()}`,
        message: newCampaign.message,
        recipient_filter: { all_customers: newCampaign.all_customers }
      })
      setShowCreate(false)
      setNewCampaign({ name: '', message: '', all_customers: true })
      loadCampaigns()
    } catch (error) {
      console.error('Failed to create campaign:', error)
    }
  }

  const sendCampaign = async (campaignId: string) => {
    if (!business?.id) return
    setSending(campaignId)
    try {
      const result = await api.post<{ message: string }>(`/admin/${business.id}/campaigns/${campaignId}/send`)
      alert(result.message)
      loadCampaigns()
    } catch (error) {
      console.error('Failed to send campaign:', error)
      alert('Failed to send campaign')
    } finally {
      setSending(null)
    }
  }

  const deleteCampaign = async (campaignId: string) => {
    if (!business?.id || !confirm('Delete this campaign?')) return
    try {
      await api.delete(`/admin/${business.id}/campaigns/${campaignId}`)
      loadCampaigns()
    } catch (error) {
      console.error('Failed to delete campaign:', error)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  }

  if (!business) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Please set up your business first.</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">SMS Marketing</h1>
          <p className="text-muted-foreground mt-1">Send SMS campaigns to your customers (mock)</p>
        </div>
        <button 
          onClick={() => setShowCreate(true)}
          className="btn btn-primary"
        >
          New Campaign
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-yellow-800">
          <strong>Note:</strong> This is a mock SMS feature for demo purposes. No actual SMS messages will be sent.
        </p>
      </div>

      {showCreate && (
        <div className="card mb-6">
          <h3 className="text-lg font-medium text-card-foreground mb-4">Create Campaign</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1">Campaign Name</label>
              <input
                type="text"
                value={newCampaign.name}
                onChange={(e) => setNewCampaign({ ...newCampaign, name: e.target.value })}
                placeholder="e.g., Holiday Special"
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-card-foreground mb-1">Message</label>
              <textarea
                value={newCampaign.message}
                onChange={(e) => setNewCampaign({ ...newCampaign, message: e.target.value })}
                placeholder="Enter your SMS message..."
                className="input w-full h-24"
                maxLength={160}
              />
              <p className="text-xs text-muted-foreground mt-1">{newCampaign.message.length}/160 characters</p>
            </div>
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={newCampaign.all_customers}
                  onChange={(e) => setNewCampaign({ ...newCampaign, all_customers: e.target.checked })}
                  className="rounded"
                />
                <span className="text-sm text-card-foreground">Send to all customers</span>
              </label>
            </div>
            <div className="flex gap-2">
              <button onClick={createCampaign} className="btn btn-primary">Create</button>
              <button onClick={() => setShowCreate(false)} className="btn btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : campaigns.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No campaigns yet</h3>
          <p className="text-muted-foreground">Create your first SMS campaign to engage with customers.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Campaign</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Message</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Recipients</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {campaigns.map((campaign) => (
                <tr key={campaign.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <div className="font-medium text-card-foreground">{campaign.name || 'Untitled'}</div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm text-card-foreground truncate max-w-xs">{campaign.message}</div>
                  </td>
                  <td className="p-4 text-card-foreground">{campaign.recipient_count}</td>
                  <td className="p-4">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${statusColors[campaign.status]}`}>
                      {campaign.status}
                    </span>
                  </td>
                  <td className="p-4 text-card-foreground text-sm">
                    {campaign.sent_at ? formatDate(campaign.sent_at) : formatDate(campaign.created_at)}
                  </td>
                  <td className="p-4">
                    <div className="flex gap-2">
                      {campaign.status === 'draft' && (
                        <>
                          <button
                            onClick={() => sendCampaign(campaign.id)}
                            disabled={sending === campaign.id}
                            className="text-sm text-primary hover:underline disabled:opacity-50"
                          >
                            {sending === campaign.id ? 'Sending...' : 'Send'}
                          </button>
                          <button
                            onClick={() => deleteCampaign(campaign.id)}
                            className="text-sm text-destructive hover:underline"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
