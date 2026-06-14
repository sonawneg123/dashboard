"""
routes/health.py — Health & readiness checks for ALB target groups
"""

from flask import Blueprint, jsonify
from sqlalchemy import text
import logging, time

log = logging.getLogger(__name__)
health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health():
    """Shallow health — always 200 if process is alive."""
    return jsonify(status="ok", service="backend"), 200


@health_bp.route("/health/ready")
def ready():
    """Deep readiness — checks DB connectivity (used by ALB)."""
    from app import db
    start = time.monotonic()
    try:
        db.session.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - start) * 1000, 2)
        return jsonify(status="ready", db="connected", latency_ms=latency_ms), 200
    except Exception as e:
        log.error("Readiness check failed: %s", e)
        return jsonify(status="not_ready", db="unreachable", error=str(e)), 503


@health_bp.route("/health/live")
def live():
    """Liveness probe."""
    return jsonify(status="alive"), 200
