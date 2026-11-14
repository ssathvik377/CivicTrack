
from flask import Flask, request, jsonify, send_file
import sqlite3
import uuid
from datetime import datetime

app = Flask(__name__)

DB_NAME = "civictrack.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE,
            name TEXT,
            category TEXT,
            description TEXT,
            location TEXT,
            priority TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    columns = [
        row[1] for row in
        conn.execute("PRAGMA table_info(complaints)")
    ]

    if "name" not in columns:
        conn.execute(
            "ALTER TABLE complaints ADD COLUMN name TEXT"
        )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/style.css")
def css():
    return send_file("style.css")


@app.route("/script.js")
def javascript():
    return send_file("script.js")


@app.route("/api/complaints", methods=["POST"])
def submit_complaint():

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    category = data.get("category", "").strip()
    description = data.get("description", "").strip()
    location = data.get("location", "").strip()
    priority = data.get("severity", "medium").capitalize()

    if not all([name, category, description, location]):
        return jsonify({"error": "Fill all required fields"}), 400

    if priority not in ["Critical", "High", "Medium", "Low"]:
        priority = "Medium"

    complaint_id = "CT" + uuid.uuid4().hex[:8].upper()

    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        INSERT INTO complaints
        (complaint_id, name, category, description,
         location, priority, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        name,
        category,
        description,
        location,
        priority,
        "Pending",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Complaint submitted successfully!",
        "id": complaint_id,
        "name": name,
        "category": category,
        "description": description,
        "location": location,
        "priority": priority,
        "status": "Pending"
    }), 201


@app.route("/api/complaints", methods=["GET"])
def get_complaints():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT * FROM complaints ORDER BY id DESC"
    ).fetchall()

    conn.close()

    result = []

    for row in rows:
        complaint = dict(row)
        complaint["id"] = complaint["complaint_id"]
        result.append(complaint)

    return jsonify(result)

# UPDATE COMPLAINT STATUS

@app.route("/api/complaints/<complaint_id>", methods=["PATCH"])
def update_complaint_status(complaint_id):

    data = request.get_json(silent=True) or {}
    status = data.get("status", "")

    allowed_statuses = ["Pending", "In Progress", "Resolved"]

    if status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        "UPDATE complaints SET status = ? WHERE complaint_id = ?",
        (status, complaint_id)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Complaint not found"}), 404

    return jsonify({
        "message": "Status updated successfully",
        "complaint_id": complaint_id,
        "status": status
    })
if __name__ == "__main__":
    create_database()
    app.run(debug=True)
