import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'

const API_URL = 'http://localhost:8001'

export default function ChatDemo() {
  const { business } = useAuth()
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  
  // Check if backend is running
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, { method: 'GET' })
        setBackendStatus(response.ok ? 'online' : 'offline')
      } catch {
        setBackendStatus('offline')
      }
    }
    
    checkBackend()
    const interval = setInterval(checkBackend, 5000) // Re-check every 5 seconds
    return () => clearInterval(interval)
  }, [])
  
  useEffect(() => {
    if (!business?.id || backendStatus !== 'online') return
    
    // Clean up any existing widget
    const existingWidget = document.getElementById('keystone-chat-widget')
    const existingScript = document.getElementById('keystone-chat-script')
    if (existingWidget) existingWidget.remove()
    if (existingScript) existingScript.remove()
    
    // Create and load the widget script
    const script = document.createElement('script')
    script.id = 'keystone-chat-script'
    script.src = `${API_URL}/static/chat.js`
    script.setAttribute('data-business-id', business.id)
    script.setAttribute('data-api-url', API_URL)
    document.body.appendChild(script)
    
    return () => {
      // Cleanup on unmount
      const widget = document.getElementById('keystone-chat-widget')
      const scr = document.getElementById('keystone-chat-script')
      if (widget) widget.remove()
      if (scr) scr.remove()
    }
  }, [business?.id, backendStatus])
  
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
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-card-foreground">Chat Demo</h1>
        <p className="text-muted-foreground mt-1">Preview your AI receptionist as customers will see it</p>
      </div>
      
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Test Your Chatbot</h2>
        <p className="text-sm text-muted-foreground mb-6">
          Click the chat bubble in the bottom right corner to test your AI receptionist. 
          Make sure your backend server is running on port 8001.
        </p>
        
        <div className="bg-secondary/30 rounded-xl p-8 min-h-[400px] relative">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-card-foreground mb-2">{business.name}</h3>
            <p className="text-muted-foreground mb-6">Your AI-powered receptionist is ready!</p>
            
            <div className="bg-card rounded-lg p-6 max-w-md mx-auto shadow-sm">
              <h4 className="font-medium mb-3">Try asking:</h4>
              <ul className="text-left text-sm text-muted-foreground space-y-2">
                <li className="flex items-center gap-2">
                  <span className="text-primary">•</span>
                  "What are your hours?"
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">•</span>
                  "What services do you offer?"
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">•</span>
                  "How much is [service name]?"
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">•</span>
                  "Do you accept walk-ins?"
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-primary">•</span>
                  "What's your cancellation policy?"
                </li>
              </ul>
            </div>
          </div>
          
          {/* Arrow pointing to chat widget */}
          <div className="absolute bottom-4 right-4 flex items-center gap-2 text-muted-foreground">
            <span className="text-sm">Click the chat bubble</span>
            <svg className="w-6 h-6 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>
        </div>
        
        {backendStatus === 'offline' && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Backend is not running.</strong> Start the server with:
            </p>
            <code className="block mt-2 bg-red-100 px-3 py-2 rounded text-red-900 font-mono text-sm">
              cd backend && uv run python -m app.main
            </code>
            <p className="text-xs text-red-600 mt-2">Server should be running on port 8001</p>
          </div>
        )}
        
        {backendStatus === 'checking' && (
          <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <p className="text-sm text-gray-600">Checking backend status...</p>
          </div>
        )}
        
        {backendStatus === 'online' && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              <strong>Backend is running.</strong> The chat widget should appear in the bottom-right corner.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
