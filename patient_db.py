import json
import os

DB_FILE = "patients_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def get_patient(username):
    db = load_db()
    return db.get(username)

def save_patient(username, age, weight):
    db = load_db()
    db[username] = {
        "age": age,
        "weight": weight,
        "history": db.get(username, {}).get("history", [])
    }
    save_db(db)

def add_history(username, diagnosis):
    db = load_db()
    if username in db:
        if "history" not in db[username]:
            db[username]["history"] = []
        db[username]["history"].append(diagnosis)
        save_db(db)
