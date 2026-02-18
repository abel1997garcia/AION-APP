'use client'

import { Trash2, Terminal, ChevronDown, ChevronUp } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { cn } from '@/lib/utils'

const typeColors: Record<string, string> = {
  log: 'text-aion-text',
  error: 'text-red-400',
  warn: 'text-yellow-400',
  info: 'text-blue-400',
}

const typeBg: Record<string, string> = {
  log: '',
  error: 'bg-red-500/5',
  warn: 'bg-yellow-500/5',
  info: 'bg-blue-500/5',
}

export default function ConsolePanel() {
  const { consoleMessages, clearConsole, consoleOpen, setConsoleOpen } = useEditorStore()

  return (
    <div className={cn('border-t border-aion-border bg-aion-bg transition-all', consoleOpen ? 'h-40' : 'h-8')}>
      {/* Console header */}
      <div
        className="flex items-center gap-2 px-3 h-8 cursor-pointer hover:bg-aion-border/20 transition-colors shrink-0"
        onClick={() => setConsoleOpen(!consoleOpen)}
      >
        <Terminal size={13} className="text-aion-muted" />
        <span className="text-xs font-medium text-aion-muted">Consola</span>
        {consoleMessages.length > 0 && (
          <span className="bg-aion-accent/30 text-aion-accent-light text-[10px] px-1.5 py-0.5 rounded-full font-bold">
            {consoleMessages.length}
          </span>
        )}
        <div className="flex-1" />
        <button
          onClick={(e) => { e.stopPropagation(); clearConsole() }}
          title="Limpiar consola"
          className="p-0.5 rounded text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
        >
          <Trash2 size={12} />
        </button>
        {consoleOpen ? <ChevronDown size={13} className="text-aion-muted" /> : <ChevronUp size={13} className="text-aion-muted" />}
      </div>

      {/* Messages */}
      {consoleOpen && (
        <div className="h-32 overflow-y-auto font-mono text-xs">
          {consoleMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-aion-muted">
              La consola está vacía
            </div>
          ) : (
            consoleMessages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  'flex gap-3 px-3 py-1 border-b border-aion-border/30',
                  typeBg[msg.type]
                )}
              >
                <span className="text-aion-muted/50 shrink-0 select-none">
                  {new Date(msg.timestamp).toLocaleTimeString('es', { hour12: false })}
                </span>
                <span className={cn('shrink-0 uppercase text-[10px] font-bold w-8', typeColors[msg.type])}>
                  {msg.type}
                </span>
                <span className={cn('flex-1 break-all', typeColors[msg.type])}>
                  {msg.content}
                </span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
