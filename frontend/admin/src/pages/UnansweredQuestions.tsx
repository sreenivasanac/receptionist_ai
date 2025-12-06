import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface UnansweredQuestion {
  id: string
  question_text: string
  category: string | null
  occurrence_count: number
  last_asked_at: string | null
  suggested_answer: string | null
  is_resolved: boolean
  created_at: string
}

interface QuestionsResponse {
  questions: UnansweredQuestion[]
  total: number
  categories: Record<string, { count: number; occurrences: number }>
}

const CATEGORIES = ['services', 'pricing', 'hours', 'policies', 'booking', 'other']

export default function UnansweredQuestions() {
  const { business } = useAuth()
  const [data, setData] = useState<QuestionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('')
  const [showResolved, setShowResolved] = useState(false)
  const [selectedQuestion, setSelectedQuestion] = useState<UnansweredQuestion | null>(null)
  const [answerText, setAnswerText] = useState('')
  const [addToFaq, setAddToFaq] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (business?.id) {
      loadQuestions()
    }
  }, [business?.id, filter, showResolved])

  const loadQuestions = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      let url = `/insights/${business.id}/unanswered?limit=100`
      if (filter) url += `&category=${filter}`
      if (showResolved) url += `&resolved=true`
      else url += `&resolved=false`
      
      const response = await api.get<QuestionsResponse>(url)
      setData(response)
    } catch (error) {
      console.error('Failed to load unanswered questions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleResolve = async () => {
    if (!business?.id || !selectedQuestion || !answerText.trim()) return

    setSaving(true)
    setMessage('')
    try {
      await api.put(`/insights/${business.id}/unanswered/${selectedQuestion.id}/resolve`, {
        answer: answerText,
        add_to_faq: addToFaq
      })
      setMessage(addToFaq ? 'Question resolved and added to FAQs!' : 'Question resolved!')
      setSelectedQuestion(null)
      setAnswerText('')
      await loadQuestions()
    } catch (error) {
      console.error('Failed to resolve question:', error)
      setMessage('Failed to resolve question')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (questionId: string) => {
    if (!business?.id || !confirm('Delete this question?')) return

    try {
      await api.delete(`/insights/${business.id}/unanswered/${questionId}`)
      await loadQuestions()
    } catch (error) {
      console.error('Failed to delete question:', error)
    }
  }

  const handleCategoryChange = async (questionId: string, category: string) => {
    if (!business?.id) return

    try {
      await api.put(`/insights/${business.id}/unanswered/${questionId}/category`, { category })
      await loadQuestions()
    } catch (error) {
      console.error('Failed to update category:', error)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  }

  if (!business) {
    return (
      <div className="p-8">
        <div className="card text-center py-12">
          <p className="text-muted-foreground">No business configured.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Unanswered Questions</h1>
          <p className="text-muted-foreground mt-1">Questions your AI couldn't answer confidently</p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 mb-6">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-purple-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-medium text-purple-900">Improve Your AI Receptionist</h3>
            <p className="text-sm text-purple-700 mt-1">
              These are questions customers asked that your AI couldn't answer. Review them to identify 
              gaps in your business information. Resolve questions by providing answers, which can be 
              automatically added to your FAQs.
            </p>
          </div>
        </div>
      </div>

      {message && (
        <div className={`mb-4 p-3 rounded-lg ${
          message.includes('Failed') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          {message}
        </div>
      )}

      {/* Category Stats */}
      {data && Object.keys(data.categories).length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 mb-6">
          {Object.entries(data.categories).map(([cat, stats]) => (
            <button
              key={cat}
              onClick={() => setFilter(filter === cat ? '' : cat)}
              className={`p-3 rounded-lg border text-left transition-colors ${
                filter === cat 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <p className="text-xs text-muted-foreground capitalize">{cat}</p>
              <p className="text-lg font-semibold text-card-foreground">{stats.count}</p>
              <p className="text-xs text-muted-foreground">{stats.occurrences} asks</p>
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input w-48"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map(cat => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showResolved}
            onChange={(e) => setShowResolved(e.target.checked)}
            className="w-4 h-4 rounded border-border text-primary"
          />
          <span className="text-sm text-card-foreground">Show resolved</span>
        </label>

        {filter && (
          <button
            onClick={() => setFilter('')}
            className="text-sm text-muted-foreground hover:text-card-foreground"
          >
            Clear filter
          </button>
        )}
      </div>

      {loading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : !data || data.questions.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-card-foreground mb-2">
            {showResolved ? 'No resolved questions' : 'No unanswered questions!'}
          </h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            {showResolved 
              ? 'Questions you resolve will appear here.'
              : 'Your AI receptionist is handling all customer questions. Great job on your business setup!'}
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Question</th>
                <th className="text-left p-4 font-medium text-muted-foreground w-24">Asked</th>
                <th className="text-left p-4 font-medium text-muted-foreground w-32">Category</th>
                <th className="text-left p-4 font-medium text-muted-foreground w-32">Last Asked</th>
                <th className="text-left p-4 font-medium text-muted-foreground w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data.questions.map((q) => (
                <tr key={q.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <p className="text-card-foreground">{q.question_text}</p>
                    {q.is_resolved && q.suggested_answer && (
                      <p className="text-sm text-green-600 mt-1">
                        <span className="font-medium">Answer:</span> {q.suggested_answer}
                      </p>
                    )}
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center justify-center w-8 h-8 bg-primary/10 text-primary rounded-full font-semibold">
                      {q.occurrence_count}
                    </span>
                  </td>
                  <td className="p-4">
                    <select
                      value={q.category || ''}
                      onChange={(e) => handleCategoryChange(q.id, e.target.value)}
                      className="text-sm border border-border rounded px-2 py-1 bg-background w-full"
                      disabled={q.is_resolved}
                    >
                      <option value="">Uncategorized</option>
                      {CATEGORIES.map(cat => (
                        <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
                      ))}
                    </select>
                  </td>
                  <td className="p-4 text-sm text-muted-foreground">
                    {formatDate(q.last_asked_at)}
                  </td>
                  <td className="p-4">
                    {q.is_resolved ? (
                      <span className="text-green-600 text-sm font-medium">Resolved</span>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedQuestion(q)
                            setAnswerText('')
                          }}
                          className="text-sm text-primary hover:underline"
                        >
                          Answer
                        </button>
                        <button
                          onClick={() => handleDelete(q.id)}
                          className="text-sm text-red-600 hover:underline"
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Answer Modal */}
      {selectedQuestion && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-semibold text-card-foreground">Answer Question</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Provide an answer to resolve this question
              </p>
            </div>

            <div className="p-6 space-y-4">
              <div className="bg-secondary/50 rounded-lg p-4">
                <p className="text-sm text-muted-foreground mb-1">Customer asked:</p>
                <p className="font-medium text-card-foreground">"{selectedQuestion.question_text}"</p>
                <p className="text-xs text-muted-foreground mt-2">
                  Asked {selectedQuestion.occurrence_count} time(s)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">Your Answer *</label>
                <textarea
                  value={answerText}
                  onChange={(e) => setAnswerText(e.target.value)}
                  className="input-field min-h-[120px]"
                  placeholder="Type your answer here..."
                  autoFocus
                />
              </div>

              <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-secondary/30">
                <input
                  type="checkbox"
                  checked={addToFaq}
                  onChange={(e) => setAddToFaq(e.target.checked)}
                  className="w-4 h-4 rounded border-border text-primary"
                />
                <div>
                  <p className="text-sm font-medium text-card-foreground">Add to FAQs</p>
                  <p className="text-xs text-muted-foreground">
                    Save this Q&A to your FAQ list so the AI can answer similar questions
                  </p>
                </div>
              </label>

              <div className="flex gap-3 justify-end pt-4 border-t border-border">
                <button 
                  onClick={() => setSelectedQuestion(null)} 
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleResolve}
                  disabled={saving || !answerText.trim()}
                  className="btn-primary disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Resolve Question'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
