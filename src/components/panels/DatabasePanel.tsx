'use client'

import { useState } from 'react'
import { Plus, Trash2, Table, ChevronDown, ChevronRight } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { generateId } from '@/lib/utils'
import type { DatabaseTable } from '@/types'

export default function DatabasePanel() {
  const { project, addDatabase, removeDatabase, updateDatabase } = useEditorStore()
  const [expandedDb, setExpandedDb] = useState<string | null>(null)
  const [expandedTable, setExpandedTable] = useState<string | null>(null)

  const handleAddDatabase = () => {
    addDatabase({
      name: `database_${project.databases.length + 1}`,
      tables: [],
    })
  }

  const handleAddTable = (dbId: string) => {
    const db = project.databases.find(d => d.id === dbId)
    if (!db) return
    const newTable: DatabaseTable = {
      id: generateId(),
      name: `tabla_${db.tables.length + 1}`,
      columns: [
        { id: generateId(), name: 'id', type: 'number' },
        { id: generateId(), name: 'nombre', type: 'text' },
        { id: generateId(), name: 'createdAt', type: 'date' },
      ],
      rows: [
        { id: 1, nombre: 'Ejemplo 1', createdAt: '2024-01-01' },
        { id: 2, nombre: 'Ejemplo 2', createdAt: '2024-01-02' },
      ],
    }
    updateDatabase(dbId, { tables: [...db.tables, newTable] })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-aion-border shrink-0">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-aion-muted">Base de datos</span>
        </div>
        <button
          onClick={handleAddDatabase}
          className="p-1 rounded text-aion-muted hover:text-aion-green hover:bg-aion-green/10 transition-colors"
          title="Nueva base de datos"
        >
          <Plus size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {project.databases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 px-4 text-center">
            <div className="text-4xl mb-3">🗄️</div>
            <p className="text-sm font-medium text-aion-text mb-1">Sin bases de datos</p>
            <p className="text-xs text-aion-muted mb-3">Añade una base de datos para gestionar tus datos</p>
            <button
              onClick={handleAddDatabase}
              className="flex items-center gap-1.5 text-xs bg-aion-green/10 hover:bg-aion-green/20 text-aion-green border border-aion-green/20 px-3 py-1.5 rounded-lg transition-colors"
            >
              <Plus size={12} />
              Crear base de datos
            </button>
          </div>
        ) : (
          <div className="py-1">
            {project.databases.map((db) => (
              <div key={db.id}>
                {/* DB header */}
                <div
                  className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-aion-border/20 transition-colors group"
                  onClick={() => setExpandedDb(expandedDb === db.id ? null : db.id)}
                >
                  {expandedDb === db.id ? <ChevronDown size={12} className="text-aion-muted" /> : <ChevronRight size={12} className="text-aion-muted" />}
                  <span className="text-sm">🗄️</span>
                  <span className="flex-1 text-xs font-mono text-aion-text">{db.name}</span>
                  <span className="text-[10px] text-aion-muted">{db.tables.length} tabla{db.tables.length !== 1 ? 's' : ''}</span>
                  <button
                    onClick={(e) => { e.stopPropagation(); removeDatabase(db.id) }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-500/20 hover:text-red-400 transition-all"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>

                {/* Tables */}
                {expandedDb === db.id && (
                  <div className="pl-5">
                    {db.tables.map((table) => (
                      <div key={table.id}>
                        <div
                          className="flex items-center gap-2 px-3 py-1.5 cursor-pointer hover:bg-aion-border/20 transition-colors group"
                          onClick={() => setExpandedTable(expandedTable === table.id ? null : table.id)}
                        >
                          {expandedTable === table.id ? <ChevronDown size={11} className="text-aion-muted" /> : <ChevronRight size={11} className="text-aion-muted" />}
                          <Table size={12} className="text-aion-green" />
                          <span className="flex-1 text-xs font-mono text-aion-muted">{table.name}</span>
                          <span className="text-[10px] text-aion-muted">{table.rows.length} filas</span>
                        </div>

                        {/* Table preview */}
                        {expandedTable === table.id && (
                          <div className="mx-3 mb-2 rounded-lg border border-aion-border overflow-hidden">
                            <div className="overflow-x-auto">
                              <table className="w-full text-[10px]">
                                <thead>
                                  <tr className="bg-aion-panel border-b border-aion-border">
                                    {table.columns.map(col => (
                                      <th key={col.id} className="px-2 py-1 text-left font-semibold text-aion-muted whitespace-nowrap">
                                        {col.name}
                                        <span className="ml-1 text-aion-border font-normal">({col.type})</span>
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {table.rows.slice(0, 3).map((row, i) => (
                                    <tr key={i} className="border-b border-aion-border/50 hover:bg-aion-border/10">
                                      {table.columns.map(col => (
                                        <td key={col.id} className="px-2 py-1 font-mono text-aion-text whitespace-nowrap">
                                          {String(row[col.name] ?? '')}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {table.rows.length > 3 && (
                              <div className="px-2 py-1 text-[10px] text-aion-muted border-t border-aion-border">
                                +{table.rows.length - 3} más filas
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Add table button */}
                    <button
                      onClick={() => handleAddTable(db.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-[11px] text-aion-muted hover:text-aion-green transition-colors w-full"
                    >
                      <Plus size={11} />
                      Añadir tabla
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SQL hint */}
      {project.databases.length > 0 && (
        <div className="px-3 py-2 border-t border-aion-border">
          <p className="text-[10px] text-aion-muted">
            💡 Accede a los datos via <code className="text-aion-green">window.__db</code> en tu código
          </p>
        </div>
      )}
    </div>
  )
}
