import Link from 'next/link'
import Hero from '@/components/landing/Hero'
import Features from '@/components/landing/Features'
import TemplatesSection from '@/components/landing/TemplatesSection'
import { ArrowRight, Github } from 'lucide-react'

export default function Home() {
  return (
    <main className="min-h-screen bg-aion-bg text-aion-text">
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 h-14 border-b border-aion-border/50 bg-aion-bg/80 backdrop-blur-xl">
        <Link href="/" className="flex items-center gap-2 font-black text-xl">
          <span>⚡</span>
          <span className="bg-gradient-to-r from-aion-accent-light to-aion-blue bg-clip-text text-transparent">
            AION
          </span>
          <span className="text-aion-muted font-normal text-sm">Builder</span>
        </Link>

        <div className="hidden md:flex items-center gap-6 text-sm text-aion-muted">
          <a href="#features" className="hover:text-aion-text transition-colors">Características</a>
          <a href="#templates" className="hover:text-aion-text transition-colors">Plantillas</a>
          <a href="#" className="hover:text-aion-text transition-colors">Docs</a>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/editor"
            className="flex items-center gap-1.5 bg-aion-accent hover:bg-aion-accent-light text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          >
            Empezar gratis
            <ArrowRight size={14} />
          </Link>
        </div>
      </nav>

      {/* Spacer for fixed nav */}
      <div className="h-14" />

      {/* Hero */}
      <Hero />

      {/* Features */}
      <div id="features">
        <Features />
      </div>

      {/* Templates */}
      <div id="templates">
        <TemplatesSection />
      </div>

      {/* Footer */}
      <footer className="border-t border-aion-border py-8 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span>⚡</span>
            <span className="font-bold text-aion-text">AION Builder</span>
            <span className="text-aion-muted text-sm">· App para cambiar tu vida</span>
          </div>
          <p className="text-aion-muted text-sm">
            Construido con ❤️ · {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </main>
  )
}
