'use client'

import { useEffect } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { useEditorStore } from '@/lib/store'
import Toolbar from './Toolbar'
import Sidebar from './Sidebar'
import FileTree from './FileTree'
import TabBar from './TabBar'
import CodeEditor from './CodeEditor'
import PreviewPanel from './PreviewPanel'
import ConsolePanel from './ConsolePanel'
import DatabasePanel from '@/components/panels/DatabasePanel'
import ApiPanel from '@/components/panels/ApiPanel'
import ImagePanel from '@/components/panels/ImagePanel'
import AudioPanel from '@/components/panels/AudioPanel'
import { TEMPLATES } from '@/lib/templates'
import type { SidebarTab } from '@/types'

const panelComponents: Record<SidebarTab, React.ReactNode> = {
  files: <FileTree />,
  database: <DatabasePanel />,
  api: <ApiPanel />,
  images: <ImagePanel />,
  audio: <AudioPanel />,
}

const panelLabels: Record<SidebarTab, string> = {
  files: 'Explorador',
  database: 'Base de datos',
  api: 'APIs',
  images: 'Imágenes',
  audio: 'Audio',
}

interface EditorLayoutProps {
  templateId?: string
}

export default function EditorLayout({ templateId }: EditorLayoutProps) {
  const { sidebarTab, sidebarOpen, setProject, project } = useEditorStore()

  // Load template if specified
  useEffect(() => {
    if (templateId) {
      const template = TEMPLATES.find(t => t.id === templateId)
      if (template) {
        setProject({
          ...project,
          template: template.template,
          files: template.files,
          activeFile: template.activeFile,
          openFiles: [template.activeFile],
          name: template.name,
        })
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId])

  return (
    <div className="flex flex-col h-screen bg-aion-bg overflow-hidden">
      {/* Top toolbar */}
      <Toolbar />

      {/* Main content */}
      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Sidebar icon rail */}
        <Sidebar />

        {/* Sidebar panel */}
        {sidebarOpen && (
          <div className="w-52 shrink-0 flex flex-col border-r border-aion-border bg-aion-surface overflow-hidden">
            <div className="flex items-center gap-2 px-3 py-1.5 border-b border-aion-border bg-aion-panel">
              <span className="text-[10px] font-bold uppercase tracking-widest text-aion-accent-light">
                {panelLabels[sidebarTab]}
              </span>
            </div>
            <div className="flex-1 overflow-hidden">
              {panelComponents[sidebarTab]}
            </div>
          </div>
        )}

        {/* Editor + Preview split */}
        <PanelGroup direction="horizontal" className="flex-1">
          {/* Code Editor */}
          <Panel defaultSize={50} minSize={25}>
            <div className="flex flex-col h-full">
              <TabBar />
              <CodeEditor />
              <ConsolePanel />
            </div>
          </Panel>

          {/* Resize handle */}
          <PanelResizeHandle className="w-1 bg-aion-border hover:bg-aion-accent/50 transition-colors cursor-col-resize group">
            <div className="w-full h-full flex items-center justify-center">
              <div className="w-0.5 h-8 bg-aion-border group-hover:bg-aion-accent/50 rounded-full transition-colors" />
            </div>
          </PanelResizeHandle>

          {/* Preview */}
          <Panel defaultSize={50} minSize={20}>
            <PreviewPanel />
          </Panel>
        </PanelGroup>
      </div>
    </div>
  )
}
