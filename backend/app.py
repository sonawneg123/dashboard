"""
Three-Tier App — Flask Backend
Connects to MySQL RDS via PyMySQL / SQLAlchemy.
Runs on port 5000 (internal, behind Internal ALB).
"""

import os
import json
import logging
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, render_template, request,
    redirect, url_for, jsonify, flash, abort
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s"
)
log = logging.getLogger(__name__)

# ── App factory ───────────────────────────────────────────────────
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("SECRET_KEY", "change-in-prod-please")

    # ── MySQL RDS connection string ───────────────────────────────
    db_url = (
        "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}"
        "?charset=utf8mb4&ssl_ca=/etc/ssl/certs/ca-certificates.crt"
    ).format(
        user=os.getenv("DB_USER",     "admin"),
        pw  =os.getenv("DB_PASSWORD", "password"),
        host=os.getenv("DB_HOST",     "localhost"),
        port=os.getenv("DB_PORT",     "3306"),
        db  =os.getenv("DB_NAME",     "usermanagement"),
    )
    app.config["SQLALCHEMY_DATABASE_URI"]        = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]      = {
        "pool_pre_ping":   True,
        "pool_recycle":    300,
        "pool_size":       10,
        "max_overflow":    20,
        "connect_args":    {"connect_timeout": 10},
    }

    db.init_app(app)
    Migrate(app, db)

    # Register blueprints
    from routes.users  import users_bp
    from routes.health import health_bp
    from routes.api    import api_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    # ── Error handlers ────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return jsonify(error="Not found"), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        log.exception("Internal error")
        if request.path.startswith("/api/"):
            return jsonify(error="Internal server error"), 500
        return render_template("errors/500.html"), 500

    return app


# ── SQLAlchemy instance (shared) ──────────────────────────────────
db = SQLAlchemy()


# ── Models ────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(255), nullable=False, unique=True)
    phone      = db.Column(db.String(20),  nullable=True)
    role       = db.Column(db.Enum("admin","editor","viewer"), default="viewer", nullable=False)
    status     = db.Column(db.Enum("active","inactive","banned"), default="active", nullable=False)
    avatar_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime,   default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "phone":      self.phone or "",
            "role":       self.role,
            "status":     self.status,
            "avatar_url": self.avatar_url or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action     = db.Column(db.String(50),  nullable=False)
    table_name = db.Column(db.String(64),  nullable=False)
    record_id  = db.Column(db.BigInteger,  nullable=True)
    old_data   = db.Column(db.JSON,        nullable=True)
    new_data   = db.Column(db.JSON,        nullable=True)
    ip_address = db.Column(db.String(45),  nullable=True)
    created_at = db.Column(db.DateTime,    default=lambda: datetime.now(timezone.utc))


# ── Entry point ───────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
