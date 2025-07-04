from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
DATABASE = 'data/database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );
        ''')
        db.commit()
        db.close()

@app.route('/')
def hello_world():
    return 'Hello from Flask Backend!'

@app.route('/items', methods=['GET'])
def get_items():
    db = get_db()
    items = db.execute('SELECT * FROM items').fetchall()
    db.close()
    return jsonify([dict(item) for item in items])

@app.route('/items', methods=['POST'])
def add_item():
    new_item = request.json
    name = new_item['name']
    db = get_db()
    db.execute('INSERT INTO items (name) VALUES (?)', (name,))
    db.commit()
    db.close()
    return jsonify({'message': 'Item added successfully', 'name': name}), 201

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8001)
