from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.get('/')
def home():
    return 'Sofyan OS API Running'

@app.get('/tasks')
def tasks():
    return jsonify([])

@app.post('/tasks')
def create_task():
    data=request.json
    return jsonify({"status":"created","task":data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
