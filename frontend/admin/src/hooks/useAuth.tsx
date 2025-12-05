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
    const response = await api.post('/auth/login', { username, role })
    const { user_id, business: bizData, ...userData } = response
    
    const userObj: User = {
      id: user_id,
      username: userData.username,
      email: userData.email,
      role: userData.role,
      business_id: userData.business_id,
    }
    
    setUser(userObj)
    localStorage.setItem('keystone_user', JSON.stringify(userObj))
    
    if (bizData) {
      setBusiness(bizData)
      localStorage.setItem('keystone_business', JSON.stringify(bizData))
    }
  }
  
  const signup = async (data: SignupData) => {
    const response = await api.post('/auth/signup', data)
    
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
