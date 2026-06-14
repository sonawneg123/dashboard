# UserVault — User Dashboard

A full-stack web app with a Flask backend, SQLite database, and a modern glassmorphism UI.

## Features
- Register users with name and email
- View all users in a real-time filterable table
- Delete users with a confirmation modal (no page reload)
- SQLite database seeded from `test.sql`

## Project Structure
```
user-dashboard/
├── app.py              ← Flask backend
├── test.sql            ← DB schema + seed data
├── requirements.txt
├── templates/
│   └── index.html      ← Jinja2 template
└── static/
    ├── css/style.css
    └── js/app.js
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app (auto-creates users.db from test.sql)
python app.py

# 3. Open in your browser
http://localhost:5000
```

## API Endpoints
| Method | Route            | Description            |
|--------|------------------|------------------------|
| GET    | `/`              | Main dashboard page    |
| POST   | `/register`      | Register a new user    |
| DELETE | `/delete/<id>`   | Delete a user (JSON)   |
| GET    | `/users`         | List all users (JSON)  |

## Database
The `test.sql` file contains the schema and sample data. On first run, `users.db`
is created automatically. To reset, delete `users.db` and restart the app.
