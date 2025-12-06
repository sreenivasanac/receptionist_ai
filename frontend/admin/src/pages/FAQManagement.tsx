import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface FAQ {
  question: string
  answer: string
}

export default function FAQManagement() {
  const { business } = useAuth()
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [formData, setFormData] = useState({ question: '', answer: '' })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (business?.id) {
      loadFAQs()
    }
  }, [business?.id])

  const loadFAQs = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      const data = await api.get<FAQ[]>(`/admin/${business.id}/faqs`)
      setFaqs(data)
    } catch (error) {
      console.error('Failed to load FAQs:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!business?.id || !formData.question.trim() || !formData.answer.trim()) return

    setSaving(true)
    setMessage('')
    try {
      if (editingIndex !== null) {
        await api.put(`/admin/${business.id}/faqs/${editingIndex}`, formData)
        setMessage('FAQ updated successfully')
      } else {
        await api.post(`/admin/${business.id}/faqs`, formData)
        setMessage('FAQ added successfully')
      }
      await loadFAQs()
      closeModal()
    } catch (error) {
      console.error('Failed to save FAQ:', error)
      setMessage('Failed to save FAQ')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (index: number) => {
    if (!business?.id || !confirm('Are you sure you want to delete this FAQ?')) return

    try {
      await api.delete(`/admin/${business.id}/faqs/${index}`)
      await loadFAQs()
      setMessage('FAQ deleted')
    } catch (error) {
      console.error('Failed to delete FAQ:', error)
    }
  }

  const openModal = (index?: number) => {
    if (index !== undefined) {
      setEditingIndex(index)
      setFormData({ question: faqs[index].question, answer: faqs[index].answer })
    } else {
      setEditingIndex(null)
      setFormData({ question: '', answer: '' })
    }
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingIndex(null)
    setFormData({ question: '', answer: '' })
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
          <h1 className="text-2xl font-semibold text-card-foreground">FAQ Management</h1>
          <p className="text-muted-foreground mt-1">Manage frequently asked questions for your AI receptionist</p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add FAQ
        </button>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-medium text-blue-900">How FAQs are used</h3>
            <p className="text-sm text-blue-700 mt-1">
              Your AI receptionist uses these FAQs to answer customer questions accurately. 
              Add common questions about your business policies, services, and procedures.
              The AI will search through these when customers ask similar questions.
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

      {loading ? (
        <div className="card flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : faqs.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-card-foreground mb-2">No FAQs yet</h3>
          <p className="text-muted-foreground mb-4 max-w-md mx-auto">
            Add frequently asked questions to help your AI receptionist answer customer inquiries accurately.
          </p>
          <button onClick={() => openModal()} className="btn-primary">
            Add Your First FAQ
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="card hover:border-primary/30 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center text-xs font-medium text-primary">
                      {index + 1}
                    </span>
                    <h3 className="font-medium text-card-foreground">{faq.question}</h3>
                  </div>
                  <p className="text-muted-foreground text-sm ml-8">{faq.answer}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => openModal(index)}
                    className="px-3 py-1.5 text-sm font-medium text-primary bg-primary/5 rounded-lg hover:bg-primary/10 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(index)}
                    className="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-6 border-b border-border">
              <h2 className="text-xl font-semibold text-card-foreground">
                {editingIndex !== null ? 'Edit FAQ' : 'Add FAQ'}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                {editingIndex !== null ? 'Update this FAQ entry' : 'Add a new frequently asked question'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">Question *</label>
                <input
                  type="text"
                  value={formData.question}
                  onChange={(e) => setFormData({ ...formData, question: e.target.value })}
                  className="input-field"
                  placeholder="e.g., Do you accept walk-ins?"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">Answer *</label>
                <textarea
                  value={formData.answer}
                  onChange={(e) => setFormData({ ...formData, answer: e.target.value })}
                  className="input-field min-h-[100px]"
                  placeholder="e.g., Yes, we welcome walk-ins! However, we recommend booking an appointment to guarantee availability."
                  required
                />
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-border">
                <button type="button" onClick={closeModal} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50">
                  {saving ? 'Saving...' : editingIndex !== null ? 'Update' : 'Add FAQ'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
