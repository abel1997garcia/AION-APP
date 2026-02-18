'use client'

import { FolderOpen, Database, Plug, ImageIcon, Music, ChevronLeft } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import type { SidebarTab } from '@/types'
import { cn } from '@/lib/utils'

const tabs: { id: SidebarTab; icon: React.ReactNode; label: string; color: string }[] = [
  { id: 'files', icon: <FolderOpen size={18} />, label: 'Archivos', color: '#7c3aed' },
  { id: 'database', icon: <Database size={18} />, label: 'Base de datos', color: '#22c55e' },
  { id: 'api', icon: <Plug size={18} />, label: 'API', color: '#eab308' },
  { id: 'images', icon: <ImageIcon size={18} />, label: 'Imágenes', color: '#ec4899' },
  { id: 'audio', icon: <Music size={18} />, label: 'Audio', color: '#f97316' },
]

export default function Sidebar() {
  const { sidebarTab, setSidebarTab, sidebarOpen, setSidebarOpen } = useEditorStore()

  return (
    <div className="flex h-full">
      {/* Icon rail */}
      <div className="w-12 bg-aion-panel border-r border-aion-border flex flex-col items-center py-2 gap-1 shrink-0">
        {tabs.map(({ id, icon, label, color }) => (
          <button
            key={id}
            title={label}
            onClick={() => {
              if (sidebarTab === id && sidebarOpen) {
                setSidebarOpen(false)
              } else {
                setSidebarTab(id)
                setSidebarOpen(true)
              }
            }}
            className={cn(
              'w-9 h-9 flex items-center justify-center rounded-lg transition-all duration-150',
              sidebarTab === id && sidebarOpen
                ? 'text-white'
                : 'text-aion-muted hover:text-aion-text hover:bg-aion-border/30'
            )}
            style={
              sidebarTab === id && sidebarOpen
                ? { background: `${color}25`, color: color }
                : {}
            }
          >
            {icon}
          </button>
        ))}

        <div className="flex-1" />

        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-all"
          title={sidebarOpen ? 'Ocultar panel' : 'Mostrar panel'}
        >
          <ChevronLeft size={16} className={cn('transition-transform', !sidebarOpen && 'rotate-180')} />
        </button>
      </div>
    </div>
  )
}
