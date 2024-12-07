from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
# Endpoint /health
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

# Endpoint /count
@app.route("/count", methods=["GET"])
def count():
    try:
        songs_count = db.songs.count_documents({})
        return jsonify({"count": songs_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/song", methods=["GET"])
def songs():
    try:
        # Recuperar todos los documentos en la colección 'songs'
        songs_list = list(db.songs.find({}, {"_id": 0}))  # Excluir el campo '_id' para simplificar la salida
        return jsonify({"songs": songs_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint /song/<id>
@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    try:
        # Buscar una canción por ID en la colección 'songs'
        song = db.songs.find_one({"id": id}, {"_id": 0})  # Excluir '_id' para simplificar la salida
        if not song:
            return jsonify({"message": f"Canción con id {id} no encontrada"}), 404
        return jsonify(song), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/song", methods=["POST"])
def create_song():
    try:
        # Extraer datos del cuerpo de la solicitud
        song = request.get_json()
        if not song or 'id' not in song:
            return jsonify({"Message": "Datos de la canción no válidos"}), 400

        # Verificar si ya existe una canción con el mismo ID
        existing_song = db.songs.find_one({"id": song['id']})
        if existing_song:
            return jsonify({"Message": f"Canción con id {song['id']} ya presente"}), 302

        # Insertar la nueva canción en la base de datos
        result = db.songs.insert_one(song)
        return jsonify({"inserted_id": str(result.inserted_id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    try:
        # Extraer datos del cuerpo de la solicitud
        updated_data = request.get_json()
        if not updated_data:
            return jsonify({"message": "Datos de la canción no válidos"}), 400

        # Buscar si la canción existe
        existing_song = db.songs.find_one({"id": id})
        if not existing_song:
            return jsonify({"message": "Canción no encontrada"}), 404

        # Actualizar la canción
        result = db.songs.update_one({"id": id}, {"$set": updated_data})

        if result.modified_count > 0:
            updated_song = db.songs.find_one({"id": id}, {"_id": 0})
            return jsonify(updated_song), 201
        else:
            return jsonify({"message": "Canción encontrada, pero no se actualizó nada"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint DELETE /song/<int:id>
@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    try:
        # Intentar eliminar la canción con el id especificado
        result = db.songs.delete_one({"id": id})

        if result.deleted_count == 0:
            # Si no se eliminó ninguna canción, retornar 404
            return jsonify({"message": "Canción no encontrada"}), 404

        # Si la canción fue eliminada exitosamente, retornar 204 No Content
        return '', 204
    except Exception as e:
        # Manejo de errores en caso de excepciones
        return jsonify({"error": str(e)}), 500