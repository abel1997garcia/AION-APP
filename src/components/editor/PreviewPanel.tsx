'use client'

import { useState, useCallback } from 'react'
import dynamic from 'next/dynamic'
import { RefreshCw, ExternalLink, Monitor, Tablet, Smartphone } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { cn } from '@/lib/utils'

// Dynamically import Sandpack to avoid SSR issues
const SandpackPreviewWrapper = dynamic(
  () => import('./SandpackPreviewWrapper'),
  { ssr: false, loading: () => <PreviewLoading /> }
)

function PreviewLoading() {
  return (
    <div className="flex-1 flex items-center justify-center bg-white text-gray-500">
      <div className="text-center">
        <div className="w-6 h-6 border-2 border-purple-300 border-t-purple-600 rounded-full animate-spin mx-auto mb-2" />
        <p className="text-sm">Preparando preview...</p>
      </div>
    </div>
  )
}

type Device = 'desktop' | 'tablet' | 'mobile'

const deviceWidths: Record<Device, string> = {
  desktop: '100%',
  tablet: '768px',
  mobile: '375px',
}

export default function PreviewPanel() {
  const { project, previewKey, refreshPreview, consoleOpen, setConsoleOpen } = useEditorStore()
  const [device, setDevice] = useState<Device>('desktop')

  const deviceOptions: { icon: React.ReactNode; value: Device; label: string }[] = [
    { icon: <Monitor size={13} />, value: 'desktop', label: 'Desktop' },
    { icon: <Tablet size={13} />, value: 'tablet', label: 'Tablet' },
    { icon: <Smartphone size={13} />, value: 'mobile', label: 'Mobile' },
  ]

  return (
    <div className="flex flex-col h-full bg-aion-surface">
      {/* Preview toolbar */}
      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-aion-border bg-aion-panel shrink-0">
        {/* Traffic lights */}
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/60" />
        </div>

        {/* URL bar */}
        <div className="flex-1 flex items-center gap-2 bg-aion-bg border border-aion-border rounded-md px-3 py-1 text-xs text-aion-muted font-mono mx-2">
          <span className="text-aion-green text-[10px]">●</span>
          <span>localhost:3000</span>
        </div>

        {/* Device selector */}
        <div className="flex items-center gap-0.5 bg-aion-bg border border-aion-border rounded-md p-0.5">
          {deviceOptions.map(({ icon, value, label }) => (
            <button
              key={value}
              title={label}
              onClick={() => setDevice(value)}
              className={cn(
                'p-1 rounded transition-colors',
                device === value
                  ? 'bg-aion-accent text-white'
                  : 'text-aion-muted hover:text-aion-text'
              )}
            >
              {icon}
            </button>
          ))}
        </div>

        <button
          onClick={refreshPreview}
          title="Refrescar"
          className="p-1 rounded text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Preview area */}
      <div className="flex-1 overflow-auto bg-[#e5e7eb] flex items-start justify-center min-h-0 p-2">
        <div
          className="relative bg-white h-full transition-all duration-300 shadow-lg overflow-hidden"
          style={{
            width: deviceWidths[device],
            maxWidth: '100%',
            minHeight: '100%',
          }}
        >
          <SandpackPreviewWrapper key={previewKey} />
        </div>
      </div>
    </div>
  )
}
