'use client'

import Link from 'next/link'
import { ArrowRight, Zap, Code2, Eye } from 'lucide-react'

export default function Hero() {
  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden px-4">
      {/* Background glow effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-aion-accent/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-aion-blue/10 rounded-full blur-[100px]" />
      </div>

      {/* Grid pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(#7c3aed 1px, transparent 1px), linear-gradient(90deg, #7c3aed 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Badge */}
      <div className="relative flex items-center gap-2 bg-aion-accent/10 border border-aion-accent/30 rounded-full px-4 py-1.5 mb-8 text-sm text-aion-accent-light">
        <Zap size={14} />
        <span>Build. Preview. Ship.</span>
      </div>

      {/* Title */}
      <h1 className="relative text-center font-black leading-tight mb-6" style={{ fontSize: 'clamp(2.5rem, 7vw, 5.5rem)' }}>
        <span className="text-aion-text">Construye cualquier</span>
        <br />
        <span className="bg-gradient-to-r from-aion-accent via-purple-400 to-aion-blue bg-clip-text text-transparent">
          cosa que imagines
        </span>
      </h1>

      <p className="relative text-center text-aion-muted max-w-2xl mb-10 leading-relaxed" style={{ fontSize: 'clamp(1rem, 2.5vw, 1.25rem)' }}>
        Editor de código profesional con preview en tiempo real, base de datos integrada,
        APIs, imágenes y audio. Todo lo que necesitas para dar vida a tus ideas.
      </p>

      {/* CTA Buttons */}
      <div className="relative flex flex-wrap gap-4 justify-center mb-16">
        <Link
          href="/editor"
          className="group flex items-center gap-2 bg-aion-accent hover:bg-aion-accent-light text-white font-semibold px-8 py-4 rounded-xl transition-all duration-200 text-lg shadow-lg shadow-aion-accent/25"
        >
          Empezar a crear
          <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
        </Link>
        <Link
          href="/editor"
          className="flex items-center gap-2 border border-aion-border hover:border-aion-accent/50 text-aion-text font-semibold px-8 py-4 rounded-xl transition-all duration-200 text-lg"
        >
          <Code2 size={20} />
          Ver demo
        </Link>
      </div>

      {/* Preview mockup */}
      <div className="relative w-full max-w-5xl">
        <div className="bg-aion-surface border border-aion-border rounded-2xl overflow-hidden shadow-2xl">
          {/* Window bar */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-aion-border bg-aion-panel">
            <div className="w-3 h-3 rounded-full bg-red-500/70" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
            <div className="w-3 h-3 rounded-full bg-green-500/70" />
            <div className="flex-1 flex justify-center">
              <div className="bg-aion-bg border border-aion-border rounded-md px-4 py-1 text-xs text-aion-muted">
                aion.app/editor
              </div>
            </div>
          </div>

          {/* Editor mockup body */}
          <div className="flex h-72">
            {/* Sidebar icons */}
            <div className="w-12 bg-aion-panel border-r border-aion-border flex flex-col items-center gap-3 py-3">
              {['📁', '🗄️', '🔌', '🖼️', '🎵'].map((icon, i) => (
                <div key={i} className="w-8 h-8 flex items-center justify-center text-base rounded hover:bg-aion-border/50 cursor-pointer">
                  {icon}
                </div>
              ))}
            </div>

            {/* File tree */}
            <div className="w-44 border-r border-aion-border bg-aion-surface/50 py-3 px-2 text-xs font-mono">
              <div className="text-aion-muted px-2 mb-2 font-sans text-[11px] uppercase tracking-wider">Archivos</div>
              {['App.tsx', 'index.css', 'components/', 'utils.ts'].map((f, i) => (
                <div key={i} className={`px-2 py-1 rounded cursor-pointer text-aion-muted hover:text-aion-text ${i === 0 ? 'bg-aion-accent/20 text-aion-accent-light' : ''}`}>
                  {i === 2 ? '📂 ' : '📄 '}{f}
                </div>
              ))}
            </div>

            {/* Code area */}
            <div className="flex-1 bg-aion-bg py-3 px-4 font-mono text-xs overflow-hidden">
              <div className="flex gap-6 text-[11px] text-aion-muted border-b border-aion-border pb-2 mb-2">
                <span className="text-aion-accent-light border-b border-aion-accent pb-2">App.tsx</span>
                <span>index.css</span>
              </div>
              {[
                { line: '1', code: <><span className="text-purple-400">import</span> <span className="text-sky-300">{'{'} useState {'}'}</span> <span className="text-purple-400">from</span> <span className="text-green-400">&quot;react&quot;</span></> },
                { line: '2', code: '' },
                { line: '3', code: <><span className="text-purple-400">export default function</span> <span className="text-yellow-300">App</span>() {'{'}</> },
                { line: '4', code: <>&nbsp;&nbsp;<span className="text-purple-400">const</span> [count, setCount] = <span className="text-yellow-300">useState</span>(0)</> },
                { line: '5', code: '' },
                { line: '6', code: <>&nbsp;&nbsp;<span className="text-purple-400">return</span> {'('}</> },
                { line: '7', code: <>&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-red-400">{'<div'}</span> <span className="text-sky-300">className</span>=<span className="text-green-400">&quot;app&quot;</span><span className="text-red-400">{'>'}</span></> },
                { line: '8', code: <>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span className="text-red-400">{'<h1>'}</span><span className="text-aion-text">⚡ AION Builder</span><span className="text-red-400">{'</h1>'}</span></> },
              ].map(({ line, code }, i) => (
                <div key={i} className="flex gap-4 leading-6">
                  <span className="text-aion-muted/40 w-4 text-right select-none">{line}</span>
                  <span className="text-aion-text/80">{code}</span>
                </div>
              ))}
            </div>

            {/* Preview */}
            <div className="w-64 border-l border-aion-border bg-white flex flex-col">
              <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-200 bg-gray-50">
                <Eye size={12} className="text-gray-400" />
                <span className="text-xs text-gray-500">Preview</span>
                <div className="w-2 h-2 rounded-full bg-green-500 ml-auto" />
              </div>
              <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-purple-500 to-blue-500 p-4">
                <div className="text-white text-center">
                  <div className="text-2xl font-bold mb-1">⚡ AION</div>
                  <div className="text-sm opacity-80 mb-3">Counter: 0</div>
                  <button className="bg-white text-purple-600 text-xs font-bold px-3 py-1.5 rounded-lg">
                    Click me!
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Floating badges */}
        <div className="absolute -top-4 -right-4 bg-aion-green/10 border border-aion-green/30 rounded-lg px-3 py-1.5 text-aion-green text-sm font-medium">
          ● Live Preview
        </div>
        <div className="absolute -bottom-4 -left-4 bg-aion-blue/10 border border-aion-blue/30 rounded-lg px-3 py-1.5 text-aion-blue text-sm font-medium">
          Monaco Editor
        </div>
      </div>
    </section>
  )
}
