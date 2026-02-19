from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from generar_idea import (
    resolver_db_path,
    cargar_base_datos,
    guardar_base_datos,
    generar_idea,
    listar_bases,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/bases", methods=["GET"])
def api_bases():
    return jsonify({"bases": listar_bases()})


@app.route("/api/crear-base", methods=["POST"])
def api_crear_base():
    nombre = request.json.get("nombre", "").strip()
    if not nombre:
        return jsonify({"error": "El nombre no puede estar vacío."}), 400
    db_path = resolver_db_path(nombre)
    if not db_path.exists():
        guardar_base_datos({"titulos_existentes": [], "ideas_generadas": []}, db_path)
    return jsonify({"ok": True, "nombre": db_path.stem})


@app.route("/api/datos", methods=["GET"])
def api_datos():
    nombre = request.args.get("db", "default")
    db_path = resolver_db_path(nombre)
    datos = cargar_base_datos(db_path)
    return jsonify(datos)


@app.route("/api/generar", methods=["POST"])
def api_generar():
    body = request.json or {}
    tematica = body.get("tematica", "").strip()
    nombre_db = body.get("db", "default").strip()

    if not tematica:
        return jsonify({"error": "La temática no puede estar vacía."}), 400
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return jsonify({"error": "ANTHROPIC_API_KEY no está configurada en el servidor."}), 500

    db_path = resolver_db_path(nombre_db)
    datos = cargar_base_datos(db_path)

    try:
        idea = generar_idea(tematica, datos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    idea["fecha"] = datetime.now().strftime("%Y-%m-%d")
    idea["tematica"] = tematica
    datos["ideas_generadas"].append(idea)
    guardar_base_datos(datos, db_path)

    return jsonify({"idea": idea})


@app.route("/api/añadir-titulos", methods=["POST"])
def api_añadir_titulos():
    body = request.json or {}
    titulos = body.get("titulos", [])
    nombre_db = body.get("db", "default").strip()

    db_path = resolver_db_path(nombre_db)
    datos = cargar_base_datos(db_path)
    nuevos = 0
    for titulo in titulos:
        titulo = titulo.strip()
        if titulo and titulo not in datos["titulos_existentes"]:
            datos["titulos_existentes"].append(titulo)
            nuevos += 1
    guardar_base_datos(datos, db_path)
    return jsonify({"ok": True, "añadidos": nuevos})


@app.route("/api/eliminar-titulo", methods=["POST"])
def api_eliminar_titulo():
    body = request.json or {}
    titulo = body.get("titulo", "").strip()
    nombre_db = body.get("db", "default").strip()

    db_path = resolver_db_path(nombre_db)
    datos = cargar_base_datos(db_path)

    if titulo in datos["titulos_existentes"]:
        datos["titulos_existentes"].remove(titulo)
        guardar_base_datos(datos, db_path)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
