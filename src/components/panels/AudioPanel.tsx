'use client'

import { useRef, useState } from 'react'
import { Upload, Trash2, Play, Pause, Copy, Check } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { formatBytes, formatDuration } from '@/lib/utils'

export default function AudioPanel() {
  const { project, addAudio, removeAudio } = useEditorStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [playing, setPlaying] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const audioRefs = useRef<Record<string, HTMLAudioElement>>({})

  const handleFiles = (files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach((file) => {
      if (!file.type.startsWith('audio/')) return
      const reader = new FileReader()
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string
        const audio = new Audio(dataUrl)
        audio.addEventListener('loadedmetadata', () => {
          addAudio({
            name: file.name,
            dataUrl,
            type: file.type,
            size: file.size,
            duration: audio.duration,
          })
        })
      }
      reader.readAsDataURL(file)
    })
  }

  const handlePlay = (id: string, dataUrl: string) => {
    if (playing === id) {
      audioRefs.current[id]?.pause()
      setPlaying(null)
      return
    }
    // Pause any currently playing
    if (playing && audioRefs.current[playing]) {
      audioRefs.current[playing].pause()
    }
    if (!audioRefs.current[id]) {
      audioRefs.current[id] = new Audio(dataUrl)
      audioRefs.current[id].addEventListener('ended', () => setPlaying(null))
    }
    audioRefs.current[id].play()
    setPlaying(id)
  }

  const handleCopy = (id: string, dataUrl: string) => {
    navigator.clipboard.writeText(dataUrl)
    setCopied(id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-aion-border shrink-0">
        <span className="text-xs font-semibold uppercase tracking-wider text-aion-muted">Audio</span>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-1 rounded text-aion-muted hover:text-orange-400 hover:bg-orange-400/10 transition-colors"
          title="Subir audio"
        >
          <Upload size={14} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Drop zone */}
        <div
          className={`m-3 border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
            dragging ? 'border-orange-400 bg-orange-400/10' : 'border-aion-border hover:border-orange-400/50'
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
        >
          <div className="text-3xl mb-2">🎵</div>
          <p className="text-xs text-aion-muted">
            Arrastra archivos de audio o <span className="text-orange-400">haz clic</span>
          </p>
          <p className="text-[10px] text-aion-muted mt-1">MP3, WAV, OGG, M4A, FLAC</p>
        </div>

        {/* Audio list */}
        {project.audios.length > 0 && (
          <div className="px-3 pb-3 space-y-2">
            {project.audios.map((audio) => (
              <div
                key={audio.id}
                className="group bg-aion-surface border border-aion-border rounded-xl p-3 hover:border-orange-400/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {/* Play button */}
                  <button
                    onClick={() => handlePlay(audio.id, audio.dataUrl)}
                    className={`w-9 h-9 flex items-center justify-center rounded-full shrink-0 transition-colors ${
                      playing === audio.id
                        ? 'bg-orange-400 text-white'
                        : 'bg-aion-panel border border-aion-border text-aion-muted hover:text-orange-400 hover:border-orange-400/50'
                    }`}
                  >
                    {playing === audio.id ? <Pause size={14} /> : <Play size={14} />}
                  </button>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-aion-text truncate">{audio.name}</p>
                    <p className="text-[10px] text-aion-muted">
                      {audio.duration ? formatDuration(audio.duration) : '?'} · {formatBytes(audio.size)}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleCopy(audio.id, audio.dataUrl)}
                      title="Copiar URL"
                      className="p-1 rounded hover:bg-aion-border/30 text-aion-muted hover:text-aion-text transition-colors"
                    >
                      {copied === audio.id ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                    <button
                      onClick={() => {
                        if (playing === audio.id) { audioRefs.current[audio.id]?.pause(); setPlaying(null) }
                        removeAudio(audio.id)
                      }}
                      title="Eliminar"
                      className="p-1 rounded hover:bg-red-500/20 text-aion-muted hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>

                {/* Waveform placeholder */}
                {playing === audio.id && (
                  <div className="mt-2 flex items-center gap-0.5 h-6">
                    {Array.from({ length: 24 }).map((_, i) => (
                      <div
                        key={i}
                        className="flex-1 bg-orange-400/60 rounded-full animate-pulse"
                        style={{
                          height: `${20 + Math.sin(i * 0.8) * 14}px`,
                          animationDelay: `${i * 0.05}s`,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {project.audios.length === 0 && (
          <p className="text-center text-xs text-aion-muted py-4">
            Sube archivos de audio para tu proyecto
          </p>
        )}
      </div>

      {/* Stats */}
      {project.audios.length > 0 && (
        <div className="px-3 py-2 border-t border-aion-border shrink-0">
          <p className="text-[10px] text-aion-muted">
            {project.audios.length} archivo{project.audios.length !== 1 ? 's' : ''} ·{' '}
            {formatBytes(project.audios.reduce((s, a) => s + a.size, 0))}
          </p>
        </div>
      )}
    </div>
  )
}
