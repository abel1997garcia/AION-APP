# AION-APP — Generador de Ideas de Video

Herramienta de línea de comandos que genera ideas originales para videos (título + descripción detallada) basadas en la temática que indiques, garantizando que nunca se repita ninguna idea ya generada o título ya existente.

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

## Uso

### Generar una idea sobre una temática

```bash
python generar_idea.py -t "productividad personal"
python generar_idea.py -t "mindset y mentalidad"
python generar_idea.py -t "hábitos de los millonarios"
```

También puedes ejecutarlo sin argumentos y te pedirá la temática de forma interactiva:

```bash
python generar_idea.py
```

### Añadir títulos de videos ya existentes (para que no se repitan)

Si ya tienes videos publicados, añádelos a la base de datos para que el generador los tenga en cuenta:

```bash
python generar_idea.py --añadir "Cómo despertar a las 5am" "Los 5 hábitos del éxito" "Por qué fracasan la mayoría"
```

### Ver todos los títulos e ideas registradas

```bash
python generar_idea.py --listar
```

---

## Ejemplo de salida

```
Generando idea sobre: "disciplina y hábitos"...

────────────────────────────────────────────────────────────
TÍTULO: El Truco Mental que Usan los Atletas de Élite para No Fallar un Solo Día
────────────────────────────────────────────────────────────

Los deportistas de alto rendimiento no dependen de la motivación para entrenar
cada día, sino de un sistema mental concreto que convierte la acción en algo
casi automático. Este video explora esa diferencia fundamental entre motivación
y disciplina, explicando cómo el cerebro consolida rutinas a través de ciclos
de señal, rutina y recompensa. Se debe desarrollar el concepto de "identidad de
comportamiento": actuar desde lo que uno es, no desde lo que uno siente. El tono
debe ser directo y práctico, con ejemplos reales de atletas conocidos. El valor
para el espectador es salir con una técnica específica que puede aplicar esa
misma noche para no volver a depender del estado de ánimo.

────────────────────────────────────────────────────────────
```

---

## Cómo funciona

1. Al generar una idea, el script lee todos los títulos ya existentes y ya generados desde `database.json`.
2. Le envía esa lista a Claude como contexto para que no repita ninguno.
3. Claude genera un título nuevo y una descripción en texto corrido con los detalles necesarios para escribir un guion.
4. La idea se guarda automáticamente en `database.json` con fecha y temática.

---

## Estructura del proyecto

```
AION-APP/
├── generar_idea.py     # Script principal
├── database.json       # Base de datos de títulos e ideas
├── requirements.txt    # Dependencias Python
├── .env.example        # Plantilla de configuración
└── .env                # Tu configuración (no subir a git)
```
