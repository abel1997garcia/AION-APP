'use client'

import { useState } from 'react'
import { Play, RefreshCw, Download, Share2, Settings, ChevronDown, Monitor, Smartphone, Tablet } from 'lucide-react'
import { useEditorStore } from '@/lib/store'

type Device = 'desktop' | 'tablet' | 'mobile'

interface ToolbarProps {
  onDeviceChange?: (device: Device) => void
  currentDevice?: Device
}

export default function Toolbar({ onDeviceChange, currentDevice = 'desktop' }: ToolbarProps) {
  const { project, updateProjectName, refreshPreview } = useEditorStore()
  const [editingName, setEditingName] = useState(false)
  const [nameValue, setNameValue] = useState(project.name)

  const handleNameSave = () => {
    updateProjectName(nameValue)
    setEditingName(false)
  }

  const deviceOptions: { icon: React.ReactNode; label: string; value: Device }[] = [
    { icon: <Monitor size={14} />, label: 'Desktop', value: 'desktop' },
    { icon: <Tablet size={14} />, label: 'Tablet', value: 'tablet' },
    { icon: <Smartphone size={14} />, label: 'Mobile', value: 'mobile' },
  ]

  return (
    <div className="h-11 flex items-center gap-2 px-3 border-b border-aion-border bg-aion-panel shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-1.5 mr-2">
        <span className="text-lg">⚡</span>
        <span className="font-bold text-sm text-aion-accent-light hidden sm:block">AION</span>
      </div>

      <div className="w-px h-5 bg-aion-border" />

      {/* Project name */}
      <div className="flex items-center">
        {editingName ? (
          <input
            autoFocus
            value={nameValue}
            onChange={(e) => setNameValue(e.target.value)}
            onBlur={handleNameSave}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleNameSave()
              if (e.key === 'Escape') { setEditingName(false); setNameValue(project.name) }
            }}
            className="bg-aion-bg border border-aion-accent/50 rounded px-2 py-0.5 text-sm text-aion-text outline-none w-40"
          />
        ) : (
          <button
            onClick={() => setEditingName(true)}
            className="text-sm text-aion-text hover:text-aion-accent-light px-2 py-0.5 rounded hover:bg-aion-border/30 transition-colors"
          >
            {project.name}
          </button>
        )}
      </div>

      <div className="flex-1" />

      {/* Device picker */}
      <div className="hidden md:flex items-center gap-1 bg-aion-bg border border-aion-border rounded-lg p-0.5">
        {deviceOptions.map(({ icon, label, value }) => (
          <button
            key={value}
            title={label}
            onClick={() => onDeviceChange?.(value)}
            className={`p-1.5 rounded-md transition-colors ${
              currentDevice === value
                ? 'bg-aion-accent text-white'
                : 'text-aion-muted hover:text-aion-text'
            }`}
          >
            {icon}
          </button>
        ))}
      </div>

      <div className="w-px h-5 bg-aion-border hidden md:block" />

      {/* Actions */}
      <button
        onClick={refreshPreview}
        title="Refrescar preview"
        className="p-1.5 rounded-lg text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
      >
        <RefreshCw size={15} />
      </button>

      <button
        title="Compartir"
        className="p-1.5 rounded-lg text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
      >
        <Share2 size={15} />
      </button>

      <button
        title="Descargar"
        className="p-1.5 rounded-lg text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
      >
        <Download size={15} />
      </button>

      {/* Run button */}
      <button
        onClick={refreshPreview}
        className="flex items-center gap-1.5 bg-aion-accent hover:bg-aion-accent-light text-white text-sm font-semibold px-3 py-1.5 rounded-lg transition-colors"
      >
        <Play size={13} />
        <span className="hidden sm:block">Ejecutar</span>
      </button>
    </div>
  )
}
