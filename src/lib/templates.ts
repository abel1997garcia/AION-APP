import type { ProjectTemplate } from '@/types'

export interface Template {
  id: string
  name: string
  description: string
  template: ProjectTemplate
  icon: string
  color: string
  files: Record<string, string>
  activeFile: string
}

export const TEMPLATES: Template[] = [
  {
    id: 'react-app',
    name: 'React App',
    description: 'Aplicación React con componentes y estado',
    template: 'react',
    icon: '⚛️',
    color: '#61dafb',
    activeFile: '/App.tsx',
    files: {
      '/App.tsx': `import { useState } from "react";

export default function App() {
  const [count, setCount] = useState(0);

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      fontFamily: "sans-serif",
      color: "white"
    }}>
      <h1 style={{ fontSize: "3rem", marginBottom: "1rem" }}>
        ⚡ Mi App AION
      </h1>
      <p style={{ fontSize: "1.2rem", marginBottom: "2rem", opacity: 0.8 }}>
        Empieza a construir algo increíble
      </p>
      <div style={{
        background: "rgba(255,255,255,0.1)",
        borderRadius: "1rem",
        padding: "2rem",
        textAlign: "center"
      }}>
        <p style={{ fontSize: "1.5rem", marginBottom: "1rem" }}>
          Contador: <strong>{count}</strong>
        </p>
        <button
          onClick={() => setCount(count + 1)}
          style={{
            background: "white",
            color: "#764ba2",
            border: "none",
            padding: "0.75rem 2rem",
            borderRadius: "0.5rem",
            fontSize: "1rem",
            cursor: "pointer",
            fontWeight: "bold"
          }}
        >
          Incrementar
        </button>
      </div>
    </div>
  );
}`,
      '/index.css': `body {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}`,
      '/public/index.html': `<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Mi App AION</title>
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>`,
    },
  },
  {
    id: 'html-page',
    name: 'HTML & CSS',
    description: 'Página web con HTML y CSS puro',
    template: 'html',
    icon: '🌐',
    color: '#e44d26',
    activeFile: '/index.html',
    files: {
      '/index.html': `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mi Página Web</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <header class="hero">
    <div class="container">
      <h1>🚀 Bienvenido a AION</h1>
      <p>Crea tu visión, da vida a tus ideas</p>
      <a href="#" class="btn">Comenzar</a>
    </div>
  </header>
  <main class="container">
    <section class="features">
      <div class="card">
        <span class="icon">⚡</span>
        <h3>Rápido</h3>
        <p>Desarrollo en tiempo real con preview instantáneo</p>
      </div>
      <div class="card">
        <span class="icon">🎨</span>
        <h3>Creativo</h3>
        <p>Sin límites para tu imaginación</p>
      </div>
      <div class="card">
        <span class="icon">🔮</span>
        <h3>Poderoso</h3>
        <p>Herramientas profesionales a tu alcance</p>
      </div>
    </section>
  </main>
</body>
</html>`,
      '/styles.css': `* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', sans-serif;
  background: #0a0a0f;
  color: #e2e8f0;
}

.container {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 2rem;
}

.hero {
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  padding: 6rem 0;
  text-align: center;
}

.hero h1 {
  font-size: 3.5rem;
  margin-bottom: 1rem;
  font-weight: 800;
}

.hero p {
  font-size: 1.3rem;
  opacity: 0.85;
  margin-bottom: 2rem;
}

.btn {
  display: inline-block;
  background: white;
  color: #7c3aed;
  padding: 0.9rem 2.5rem;
  border-radius: 2rem;
  text-decoration: none;
  font-weight: 700;
  font-size: 1.1rem;
  transition: transform 0.2s;
}

.btn:hover {
  transform: translateY(-2px);
}

.features {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  padding: 5rem 0;
}

.card {
  background: #12121a;
  border: 1px solid #2a2a3d;
  border-radius: 1rem;
  padding: 2rem;
  text-align: center;
  transition: border-color 0.2s;
}

.card:hover {
  border-color: #7c3aed;
}

.icon {
  font-size: 2.5rem;
  display: block;
  margin-bottom: 1rem;
}

.card h3 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  color: #c4b5fd;
}

.card p {
  color: #64748b;
  line-height: 1.6;
}`,
    },
  },
  {
    id: 'vanilla-js',
    name: 'JavaScript',
    description: 'JavaScript vanilla con DOM puro',
    template: 'vanilla-js',
    icon: '⚡',
    color: '#f7df1e',
    activeFile: '/index.js',
    files: {
      '/index.html': `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Vanilla JS App</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: sans-serif;
      background: #0a0a0f;
      color: #e2e8f0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
    }
    h1 { font-size: 2.5rem; margin-bottom: 1rem; }
    #app { text-align: center; }
    .output {
      background: #12121a;
      border: 1px solid #2a2a3d;
      border-radius: 0.5rem;
      padding: 1.5rem;
      margin-top: 2rem;
      min-width: 300px;
      font-family: monospace;
      font-size: 1.1rem;
    }
    button {
      background: #7c3aed;
      color: white;
      border: none;
      padding: 0.75rem 2rem;
      border-radius: 0.5rem;
      cursor: pointer;
      font-size: 1rem;
      margin: 0.5rem;
    }
    button:hover { background: #6d28d9; }
  </style>
</head>
<body>
  <div id="app">
    <h1>⚡ Vanilla JS</h1>
    <button onclick="greet()">Saludar</button>
    <button onclick="randomColor()">Color aleatorio</button>
    <div class="output" id="output">¡Haz clic en un botón!</div>
  </div>
  <script src="index.js"></script>
</body>
</html>`,
      '/index.js': `const output = document.getElementById('output');

function greet() {
  const greetings = [
    '¡Hola Mundo! 👋',
    '¡Bienvenido a AION! 🚀',
    '¡Construyamos algo increíble! ⚡',
    '¡El poder del código! 💻',
  ];
  const random = greetings[Math.floor(Math.random() * greetings.length)];
  output.textContent = random;
}

function randomColor() {
  const r = Math.floor(Math.random() * 255);
  const g = Math.floor(Math.random() * 255);
  const b = Math.floor(Math.random() * 255);
  const color = \`rgb(\${r}, \${g}, \${b})\`;
  output.style.color = color;
  output.textContent = \`Color: \${color}\`;
}

console.log('JavaScript iniciado correctamente ✅');`,
    },
  },
  {
    id: 'dashboard',
    name: 'Dashboard',
    description: 'Panel de control con estadísticas',
    template: 'react',
    icon: '📊',
    color: '#22c55e',
    activeFile: '/App.tsx',
    files: {
      '/App.tsx': `import { useState } from "react";

const stats = [
  { label: "Usuarios", value: "12,847", change: "+12%", color: "#7c3aed" },
  { label: "Ingresos", value: "$48.2K", change: "+8.4%", color: "#22c55e" },
  { label: "Pedidos", value: "3,241", change: "+23%", color: "#3b82f6" },
  { label: "Conversión", value: "4.8%", change: "+1.2%", color: "#eab308" },
];

export default function Dashboard() {
  const [active, setActive] = useState("inicio");

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0a0a0f", color: "#e2e8f0", fontFamily: "sans-serif" }}>
      {/* Sidebar */}
      <nav style={{ width: 220, background: "#12121a", borderRight: "1px solid #2a2a3d", padding: "1.5rem 0" }}>
        <div style={{ padding: "0 1.5rem 2rem", fontSize: "1.3rem", fontWeight: "bold", color: "#c4b5fd" }}>
          ⚡ Dashboard
        </div>
        {["inicio", "usuarios", "reportes", "configuración"].map(item => (
          <button key={item} onClick={() => setActive(item)}
            style={{
              display: "block", width: "100%", textAlign: "left",
              padding: "0.75rem 1.5rem", border: "none", cursor: "pointer",
              background: active === item ? "#1e1a2e" : "transparent",
              color: active === item ? "#c4b5fd" : "#64748b",
              borderLeft: active === item ? "3px solid #7c3aed" : "3px solid transparent",
              textTransform: "capitalize", fontSize: "0.95rem",
            }}>
            {item}
          </button>
        ))}
      </nav>
      {/* Main */}
      <main style={{ flex: 1, padding: "2rem" }}>
        <h1 style={{ fontSize: "1.75rem", marginBottom: "2rem", fontWeight: "700" }}>
          Resumen General
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1.5rem", marginBottom: "2rem" }}>
          {stats.map(stat => (
            <div key={stat.label} style={{
              background: "#12121a", border: "1px solid #2a2a3d",
              borderRadius: "0.75rem", padding: "1.5rem"
            }}>
              <p style={{ color: "#64748b", fontSize: "0.875rem", marginBottom: "0.5rem" }}>{stat.label}</p>
              <p style={{ fontSize: "1.75rem", fontWeight: "bold", marginBottom: "0.5rem" }}>{stat.value}</p>
              <span style={{ color: stat.color, fontSize: "0.875rem", fontWeight: 600 }}>{stat.change} este mes</span>
            </div>
          ))}
        </div>
        <div style={{ background: "#12121a", border: "1px solid #2a2a3d", borderRadius: "0.75rem", padding: "1.5rem" }}>
          <h2 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>Actividad Reciente</h2>
          {["Usuario #4821 se registró", "Pedido #2341 completado", "Nuevo reporte disponible", "Pago recibido $1,200"].map((item, i) => (
            <div key={i} style={{
              padding: "0.75rem 0", borderBottom: i < 3 ? "1px solid #2a2a3d" : "none",
              display: "flex", justifyContent: "space-between", color: "#94a3b8"
            }}>
              <span>{item}</span>
              <span style={{ fontSize: "0.8rem" }}>{i + 1}h ago</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}`,
      '/index.css': 'body { margin: 0; }',
    },
  },
]

export const DEFAULT_TEMPLATE = TEMPLATES[0]

export function getTemplateById(id: string): Template | undefined {
  return TEMPLATES.find(t => t.id === id)
}
