'use client'

import { X } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { getFileIcon } from '@/lib/utils'
import { cn } from '@/lib/utils'

export default function TabBar() {
  const { project, setActiveFile, closeFile, openFile } = useEditorStore()
  const { openFiles, activeFile } = project

  if (openFiles.length === 0) return null

  return (
    <div className="flex items-stretch overflow-x-auto bg-aion-panel border-b border-aion-border shrink-0 min-h-[36px]">
      {openFiles.map((filePath) => {
        const name = filePath.split('/').pop() || filePath
        const isActive = activeFile === filePath

        return (
          <div
            key={filePath}
            className={cn(
              'group flex items-center gap-2 px-3 py-1 border-r border-aion-border cursor-pointer text-xs whitespace-nowrap transition-colors shrink-0 relative',
              isActive
                ? 'bg-aion-bg text-aion-text after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-aion-accent'
                : 'text-aion-muted hover:text-aion-text hover:bg-aion-bg/50'
            )}
            onClick={() => setActiveFile(filePath)}
          >
            <span className="text-[11px]">{getFileIcon(name)}</span>
            <span className="font-mono">{name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                closeFile(filePath)
              }}
              className="ml-0.5 opacity-0 group-hover:opacity-100 w-4 h-4 flex items-center justify-center rounded hover:bg-aion-border/50 transition-all"
            >
              <X size={10} />
            </button>
          </div>
        )
      })}
    </div>
  )
}
