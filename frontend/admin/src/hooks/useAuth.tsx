import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../services/api'

interface User {
  id: string
  username: string
  email?: string
  role: string
  business_id?: string
}

interface Business {
  id: string
  name: string
  type: string
  address?: string
  phone?: string
  email?: string
  website?: string
  features_enabled: Record<string, boolean>
}

interface AuthContextType {
  user: User | null
  business: Business | null
  loading: boolean
  login: (username: string, role: string) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => void
}

interface SignupData {
  username: string
  email?: string
  role: string
  business_name?: string
  business_type?: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [business, setBusiness] = useState<Business | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    const storedUser = localStorage.getItem('keystone_user')
    const storedBusiness = localStorage.getItem('keystone_business')
    
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
    if (storedBusiness) {
      setBusiness(JSON.parse(storedBusiness))
    }
    setLoading(false)
  }, [])
  
  const login = async (username: string, role: string) => {
    const response = await api.post<{
      user_id: string
      username: string
      email?: string
      role: string
      business_id?: string
      business?: Business
    }>('/auth/login', { username, role })
    
    const userObj: User = {
      id: response.user_id,
      username: response.username,
      email: response.email,
      role: response.role,
      business_id: response.business_id,
    }
    
    setUser(userObj)
    localStorage.setItem('keystone_user', JSON.stringify(userObj))
    
    if (response.business) {
      setBusiness(response.business)
      localStorage.setItem('keystone_business', JSON.stringify(response.business))
    }
  }
  
  const signup = async (data: SignupData) => {
    await api.post('/auth/signup', data)
    await login(data.username, data.role)
  }
  
  const logout = () => {
    setUser(null)
    setBusiness(null)
    localStorage.removeItem('keystone_user')
    localStorage.removeItem('keystone_business')
  }
  
  return (
    <AuthContext.Provider value={{ user, business, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
