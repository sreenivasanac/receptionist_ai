import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Lead {
  id: string
  name: string
  email?: string
  phone?: string
  interest: string
  notes?: string
  company?: string
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost'
  source: string
  created_at?: string
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-purple-100 text-purple-800',
  converted: 'bg-green-100 text-green-800',
  lost: 'bg-red-100 text-red-800',
}

export default function Leads() {
  const { business } = useAuth()
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')

  useEffect(() => {
    if (business?.id) {
      loadLeads()
    }
  }, [business?.id, filter])

  const loadLeads = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      let url = `/admin/${business.id}/leads?limit=50`
      if (filter) url += `&status=${filter}`
      const data = await api.get<Lead[]>(url)
      setLeads(data)
    } catch (error) {
      console.error('Failed to load leads:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (leadId: string, newStatus: string) => {
    if (!business?.id) return
    try {
      await api.post(`/admin/${business.id}/leads/${leadId}/status?status=${newStatus}`)
      loadLeads()
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', day: 'numeric', year: 'numeric' 
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
          <h1 className="text-2xl font-semibold text-card-foreground">Leads</h1>
          <p className="text-muted-foreground mt-1">{business?.name ? `${business.name}'s` : 'Your'} sales leads</p>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-4 mb-6">
        {['new', 'contacted', 'qualified', 'converted', 'lost'].map((status) => {
          const count = leads.filter(l => l.status === status).length
          return (
            <div key={status} className="card text-center">
              <div className={`inline-flex px-2 py-1 rounded-full text-xs font-medium mb-2 ${statusColors[status]}`}>
                {status}
              </div>
              <div className="text-2xl font-semibold text-card-foreground">{count}</div>
            </div>
          )
        })}
      </div>

      <div className="flex gap-4 mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input w-48"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="qualified">Qualified</option>
          <option value="converted">Converted</option>
          <option value="lost">Lost</option>
        </select>
        
        {filter && (
          <button
            onClick={() => setFilter('')}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Clear filter
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : leads.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No leads yet</h3>
          <p className="text-muted-foreground">Leads captured through the chatbot will appear here.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Lead</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Interest</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Contact</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Source</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <div className="font-medium text-card-foreground">{lead.name}</div>
                    {lead.company && <div className="text-sm text-muted-foreground">{lead.company}</div>}
                  </td>
                  <td className="p-4">
                    <div className="text-card-foreground">{lead.interest}</div>
                    {lead.notes && <div className="text-sm text-muted-foreground truncate max-w-xs">{lead.notes}</div>}
                  </td>
                  <td className="p-4">
                    {lead.email && <div className="text-sm text-card-foreground">{lead.email}</div>}
                    {lead.phone && <div className="text-sm text-muted-foreground">{lead.phone}</div>}
                  </td>
                  <td className="p-4 text-card-foreground capitalize">{lead.source}</td>
                  <td className="p-4 text-card-foreground">{formatDate(lead.created_at)}</td>
                  <td className="p-4">
                    <select
                      value={lead.status}
                      onChange={(e) => updateStatus(lead.id, e.target.value)}
                      className={`text-sm border-0 rounded px-2 py-1 font-medium ${statusColors[lead.status]}`}
                    >
                      <option value="new">New</option>
                      <option value="contacted">Contacted</option>
                      <option value="qualified">Qualified</option>
                      <option value="converted">Converted</option>
                      <option value="lost">Lost</option>
                    </select>
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
