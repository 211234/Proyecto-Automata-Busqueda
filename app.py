from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import json_util, ObjectId
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
import re

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

app.config['JWT_SECRET_KEY'] = '12345678'

jwt = JWTManager(app)

client = MongoClient('localhost', 27017)
db = client['automata']
collection = db['data']
users_collection = db['users']

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({'message': 'El correo electrónico ya está registrado.'}), 400

    new_user = {'email': email, 'password': password}
    users_collection.insert_one(new_user)

    return jsonify({'message': 'Usuario registrado exitosamente.'}), 201

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email, 'password': password})
    if not user:
        return jsonify({'message': 'Correo electrónico o contraseña incorrectos.'}), 401

    token = create_access_token(identity=str(user['_id']))
    return jsonify({'token': token}), 200

@app.route('/api/data')
def get_all_data():
    cursor = collection.find({})
    data = json_util.dumps(cursor)
    return data

@app.route('/api/data/<nombre_contacto>')
def search_by_nombre_contacto(nombre_contacto):
    if len(nombre_contacto) == 1:
        query_regex = re.compile('^' + re.escape(nombre_contacto), re.IGNORECASE)
    else:
        query_regex = re.compile(re.escape(nombre_contacto), re.IGNORECASE)
    
    cursor = collection.find({"nombre_contacto": {"$regex": query_regex}})
    data = list(cursor)

    data.sort(key=lambda x: x['nombre_contacto'].lower().startswith(nombre_contacto.lower()), reverse=True)
    
    if not data:
        return jsonify({"message": "No se encontraron resultados para el nombre de contacto proporcionado."}), 404
    
    for item in data:
        item['_id'] = str(item['_id'])

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
