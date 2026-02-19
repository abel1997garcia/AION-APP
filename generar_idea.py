#!/usr/bin/env python3
"""
Generador de Ideas de Video
---------------------------
Genera ideas originales para videos basadas en una temática,
evitando repetir títulos ya existentes o ideas ya generadas.

Soporta múltiples bases de datos con el flag --db.
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

try:
    import anthropic
except ImportError:
    print("ERROR: Instala las dependencias con: pip install -r requirements.txt")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASES_DIR = Path(__file__).parent / "bases"
BASES_DIR.mkdir(exist_ok=True)


def resolver_db_path(nombre: str) -> Path:
    """Convierte un nombre de base de datos en su ruta de archivo."""
    nombre = nombre.strip().lower().replace(" ", "_")
    if not nombre.endswith(".json"):
        nombre += ".json"
    return BASES_DIR / nombre


def cargar_base_datos(db_path: Path) -> dict:
    if not db_path.exists():
        return {"titulos_existentes": [], "ideas_generadas": []}
    with open(db_path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_base_datos(datos: dict, db_path: Path):
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def listar_bases() -> list[str]:
    """Lista los nombres de todas las bases de datos disponibles."""
    return sorted([p.stem for p in BASES_DIR.glob("*.json")])


def construir_lista_titulos(datos: dict) -> str:
    todos = []
    for titulo in datos.get("titulos_existentes", []):
        todos.append(f"- {titulo}")
    for idea in datos.get("ideas_generadas", []):
        todos.append(f"- {idea['titulo']}")
    if not todos:
        return "Ninguno todavía."
    return "\n".join(todos)


def generar_idea(tematica: str, datos: dict) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Define ANTHROPIC_API_KEY en tu archivo .env o como variable de entorno.")

    cliente = anthropic.Anthropic(api_key=api_key)
    lista_titulos = construir_lista_titulos(datos)

    prompt = f"""Eres un experto en creación de contenido para YouTube y redes sociales.
Tu tarea es generar UNA SOLA idea de video original y específica sobre la siguiente temática: "{tematica}".

TÍTULOS YA EXISTENTES O GENERADOS (NO debes repetir ni parecerte a ninguno de estos):
{lista_titulos}

INSTRUCCIONES ESTRICTAS:
1. El título debe ser original, llamativo y diferente a todos los ya listados.
2. La descripción debe ser un texto corrido (sin listas, sin puntos, sin secciones), con detalles concretos y específicos que sirvan de guía para elaborar un guion completo.
3. La descripción debe incluir: el enfoque principal del video, los puntos clave que se deben desarrollar, el tono y estilo narrativo recomendado, y el valor que aporta al espectador.
4. La descripción debe tener entre 150 y 250 palabras.
5. Responde ÚNICAMENTE con el siguiente formato, sin nada más:

TÍTULO: [el título del video]
DESCRIPCIÓN: [la descripción en texto corrido]"""

    mensaje = cliente.messages.create(
        model="claude-opus-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    respuesta = mensaje.content[0].text.strip()
    return parsear_respuesta(respuesta)


def parsear_respuesta(respuesta: str) -> dict:
    titulo = ""
    descripcion = ""
    modo = None

    for linea in respuesta.split("\n"):
        linea = linea.strip()
        if linea.startswith("TÍTULO:"):
            titulo = linea.replace("TÍTULO:", "").strip()
            modo = "titulo"
        elif linea.startswith("DESCRIPCIÓN:"):
            descripcion = linea.replace("DESCRIPCIÓN:", "").strip()
            modo = "descripcion"
        elif modo == "descripcion" and linea:
            descripcion += " " + linea

    descripcion = " ".join(descripcion.split())

    if not titulo or not descripcion:
        raise ValueError(f"No se pudo parsear la respuesta del modelo:\n{respuesta}")

    return {"titulo": titulo, "descripcion": descripcion}


def mostrar_idea(idea: dict):
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"TÍTULO: {idea['titulo']}")
    print(f"{sep}")
    print(f"\n{idea['descripcion']}\n")
    print(sep)


def agregar_titulos_existentes(titulos: list[str], db_path: Path):
    datos = cargar_base_datos(db_path)
    nuevos = 0
    for titulo in titulos:
        titulo = titulo.strip()
        if titulo and titulo not in datos["titulos_existentes"]:
            datos["titulos_existentes"].append(titulo)
            nuevos += 1
    guardar_base_datos(datos, db_path)
    print(f"Se añadieron {nuevos} título(s) a '{db_path.stem}'.")


def listar_todo(db_path: Path):
    datos = cargar_base_datos(db_path)
    print(f"\n=== BASE: {db_path.stem.upper()} ===")
    print("\n-- TÍTULOS EXISTENTES --")
    if datos["titulos_existentes"]:
        for t in datos["titulos_existentes"]:
            print(f"  • {t}")
    else:
        print("  (ninguno)")

    print("\n-- IDEAS GENERADAS --")
    if datos["ideas_generadas"]:
        for i, idea in enumerate(datos["ideas_generadas"], 1):
            fecha = idea.get("fecha", "")
            print(f"  {i}. [{fecha}] {idea['titulo']}")
    else:
        print("  (ninguna)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generador de ideas de video originales sin repetición.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python generar_idea.py -t "productividad personal"
  python generar_idea.py -t "finanzas" --db finanzas
  python generar_idea.py --añadir "Título 1" "Título 2" --db mindset
  python generar_idea.py --listar --db productividad
  python generar_idea.py --listar-bases
        """
    )
    parser.add_argument("-t", "--tematica", type=str,
                        help="Temática sobre la que generar la idea.")
    parser.add_argument("--db", type=str, default="default",
                        help="Nombre de la base de datos a usar (default: 'default').")
    parser.add_argument("--añadir", nargs="+", metavar="TÍTULO",
                        help="Añadir títulos existentes a la base de datos.")
    parser.add_argument("--listar", action="store_true",
                        help="Mostrar todos los títulos e ideas de una base.")
    parser.add_argument("--listar-bases", action="store_true",
                        help="Mostrar todas las bases de datos disponibles.")

    args = parser.parse_args()
    db_path = resolver_db_path(args.db)

    if args.listar_bases:
        bases = listar_bases()
        print("\nBases de datos disponibles:")
        for b in bases:
            print(f"  • {b}")
        print()
        return

    if args.listar:
        listar_todo(db_path)
        return

    if args.añadir:
        agregar_titulos_existentes(args.añadir, db_path)
        return

    if args.tematica:
        tematica = args.tematica
    else:
        print("Generador de Ideas de Video")
        print(f"Base de datos: {db_path.stem}")
        print("────────────────────────────")
        tematica = input("¿Sobre qué temática quieres la idea? ").strip()
        if not tematica:
            print("ERROR: Debes indicar una temática.")
            sys.exit(1)

    print(f"\nGenerando idea sobre: \"{tematica}\" en '{db_path.stem}'...")

    datos = cargar_base_datos(db_path)
    try:
        idea = generar_idea(tematica, datos)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    idea["fecha"] = datetime.now().strftime("%Y-%m-%d")
    idea["tematica"] = tematica
    datos["ideas_generadas"].append(idea)
    guardar_base_datos(datos, db_path)

    mostrar_idea(idea)


if __name__ == "__main__":
    main()
