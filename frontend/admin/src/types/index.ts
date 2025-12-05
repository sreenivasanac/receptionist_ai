export interface Business {
  id: string
  name: string
  type: string
  address?: string
  phone?: string
  email?: string
  website?: string
  config_yaml?: string
  features_enabled: Record<string, boolean>
  created_at?: string
  updated_at?: string
}

export interface Staff {
  id: string
  business_id: string
  name: string
  role_title?: string
  services_offered: string[]
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface Service {
  id: string
  business_id: string
  name: string
  description?: string
  duration_minutes: number
  price: number
  requires_consultation: boolean
  is_active: boolean
  created_at?: string
  updated_at?: string
}

export interface BusinessConfig {
  business_id?: string
  name?: string
  location?: string
  phone?: string
  email?: string
  hours?: Record<string, { open?: string; close?: string; closed?: boolean }>
  services?: Array<{
    id: string
    name: string
    duration_minutes: number
    price: number
    description: string
  }>
  policies?: {
    cancellation?: string
    deposit?: boolean
    deposit_amount?: number
    walk_ins?: string
  }
  faqs?: Array<{ question: string; answer: string }>
}
