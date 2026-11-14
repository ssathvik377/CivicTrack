from flask import Flask, request, jsonify, send_file, session
import sqlite3
import uuid
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = os.environ.get(
    "CIVICTRACK_SECRET_KEY",
    "change-this-secret-before-deployment"
)

DB_NAME = "civictrack.db"

# DEMO ADMIN ACCOUNT

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "CivicTrack@123"

ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

# CHECK ADMIN LOGIN

def admin_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return jsonify({"error": "Admin login required"}), 401

        return function(*args, **kwargs)

    return wrapper


# CREATE DATABASE

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


# HOME PAGE

@app.route("/")
def home():
    return send_file("index.html")


@app.route("/style.css")
def css():
    return send_file("style.css")


@app.route("/script.js")
def javascript():
    return send_file("script.js")


# ADMIN LOGIN

@app.route("/api/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json(silent=True) or {}

    username = data.get("username", "")
    password = data.get("password", "")

    if (
        username == ADMIN_USERNAME
        and check_password_hash(ADMIN_PASSWORD_HASH, password)
    ):

        session.clear()
        session["admin_logged_in"] = True

        return jsonify({
            "message": "Admin login successful"
        })

    return jsonify({
        "error": "Invalid username or password"
    }), 401


# CHECK LOGIN STATUS

@app.route("/api/admin/session", methods=["GET"])
def admin_session():

    return jsonify({
        "logged_in": bool(session.get("admin_logged_in"))
    })


# ADMIN LOGOUT

@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():

    session.clear()

    return jsonify({
        "message": "Admin logged out successfully"
    })


# SUBMIT COMPLAINT

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


# GET ALL COMPLAINTS

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


# UPDATE COMPLAINT STATUS - ADMIN ONLY

@app.route("/api/complaints/<complaint_id>", methods=["PATCH"])
@admin_required
def update_complaint_status(complaint_id):

    data = request.get_json(silent=True) or {}
    status = data.get("status", "")

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

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


# ADMIN LOGIN PAGE
@app.route("/admin")
def admin():
    return send_file("admin.html")


# ADMIN DASHBOARD PAGE
@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    return send_file("admin_dashboard.html")

# START FLASK SERVER

if __name__ == "__main__":
    create_database()
    app.run(debug=True)