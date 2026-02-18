'use client'

const features = [
  {
    icon: '⚡',
    title: 'Editor Monaco',
    description: 'El mismo motor de VS Code. Autocompletado inteligente, resaltado de sintaxis, multi-cursor y mucho más.',
    color: '#7c3aed',
    tags: ['IntelliSense', 'Multi-cursor', 'Git diff'],
  },
  {
    icon: '👁️',
    title: 'Preview en Tiempo Real',
    description: 'Ve los cambios al instante. Soporte para React, HTML/CSS, JavaScript vanilla y más frameworks.',
    color: '#3b82f6',
    tags: ['React', 'HTML/CSS', 'Vanilla JS'],
  },
  {
    icon: '🗄️',
    title: 'Base de Datos',
    description: 'Diseña tablas, define esquemas y trabaja con datos directamente en tu proyecto sin configuración extra.',
    color: '#22c55e',
    tags: ['Tablas', 'Esquemas', 'Mock data'],
  },
  {
    icon: '🔌',
    title: 'APIs & Endpoints',
    description: 'Integra APIs externas o crea endpoints mock para prototipar sin necesitar un backend real.',
    color: '#eab308',
    tags: ['REST', 'Mock', 'Headers'],
  },
  {
    icon: '🖼️',
    title: 'Gestión de Imágenes',
    description: 'Sube, gestiona y usa imágenes directamente en tu código. Optimización automática incluida.',
    color: '#ec4899',
    tags: ['Upload', 'Preview', 'Base64'],
  },
  {
    icon: '🎵',
    title: 'Audio & Media',
    description: 'Integra archivos de audio en tus proyectos. Perfecto para apps de música, juegos y experiencias interactivas.',
    color: '#f97316',
    tags: ['MP3/WAV', 'Player', 'Controls'],
  },
]

export default function Features() {
  return (
    <section className="py-32 px-4 relative">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <span className="text-aion-accent-light text-sm font-semibold uppercase tracking-widest">
            Características
          </span>
          <h2 className="text-4xl md:text-5xl font-black text-aion-text mt-3 mb-4">
            Todo lo que necesitas
          </h2>
          <p className="text-aion-muted text-lg max-w-2xl mx-auto">
            Una plataforma completa para construir, probar y lanzar tus aplicaciones sin salir del navegador.
          </p>
        </div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="group relative bg-aion-surface border border-aion-border rounded-2xl p-6 hover:border-aion-border/80 transition-all duration-300 overflow-hidden"
            >
              {/* Hover glow */}
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 rounded-2xl"
                style={{ background: feature.color }}
              />

              {/* Icon */}
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4"
                style={{ background: `${feature.color}15`, border: `1px solid ${feature.color}30` }}
              >
                {feature.icon}
              </div>

              <h3 className="text-xl font-bold text-aion-text mb-2">{feature.title}</h3>
              <p className="text-aion-muted leading-relaxed mb-4">{feature.description}</p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {feature.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded-md font-medium"
                    style={{ color: feature.color, background: `${feature.color}15`, border: `1px solid ${feature.color}25` }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
