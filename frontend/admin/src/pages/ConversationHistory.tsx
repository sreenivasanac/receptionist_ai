import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Message {
  role: string
  content: string
  timestamp: string
}

interface Conversation {
  id: string
  session_id: string
  messages: Message[]
  customer_info: {
    first_name?: string
    phone?: string
    email?: string
  }
  message_count: number
  preview: string
  last_message: string
  created_at: string
  updated_at: string
}

interface ConversationsResponse {
  conversations: Conversation[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export default function ConversationHistory() {
  const { business } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const limit = 20

  const fetchConversations = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.set('query', searchQuery)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      params.set('limit', limit.toString())
      params.set('offset', (page * limit).toString())
      
      const data = await api.get<ConversationsResponse>(
        `/conversations/${business.id}?${params.toString()}`
      )
      setConversations(data.conversations)
      setTotal(data.total)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConversations()
  }, [business?.id, page])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(0)
    fetchConversations()
  }

  const handleExport = async (format: 'json' | 'csv') => {
    if (!business?.id) return
    try {
      const params = new URLSearchParams()
      params.set('format', format)
      if (startDate) params.set('start_date', startDate)
      if (endDate) params.set('end_date', endDate)
      
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/conversations/${business.id}/export/all?${params.toString()}`
      )
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `conversations_export.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Conversation History</h1>
          <p className="text-muted-foreground mt-1">View and search chat transcripts</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleExport('csv')}
            className="btn btn-secondary text-sm"
          >
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className="btn btn-secondary text-sm"
          >
            Export JSON
          </button>
        </div>
      </div>

      <form onSubmit={handleSearch} className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-muted-foreground mb-1">Search</label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search messages..."
              className="input w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">From</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-muted-foreground mb-1">To</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input"
            />
          </div>
          <div className="flex items-end">
            <button type="submit" className="btn btn-primary">
              Search
            </button>
          </div>
        </div>
      </form>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-medium text-card-foreground mb-4">
            Conversations ({total})
          </h2>
          
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : conversations.length === 0 ? (
            <p className="text-muted-foreground py-8 text-center">No conversations found</p>
          ) : (
            <div className="space-y-2">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConversation(conv)}
                  className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedConversation?.id === conv.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-card-foreground">
                      {conv.customer_info?.first_name || 'Anonymous'}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatDate(conv.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground truncate">{conv.preview}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span>{conv.message_count} messages</span>
                    {conv.customer_info?.phone && (
                      <span>| {conv.customer_info.phone}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {total > limit && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="btn btn-secondary text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <span className="text-sm text-muted-foreground">
                Page {page + 1} of {Math.ceil(total / limit)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={(page + 1) * limit >= total}
                className="btn btn-secondary text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-medium text-card-foreground mb-4">
            Transcript
          </h2>
          
          {selectedConversation ? (
            <div className="space-y-4">
              <div className="pb-4 border-b border-border">
                <div className="text-sm text-muted-foreground">
                  <p>Session: {selectedConversation.session_id.slice(0, 8)}...</p>
                  <p>Started: {formatDate(selectedConversation.created_at)}</p>
                  {selectedConversation.customer_info?.phone && (
                    <p>Phone: {selectedConversation.customer_info.phone}</p>
                  )}
                  {selectedConversation.customer_info?.email && (
                    <p>Email: {selectedConversation.customer_info.email}</p>
                  )}
                </div>
              </div>
              
              <div className="space-y-4 max-h-[500px] overflow-y-auto">
                {selectedConversation.messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary text-secondary-foreground'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground text-center py-8">
              Select a conversation to view the transcript
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
