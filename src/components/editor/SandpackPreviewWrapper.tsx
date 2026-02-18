'use client'

import { useEffect, useRef } from 'react'
import { SandpackProvider, SandpackPreview, useSandpack } from '@codesandbox/sandpack-react'
import { useEditorStore } from '@/lib/store'

// Inner component that syncs files from our store to Sandpack
function SandpackSync() {
  const { project } = useEditorStore()
  const { sandpack } = useSandpack()
  const prevFilesRef = useRef<Record<string, string>>({})

  useEffect(() => {
    const currentFiles = project.files
    const prevFiles = prevFilesRef.current

    // Update changed files
    Object.entries(currentFiles).forEach(([path, content]) => {
      if (prevFiles[path] !== content) {
        try {
          sandpack.updateFile(path, content)
        } catch (e) {
          // File might not exist in sandpack yet, add it
          sandpack.addFile(path, content)
        }
      }
    })

    prevFilesRef.current = { ...currentFiles }
  }, [project.files, sandpack])

  return null
}

function getTemplate(template: string) {
  if (template === 'react') return 'react' as const
  if (template === 'html') return 'static' as const
  if (template === 'vanilla-js') return 'vanilla' as const
  if (template === 'vue') return 'vue' as const
  return 'react' as const
}

export default function SandpackPreviewWrapper() {
  const { project } = useEditorStore()

  const sandpackTemplate = getTemplate(project.template)

  // Build the files object for Sandpack
  const sandpackFiles: Record<string, { code: string; active?: boolean }> = {}
  Object.entries(project.files).forEach(([path, content]) => {
    sandpackFiles[path] = { code: content }
  })

  return (
    <SandpackProvider
      key={`${project.template}-${project.id}`}
      template={sandpackTemplate}
      files={sandpackFiles}
      options={{
        recompileMode: 'delayed',
        recompileDelay: 500,
        externalResources: [],
      }}
      theme={{
        colors: {
          surface1: '#ffffff',
          surface2: '#f9fafb',
          surface3: '#f3f4f6',
          clickable: '#6b7280',
          base: '#1f2937',
          disabled: '#d1d5db',
          hover: '#e5e7eb',
          accent: '#7c3aed',
          error: '#ef4444',
          errorSurface: '#fef2f2',
        },
        font: {
          body: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          mono: '"JetBrains Mono", "Fira Code", monospace',
          size: '14px',
          lineHeight: '1.6',
        },
      }}
    >
      <SandpackSync />
      <SandpackPreview
        style={{ height: '100%', width: '100%' }}
        showOpenInCodeSandbox={false}
        showRefreshButton={false}
        showNavigator={false}
      />
    </SandpackProvider>
  )
}
