"""
routes/api.py — JSON REST API (used by dynamic frontend)
Prefix: /api/v1
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
import logging

log = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


def _get_db_and_models():
    from app import db, User, AuditLog
    return db, User, AuditLog


def _audit(db, AuditLog, action, record_id, old=None, new=None):
    entry = AuditLog(
        action=action, table_name="users", record_id=record_id,
        old_data=old, new_data=new, ip_address=request.remote_addr,
    )
    db.session.add(entry)


# ── List / Search ─────────────────────────────────────────────────
@api_bp.route("/users", methods=["GET"])
def list_users():
    db, User, _ = _get_db_and_models()
    page    = request.args.get("page",   1, type=int)
    per_pg  = request.args.get("limit", 10, type=int)
    search  = request.args.get("q",     "").strip()
    role    = request.args.get("role",  "")
    status  = request.args.get("status","")

    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.like(like)) | (User.email.like(like)) | (User.phone.like(like))
        )
    if role:   query = query.filter_by(role=role)
    if status: query = query.filter_by(status=status)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=min(per_pg, 100), error_out=False
    )
    return jsonify({
        "users":    [u.to_dict() for u in pagination.items],
        "total":    pagination.total,
        "pages":    pagination.pages,
        "page":     pagination.page,
        "per_page": pagination.per_page,
    })


# ── Get one ───────────────────────────────────────────────────────
@api_bp.route("/users/<int:uid>", methods=["GET"])
def get_user(uid):
    _, User, _ = _get_db_and_models()
    user = User.query.get_or_404(uid)
    return jsonify(user.to_dict())


# ── Create ────────────────────────────────────────────────────────
@api_bp.route("/users", methods=["POST"])
def create_user():
    db, User, AuditLog = _get_db_and_models()
    data = request.get_json(silent=True) or {}

    name   = data.get("name","").strip()
    email  = data.get("email","").strip().lower()
    phone  = data.get("phone","").strip() or None
    role   = data.get("role","viewer")
    status = data.get("status","active")

    if not name or not email:
        return jsonify(error="name and email are required"), 400
    if role not in ("admin","editor","viewer"):
        return jsonify(error="invalid role"), 400
    if status not in ("active","inactive","banned"):
        return jsonify(error="invalid status"), 400

    user = User(name=name, email=email, phone=phone, role=role, status=status)
    try:
        db.session.add(user)
        db.session.flush()
        _audit(db, AuditLog, "CREATE", user.id, new=user.to_dict())
        db.session.commit()
        return jsonify(user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Email already exists"), 409
    except Exception:
        db.session.rollback()
        log.exception("API create user failed")
        return jsonify(error="Internal error"), 500


# ── Update ────────────────────────────────────────────────────────
@api_bp.route("/users/<int:uid>", methods=["PUT","PATCH"])
def update_user(uid):
    db, User, AuditLog = _get_db_and_models()
    user = User.query.get_or_404(uid)
    data = request.get_json(silent=True) or {}
    old  = user.to_dict()

    if "name"   in data: user.name   = data["name"].strip()
    if "email"  in data: user.email  = data["email"].strip().lower()
    if "phone"  in data: user.phone  = data["phone"].strip() or None
    if "role"   in data: user.role   = data["role"]
    if "status" in data: user.status = data["status"]

    try:
        _audit(db, AuditLog, "UPDATE", user.id, old=old, new=user.to_dict())
        db.session.commit()
        return jsonify(user.to_dict())
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="Email already in use"), 409
    except Exception:
        db.session.rollback()
        log.exception("API update user failed")
        return jsonify(error="Internal error"), 500


# ── Delete ────────────────────────────────────────────────────────
@api_bp.route("/users/<int:uid>", methods=["DELETE"])
def delete_user(uid):
    db, User, AuditLog = _get_db_and_models()
    user = User.query.get_or_404(uid)
    try:
        _audit(db, AuditLog, "DELETE", user.id, old=user.to_dict())
        db.session.delete(user)
        db.session.commit()
        return jsonify(ok=True, message=f"User '{user.name}' deleted")
    except Exception:
        db.session.rollback()
        log.exception("API delete user failed")
        return jsonify(error="Internal error"), 500


# ── Stats ─────────────────────────────────────────────────────────
@api_bp.route("/stats", methods=["GET"])
def stats():
    db, User, AuditLog = _get_db_and_models()
    return jsonify({
        "total":    User.query.count(),
        "active":   User.query.filter_by(status="active").count(),
        "inactive": User.query.filter_by(status="inactive").count(),
        "banned":   User.query.filter_by(status="banned").count(),
        "admin":    User.query.filter_by(role="admin").count(),
        "editor":   User.query.filter_by(role="editor").count(),
        "viewer":   User.query.filter_by(role="viewer").count(),
        "recent_actions": AuditLog.query.order_by(AuditLog.created_at.desc()).limit(5).count(),
    })
