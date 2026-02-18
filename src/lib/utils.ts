import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { Language } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function getLanguageFromFilename(filename: string): Language {
  const ext = filename.split('.').pop()?.toLowerCase()
  const map: Record<string, Language> = {
    js: 'javascript',
    jsx: 'javascript',
    ts: 'typescript',
    tsx: 'typescript',
    html: 'html',
    css: 'css',
    json: 'json',
    md: 'markdown',
    mdx: 'markdown',
  }
  return map[ext || ''] || 'javascript'
}

export function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    js: '🟨',
    jsx: '⚛️',
    ts: '🔷',
    tsx: '⚛️',
    html: '🌐',
    css: '🎨',
    json: '📋',
    md: '📝',
    svg: '🖼️',
    png: '🖼️',
    jpg: '🖼️',
    jpeg: '🖼️',
  }
  return icons[ext || ''] || '📄'
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9)
}
