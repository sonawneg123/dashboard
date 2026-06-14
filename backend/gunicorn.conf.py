# ================================================================
#  Gunicorn Production Config — NexusDB Backend
#  Usage: gunicorn -c gunicorn.conf.py app:app
# ================================================================

import multiprocessing, os

# ── Binding ───────────────────────────────────────────────────────
bind        = "127.0.0.1:5000"
backlog     = 2048

# ── Workers ───────────────────────────────────────────────────────
# Rule of thumb: 2 × CPU cores + 1
workers     = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "gthread"        # threaded; good for I/O-bound Flask + DB
threads     = int(os.getenv("GUNICORN_THREADS", 4))
worker_connections = 1000

# ── Timeouts ──────────────────────────────────────────────────────
timeout          = 60
keepalive        = 5
graceful_timeout = 30

# ── Logging ───────────────────────────────────────────────────────
accesslog  = "/var/log/gunicorn/access.log"
errorlog   = "/var/log/gunicorn/error.log"
loglevel   = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# ── Process naming ────────────────────────────────────────────────
proc_name  = "nexusdb-backend"

# ── Security ──────────────────────────────────────────────────────
limit_request_line        = 4096
limit_request_fields      = 100
limit_request_field_size  = 8190

# ── Hooks ─────────────────────────────────────────────────────────
def on_starting(server):
    server.log.info("NexusDB Gunicorn starting — workers: %s", workers)

def worker_exit(server, worker):
    server.log.info("Worker %s exited (pid: %s)", worker.age, worker.pid)
