import JSZip from 'jszip'
import type { Project } from '@/types'

// ─── Icon Generator ───────────────────────────────────────────────────────────

async function generateIcon(size: number): Promise<Blob> {
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')!

  // Purple → blue gradient background
  const gradient = ctx.createLinearGradient(0, 0, size, size)
  gradient.addColorStop(0, '#7c3aed')
  gradient.addColorStop(1, '#3b82f6')
  ctx.fillStyle = gradient

  // Rounded rect
  const r = size * 0.22
  ctx.beginPath()
  ctx.moveTo(r, 0)
  ctx.lineTo(size - r, 0)
  ctx.quadraticCurveTo(size, 0, size, r)
  ctx.lineTo(size, size - r)
  ctx.quadraticCurveTo(size, size, size - r, size)
  ctx.lineTo(r, size)
  ctx.quadraticCurveTo(0, size, 0, size - r)
  ctx.lineTo(0, r)
  ctx.quadraticCurveTo(0, 0, r, 0)
  ctx.closePath()
  ctx.fill()

  // Lightning bolt emoji
  ctx.font = `bold ${size * 0.52}px sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('⚡', size / 2, size / 2 + size * 0.04)

  return new Promise<Blob>(resolve => canvas.toBlob(b => resolve(b!), 'image/png'))
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function slugify(str: string): string {
  return (
    str
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
      .slice(0, 30) || 'my-app'
  )
}

function injectPWATags(html: string, appName: string): string {
  const tags = `
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    <meta name="apple-mobile-web-app-title" content="${appName}" />
    <meta name="theme-color" content="#7c3aed" />
    <link rel="manifest" href="manifest.json" />
    <link rel="apple-touch-icon" href="icons/icon-192.png" />`
  return html.replace('</head>', `${tags}\n  </head>`)
}

// ─── Asset Generators ─────────────────────────────────────────────────────────

function buildManifest(project: Project) {
  return {
    name: project.name,
    short_name: project.name.slice(0, 12),
    description: project.description || `${project.name} - creada con AION Builder`,
    start_url: '/',
    display: 'standalone',
    background_color: '#0a0a0f',
    theme_color: '#7c3aed',
    orientation: 'portrait-primary',
    lang: 'es',
    icons: [
      { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
    ],
    categories: ['productivity'],
  }
}

function buildServiceWorker(): string {
  return `const CACHE = 'app-v1';
const URLS = ['/'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(URLS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks =>
    Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(r =>
      r || fetch(e.request).then(res => {
        if (!res || res.status !== 200 || res.type !== 'basic') return res;
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
        return res;
      }).catch(() => caches.match('/'))
    )
  );
});
`
}

function buildSWRegistration(): string {
  return `if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(r => console.log('SW registrado:', r.scope))
      .catch(e => console.warn('SW error:', e));
  });
}
`
}

function buildCapacitorIndexHtml(appName: string): string {
  return `<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, user-scalable=no" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="default" />
    <meta name="apple-mobile-web-app-title" content="${appName}" />
    <meta name="theme-color" content="#7c3aed" />
    <link rel="manifest" href="/manifest.json" />
    <link rel="apple-touch-icon" href="/icons/icon-192.png" />
    <title>${appName}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
`
}

function buildReactMain(): string {
  return `import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
`
}

function buildViteConfig(): string {
  return `import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: { outDir: 'dist' },
})
`
}

function buildTsConfig(): object {
  return {
    compilerOptions: {
      target: 'ES2020',
      useDefineForClassFields: true,
      lib: ['ES2020', 'DOM', 'DOM.Iterable'],
      module: 'ESNext',
      skipLibCheck: true,
      moduleResolution: 'bundler',
      allowImportingTsExtensions: true,
      resolveJsonModule: true,
      isolatedModules: true,
      noEmit: true,
      jsx: 'react-jsx',
      strict: true,
    },
    include: ['src'],
  }
}

function buildCapacitorConfig(appId: string, appName: string): string {
  return `import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: '${appId}',
  appName: '${appName}',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
  ios: {
    contentInset: 'automatic',
  },
  plugins: {
    StatusBar: {
      style: 'Default',
      backgroundColor: '#7c3aed',
    },
    SplashScreen: {
      launchShowDuration: 0,
    },
  },
}

