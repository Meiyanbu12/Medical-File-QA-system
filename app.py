from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os, threading
from datetime import datetime
from extractors import extract_text_from_file
from ollama_qa import ask_ollama
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
app.secret_key = "supersecret"
CORS(app, supports_credentials=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

client = MongoClient("mongodb://localhost:27017/")
db = client["medical_qa"]
users_collection = db["users"]
history_collection = db["history"]

stored_context = {}

def delete_file_after_delay(filepath, delay=600):
    def delayed_delete():
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"🗑️ Deleted {filepath}")
    threading.Timer(delay, delayed_delete).start()

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    if users_collection.find_one({"username": data["username"]}):
        return jsonify({"success": False, "message": "❌ Username already exists"})
    users_collection.insert_one(data)
    return jsonify({"success": True, "message": "✅ Signup successful"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = users_collection.find_one({"username": data["username"], "password": data["password"]})
    if user:
        session["user"] = data["username"]
        return jsonify({"success": True, "message": "✅ Login successful"})
    return jsonify({"success": False, "message": "❌ Invalid credentials"})

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"success": True})

@app.route("/upload", methods=["POST"])
def upload_files():
    files = request.files.getlist("files")
    uploaded = []

    for file in files:
        if file.filename:
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            content = extract_text_from_file(path)
            stored_context[file.filename] = content
            uploaded.append(file.filename)
            delete_file_after_delay(path)

    return jsonify({"uploaded": uploaded})

@app.route("/uploaded-files", methods=["GET"])
def list_files():
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ask", methods=["POST"])
def ask_question():
    data = request.get_json()
    question = data.get("question", "").strip()
    username = session.get("user", "guest")

    if not question:
        return jsonify({"error": "❌ Question missing"}), 400

    results = []

    for filename in os.listdir(UPLOAD_FOLDER):
        path = os.path.join(UPLOAD_FOLDER, filename)

        # Load content if not already loaded
        if filename not in stored_context:
            content = extract_text_from_file(path)
            stored_context[filename] = content
        else:
            content = stored_context[filename]

        # Ask question using full content
        if content and len(content) > 0:
            answer = ask_ollama(content, question)
            results.append({
                "filename": filename,
                "answer": answer
            })

            # Always store history
            history_collection.insert_one({
                "username": username,
                "filename": filename,
                "question": question,
                "answer": answer,
                "timestamp": datetime.utcnow()
            })

    if not results:
        return jsonify({"answers": [], "message": "❌ No relevant files found."})

    return jsonify({"answers": results, "message": f"✅ Found {len(results)} file(s) processed."})

@app.route("/history", methods=["GET"])
def get_history():
    username = session.get("user", "guest")
    history = history_collection.find({"username": username}).sort("timestamp", -1)
    return jsonify([
        {
            "_id": str(h["_id"]),
            "filename": h["filename"],
            "question": h["question"],
            "answer": h["answer"],
            "timestamp": h["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        } for h in history
    ])

@app.route("/history/<id>", methods=["DELETE"])
def delete_history_item(id):
    try:
        result = history_collection.delete_one({"_id": ObjectId(id)})
        return jsonify({"success": result.deleted_count == 1})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/history", methods=["DELETE"])
def clear_history():
    username = session.get("user", "guest")
    result = history_collection.delete_many({"username": username})
    return jsonify({"success": True, "deleted_count": result.deleted_count})

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("../frontend", path)

if __name__ == "__main__":
    app.run(debug=True)
