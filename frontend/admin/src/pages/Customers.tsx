import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface Customer {
  id: string
  first_name: string
  last_name?: string
  email?: string
  phone?: string
  visit_count: number
  last_visit_date?: string
  favorite_service_name?: string
  notes?: string
  created_at?: string
}

export default function Customers() {
  const { business } = useAuth()
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [totalCount, setTotalCount] = useState(0)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{ imported: number; skipped: number; errors: string[] } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (business?.id) {
      loadCustomers()
      loadCount()
    }
  }, [business?.id])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (business?.id) loadCustomers()
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  const loadCustomers = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      let url = `/admin/${business.id}/customers?limit=50`
      if (search) url += `&search=${encodeURIComponent(search)}`
      const data = await api.get<Customer[]>(url)
      setCustomers(data)
    } catch (error) {
      console.error('Failed to load customers:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCount = async () => {
    if (!business?.id) return
    try {
      const data = await api.get<{ count: number }>(`/admin/${business.id}/customers/count`)
      setTotalCount(data.count)
    } catch (error) {
      console.error('Failed to load count:', error)
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !business?.id) return

    setImporting(true)
    setImportResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/admin/${business.id}/customers/import`,
        {
          method: 'POST',
          body: formData,
        }
      )
      const result = await response.json()
      setImportResult(result)
      loadCustomers()
      loadCount()
    } catch (error) {
      console.error('Failed to import:', error)
      setImportResult({ imported: 0, skipped: 0, errors: ['Failed to upload file'] })
    } finally {
      setImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
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
          <h1 className="text-2xl font-semibold text-card-foreground">Customers</h1>
          <p className="text-muted-foreground mt-1">{totalCount} total customers</p>
        </div>
        <div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
            className="btn btn-secondary"
          >
            {importing ? 'Importing...' : 'Import CSV'}
          </button>
        </div>
      </div>

      {importResult && (
        <div className={`mb-6 p-4 rounded-lg ${importResult.errors.length > 0 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
          <p className="font-medium">
            Imported {importResult.imported} customers, skipped {importResult.skipped}
          </p>
          {importResult.errors.length > 0 && (
            <ul className="mt-2 text-sm text-yellow-700">
              {importResult.errors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          )}
          <button 
            onClick={() => setImportResult(null)} 
            className="text-sm text-muted-foreground mt-2 hover:underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search by name, email, or phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input w-80"
        />
      </div>

      <div className="text-sm text-muted-foreground mb-4">
        CSV format: first_name, last_name, email, mobile_number
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : customers.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-muted-foreground mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <h3 className="text-lg font-medium text-card-foreground mb-2">
            {search ? 'No customers found' : 'No customers yet'}
          </h3>
          <p className="text-muted-foreground">
            {search ? 'Try a different search term' : 'Import a CSV or customers will be added through bookings'}
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 font-medium text-muted-foreground">Customer</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Contact</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Visits</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Last Visit</th>
                <th className="text-left p-4 font-medium text-muted-foreground">Favorite Service</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {customers.map((customer) => (
                <tr key={customer.id} className="hover:bg-muted/30">
                  <td className="p-4">
                    <div className="font-medium text-card-foreground">
                      {customer.first_name} {customer.last_name || ''}
                    </div>
                  </td>
                  <td className="p-4">
                    {customer.email && <div className="text-sm text-card-foreground">{customer.email}</div>}
                    {customer.phone && <div className="text-sm text-muted-foreground">{customer.phone}</div>}
                  </td>
                  <td className="p-4">
                    <span className="inline-flex items-center justify-center w-8 h-8 bg-primary/10 text-primary rounded-full font-medium">
                      {customer.visit_count}
                    </span>
                  </td>
                  <td className="p-4 text-card-foreground">{formatDate(customer.last_visit_date)}</td>
                  <td className="p-4 text-card-foreground">{customer.favorite_service_name || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
