import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Link } from 'react-router-dom'
import { api } from '../services/api'

interface DashboardStats {
  total_conversations: number
  total_appointments: number
  total_leads: number
  total_customers: number
}

interface UnansweredCount {
  total: number
}

export default function Dashboard() {
  const { user, business } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [newLeads, setNewLeads] = useState(0)
  const [unansweredCount, setUnansweredCount] = useState(0)
  
  useEffect(() => {
    if (business?.id) {
      loadStats()
      loadAlerts()
    }
  }, [business?.id])
  
  const loadStats = async () => {
    if (!business?.id) return
    try {
      const data = await api.get<{ summary: DashboardStats }>(`/analytics/summary/${business.id}`)
      setStats(data.summary)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }
  
  const loadAlerts = async () => {
    if (!business?.id) return
    try {
      // Load new leads count
      const leadsData = await api.get<Array<{ status: string }>>(`/admin/${business.id}/leads?status=new&limit=100`)
      setNewLeads(Array.isArray(leadsData) ? leadsData.length : 0)
      
      // Load unanswered questions count
      try {
        const unansweredData = await api.get<UnansweredCount>(`/insights/${business.id}/unanswered?resolved=false&limit=1`)
        setUnansweredCount(unansweredData.total || 0)
      } catch {
        // Insights endpoint may not exist yet
        setUnansweredCount(0)
      }
    } catch (error) {
      console.error('Failed to load alerts:', error)
    }
  }
  
  const quickActions = [
    {
      title: 'Configure Business',
      description: 'Set up hours, services, and policies',
      icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4',
      link: '/business',
      color: 'primary',
    },
    {
      title: 'Test Chatbot',
      description: 'Preview your AI receptionist',
      icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
      link: '/demo',
      color: 'green',
    },
    {
      title: 'View Appointments',
      description: 'Manage bookings and schedules',
      icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
      link: '/appointments',
      color: 'blue',
    },
    {
      title: 'View Analytics',
      description: 'Track performance and insights',
      icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      link: '/analytics',
      color: 'purple',
    },
  ]
  
  const moreActions = [
    { title: 'Customers', description: 'View customer database', link: '/customers', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
    { title: 'Leads', description: 'Track sales inquiries', link: '/leads', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
    { title: 'Question Gaps', description: 'Unanswered questions', link: '/insights', icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    { title: 'FAQs', description: 'Manage FAQ answers', link: '/faqs', icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
    { title: 'Workflows', description: 'Automate chat responses', link: '/workflows', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
    { title: 'SMS Marketing', description: 'Send campaigns', link: '/marketing', icon: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z' },
    { title: 'Conversations', description: 'View chat history', link: '/conversations', icon: 'M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z' },
    { title: 'Staff', description: 'Manage team members', link: '/staff', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
    { title: 'Waitlist', description: 'Manage waiting customers', link: '/waitlist', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
    { title: 'Settings', description: 'Embed code and features', link: '/settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
  ]
  
  const colorClasses: Record<string, string> = {
    primary: 'bg-primary/10 text-primary group-hover:bg-primary/15',
    green: 'bg-green-500/10 text-green-600 group-hover:bg-green-500/15',
    blue: 'bg-blue-500/10 text-blue-600 group-hover:bg-blue-500/15',
    purple: 'bg-purple-500/10 text-purple-600 group-hover:bg-purple-500/15',
  }
  
  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-card-foreground">
          Welcome back, {user?.username}!
        </h1>
        <p className="text-muted-foreground mt-1">
          {business ? `Managing ${business.name}` : 'Set up your business to get started'}
        </p>
      </div>
      
      {/* Alerts Section */}
      {business && (newLeads > 0 || unansweredCount > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {newLeads > 0 && (
            <Link to="/leads" className="flex items-center gap-4 p-4 bg-blue-50 border border-blue-200 rounded-xl hover:bg-blue-100 transition-colors">
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">{newLeads}</span>
              </div>
              <div>
                <p className="font-medium text-blue-900">New leads waiting</p>
                <p className="text-sm text-blue-700">Review and follow up on new inquiries</p>
              </div>
              <svg className="w-5 h-5 text-blue-500 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          )}
          {unansweredCount > 0 && (
            <Link to="/insights" className="flex items-center gap-4 p-4 bg-purple-50 border border-purple-200 rounded-xl hover:bg-purple-100 transition-colors">
              <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">{unansweredCount}</span>
              </div>
              <div>
                <p className="font-medium text-purple-900">Unanswered questions</p>
                <p className="text-sm text-purple-700">Review questions your AI couldn't answer</p>
              </div>
              <svg className="w-5 h-5 text-purple-500 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          )}
        </div>
      )}
      
      {business && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Link to="/conversations" className="card hover:border-primary transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Conversations</p>
                <p className="text-xl font-semibold text-card-foreground">{stats?.total_conversations ?? '-'}</p>
              </div>
            </div>
          </Link>
          
          <Link to="/appointments" className="card hover:border-blue-500 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500/10 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Appointments</p>
                <p className="text-xl font-semibold text-card-foreground">{stats?.total_appointments ?? '-'}</p>
              </div>
            </div>
          </Link>
          
          <Link to="/leads" className="card hover:border-purple-500 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-500/10 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Leads</p>
                <p className="text-xl font-semibold text-card-foreground">{stats?.total_leads ?? '-'}</p>
              </div>
            </div>
          </Link>
          
          <Link to="/customers" className="card hover:border-green-500 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Customers</p>
                <p className="text-xl font-semibold text-card-foreground">{stats?.total_customers ?? '-'}</p>
              </div>
            </div>
          </Link>
        </div>
      )}
      
      <h2 className="text-lg font-semibold text-card-foreground mb-4">Quick Actions</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {quickActions.map((action) => (
          <Link
            key={action.link}
            to={action.link}
            className="card-hover group"
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-colors ${colorClasses[action.color]}`}>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={action.icon} />
              </svg>
            </div>
            <h3 className="font-medium text-card-foreground group-hover:text-primary transition-colors">
              {action.title}
            </h3>
            <p className="text-sm text-muted-foreground mt-1">{action.description}</p>
          </Link>
        ))}
      </div>
      
      <h2 className="text-lg font-semibold text-card-foreground mb-4">All Features</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {moreActions.map((action) => (
          <Link
            key={action.link}
            to={action.link}
            className="card p-3 hover:border-primary transition-colors group text-center"
          >
            <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:bg-primary/10 transition-colors">
              <svg className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={action.icon} />
              </svg>
            </div>
            <p className="text-xs font-medium text-card-foreground group-hover:text-primary transition-colors">{action.title}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
