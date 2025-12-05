const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

class ApiError extends Error {
  status: number
  
  constructor(message: string, status: number) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  })
  
  if (!response.ok) {
    let message = 'An error occurred'
    try {
      const error = await response.json()
      message = error.detail || error.message || message
    } catch {}
    throw new ApiError(message, response.status)
  }
  
  return response.json()
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  delete: <T>(endpoint: string) =>
    request<T>(endpoint, {
      method: 'DELETE',
    }),
}

export { ApiError }
