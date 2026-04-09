# Cultural Etiquette Advisory System

This version is a real Python-backed implementation of the SRS using **FastAPI**, **MySQL**, and a **React** frontend that talks to a CRUD API.

## Stack

- Backend: `FastAPI`
- Database: `MySQL` via `PyMySQL`
- Frontend: React + Vite
- Auth: token-based sessions stored in the database

## What is included

- User registration and login
- Admin login with role checks
- Real database persistence in MySQL
- CRUD API for cultures, scenarios, rules, saved advice, and feedback
- Advice generation endpoint with risk meter calculation
- React frontend wired to the API with separate pages for login, rules, dashboard, and feedback
- Seeded all-country coverage using `pycountry`
- Seeded starter data and admin account

## Run

1. Create a MySQL database user with permission to create databases/tables.

2. Set environment variables:

```bash
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=your_password
set MYSQL_DATABASE=ceas
```

3. Build the React frontend:

```bash
npm run build
```

4. Start the server:

```bash
uvicorn main:app --reload
```

5. Open `http://127.0.0.1:8000`

6. Optional admin credentials:

- Email: `admin@ceas.local`
- Password: `admin123`

## API docs

FastAPI Swagger UI is available at:

- `http://127.0.0.1:8000/docs`

## Main files

- Backend: [main.py](/c:/Users/DELL/Pictures/codee/main.py)
- React app shell: [src/App.jsx](/c:/Users/DELL/Pictures/codee/src/App.jsx)
- Dashboard page: [src/pages/DashboardPage.jsx](/c:/Users/DELL/Pictures/codee/src/pages/DashboardPage.jsx)
- Rules page: [src/pages/RulesPage.jsx](/c:/Users/DELL/Pictures/codee/src/pages/RulesPage.jsx)
- Feedback page: [src/pages/FeedbackPage.jsx](/c:/Users/DELL/Pictures/codee/src/pages/FeedbackPage.jsx)
- Login page: [src/pages/LoginPage.jsx](/c:/Users/DELL/Pictures/codee/src/pages/LoginPage.jsx)

## Notes

- The MySQL database named by `MYSQL_DATABASE` is created automatically on first run if the configured user has permission.
- The frontend only uses `localStorage` for the auth token.
- All countries are seeded into the `cultures` table, and each country gets default rules for all seeded scenarios.
- You can extend the seeded knowledge base from the admin rules page or directly through the API.
