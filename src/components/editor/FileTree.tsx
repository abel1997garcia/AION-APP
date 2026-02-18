'use client'

import { useState } from 'react'
import { Plus, Trash2, FilePlus, X } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { getFileIcon, getLanguageFromFilename } from '@/lib/utils'
import { cn } from '@/lib/utils'

export default function FileTree() {
  const { project, setActiveFile, openFile, deleteFile, addFile } = useEditorStore()
  const [addingFile, setAddingFile] = useState(false)
  const [newFileName, setNewFileName] = useState('')

  const handleAddFile = () => {
    if (!newFileName.trim()) { setAddingFile(false); return }
    addFile(newFileName.trim())
    setNewFileName('')
    setAddingFile(false)
  }

  const files = Object.keys(project.files)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-aion-border">
        <span className="text-xs font-semibold uppercase tracking-wider text-aion-muted">
          Archivos
        </span>
        <button
          onClick={() => setAddingFile(true)}
          title="Nuevo archivo"
          className="p-1 rounded text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
        >
          <FilePlus size={14} />
        </button>
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto py-1">
        {/* New file input */}
        {addingFile && (
          <div className="flex items-center gap-1 px-2 py-1">
            <span className="text-sm">📄</span>
            <input
              autoFocus
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddFile()
                if (e.key === 'Escape') { setAddingFile(false); setNewFileName('') }
              }}
              onBlur={handleAddFile}
              placeholder="nombre.tsx"
              className="flex-1 bg-aion-bg border border-aion-accent/50 rounded px-1.5 py-0.5 text-xs text-aion-text outline-none"
            />
          </div>
        )}

        {files.map((filePath) => {
          const name = filePath.split('/').pop() || filePath
          const isActive = project.activeFile === filePath

          return (
            <div
              key={filePath}
              className={cn(
                'group flex items-center gap-2 px-3 py-1.5 cursor-pointer text-sm transition-colors',
                isActive
                  ? 'bg-aion-accent/15 text-aion-text border-l-2 border-aion-accent'
                  : 'text-aion-muted hover:text-aion-text hover:bg-aion-border/20 border-l-2 border-transparent'
              )}
              onClick={() => {
                setActiveFile(filePath)
                openFile(filePath)
              }}
            >
              <span className="text-xs shrink-0">{getFileIcon(name)}</span>
              <span className="flex-1 truncate font-mono text-xs">{name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  if (files.length > 1) deleteFile(filePath)
                }}
                className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-red-500/20 hover:text-red-400 transition-all"
              >
                <Trash2 size={11} />
              </button>
            </div>
          )
        })}
      </div>

      {/* Project info */}
      <div className="px-3 py-2 border-t border-aion-border">
        <p className="text-xs text-aion-muted">
          {files.length} archivo{files.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  )
}
