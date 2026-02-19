# AION-APP — Generador de Ideas de Video

Herramienta que genera ideas originales para videos (título + descripción detallada) basadas en la temática que indiques, garantizando que nunca se repita ninguna idea. Disponible como **interfaz web** y como **script de terminal**.

---

## Requisitos

- Python 3.9 o superior
- Una clave de API de [Anthropic](https://console.anthropic.com/)

---

## Instalación

```bash
# 1. Instala las dependencias
pip install -r requirements.txt

# 2. Crea tu archivo de configuración
cp .env.example .env

# 3. Edita .env y añade tu clave de API
# ANTHROPIC_API_KEY=sk-ant-...
```

---

## Interfaz web (recomendado)

```bash
python app.py
```

Abre el navegador en **http://localhost:5000**

Desde la interfaz puedes:
- Crear múltiples bases de datos (una por temática)
- Generar ideas con un clic
- Ver el historial completo de ideas (expandibles)
- Añadir y eliminar títulos ya publicados

---

## Terminal (CLI)

### Generar una idea

```bash
python generar_idea.py -t "productividad personal"
python generar_idea.py -t "finanzas" --db finanzas
python generar_idea.py -t "mindset" --db mindset
```

### Múltiples bases de datos con `--db`

Cada `--db` es una base independiente. Si no se especifica, se usa `default`.

```bash
# Genera en la base "productividad"
python generar_idea.py -t "hábitos" --db productividad

# Genera en la base "finanzas"
python generar_idea.py -t "inversión" --db finanzas
```

### Añadir títulos ya publicados

```bash
python generar_idea.py --añadir "Título 1" "Título 2" --db productividad
```

### Ver historial

```bash
python generar_idea.py --listar --db productividad
python generar_idea.py --listar-bases
```

---

## Estructura del proyecto

```
AION-APP/
├── app.py              # Servidor web Flask
├── generar_idea.py     # Script CLI
├── bases/              # Bases de datos JSON (una por temática)
├── templates/
│   └── index.html      # Interfaz web
├── requirements.txt    # Dependencias
├── .env.example        # Plantilla de configuración
└── .env                # Tu configuración (no subir a git)
```
