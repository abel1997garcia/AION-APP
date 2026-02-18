'use client'

import { useState } from 'react'
import { Plus, Trash2, ChevronDown, ChevronRight, Send } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { generateId } from '@/lib/utils'
import { cn } from '@/lib/utils'
import type { ApiEndpoint } from '@/types'

const methodColors: Record<string, string> = {
  GET: 'text-aion-green bg-aion-green/10 border-aion-green/20',
  POST: 'text-blue-400 bg-blue-400/10 border-blue-400/20',
  PUT: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
  DELETE: 'text-red-400 bg-red-400/10 border-red-400/20',
  PATCH: 'text-orange-400 bg-orange-400/10 border-orange-400/20',
}

export default function ApiPanel() {
  const { project, addApi, removeApi, updateApi } = useEditorStore()
  const [expandedApi, setExpandedApi] = useState<string | null>(null)
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<Record<string, string>>({})

  const handleAddApi = () => {
    addApi({
      name: `api_${project.apis.length + 1}`,
      baseUrl: 'https://api.ejemplo.com',
      endpoints: [],
    })
  }

  const handleAddEndpoint = (apiId: string) => {
    const api = project.apis.find(a => a.id === apiId)
    if (!api) return
    const newEndpoint: ApiEndpoint = {
      id: generateId(),
      method: 'GET',
      path: '/usuarios',
      description: 'Obtener usuarios',
      response: JSON.stringify({ data: [{ id: 1, name: 'Usuario 1' }], total: 1 }, null, 2),
      headers: [{ key: 'Content-Type', value: 'application/json' }],
    }
    updateApi(apiId, { endpoints: [...api.endpoints, newEndpoint] })
  }

  const handleTestEndpoint = async (apiId: string, endpoint: ApiEndpoint) => {
    const api = project.apis.find(a => a.id === apiId)
    if (!api) return
    const url = `${api.baseUrl}${endpoint.path}`
    setTestResult(prev => ({ ...prev, [endpoint.id]: `Enviando ${endpoint.method} ${url}...` }))
    try {
      const res = await fetch(url, { method: endpoint.method })
      const text = await res.text()
      setTestResult(prev => ({ ...prev, [endpoint.id]: `${res.status} ${res.statusText}\n${text.slice(0, 200)}` }))
    } catch (e) {
      setTestResult(prev => ({ ...prev, [endpoint.id]: `Error: ${e instanceof Error ? e.message : 'Fallo en la petición'}` }))
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-aion-border shrink-0">
        <span className="text-xs font-semibold uppercase tracking-wider text-aion-muted">APIs</span>
        <button
          onClick={handleAddApi}
          className="p-1 rounded text-aion-muted hover:text-yellow-400 hover:bg-yellow-400/10 transition-colors"
          title="Nueva API"
        >
          <Plus size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {project.apis.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 px-4 text-center">
            <div className="text-4xl mb-3">🔌</div>
            <p className="text-sm font-medium text-aion-text mb-1">Sin APIs configuradas</p>
            <p className="text-xs text-aion-muted mb-3">Conecta APIs externas o crea endpoints mock</p>
            <button
              onClick={handleAddApi}
              className="flex items-center gap-1.5 text-xs bg-yellow-400/10 hover:bg-yellow-400/20 text-yellow-400 border border-yellow-400/20 px-3 py-1.5 rounded-lg transition-colors"
            >
              <Plus size={12} />
              Añadir API
            </button>
          </div>
        ) : (
          <div className="py-1">
            {project.apis.map((api) => (
              <div key={api.id}>
                {/* API header */}
                <div
                  className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-aion-border/20 group"
                  onClick={() => setExpandedApi(expandedApi === api.id ? null : api.id)}
                >
                  {expandedApi === api.id ? <ChevronDown size={12} className="text-aion-muted" /> : <ChevronRight size={12} className="text-aion-muted" />}
                  <span className="text-sm">🔌</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-mono text-aion-text truncate">{api.name}</div>
                    <div className="text-[10px] text-aion-muted truncate">{api.baseUrl}</div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeApi(api.id) }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-500/20 hover:text-red-400"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>

                {/* Endpoints */}
                {expandedApi === api.id && (
                  <div className="pl-5">
                    {api.endpoints.map((endpoint) => (
                      <div key={endpoint.id} className="mb-1">
                        <div
                          className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-aion-border/20 group"
                          onClick={() => setExpandedEndpoint(expandedEndpoint === endpoint.id ? null : endpoint.id)}
                        >
                          <span className={cn('text-[9px] font-bold px-1.5 py-0.5 rounded border shrink-0', methodColors[endpoint.method])}>
                            {endpoint.method}
                          </span>
                          <span className="flex-1 text-[11px] font-mono text-aion-muted truncate">{endpoint.path}</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleTestEndpoint(api.id, endpoint) }}
                            title="Probar endpoint"
                            className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-aion-green/10 hover:text-aion-green text-aion-muted transition-all"
                          >
                            <Send size={11} />
                          </button>
                        </div>

                        {expandedEndpoint === endpoint.id && (
                          <div className="mx-3 mb-2">
                            {endpoint.description && (
                              <p className="text-[10px] text-aion-muted mb-2">{endpoint.description}</p>
                            )}
                            {testResult[endpoint.id] && (
                              <div className="bg-aion-bg border border-aion-border rounded p-2 text-[10px] font-mono text-aion-text whitespace-pre-wrap break-all max-h-24 overflow-auto">
                                {testResult[endpoint.id]}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}

                    <button
                      onClick={() => handleAddEndpoint(api.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] text-aion-muted hover:text-yellow-400 transition-colors w-full"
                    >
                      <Plus size={11} />
                      Añadir endpoint
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
