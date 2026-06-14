# NexusDB — Three-Tier Monolithic Application

> Flask · MySQL RDS · External ALB → Internal ALB → Gunicorn · Full CRUD · Dynamic UI

---

## Architecture Overview

```
Internet
    │
    ▼
┌───────────────────────────────────────┐
│         External ALB (HTTPS/443)       │  ← Public-facing, ACM TLS cert
│         Security Group: 0.0.0.0:443   │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────┐
│   Frontend EC2 Fleet (Nginx)           │  ← Public Subnet
│   • Receives traffic from Ext ALB     │    Security Group: from Ext ALB SG
│   • Reverse proxies to Internal ALB   │
└─────────────────┬─────────────────────┘
                  │  (HTTP to Internal ALB)
                  ▼
┌───────────────────────────────────────┐
│         Internal ALB (HTTP/80)         │  ← Private Subnet, not public
│         Target: Backend EC2 fleet      │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────┐
│   Backend EC2 Fleet (Nginx→Gunicorn)   │  ← Private Subnet
│   • Nginx: port 80 → Gunicorn: 5000   │    Security Group: from Int ALB SG
│   • Flask app with SQLAlchemy ORM     │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────┐
│   MySQL RDS (Multi-AZ)                 │  ← Private Subnet
│   Port 3306 · db: usermanagement      │    Security Group: from Backend SG
└───────────────────────────────────────┘
```

---

## Project Structure

```
three-tier-app/
├── schema.sql                        ← MySQL RDS schema + seed data
├── backend/
│   ├── app.py                        ← Flask app factory + models
│   ├── gunicorn.conf.py              ← Production Gunicorn config
│   ├── requirements.txt
│   ├── .env.example                  ← Copy to .env and fill values
│   ├── routes/
│   │   ├── users.py                  ← HTML CRUD (Create/Read/Update/Delete)
│   │   ├── api.py                    ← REST JSON API (/api/v1/*)
│   │   └── health.py                 ← ALB health check endpoints
│   ├── templates/
│   │   ├── base.html                 ← Sidebar layout + modal + toast
│   │   ├── index.html                ← Dashboard (paginated table + filters)
│   │   ├── create.html               ← Add user form
│   │   ├── edit.html                 ← Edit user form
│   │   ├── view.html                 ← User detail + audit log
│   │   └── errors/{404,500}.html
│   └── static/
│       ├── css/main.css              ← Full design system (glassmorphism)
│       └── js/main.js                ← Dynamic interactions, AJAX, modal
├── nginx/
│   ├── frontend/frontend.conf        ← Nginx on Frontend EC2 (Ext ALB proxy)
│   └── backend/backend.conf          ← Nginx on Backend EC2 (→ Gunicorn)
└── infra/
    └── nexusdb.service               ← systemd service unit
```

---

## AWS Setup Guide

### 1 — RDS MySQL

```
Engine         : MySQL 8.0
Instance       : db.t3.medium (or db.r6g.large for prod)
Multi-AZ       : Yes (for prod)
DB Name        : usermanagement
Subnet Group   : Private subnets only
Security Group : Allow port 3306 from Backend EC2 SG
```

Apply schema:
```bash
mysql -h <RDS_ENDPOINT> -u admin -p usermanagement < schema.sql
```

---

### 2 — Backend EC2 (Private Subnet)

```bash
# 1. Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx

# 2. Create app directory
sudo mkdir -p /opt/nexusdb
sudo cp -r backend/ /opt/nexusdb/backend

# 3. Python venv + packages
python3 -m venv /opt/nexusdb/venv
/opt/nexusdb/venv/bin/pip install -r /opt/nexusdb/backend/requirements.txt

# 4. Configure env
sudo cp /opt/nexusdb/backend/.env.example /opt/nexusdb/backend/.env
sudo nano /opt/nexusdb/backend/.env          # Fill in your RDS credentials

# 5. Run DB migrations (creates tables from models)
cd /opt/nexusdb/backend
/opt/nexusdb/venv/bin/flask db init
/opt/nexusdb/venv/bin/flask db migrate -m "initial"
/opt/nexusdb/venv/bin/flask db upgrade

# 6. Nginx config
sudo cp nginx/backend/backend.conf /etc/nginx/conf.d/backend.conf
sudo nginx -t && sudo systemctl reload nginx

# 7. Start as systemd service
sudo cp infra/nexusdb.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nexusdb

# 8. Create Gunicorn log directory
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn
```

---

### 3 — Internal ALB

```
Scheme              : Internal
Listeners           : HTTP:80
Target Group        : Backend EC2 instances, port 80
Health Check Path   : /health/ready
Health Check Interval: 15s
Healthy Threshold   : 2
Unhealthy Threshold : 3
```

---

### 4 — Frontend EC2 (Public Subnet)

```bash
sudo apt install -y nginx

# Edit INTERNAL_ALB_DNS in frontend.conf first!
sudo cp nginx/frontend/frontend.conf /etc/nginx/conf.d/default.conf
sudo nginx -t && sudo systemctl reload nginx
```

Edit `nginx/frontend/frontend.conf` and replace `<INTERNAL_ALB_DNS>` with
your actual Internal ALB DNS name.

---

### 5 — External ALB

```
Scheme              : Internet-facing
Listeners           : HTTPS:443 (ACM cert), HTTP:80 → redirect to HTTPS
Target Group        : Frontend EC2 instances, port 443
Health Check Path   : /health
Security Group      : Inbound 443/80 from 0.0.0.0/0
```

---

## API Reference

| Method | Endpoint               | Description            |
|--------|------------------------|------------------------|
| GET    | `/`                    | Dashboard HTML         |
| GET    | `/users/create`        | Create user form       |
| POST   | `/users/create`        | Submit create form     |
| GET    | `/users/<id>`          | View user + audit log  |
| GET    | `/users/<id>/edit`     | Edit user form         |
| POST   | `/users/<id>/edit`     | Submit edit form       |
| POST   | `/users/<id>/delete`   | Delete user            |
| GET    | `/api/v1/users`        | List users (JSON)      |
| POST   | `/api/v1/users`        | Create user (JSON)     |
| GET    | `/api/v1/users/<id>`   | Get user (JSON)        |
| PUT    | `/api/v1/users/<id>`   | Update user (JSON)     |
| DELETE | `/api/v1/users/<id>`   | Delete user (JSON)     |
| GET    | `/api/v1/stats`        | Dashboard stats (JSON) |
| GET    | `/health`              | Shallow health check   |
| GET    | `/health/ready`        | Deep DB health check   |
| GET    | `/health/live`         | Liveness probe         |

---

## Local Dev (SQLite fallback)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Set DB_HOST=localhost and a local MySQL, OR use SQLite:
# Change DB URI in app.py to: sqlite:///dev.db

flask db init && flask db migrate && flask db upgrade
flask run --debug
```

Open: http://localhost:5000