export default config
`
}

function buildCapacitorPackageJson(appName: string): object {
  return {
    name: slugify(appName),
    private: true,
    version: '1.0.0',
    type: 'module',
    scripts: {
      dev: 'vite',
      build: 'tsc && vite build',
      preview: 'vite preview',
      'cap:add:ios': 'npx cap add ios',
      'cap:add:android': 'npx cap add android',
      'cap:sync': 'npm run build && npx cap sync',
      'cap:open:ios': 'npx cap open ios',
      'cap:open:android': 'npx cap open android',
    },
    dependencies: {
      react: '^18.2.0',
      'react-dom': '^18.2.0',
      '@capacitor/core': '^5.7.0',
      '@capacitor/app': '^5.0.7',
      '@capacitor/haptics': '^5.0.7',
      '@capacitor/keyboard': '^5.0.7',
      '@capacitor/status-bar': '^5.0.7',
    },
    devDependencies: {
      '@types/react': '^18.2.48',
      '@types/react-dom': '^18.2.18',
      '@vitejs/plugin-react': '^4.2.1',
      typescript: '^5.2.2',
      vite: '^5.0.11',
      '@capacitor/cli': '^5.7.0',
    },
  }
}

function buildReadme(appName: string): string {
  return `# ${appName}

> App generada con **AION Builder** · Lista para publicar en **App Store** y **Google Play**.

---

## 🚀 Publicar en tiendas de aplicaciones

### Requisitos previos
- Node.js 18+
- **iOS**: macOS con Xcode 14+ instalado
- **Android**: Android Studio instalado

### 1. Instalar dependencias
\`\`\`bash
npm install
\`\`\`

### 2. Build y sincronizar con Capacitor
\`\`\`bash
npm run cap:sync
\`\`\`

### 3. Agregar plataformas (solo la primera vez)
\`\`\`bash
npm run cap:add:ios
npm run cap:add:android
\`\`\`

---

## 📱 Publicar en App Store (iOS)

\`\`\`bash
npm run cap:open:ios
\`\`\`

1. Abre el proyecto en **Xcode**
2. Selecciona tu **Team** (requiere Apple Developer Account)
3. Ajusta el **Bundle Identifier** en \`capacitor.config.ts\` → appId
4. Cambia el **nombre** e **iconos** en los Assets de Xcode
5. Ve a **Product → Archive**
6. Distribuye via **App Store Connect**
7. Sube a **TestFlight** para pruebas
8. Envía para revisión de Apple (~24-48h)

**Coste**: Apple Developer Program = **$99/año**

---

## 🤖 Publicar en Google Play (Android)

\`\`\`bash
npm run cap:open:android
\`\`\`

1. Abre el proyecto en **Android Studio**
2. Cambia el **applicationId** en \`android/app/build.gradle\`
3. Ve a **Build → Generate Signed Bundle/APK**
4. Crea o usa tu **keystore** existente
5. Genera el **App Bundle (.aab)**
6. Sube a **Google Play Console**
7. Completa la ficha de la app, capturas y descripción
8. Envía para revisión (~3-7 días)

**Coste**: Google Play Developer = **$25 pago único**

---

## 🌐 Alternativa gratuita: PWA

Si no quieres pagar para las tiendas de aplicaciones:

1. Despliega tu app en **Vercel** o **Netlify** (gratis)
2. Los usuarios pueden usar **"Añadir a la pantalla de inicio"** en iOS/Android
3. La app funciona como nativa, sin pasar por las tiendas
4. Actualizaciones instantáneas sin revisión de Apple/Google

---

## 📁 Estructura del proyecto

\`\`\`
├── src/                  # Código fuente React
│   ├── App.tsx           # Componente principal
│   └── main.tsx          # Punto de entrada
├── public/               # Assets estáticos
│   ├── manifest.json     # Configuración PWA
│   └── icons/            # Iconos de la app
├── dist/                 # Build de producción (generado)
├── ios/                  # Proyecto iOS nativo (generado)
├── android/              # Proyecto Android nativo (generado)
├── capacitor.config.ts   # Configuración Capacitor
└── vite.config.ts        # Configuración Vite
\`\`\`

---

Creado con ❤️ por [AION Builder](https://aion.app)
`
}

// ─── Public Export Functions ──────────────────────────────────────────────────

