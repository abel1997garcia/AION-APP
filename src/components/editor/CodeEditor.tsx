'use client'

import { useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { useEditorStore } from '@/lib/store'
import { getLanguageFromFilename } from '@/lib/utils'

const MonacoEditor = dynamic(
  () => import('@monaco-editor/react').then((m) => m.default),
  { ssr: false, loading: () => <EditorLoading /> }
)

function EditorLoading() {
  return (
    <div className="flex-1 flex items-center justify-center bg-aion-bg text-aion-muted">
      <div className="text-center">
        <div className="w-6 h-6 border-2 border-aion-accent/30 border-t-aion-accent rounded-full animate-spin mx-auto mb-2" />
        <p className="text-sm">Cargando editor...</p>
      </div>
    </div>
  )
}

export default function CodeEditor() {
  const { project, updateFile } = useEditorStore()
  const { activeFile, files } = project
  const content = files[activeFile] ?? ''
  const language = getLanguageFromFilename(activeFile)

  const handleChange = (value: string | undefined) => {
    if (value !== undefined) {
      updateFile(activeFile, value)
    }
  }

  if (!activeFile) {
    return (
      <div className="flex-1 flex items-center justify-center bg-aion-bg text-aion-muted">
        <div className="text-center">
          <div className="text-5xl mb-4">📄</div>
          <p className="text-lg font-medium text-aion-text mb-1">Sin archivo abierto</p>
          <p className="text-sm">Selecciona un archivo del panel lateral</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0">
      <MonacoEditor
        height="100%"
        language={language}
        value={content}
        onChange={handleChange}
        theme="vs-dark"
        options={{
          fontSize: 14,
          fontFamily: '"JetBrains Mono", "Fira Code", "Cascadia Code", monospace',
          fontLigatures: true,
          lineNumbers: 'on',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: 'on',
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: 'gutter',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          bracketPairColorization: { enabled: true },
          guides: { bracketPairs: true },
          suggest: { preview: true },
          inlayHints: { enabled: 'on' },
          formatOnType: true,
          formatOnPaste: true,
          contextmenu: true,
          quickSuggestions: {
            other: true,
            comments: true,
            strings: true,
          },
        }}
        beforeMount={(monaco) => {
          // Custom theme
          monaco.editor.defineTheme('aion-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
              { token: 'comment', foreground: '6b7280', fontStyle: 'italic' },
              { token: 'keyword', foreground: 'c084fc' },
              { token: 'string', foreground: '86efac' },
              { token: 'number', foreground: 'fbbf24' },
              { token: 'type', foreground: '67e8f9' },
              { token: 'variable', foreground: 'e2e8f0' },
              { token: 'function', foreground: 'fde68a' },
            ],
            colors: {
              'editor.background': '#0a0a0f',
              'editor.foreground': '#e2e8f0',
              'editor.lineHighlightBackground': '#12121a',
              'editor.selectionBackground': '#7c3aed33',
              'editor.inactiveSelectionBackground': '#7c3aed1a',
              'editorLineNumber.foreground': '#374151',
              'editorLineNumber.activeForeground': '#7c3aed',
              'editorCursor.foreground': '#7c3aed',
              'editor.findMatchBackground': '#7c3aed40',
              'editor.findMatchHighlightBackground': '#7c3aed20',
              'editorWidget.background': '#12121a',
              'editorWidget.border': '#2a2a3d',
              'editorSuggestWidget.background': '#12121a',
              'editorSuggestWidget.border': '#2a2a3d',
              'editorSuggestWidget.selectedBackground': '#1e1a2e',
              'scrollbarSlider.background': '#2a2a3d80',
              'scrollbarSlider.hoverBackground': '#3d3d5c80',
            },
          })
          monaco.editor.setTheme('aion-dark')
        }}
      />
    </div>
  )
}
