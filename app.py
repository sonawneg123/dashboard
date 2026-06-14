"""
User Dashboard — Flask Backend
Run:  python app.py
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash

# ── Config ────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, "users.db")
SQL_PATH  = os.path.join(BASE_DIR, "test.sql")

app = Flask(__name__)
app.secret_key = "change-me-in-production"


# ── Database helpers ──────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # rows behave like dicts
    return conn


def init_db():
    """Create and seed the database from test.sql if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        with get_db() as conn:
            with open(SQL_PATH, "r") as f:
                conn.executescript(f.read())
        print("✓ Database initialised from test.sql")


# ── Routes ────────────────────────────────────────────────────
@app.route("/")
def index():
    with get_db() as conn:
        users = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
    return render_template("index.html", users=users)


@app.route("/register", methods=["POST"])
def register():
    name  = request.form.get("name",  "").strip()
    email = request.form.get("email", "").strip().lower()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("index"))

    try:
        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)", (name, email)
            )
        flash(f"Welcome, {name}! You've been registered successfully.", "success")
    except sqlite3.IntegrityError:
        flash("That email is already registered.", "error")

    return redirect(url_for("index"))


@app.route("/delete/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None:
            return jsonify({"ok": False, "error": "User not found"}), 404
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return jsonify({"ok": True, "name": row["name"]})


@app.route("/users")
def users_json():
    """JSON endpoint — useful for debugging / AJAX refreshes."""
    with get_db() as conn:
        users = conn.execute(
            "SELECT * FROM users ORDER BY created_at DESC"
        ).fetchall()
    return jsonify([dict(u) for u in users])


# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
