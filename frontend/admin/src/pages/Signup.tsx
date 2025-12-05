import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../components/auth/AuthLayout'

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
    <AuthLayout title="Create account" subtitle="Get started with Keystone AI Receptionist">
      {error && (
        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 text-destructive rounded-lg text-sm">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
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
            Email
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
    </AuthLayout>
  )
}
