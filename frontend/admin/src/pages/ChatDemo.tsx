import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'


const API_URL = 'https://receptionist-ai.pragnyalabs.com/api'

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
          Look for the chat bubble in the bottom-right corner of your screen to test your AI receptionist. 
          The chat widget connects to the production API.
        </p>
        
        <div className="bg-secondary/30 rounded-xl p-8 min-h-[400px] relative">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-card-foreground mb-2">{business.name}</h3>
            <p className="text-muted-foreground mb-6">Your AI-powered receptionist is ready!</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
              <div className="bg-card rounded-lg p-5 shadow-sm text-left">
                <h4 className="font-medium mb-3 text-primary">Book an Appointment</h4>
                <ul className="text-sm text-muted-foreground space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>"I'd like to book a Women's Haircut for next Tuesday at 2pm"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>"Can I schedule an appointment with Sarah for a Balayage?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>"What times are available tomorrow afternoon?"</span>
                  </li>
                </ul>
              </div>
              
              <div className="bg-card rounded-lg p-5 shadow-sm text-left">
                <h4 className="font-medium mb-3 text-green-600">Reschedule or Cancel</h4>
                <ul className="text-sm text-muted-foreground space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>"I need to reschedule my appointment to next week"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>"Can I change my 10am appointment to 2pm?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-600 mt-1">•</span>
                    <span>"I need to cancel my appointment for tomorrow"</span>
                  </li>
                </ul>
              </div>
              
              <div className="bg-card rounded-lg p-5 shadow-sm text-left">
                <h4 className="font-medium mb-3 text-blue-600">General Questions</h4>
                <ul className="text-sm text-muted-foreground space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>"What are your hours on Saturday?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>"How much does a Men's Haircut cost?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span>"Do you offer any hair coloring services?"</span>
                  </li>
                </ul>
              </div>
              
              <div className="bg-card rounded-lg p-5 shadow-sm text-left">
                <h4 className="font-medium mb-3 text-purple-600">Waitlist & Special Requests</h4>
                <ul className="text-sm text-muted-foreground space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 mt-1">•</span>
                    <span>"No slots available? Add me to the waitlist please"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 mt-1">•</span>
                    <span>"It's my birthday next week - any specials?"</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-purple-600 mt-1">•</span>
                    <span>"I'm looking for bridal hair services"</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          
          {/* Arrow pointing to chat widget */}
          <div className="absolute bottom-8 right-8 flex flex-col items-end gap-3 text-muted-foreground">
            <span className="text-sm font-medium">Open the chat widget below</span>
            <svg className="w-6 h-6 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </div>
        
        {backendStatus === 'offline' && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Backend is not reachable.</strong> The production API at receptionist-ai.pragnyalabs.com is currently unavailable.
            </p>
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
