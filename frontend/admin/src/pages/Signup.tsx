import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const verticals = [
  { value: 'beauty', label: 'Beauty (Salon, Barber, Nail)' },
  { value: 'wellness', label: 'Wellness (Medspa, Massage, Chiro)' },
  { value: 'medical', label: 'Medical (Dental, Dermatology, Plastic Surgery)' },
  { value: 'fitness', label: 'Fitness (Gym, Yoga, Pilates)' },
]

export default function Signup() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<'admin' | 'business_owner'>('business_owner')
  const [businessName, setBusinessName] = useState('')
  const [businessType, setBusinessType] = useState('beauty')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { signup } = useAuth()
  const navigate = useNavigate()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      await signup({
        username,
        email: email || undefined,
        role,
        business_name: role === 'business_owner' ? businessName : undefined,
        business_type: role === 'business_owner' ? businessType : undefined,
      })
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-4">
            <svg className="w-6 h-6 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold text-card-foreground">Create account</h1>
          <p className="text-muted-foreground mt-2">Get started with Keystone AI Receptionist</p>
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg text-sm">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1.5">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              placeholder="Choose a username"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1.5">
              Email (optional)
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field"
              placeholder="your@email.com"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-card-foreground mb-1.5">
              Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'admin' | 'business_owner')}
              className="input-field"
            >
              <option value="business_owner">Business Owner</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          
          {role === 'business_owner' && (
            <>
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">
                  Business Name
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  className="input-field"
                  placeholder="Your business name"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-card-foreground mb-1.5">
                  Business Type
                </label>
                <select
                  value={businessType}
                  onChange={(e) => setBusinessType(e.target.value)}
                  className="input-field"
                >
                  {verticals.map((v) => (
                    <option key={v.value} value={v.value}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </div>
            </>
          )}
          
          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-3 disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        
        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link to="/login" className="text-primary hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
