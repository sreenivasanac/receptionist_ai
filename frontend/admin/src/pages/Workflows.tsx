import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { api } from '../services/api'

interface WorkflowAction {
  type: string
  config: Record<string, unknown>
}

interface TriggerConfig {
  keywords?: string[]
  customer_type?: string
  segment?: string
  time_condition?: string
}

interface Workflow {
  id: string
  business_id: string
  name: string
  description: string | null
  trigger_type: 'keyword' | 'segment' | 'time'
  trigger_config: TriggerConfig
  actions: WorkflowAction[]
  is_active: boolean
  created_at: string
  updated_at: string
}

interface WorkflowTemplate {
  name: string
  description: string
  trigger_type: string
  trigger_config: TriggerConfig
  actions: WorkflowAction[]
}

interface WorkflowsResponse {
  workflows: Workflow[]
  count: number
}

interface TemplatesResponse {
  templates: WorkflowTemplate[]
  count: number
}

export default function Workflows() {
  const { business } = useAuth()
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null)

  const fetchWorkflows = async () => {
    if (!business?.id) return
    setLoading(true)
    try {
      const [workflowsData, templatesData] = await Promise.all([
        api.get<WorkflowsResponse>(`/workflows/${business.id}`),
        api.get<TemplatesResponse>(`/workflows/${business.id}/templates`)
      ])
      setWorkflows(workflowsData.workflows)
      setTemplates(templatesData.templates)
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkflows()
  }, [business?.id])

  const toggleWorkflow = async (workflowId: string) => {
    if (!business?.id) return
    try {
      await api.post(`/workflows/${business.id}/${workflowId}/toggle`)
      fetchWorkflows()
    } catch (error) {
      console.error('Failed to toggle workflow:', error)
    }
  }

  const createFromTemplate = async (templateName: string) => {
    if (!business?.id) return
    try {
      await api.post(`/workflows/${business.id}/from-template?template_name=${encodeURIComponent(templateName)}`)
      fetchWorkflows()
      setShowCreateModal(false)
    } catch (error) {
      console.error('Failed to create workflow:', error)
    }
  }

  const deleteWorkflow = async (workflowId: string) => {
    if (!business?.id) return
    if (!confirm('Are you sure you want to delete this workflow?')) return
    try {
      await api.delete(`/workflows/${business.id}/${workflowId}`)
      fetchWorkflows()
      setSelectedWorkflow(null)
    } catch (error) {
      console.error('Failed to delete workflow:', error)
    }
  }

  const getTriggerLabel = (type: string) => {
    switch (type) {
      case 'keyword': return 'Keyword Match'
      case 'segment': return 'Customer Segment'
      case 'time': return 'Time-Based'
      default: return type
    }
  }

  const getActionLabel = (type: string) => {
    switch (type) {
      case 'send_message': return 'Send Message'
      case 'apply_discount': return 'Apply Discount'
      case 'capture_lead': return 'Capture Lead'
      case 'offer_service': return 'Offer Service'
      case 'escalate': return 'Escalate to Human'
      default: return type
    }
  }

  if (!business) {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">Please set up your business first.</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-card-foreground">Workflows</h1>
          <p className="text-muted-foreground mt-1">Automate customer interactions with custom workflows</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary"
        >
          + Add Workflow
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-card-foreground">Active Workflows ({workflows.length})</h2>
            
            {workflows.length === 0 ? (
              <div className="card text-center py-8">
                <p className="text-muted-foreground mb-4">No workflows configured yet</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="btn btn-secondary"
                >
                  Create Your First Workflow
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {workflows.map((workflow) => (
                  <div
                    key={workflow.id}
                    onClick={() => setSelectedWorkflow(workflow)}
                    className={`card cursor-pointer transition-colors ${
                      selectedWorkflow?.id === workflow.id ? 'ring-2 ring-primary' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium text-card-foreground">{workflow.name}</h3>
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            workflow.is_active
                              ? 'bg-green-500/10 text-green-600'
                              : 'bg-gray-500/10 text-gray-500'
                          }`}>
                            {workflow.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        {workflow.description && (
                          <p className="text-sm text-muted-foreground mt-1">{workflow.description}</p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>Trigger: {getTriggerLabel(workflow.trigger_type)}</span>
                          <span>{workflow.actions.length} action(s)</span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleWorkflow(workflow.id)
                        }}
                        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors ${
                          workflow.is_active ? 'bg-primary' : 'bg-gray-300'
                        }`}
                      >
                        <span
                          className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm transition-transform ${
                            workflow.is_active ? 'translate-x-5' : 'translate-x-0.5'
                          } mt-0.5`}
                        />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            {selectedWorkflow ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-card-foreground">{selectedWorkflow.name}</h2>
                  <button
                    onClick={() => deleteWorkflow(selectedWorkflow.id)}
                    className="text-red-500 hover:text-red-600 text-sm"
                  >
                    Delete
                  </button>
                </div>
                
                {selectedWorkflow.description && (
                  <p className="text-muted-foreground mb-4">{selectedWorkflow.description}</p>
                )}

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-card-foreground mb-2">Trigger</h3>
                    <div className="bg-secondary rounded-lg p-3">
                      <p className="text-sm font-medium text-card-foreground">
                        {getTriggerLabel(selectedWorkflow.trigger_type)}
                      </p>
                      {selectedWorkflow.trigger_type === 'keyword' && selectedWorkflow.trigger_config.keywords && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {selectedWorkflow.trigger_config.keywords.map((kw, idx) => (
                            <span key={idx} className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">
                              {kw}
                            </span>
                          ))}
                        </div>
                      )}
                      {selectedWorkflow.trigger_type === 'segment' && (
                        <p className="text-sm text-muted-foreground mt-1">
                          Customer type: {selectedWorkflow.trigger_config.customer_type || 'any'}
                        </p>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-card-foreground mb-2">Actions</h3>
                    <div className="space-y-2">
                      {selectedWorkflow.actions.map((action, idx) => (
                        <div key={idx} className="bg-secondary rounded-lg p-3">
                          <p className="text-sm font-medium text-card-foreground">
                            {idx + 1}. {getActionLabel(action.type)}
                          </p>
                          {action.type === 'send_message' && 'message' in action.config && (
                            <p className="text-sm text-muted-foreground mt-1 italic">
                              &quot;{String(action.config.message)}&quot;
                            </p>
                          )}
                          {action.type === 'apply_discount' && 'percent' in action.config && (
                            <p className="text-sm text-muted-foreground mt-1">
                              {String(action.config.percent)}% off ({String(action.config.reason)})
                            </p>
                          )}
                          {action.type === 'capture_lead' && 'interest' in action.config && (
                            <p className="text-sm text-muted-foreground mt-1">
                              Interest: {String(action.config.interest)}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground">Select a workflow to view details</p>
              </div>
            )}
          </div>
        </div>
      )}

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-xl shadow-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-border">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-card-foreground">Add Workflow</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-muted-foreground hover:text-card-foreground"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <p className="text-muted-foreground mt-1">Choose a template to get started</p>
            </div>
            
            <div className="p-6 space-y-4">
              {templates.map((template) => (
                <div
                  key={template.name}
                  className="border border-border rounded-lg p-4 hover:border-primary transition-colors cursor-pointer"
                  onClick={() => createFromTemplate(template.name)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-medium text-card-foreground">{template.name}</h3>
                      <p className="text-sm text-muted-foreground mt-1">{template.description}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span>Trigger: {getTriggerLabel(template.trigger_type)}</span>
                        <span>{template.actions.length} action(s)</span>
                      </div>
                    </div>
                    <button className="btn btn-secondary text-sm">
                      Use Template
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
