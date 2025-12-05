import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Appointment {
  id: string
  customer_name: string
  customer_phone: string
  customer_email?: string
  service_name?: string
  staff_name?: string
  date: string
  time: string
  duration_minutes: number
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  notes?: string
  created_at?: string
}

const statusColors: Record<string, string> = {
  scheduled: 'bg-blue-100 text-blue-800',
  confirmed: 'bg-green-100 text-green-800',
  completed: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-red-100 text-red-800',
  no_show: 'bg-yellow-100 text-yellow-800',
}

export default function Appointments() {
  const { business } = useAuth()
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [dateFilter, setDateFilter] = useState<string>('')
  const [searchName, setSearchName] = useState<string>('')

  useEffect(() => {
    if (business?.id) {
      loadAppointments()
    }
  }, [business?.id, filter, dateFilter])

  const loadAppointments = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      let url = `/admin/${business.id}/appointments?limit=50`
      if (filter) url += `&status=${filter}`
      if (dateFilter) url += `&date_from=${dateFilter}`
      const data = await api.get<Appointment[]>(url)
      setAppointments(data)
    } catch (error) {
      console.error('Failed to load appointments:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateStatus = async (appointmentId: string, newStatus: string) => {
    if (!business?.id) return
    try {
      await api.post(`/admin/${business.id}/appointments/${appointmentId}/status?status=${newStatus}`)
      loadAppointments()
    } catch (error) {
      console.error('Failed to update status:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':')
    const hour = parseInt(hours)
    const ampm = hour >= 12 ? 'PM' : 'AM'
    const hour12 = hour % 12 || 12
    return `${hour12}:${minutes} ${ampm}`
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
          <h1 className="text-2xl font-semibold text-card-foreground">Appointments</h1>
          <p className="text-muted-foreground mt-1">Manage your scheduled appointments</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search by name..."
            value={searchName}
            onChange={(e) => setSearchName(e.target.value)}
            className="input pl-9 w-48"
          />
        </div>
        
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input w-48"
        >
          <option value="">All Statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="confirmed">Confirmed</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
          <option value="no_show">No Show</option>
        </select>

        <input
          type="date"
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
          className="input w-48"
        />
        
        {(filter || dateFilter || searchName) && (
          <button
            onClick={() => { setFilter(''); setDateFilter(''); setSearchName('') }}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Clear filters
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : appointments.filter(apt => 
          !searchName || apt.customer_name.toLowerCase().includes(searchName.toLowerCase())
        ).length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No appointments yet</h3>
          <p className="text-muted-foreground">Appointments booked through the chatbot will appear here.</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Customer</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Service</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Date & Time</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Staff</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {appointments.filter(apt => 
                !searchName || apt.customer_name.toLowerCase().includes(searchName.toLowerCase())
              ).map((apt) => (
                <tr key={apt.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <div className="font-medium text-card-foreground">{apt.customer_name}</div>
                    <div className="text-sm text-muted-foreground">{apt.customer_phone}</div>
                  </td>
                  <td className="p-4">
                    <div className="text-card-foreground">{apt.service_name || '-'}</div>
                    <div className="text-sm text-muted-foreground">{apt.duration_minutes} min</div>
                  </td>
                  <td className="p-4">
                    <div className="text-card-foreground">{formatDate(apt.date)}</div>
                    <div className="text-sm text-muted-foreground">{formatTime(apt.time)}</div>
                  </td>
                  <td className="p-4 text-card-foreground">{apt.staff_name || '-'}</td>
                  <td className="p-4">
                    <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${statusColors[apt.status]}`}>
                      {apt.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-4">
                    <select
                      value={apt.status}
                      onChange={(e) => updateStatus(apt.id, e.target.value)}
                      className="text-sm border border-border rounded px-2 py-1 bg-background"
                    >
                      <option value="scheduled">Scheduled</option>
                      <option value="confirmed">Confirmed</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                      <option value="no_show">No Show</option>
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