export async function exportAsWebZip(project: Project): Promise<void> {
  const zip = new JSZip()

  Object.entries(project.files).forEach(([path, content]) => {
    const clean = path.startsWith('/') ? path.slice(1) : path
    zip.file(clean, content)
  })

  const blob = await zip.generateAsync({ type: 'blob' })
  downloadBlob(blob, `${slugify(project.name)}.zip`)
}

export async function exportAsPWA(project: Project): Promise<void> {
  const zip = new JSZip()

  Object.entries(project.files).forEach(([path, content]) => {
    const clean = path.startsWith('/') ? path.slice(1) : path
    const injected =
      clean.endsWith('.html') && content.includes('</head>')
        ? injectPWATags(content, project.name)
        : content
    zip.file(clean, injected)
  })

  // Add PWA assets
  zip.file('manifest.json', JSON.stringify(buildManifest(project), null, 2))
  zip.file('service-worker.js', buildServiceWorker())
  zip.file('register-sw.js', buildSWRegistration())

  // Generate icons
  const [icon192, icon512] = await Promise.all([generateIcon(192), generateIcon(512)])
  zip.file('icons/icon-192.png', icon192)
  zip.file('icons/icon-512.png', icon512)

  const blob = await zip.generateAsync({ type: 'blob' })
  downloadBlob(blob, `${slugify(project.name)}-pwa.zip`)
}

export async function exportAsCapacitor(project: Project): Promise<void> {
  const zip = new JSZip()
  const appName = project.name
  const appId = `com.aion.${slugify(appName).replace(/-/g, '')}`
  const isReact = project.template === 'react'

  if (isReact) {
    // index.html at root (Vite standard)
    zip.file('index.html', buildCapacitorIndexHtml(appName))

    // User source files → src/
    Object.entries(project.files).forEach(([path, content]) => {
      const clean = path.startsWith('/') ? path.slice(1) : path
      if (clean === 'public/index.html') return
      zip.file(`src/${clean}`, content)
    })

    // Ensure main.tsx exists
    if (!project.files['/main.tsx'] && !project.files['main.tsx']) {
      zip.file('src/main.tsx', buildReactMain())
    }

    zip.file('vite.config.ts', buildViteConfig())
    zip.file('tsconfig.json', JSON.stringify(buildTsConfig(), null, 2))
    zip.file('package.json', JSON.stringify(buildCapacitorPackageJson(appName), null, 2))
    zip.file('capacitor.config.ts', buildCapacitorConfig(appId, appName))
  } else {
    // HTML/Vanilla project — files go at root, webDir = '.'
    Object.entries(project.files).forEach(([path, content]) => {
      const clean = path.startsWith('/') ? path.slice(1) : path
      const injected =
        clean.endsWith('.html') && content.includes('</head>')
          ? injectPWATags(content, appName)
          : content
      zip.file(clean, injected)
    })

    const htmlPkg = {
      name: slugify(appName),
      private: true,
      version: '1.0.0',
      scripts: {
        'cap:add:ios': 'npx cap add ios',
        'cap:add:android': 'npx cap add android',
        'cap:sync': 'npx cap sync',
        'cap:open:ios': 'npx cap open ios',
        'cap:open:android': 'npx cap open android',
      },
      dependencies: { '@capacitor/core': '^5.7.0' },
      devDependencies: { '@capacitor/cli': '^5.7.0' },
    }
    zip.file('package.json', JSON.stringify(htmlPkg, null, 2))

    // For HTML projects webDir is '.'
    const htmlCapConfig = `import type { CapacitorConfig } from '@capacitor/cli'
const config: CapacitorConfig = {
  appId: '${appId}',
  appName: '${appName}',
  webDir: '.',
  server: { androidScheme: 'https' },
}
export default config
`
    zip.file('capacitor.config.ts', htmlCapConfig)
  }

  // PWA manifest & icons (for both)
  zip.file('public/manifest.json', JSON.stringify(buildManifest(project), null, 2))
  const [icon192, icon512] = await Promise.all([generateIcon(192), generateIcon(512)])
  zip.file('public/icons/icon-192.png', icon192)
  zip.file('public/icons/icon-512.png', icon512)

  // README with App Store / Play Store instructions
  zip.file('README.md', buildReadme(appName))

  const blob = await zip.generateAsync({ type: 'blob' })
  downloadBlob(blob, `${slugify(project.name)}-capacitor.zip`)
}
