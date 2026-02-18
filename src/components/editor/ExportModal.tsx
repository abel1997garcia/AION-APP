'use client'

import { useState } from 'react'
import { X, Download, Smartphone, Globe, Package, Check, Loader2, ExternalLink } from 'lucide-react'
import { useEditorStore } from '@/lib/store'
import { exportAsWebZip, exportAsPWA, exportAsCapacitor } from '@/lib/export'
import { cn } from '@/lib/utils'

interface ExportModalProps {
  onClose: () => void
}

type ExportType = 'web' | 'pwa' | 'capacitor'

const options: {
  id: ExportType
  icon: React.ReactNode
  title: string
  subtitle: string
  description: string
  badge?: { label: string; color: string }
  color: string
  features: string[]
  stores?: { name: string; cost: string }[]
}[] = [
  {
    id: 'web',
    icon: <Globe size={22} />,
    title: 'Web App',
    subtitle: 'Vercel · Netlify · GitHub Pages',
    description: 'Descarga tu proyecto como ZIP y súbelo a cualquier hosting web.',
    color: '#3b82f6',
    features: [
      'Todos los archivos del proyecto',
      'Listo para Vercel, Netlify, GitHub Pages',
      'Sin configuración adicional',
    ],
  },
  {
    id: 'pwa',
    icon: <Smartphone size={22} />,
    title: 'PWA Instalable',
    subtitle: 'iOS · Android · Escritorio',
    description:
      'Añade capacidades nativas. Los usuarios pueden instalarla desde el navegador directamente en su pantalla de inicio.',
    badge: { label: 'Gratis', color: '#22c55e' },
    color: '#7c3aed',
    features: [
      'manifest.json con metadatos de la app',
      'Service Worker para modo offline',
      'Iconos generados automáticamente (192×192, 512×512)',
      'Meta tags para iOS (apple-touch-icon, etc.)',
      'Instalable en iOS y Android sin App Store',
    ],
  },
  {
    id: 'capacitor',
    icon: <Package size={22} />,
    title: 'App Nativa — App Store & Google Play',
    subtitle: 'iOS (Xcode) · Android (Android Studio)',
    description:
      'Exporta como proyecto Capacitor. Compila a app nativa y publica en las tiendas oficiales con todas las capacidades del dispositivo.',
    badge: { label: 'App Stores', color: '#f97316' },
    color: '#f97316',
    features: [
      'Proyecto Vite + React + Capacitor 5',
      'capacitor.config.ts configurado',
      'manifest.json + iconos incluidos',
      'Acceso a cámara, GPS, notificaciones push, etc.',
      'Compatible con Xcode (iOS) y Android Studio',
      'README con instrucciones paso a paso',
    ],
    stores: [
      { name: 'App Store (iOS)', cost: '$99/año' },
      { name: 'Google Play (Android)', cost: '$25 único pago' },
    ],
  },
]

export default function ExportModal({ onClose }: ExportModalProps) {
  const { project } = useEditorStore()
  const [loading, setLoading] = useState<ExportType | null>(null)
  const [done, setDone] = useState<ExportType | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async (type: ExportType) => {
    setLoading(type)
    setError(null)
    try {
      if (type === 'web') await exportAsWebZip(project)
      if (type === 'pwa') await exportAsPWA(project)
      if (type === 'capacitor') await exportAsCapacitor(project)
      setDone(type)
      setTimeout(() => setDone(null), 2500)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al exportar')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-aion-surface border border-aion-border rounded-t-3xl sm:rounded-2xl w-full max-w-2xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-aion-surface border-b border-aion-border flex items-center justify-between p-5 z-10">
          <div>
            <h2 className="text-lg font-bold text-aion-text">Exportar proyecto</h2>
            <p className="text-xs text-aion-muted mt-0.5">
              <span className="text-aion-accent-light font-medium">{project.name}</span>
              {' '}·{' '}
              {Object.keys(project.files).length} archivos
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-aion-muted hover:text-aion-text hover:bg-aion-border/30 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Export options */}
        <div className="p-5 space-y-3">
          {options.map((opt) => {
            const isLoading = loading === opt.id
            const isDone = done === opt.id

            return (
              <div
                key={opt.id}
                className="border border-aion-border rounded-xl p-4 hover:border-aion-border/80 transition-all group"
                style={{ borderColor: isDone ? opt.color + '60' : undefined }}
              >
                <div className="flex gap-4">
                  {/* Icon */}
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ background: `${opt.color}15`, color: opt.color, border: `1px solid ${opt.color}25` }}
                  >
                    {opt.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center flex-wrap gap-2 mb-0.5">
                      <span className="font-bold text-aion-text text-sm">{opt.title}</span>
                      {opt.badge && (
                        <span
                          className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
                          style={{ color: opt.badge.color, background: `${opt.badge.color}18` }}
                        >
                          {opt.badge.label}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-aion-muted mb-2">{opt.subtitle}</p>
                    <p className="text-xs text-aion-muted leading-relaxed mb-3">{opt.description}</p>

                    {/* Features */}
                    <ul className="space-y-1 mb-3">
                      {opt.features.map((f) => (
                        <li key={f} className="flex items-center gap-1.5 text-[11px] text-aion-muted">
                          <Check size={10} style={{ color: opt.color, flexShrink: 0 }} />
                          {f}
                        </li>
                      ))}
                    </ul>

                    {/* Store costs */}
                    {opt.stores && (
                      <div className="flex gap-3 mb-3">
                        {opt.stores.map((store) => (
                          <div
                            key={store.name}
                            className="flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-lg border"
                            style={{ borderColor: `${opt.color}30`, color: opt.color, background: `${opt.color}08` }}
                          >
                            <span className="font-semibold">{store.name}</span>
                            <span className="opacity-70">— {store.cost}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Export button */}
                    <button
                      onClick={() => handleExport(opt.id)}
                      disabled={loading !== null}
                      className={cn(
                        'flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                      style={{
                        background: isDone ? `${opt.color}20` : `${opt.color}12`,
                        color: opt.color,
                        border: `1px solid ${opt.color}30`,
                      }}
                    >
                      {isLoading ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : isDone ? (
                        <Check size={13} />
                      ) : (
                        <Download size={13} />
                      )}
                      {isLoading
                        ? 'Generando ZIP...'
                        : isDone
                        ? '¡Descarga lista!'
                        : `Exportar como ${opt.title.split('—')[0].trim()}`}
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-5 mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400">
            {error}
          </div>
        )}

        {/* Info card */}
        <div className="px-5 pb-6">
          <div className="bg-aion-panel border border-aion-border rounded-xl p-4 text-xs">
            <p className="font-semibold text-aion-text mb-2.5">💡 ¿Cuál elegir?</p>
            <div className="space-y-2 text-aion-muted">
              <p>
                <span className="text-aion-text font-medium">Web App</span> → Si quieres publicar en Vercel/Netlify
                con tu propio dominio.
              </p>
              <p>
                <span className="text-aion-text font-medium">PWA</span> → Si quieres experiencia de app nativa gratis,
                sin pasar por App Store ni Google Play.
              </p>
              <p>
                <span className="text-aion-text font-medium">Capacitor</span> → Si quieres estar en las tiendas
                oficiales con acceso a sensores, notificaciones push y más.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
