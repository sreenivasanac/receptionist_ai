import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../components/auth/AuthLayout'

export default function Login() {
  const [username, setUsername] = useState('')
  const [role, setRole] = useState<'admin' | 'business_owner'>('business_owner')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { login } = useAuth()
  const navigate = useNavigate()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      await login(username, role)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to manage your AI receptionist">
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
            placeholder="Enter your username"
            required
          />
          <p className="text-xs text-muted-foreground mt-1.5">
            Try <button type="button" onClick={() => setUsername('salon_sheela')} className="text-primary hover:underline font-medium">salon_sheela</button> to test
          </p>
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
        
        <button
          type="submit"
          disabled={loading}
          className="w-full btn-primary py-3 disabled:opacity-50"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
      
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don't have an account?{' '}
        <Link to="/signup" className="text-primary hover:underline font-medium">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  )
}
