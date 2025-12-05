import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface WaitlistEntry {
  id: string
  customer_name: string
  customer_contact: string
  service_name?: string
  preferred_dates: string[]
  preferred_times: string[]
  contact_method: 'phone' | 'email' | 'sms'
  status: 'waiting' | 'notified' | 'booked' | 'expired' | 'cancelled'
  notes?: string
  created_at?: string
}

const statusColors: Record<string, string> = {
  waiting: 'bg-blue-100 text-blue-800',
  notified: 'bg-yellow-100 text-yellow-800',
  booked: 'bg-green-100 text-green-800',
  expired: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-red-100 text-red-800',
}

export default function Waitlist() {
  const { business } = useAuth()
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('waiting')

  useEffect(() => {
    if (business?.id) {
      loadWaitlist()
    }
  }, [business?.id, filter])

  const loadWaitlist = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      let url = `/admin/${business.id}/waitlist?limit=50`
      if (filter) url += `&status=${filter}`
      const data = await api.get<WaitlistEntry[]>(url)
      setEntries(data)
    } catch (error) {
      console.error('Failed to load waitlist:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (entryId: string, newStatus: string) => {
    if (!business?.id) return
    try {
      await api.put(`/admin/${business.id}/waitlist/${entryId}`, { status: newStatus })
      loadWaitlist()
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
          <h1 className="text-2xl font-semibold text-card-foreground">Waitlist</h1>
          <p className="text-muted-foreground mt-1">{business?.name ? `${business.name}'s` : 'Your'} waiting customers</p>
        </div>
      </div>

      <div className="flex gap-4 mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input w-48"
        >
          <option value="">All Statuses</option>
          <option value="waiting">Waiting</option>
          <option value="notified">Notified</option>
          <option value="booked">Booked</option>
          <option value="expired">Expired</option>
          <option value="cancelled">Cancelled</option>
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
      ) : entries.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No waitlist entries</h3>
          <p className="text-muted-foreground">Customers added to the waitlist through the chatbot will appear here.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Customer</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Service</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Preferences</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Contact</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Added</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {entries.map((entry) => (
                <tr key={entry.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <div className="font-medium text-card-foreground">{entry.customer_name}</div>
                  </td>
                  <td className="p-4 text-card-foreground">{entry.service_name || '-'}</td>
                  <td className="p-4">
                    <div className="text-sm text-card-foreground">
                      {entry.preferred_dates.length > 0 && (
                        <div>Dates: {entry.preferred_dates.join(', ')}</div>
                      )}
                      {entry.preferred_times.length > 0 && (
                        <div className="text-muted-foreground">Times: {entry.preferred_times.join(', ')}</div>
                      )}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm text-card-foreground">{entry.customer_contact}</div>
                    <div className="text-xs text-muted-foreground capitalize">{entry.contact_method}</div>
                  </td>
                  <td className="p-4 text-card-foreground">{formatDate(entry.created_at)}</td>
                  <td className="p-4">
                    <select
                      value={entry.status}
                      onChange={(e) => updateStatus(entry.id, e.target.value)}
                      className={`text-sm border-0 rounded px-2 py-1 font-medium ${statusColors[entry.status]}`}
                    >
                      <option value="waiting">Waiting</option>
                      <option value="notified">Notified</option>
                      <option value="booked">Booked</option>
                      <option value="expired">Expired</option>
                      <option value="cancelled">Cancelled</option>
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
