'use client'

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { TEMPLATES } from '@/lib/templates'

export default function TemplatesSection() {
  return (
    <section className="py-24 px-4 relative">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-aion-accent/3 to-transparent pointer-events-none" />

      <div className="max-w-6xl mx-auto relative">
        <div className="text-center mb-16">
          <span className="text-aion-accent-light text-sm font-semibold uppercase tracking-widest">
            Plantillas
          </span>
          <h2 className="text-4xl md:text-5xl font-black text-aion-text mt-3 mb-4">
            Empieza con una plantilla
          </h2>
          <p className="text-aion-muted text-lg max-w-2xl mx-auto">
            Elige una plantilla de inicio y personalízala a tu gusto. Desde landing pages hasta dashboards completos.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {TEMPLATES.map((template) => (
            <Link
              key={template.id}
              href={`/editor?template=${template.id}`}
              className="group block bg-aion-surface border border-aion-border rounded-2xl overflow-hidden hover:border-aion-accent/50 transition-all duration-300 hover:-translate-y-1"
            >
              {/* Preview area */}
              <div
                className="h-36 flex items-center justify-center relative overflow-hidden"
                style={{ background: `${template.color}12` }}
              >
                <div className="text-5xl">{template.icon}</div>
                <div
                  className="absolute inset-0 opacity-10"
                  style={{
                    backgroundImage: `linear-gradient(${template.color} 1px, transparent 1px), linear-gradient(90deg, ${template.color} 1px, transparent 1px)`,
                    backgroundSize: '20px 20px',
                  }}
                />
              </div>

              {/* Info */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="font-bold text-aion-text">{template.name}</h3>
                  <ArrowRight
                    size={16}
                    className="text-aion-muted group-hover:text-aion-accent-light group-hover:translate-x-1 transition-all"
                  />
                </div>
                <p className="text-sm text-aion-muted">{template.description}</p>
              </div>
            </Link>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <div className="inline-flex flex-col items-center gap-6 bg-aion-surface border border-aion-border rounded-3xl p-10">
            <div className="text-6xl">🚀</div>
            <div>
              <h3 className="text-2xl font-black text-aion-text mb-2">
                ¿Listo para construir?
              </h3>
              <p className="text-aion-muted">
                Sin registro. Sin instalaciones. Empieza a crear ahora mismo.
              </p>
            </div>
            <Link
              href="/editor"
              className="flex items-center gap-2 bg-aion-accent hover:bg-aion-accent-light text-white font-semibold px-8 py-4 rounded-xl transition-colors text-lg"
            >
              Abrir el Editor
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
