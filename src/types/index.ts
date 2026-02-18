export type Language = 'javascript' | 'typescript' | 'html' | 'css' | 'json' | 'markdown'

export type ProjectTemplate = 'react' | 'html' | 'vanilla-js' | 'vue'

export interface FileNode {
  id: string
  name: string
  content: string
  language: Language
  path: string
}

export interface DatabaseTable {
  id: string
  name: string
  columns: { id: string; name: string; type: 'text' | 'number' | 'boolean' | 'date' }[]
  rows: Record<string, string | number | boolean>[]
}

export interface DatabaseConfig {
  id: string
  name: string
  tables: DatabaseTable[]
}

export interface ApiEndpoint {
  id: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  path: string
  response: string
  description: string
  headers: { key: string; value: string }[]
}

export interface ApiConfig {
  id: string
  name: string
  baseUrl: string
  endpoints: ApiEndpoint[]
}

export interface ImageAsset {
  id: string
  name: string
  dataUrl: string
  type: string
  size: number
  width?: number
  height?: number
}

export interface AudioAsset {
  id: string
  name: string
  dataUrl: string
  type: string
  size: number
  duration?: number
}

export interface Project {
  id: string
  name: string
  description: string
  template: ProjectTemplate
  files: Record<string, string>
  activeFile: string
  openFiles: string[]
  databases: DatabaseConfig[]
  apis: ApiConfig[]
  images: ImageAsset[]
  audios: AudioAsset[]
  createdAt: string
  updatedAt: string
}

export type SidebarTab = 'files' | 'database' | 'api' | 'images' | 'audio'

export interface ConsoleMessage {
  id: string
  type: 'log' | 'error' | 'warn' | 'info'
  content: string
  timestamp: number
}
