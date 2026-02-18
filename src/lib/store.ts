import { create } from 'zustand'
import type {
  Project,
  SidebarTab,
  ConsoleMessage,
  DatabaseConfig,
  ApiConfig,
  ImageAsset,
  AudioAsset,
} from '@/types'
import { TEMPLATES } from './templates'
import { generateId, getLanguageFromFilename } from './utils'

interface EditorStore {
  // Project state
  project: Project
  setProject: (project: Project) => void
  updateProjectName: (name: string) => void

  // File management
  updateFile: (path: string, content: string) => void
  addFile: (name: string, content?: string) => void
  deleteFile: (path: string) => void
  renameFile: (oldPath: string, newPath: string) => void
  setActiveFile: (path: string) => void
  openFile: (path: string) => void
  closeFile: (path: string) => void

  // UI state
  sidebarTab: SidebarTab
  setSidebarTab: (tab: SidebarTab) => void
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  consoleOpen: boolean
  setConsoleOpen: (open: boolean) => void
  previewKey: number
  refreshPreview: () => void

  // Console
  consoleMessages: ConsoleMessage[]
  addConsoleMessage: (msg: Omit<ConsoleMessage, 'id' | 'timestamp'>) => void
  clearConsole: () => void

  // Database
  addDatabase: (db: Omit<DatabaseConfig, 'id'>) => void
  updateDatabase: (id: string, db: Partial<DatabaseConfig>) => void
  removeDatabase: (id: string) => void

  // API
  addApi: (api: Omit<ApiConfig, 'id'>) => void
  updateApi: (id: string, api: Partial<ApiConfig>) => void
  removeApi: (id: string) => void

  // Images
  addImage: (image: Omit<ImageAsset, 'id'>) => void
  removeImage: (id: string) => void

  // Audio
  addAudio: (audio: Omit<AudioAsset, 'id'>) => void
  removeAudio: (id: string) => void
}

const defaultTemplate = TEMPLATES[0]

const createDefaultProject = (): Project => ({
  id: generateId(),
  name: 'Mi Proyecto',
  description: 'Un proyecto increíble',
  template: defaultTemplate.template,
  files: defaultTemplate.files,
  activeFile: defaultTemplate.activeFile,
  openFiles: [defaultTemplate.activeFile],
  databases: [],
  apis: [],
  images: [],
  audios: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
})

export const useEditorStore = create<EditorStore>((set) => ({
  project: createDefaultProject(),
  setProject: (project) => set({ project }),
  updateProjectName: (name) =>
    set((state) => ({ project: { ...state.project, name } })),

  // File management
  updateFile: (path, content) =>
    set((state) => ({
      project: {
        ...state.project,
        files: { ...state.project.files, [path]: content },
        updatedAt: new Date().toISOString(),
      },
    })),

  addFile: (name, content = '') => {
    const path = name.startsWith('/') ? name : `/${name}`
    set((state) => ({
      project: {
        ...state.project,
        files: { ...state.project.files, [path]: content },
        activeFile: path,
        openFiles: state.project.openFiles.includes(path)
          ? state.project.openFiles
          : [...state.project.openFiles, path],
      },
    }))
  },

  deleteFile: (path) =>
    set((state) => {
      const files = { ...state.project.files }
      delete files[path]
      const openFiles = state.project.openFiles.filter((f) => f !== path)
      const activeFile =
        state.project.activeFile === path
          ? openFiles[openFiles.length - 1] || Object.keys(files)[0] || ''
          : state.project.activeFile
      return { project: { ...state.project, files, openFiles, activeFile } }
    }),

  renameFile: (oldPath, newPath) =>
    set((state) => {
      const files = { ...state.project.files }
      files[newPath] = files[oldPath]
      delete files[oldPath]
      const openFiles = state.project.openFiles.map((f) =>
        f === oldPath ? newPath : f
      )
      const activeFile =
        state.project.activeFile === oldPath ? newPath : state.project.activeFile
      return { project: { ...state.project, files, openFiles, activeFile } }
    }),

  setActiveFile: (path) =>
    set((state) => ({
      project: { ...state.project, activeFile: path },
    })),

  openFile: (path) =>
    set((state) => ({
      project: {
        ...state.project,
        activeFile: path,
        openFiles: state.project.openFiles.includes(path)
          ? state.project.openFiles
          : [...state.project.openFiles, path],
      },
    })),

  closeFile: (path) =>
    set((state) => {
      const openFiles = state.project.openFiles.filter((f) => f !== path)
      const activeFile =
        state.project.activeFile === path
          ? openFiles[openFiles.length - 1] || ''
          : state.project.activeFile
      return { project: { ...state.project, openFiles, activeFile } }
    }),

  // UI state
  sidebarTab: 'files',
  setSidebarTab: (tab) => set({ sidebarTab: tab }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  consoleOpen: false,
  setConsoleOpen: (open) => set({ consoleOpen: open }),
  previewKey: 0,
  refreshPreview: () => set((state) => ({ previewKey: state.previewKey + 1 })),

  // Console
  consoleMessages: [],
  addConsoleMessage: (msg) =>
    set((state) => ({
      consoleMessages: [
        ...state.consoleMessages,
        { ...msg, id: generateId(), timestamp: Date.now() },
      ].slice(-100),
    })),
  clearConsole: () => set({ consoleMessages: [] }),

  // Database
  addDatabase: (db) =>
    set((state) => ({
      project: {
        ...state.project,
        databases: [
          ...state.project.databases,
          { ...db, id: generateId() },
        ],
      },
    })),
  updateDatabase: (id, db) =>
    set((state) => ({
      project: {
        ...state.project,
        databases: state.project.databases.map((d) =>
          d.id === id ? { ...d, ...db } : d
        ),
      },
    })),
  removeDatabase: (id) =>
    set((state) => ({
      project: {
        ...state.project,
        databases: state.project.databases.filter((d) => d.id !== id),
      },
    })),

  // API
  addApi: (api) =>
    set((state) => ({
      project: {
        ...state.project,
        apis: [...state.project.apis, { ...api, id: generateId() }],
      },
    })),
  updateApi: (id, api) =>
    set((state) => ({
      project: {
        ...state.project,
        apis: state.project.apis.map((a) =>
          a.id === id ? { ...a, ...api } : a
        ),
      },
    })),
  removeApi: (id) =>
    set((state) => ({
      project: {
        ...state.project,
        apis: state.project.apis.filter((a) => a.id !== id),
      },
    })),

  // Images
  addImage: (image) =>
    set((state) => ({
      project: {
        ...state.project,
        images: [
          ...state.project.images,
          { ...image, id: generateId() },
        ],
      },
    })),
  removeImage: (id) =>
    set((state) => ({
      project: {
        ...state.project,
        images: state.project.images.filter((i) => i.id !== id),
      },
    })),

  // Audio
  addAudio: (audio) =>
    set((state) => ({
      project: {
        ...state.project,
        audios: [
          ...state.project.audios,
          { ...audio, id: generateId() },
        ],
      },
    })),
  removeAudio: (id) =>
    set((state) => ({
      project: {
        ...state.project,
        audios: state.project.audios.filter((a) => a.id !== id),
      },
    })),
}))
