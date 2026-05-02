# CredScore — Your Work. Verified.

A marketplace platform where college students complete real paid tasks for small businesses. Every task automatically builds into a verified performance profile.

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

The app will start at `http://localhost:5000`. On first run it will auto-create `credscore.db` and seed demo data.

### 3. Expose with ngrok (for public sharing)

```bash
ngrok http 5000
```

Copy the ngrok URL — Share Profile links on student dashboards will automatically use the live URL.

---

## Demo Accounts (seeded on first run)

| Role | Email | Password |
|---|---|---|
| Student | vaibhav@sai.edu | demo123 |
| Student | lingaesh@vit.edu | demo123 |
| Student | navya@srm.edu | demo123 |
| Business | cafe@brewbites.com | demo123 |
| Business | info@zestify.com | demo123 |
| Recruiter | hr@technova.com | demo123 |
| Admin | admin@credscore.io | admin123 |

---

## Project Structure

```
CredScore/
├── app.py                  ← Flask entry point
├── requirements.txt
├── README.md
├── credscore.db            ← SQLite DB (auto-created)
├── static/
│   ├── css/style.css
│   ├── js/main.js
│   └── logo.png
└── templates/
    ├── base.html
    ├── auth.html
    ├── index.html
    ├── student_dashboard.html
    ├── business_dashboard.html
    ├── recruiter_dashboard.html
    ├── explore.html
    ├── profile.html
    ├── admin_flags.html
    ├── how_it_works.html
    ├── pricing.html
    ├── about.html
    └── contact.html
```

## Features

- **Authentication**: Role-based login/signup (Student / Business / Recruiter / Admin)
- **Student Dashboard**: Real CredScore, task history, performance chart, shareable profile link
- **Business Dashboard**: Post tasks, review applicants, hire students, track history
- **Recruiter Dashboard**: Filter verified students by CredScore, college, category
- **Explore Tasks**: Browse and apply to open tasks
- **Public Profiles**: `/profile/<student_id>` — viewable without login
- **Anti-Gaming Layer**: 5 automatic fraud detection triggers
- **Blind Mutual Ratings**: Neither side sees the other's rating until both submit or 48h pass
- **Admin Flags**: `/admin/flags` — review all flagged activities
- **Dark/Light Theme**: Persisted in localStorage
