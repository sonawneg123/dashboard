"""
routes/users.py — HTML CRUD routes (server-side rendered)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
import logging

log = logging.getLogger(__name__)
users_bp = Blueprint("users", __name__)


def _get_db_and_models():
    from app import db, User, AuditLog
    return db, User, AuditLog


def _audit(db, AuditLog, action, record_id, old=None, new=None):
    entry = AuditLog(
        action=action,
        table_name="users",
        record_id=record_id,
        old_data=old,
        new_data=new,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)


@users_bp.route("/")
def index():
    db, User, AuditLog = _get_db_and_models()
    page    = request.args.get("page", 1, type=int)
    search  = request.args.get("q", "").strip()
    role    = request.args.get("role", "")
    status  = request.args.get("status", "")
    per_page = 10

    query = User.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.name.like(like)) |
            (User.email.like(like)) |
            (User.phone.like(like))
        )
    if role:
        query = query.filter_by(role=role)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    stats = {
        "total":    User.query.count(),
        "active":   User.query.filter_by(status="active").count(),
        "inactive": User.query.filter_by(status="inactive").count(),
        "admin":    User.query.filter_by(role="admin").count(),
    }

    return render_template(
        "index.html",
        users=pagination.items,
        pagination=pagination,
        search=search,
        role=role,
        status=status,
        stats=stats,
    )


@users_bp.route("/users/create", methods=["GET","POST"])
def create_user():
    db, User, AuditLog = _get_db_and_models()
    if request.method == "POST":
        name   = request.form.get("name","").strip()
        email  = request.form.get("email","").strip().lower()
        phone  = request.form.get("phone","").strip()
        role   = request.form.get("role","viewer")
        status = request.form.get("status","active")

        if not name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("users.create_user"))

        user = User(name=name, email=email, phone=phone or None, role=role, status=status)
        try:
            db.session.add(user)
            db.session.flush()
            _audit(db, AuditLog, "CREATE", user.id, new=user.to_dict())
            db.session.commit()
            flash(f"User '{name}' created successfully.", "success")
            return redirect(url_for("users.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already exists.", "error")
        except Exception as e:
            db.session.rollback()
            log.exception("Create user failed")
            flash("An unexpected error occurred.", "error")

    return render_template("create.html")


@users_bp.route("/users/<int:uid>/edit", methods=["GET","POST"])
def edit_user(uid):
    db, User, AuditLog = _get_db_and_models()
    user = User.query.get_or_404(uid)

    if request.method == "POST":
        old_data = user.to_dict()
        user.name   = request.form.get("name",   user.name).strip()
        user.email  = request.form.get("email",  user.email).strip().lower()
        user.phone  = request.form.get("phone",  user.phone or "").strip() or None
        user.role   = request.form.get("role",   user.role)
        user.status = request.form.get("status", user.status)

        try:
            _audit(db, AuditLog, "UPDATE", user.id, old=old_data, new=user.to_dict())
            db.session.commit()
            flash(f"User '{user.name}' updated.", "success")
            return redirect(url_for("users.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already in use by another user.", "error")
        except Exception:
            db.session.rollback()
            log.exception("Edit user failed")
            flash("An unexpected error occurred.", "error")

    return render_template("edit.html", user=user)


@users_bp.route("/users/<int:uid>/delete", methods=["POST"])
def delete_user(uid):
    db, User, AuditLog = _get_db_and_models()
    user = User.query.get_or_404(uid)
    try:
        _audit(db, AuditLog, "DELETE", user.id, old=user.to_dict())
        db.session.delete(user)
        db.session.commit()
        flash(f"User '{user.name}' deleted.", "success")
    except Exception:
        db.session.rollback()
        log.exception("Delete user failed")
        flash("Could not delete user.", "error")
    return redirect(url_for("users.index"))


@users_bp.route("/users/<int:uid>")
def view_user(uid):
    db, User, AuditLog = _get_db_and_models()
    user = User.query.get_or_404(uid)
    logs = AuditLog.query.filter_by(record_id=uid, table_name="users") \
                         .order_by(AuditLog.created_at.desc()).limit(20).all()
    return render_template("view.html", user=user, logs=logs)
