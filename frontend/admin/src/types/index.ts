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

// V2 Types
export interface Appointment {
  id: string
  business_id: string
  customer_id?: string
  service_id: string
  staff_id?: string
  customer_name: string
  customer_phone: string
  customer_email?: string
  date: string
  time: string
  duration_minutes: number
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'
  notes?: string
  service_name?: string
  staff_name?: string
  created_at?: string
  updated_at?: string
}

export interface Lead {
  id: string
  business_id: string
  name: string
  email?: string
  phone?: string
  interest: string
  notes?: string
  company?: string
  status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost'
  source: string
  created_at?: string
  updated_at?: string
}

export interface Customer {
  id: string
  business_id: string
  first_name: string
  last_name?: string
  email?: string
  phone?: string
  visit_count: number
  last_visit_date?: string
  favorite_service_id?: string
  favorite_service_name?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

export interface WaitlistEntry {
  id: string
  business_id: string
  customer_id?: string
  service_id: string
  customer_name: string
  customer_contact: string
  preferred_dates: string[]
  preferred_times: string[]
  contact_method: 'phone' | 'email' | 'sms'
  status: 'waiting' | 'notified' | 'booked' | 'expired' | 'cancelled'
  notes?: string
  service_name?: string
  created_at?: string
  updated_at?: string
}
