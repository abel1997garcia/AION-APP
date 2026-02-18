'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import dynamic from 'next/dynamic'

const EditorLayout = dynamic(
  () => import('@/components/editor/EditorLayout'),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-screen items-center justify-center bg-[#0a0a0f]">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-pulse">⚡</div>
          <p className="text-[#7c3aed] font-semibold text-lg mb-2">AION Builder</p>
          <p className="text-[#64748b] text-sm">Preparando el editor...</p>
          <div className="mt-4 flex justify-center gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 bg-[#7c3aed] rounded-full animate-bounce"
                style={{ animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>
        </div>
      </div>
    ),
  }
)

function EditorWithParams() {
  const searchParams = useSearchParams()
  const templateId = searchParams.get('template') || undefined
  return <EditorLayout templateId={templateId} />
}

export default function EditorPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[#0a0a0f]">
          <div className="text-center">
            <div className="text-5xl mb-4 animate-pulse">⚡</div>
            <p className="text-[#7c3aed] font-semibold text-lg">AION Builder</p>
          </div>
        </div>
      }
    >
      <EditorWithParams />
    </Suspense>
  )
}
