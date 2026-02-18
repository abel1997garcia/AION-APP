'use client'

import { useRef } from 'react'
import { Upload, Trash2, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { useEditorStore } from '@/lib/store'
import { formatBytes } from '@/lib/utils'

export default function ImagePanel() {
  const { project, addImage, removeImage } = useEditorStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach((file) => {
      if (!file.type.startsWith('image/')) return
      const reader = new FileReader()
      reader.onload = (e) => {
        const dataUrl = e.target?.result as string
        const img = new window.Image()
        img.onload = () => {
          addImage({
            name: file.name,
            dataUrl,
            type: file.type,
            size: file.size,
            width: img.width,
            height: img.height,
          })
        }
        img.src = dataUrl
      }
      reader.readAsDataURL(file)
    })
  }

  const handleCopyUrl = (id: string, dataUrl: string) => {
    navigator.clipboard.writeText(dataUrl)
    setCopied(id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-aion-border shrink-0">
        <span className="text-xs font-semibold uppercase tracking-wider text-aion-muted">Imágenes</span>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-1 rounded text-aion-muted hover:text-pink-400 hover:bg-pink-400/10 transition-colors"
          title="Subir imagen"
        >
          <Upload size={14} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Drop zone */}
        <div
          className={`m-3 border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
            dragging ? 'border-pink-400 bg-pink-400/10' : 'border-aion-border hover:border-pink-400/50'
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
        >
          <div className="text-3xl mb-2">🖼️</div>
          <p className="text-xs text-aion-muted">
            Arrastra imágenes aquí o <span className="text-pink-400">haz clic</span>
          </p>
          <p className="text-[10px] text-aion-muted mt-1">PNG, JPG, GIF, SVG, WebP</p>
        </div>

        {/* Image grid */}
        {project.images.length > 0 && (
          <div className="grid grid-cols-2 gap-2 px-3 pb-3">
            {project.images.map((img) => (
              <div
                key={img.id}
                className="group relative bg-aion-surface border border-aion-border rounded-xl overflow-hidden hover:border-pink-400/40 transition-colors"
              >
                {/* Image preview */}
                <div className="aspect-square bg-[url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAGElEQVQoU2NkYGBgJAYAAf8AAP9/AAAACQAAAAoBAAE0AAAAABJRU5ErkJggg==')] bg-repeat">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={img.dataUrl}
                    alt={img.name}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Info overlay */}
                <div className="p-2">
                  <p className="text-[10px] font-medium text-aion-text truncate">{img.name}</p>
                  <p className="text-[9px] text-aion-muted">
                    {img.width}×{img.height} · {formatBytes(img.size)}
                  </p>
                </div>

                {/* Actions overlay */}
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <button
                    onClick={() => handleCopyUrl(img.id, img.dataUrl)}
                    title="Copiar URL"
                    className="p-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
                  >
                    {copied === img.id ? <Check size={14} /> : <Copy size={14} />}
                  </button>
                  <button
                    onClick={() => removeImage(img.id)}
                    title="Eliminar"
                    className="p-2 bg-red-500/20 hover:bg-red-500/40 rounded-lg text-red-400 transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {project.images.length === 0 && (
          <p className="text-center text-xs text-aion-muted py-4">
            Sube imágenes para usarlas en tu proyecto
          </p>
        )}
      </div>

      {/* Stats */}
      {project.images.length > 0 && (
        <div className="px-3 py-2 border-t border-aion-border shrink-0">
          <p className="text-[10px] text-aion-muted">
            {project.images.length} imagen{project.images.length !== 1 ? 'es' : ''} ·{' '}
            {formatBytes(project.images.reduce((s, i) => s + i.size, 0))}
          </p>
        </div>
      )}
    </div>
  )
}
