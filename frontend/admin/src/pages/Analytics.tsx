import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface AnalyticsSummary {
  total_leads: number
  total_appointments: number
  total_conversations: number
  total_customers: number
  conversion_rate: number
  leads_this_period: number
  appointments_this_period: number
  conversations_this_period: number
}

interface LeadStats {
  total: number
  by_status: Record<string, number>
  by_source: Record<string, number>
  by_day: Array<{ date: string; count: number }>
  conversion_rate: number
}

interface AppointmentStats {
  total: number
  by_status: Record<string, number>
  by_service: Array<{ service: string; count: number }>
  by_day: Array<{ date: string; count: number }>
  completion_rate: number
}

interface ConversationStats {
  total: number
  avg_message_count: number
  by_day: Array<{ date: string; count: number }>
  peak_hours: Array<{ hour: string; count: number }>
}

interface OverviewResponse {
  period: string
  summary: AnalyticsSummary
  leads: LeadStats
  appointments: AppointmentStats
  conversations: ConversationStats
  waitlist: {
    total: number
    conversion_rate: number
    booked: number
    waiting: number
  }
}

const periods = [
  { value: 'today', label: 'Today' },
  { value: 'this_week', label: 'This Week' },
  { value: 'this_month', label: 'This Month' },
  { value: 'last_30_days', label: 'Last 30 Days' },
  { value: 'last_90_days', label: 'Last 90 Days' },
]

export default function Analytics() {
  const { business } = useAuth()
  const [period, setPeriod] = useState('last_30_days')
  const [data, setData] = useState<OverviewResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAnalytics = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      const response = await api.get<OverviewResponse>(
        `/analytics/overview/${business.id}?period=${period}`
      )
      setData(response)
    } catch (error) {
      console.error('Failed to fetch analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnalytics()
  }, [business?.id, period])

  if (!business) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Please set up your business first.</p>
      </div>
    )
  }

  const StatCard = ({ title, value, subtitle, trend, color = 'primary' }: {
    title: string
    value: string | number
    subtitle?: string
    trend?: string
    color?: 'primary' | 'green' | 'blue' | 'purple'
  }) => {
    const colors = {
      primary: 'bg-primary/10 text-primary',
      green: 'bg-green-500/10 text-green-600',
      blue: 'bg-blue-500/10 text-blue-600',
      purple: 'bg-purple-500/10 text-purple-600'
    }
    
    return (
      <div className="card">
        <div className="flex items-center gap-4">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colors[color]}`}>
            <span className="text-xl font-bold">{typeof value === 'number' ? value : '#'}</span>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-semibold text-card-foreground">{value}</p>
            {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
            {trend && <p className="text-xs text-green-600">{trend}</p>}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Analytics</h1>
          <p className="text-muted-foreground mt-1">Business performance insights</p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="input"
        >
          {periods.map(p => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Conversations"
              value={data.summary.total_conversations}
              subtitle={`${data.summary.conversations_this_period} this period`}
              color="primary"
            />
            <StatCard
              title="Total Leads"
              value={data.summary.total_leads}
              subtitle={`${data.summary.leads_this_period} this period`}
              color="blue"
            />
            <StatCard
              title="Appointments"
              value={data.summary.total_appointments}
              subtitle={`${data.summary.appointments_this_period} this period`}
              color="green"
            />
            <StatCard
              title="Conversion Rate"
              value={`${data.summary.conversion_rate}%`}
              subtitle="Leads to customers"
              color="purple"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Lead Status</h2>
              <div className="space-y-3">
                {Object.entries(data.leads.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        status === 'new' ? 'bg-blue-500' :
                        status === 'contacted' ? 'bg-yellow-500' :
                        status === 'converted' ? 'bg-green-500' :
                        status === 'lost' ? 'bg-red-500' : 'bg-gray-500'
                      }`} />
                      <span className="text-sm text-card-foreground capitalize">{status}</span>
                    </div>
                    <span className="text-sm font-medium text-card-foreground">{count}</span>
                  </div>
                ))}
                {Object.keys(data.leads.by_status).length === 0 && (
                  <p className="text-sm text-muted-foreground">No leads yet</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Appointment Status</h2>
              <div className="space-y-3">
                {Object.entries(data.appointments.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${
                        status === 'scheduled' ? 'bg-blue-500' :
                        status === 'completed' ? 'bg-green-500' :
                        status === 'cancelled' ? 'bg-red-500' :
                        status === 'no_show' ? 'bg-orange-500' : 'bg-gray-500'
                      }`} />
                      <span className="text-sm text-card-foreground capitalize">{status.replace('_', ' ')}</span>
                    </div>
                    <span className="text-sm font-medium text-card-foreground">{count}</span>
                  </div>
                ))}
                {Object.keys(data.appointments.by_status).length === 0 && (
                  <p className="text-sm text-muted-foreground">No appointments yet</p>
                )}
              </div>
              <div className="mt-4 pt-4 border-t border-border">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Completion Rate</span>
                  <span className="font-medium text-card-foreground">{data.appointments.completion_rate}%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Top Services</h2>
              <div className="space-y-3">
                {data.appointments.by_service.slice(0, 5).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm text-card-foreground">{item.service}</span>
                    <span className="text-sm font-medium text-card-foreground">{item.count} bookings</span>
                  </div>
                ))}
                {data.appointments.by_service.length === 0 && (
                  <p className="text-sm text-muted-foreground">No service data yet</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Peak Hours</h2>
              <div className="space-y-3">
                {data.conversations.peak_hours.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-sm text-card-foreground">{item.hour}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-secondary rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary rounded-full"
                          style={{ 
                            width: `${Math.min(100, (item.count / (data.conversations.peak_hours[0]?.count || 1)) * 100)}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium text-card-foreground w-8">{item.count}</span>
                    </div>
                  </div>
                ))}
                {data.conversations.peak_hours.length === 0 && (
                  <p className="text-sm text-muted-foreground">No conversation data yet</p>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Conversation Metrics</h2>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Total Conversations</span>
                  <span className="font-medium text-card-foreground">{data.conversations.total}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Avg. Messages per Chat</span>
                  <span className="font-medium text-card-foreground">{data.conversations.avg_message_count}</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Waitlist</h2>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Currently Waiting</span>
                  <span className="font-medium text-card-foreground">{data.waitlist.waiting}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Booked from Waitlist</span>
                  <span className="font-medium text-card-foreground">{data.waitlist.booked}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Conversion Rate</span>
                  <span className="font-medium text-card-foreground">{data.waitlist.conversion_rate}%</span>
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-medium text-card-foreground mb-4">Lead Sources</h2>
              <div className="space-y-3">
                {Object.entries(data.leads.by_source).map(([source, count]) => (
                  <div key={source} className="flex items-center justify-between">
                    <span className="text-sm text-card-foreground capitalize">{source}</span>
                    <span className="text-sm font-medium text-card-foreground">{count}</span>
                  </div>
                ))}
                {Object.keys(data.leads.by_source).length === 0 && (
                  <p className="text-sm text-muted-foreground">No lead sources yet</p>
                )}
              </div>
            </div>
          </div>
        </>
      ) : (
        <p className="text-muted-foreground text-center py-8">Failed to load analytics</p>
      )}
    </div>
  )
}
