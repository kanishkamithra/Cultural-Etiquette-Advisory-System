# Cultural Etiquette Advisory System (CEAS)

CEAS is a premium SaaS-style dashboard that delivers scenario-based cultural guidance, risk awareness, and safe alternatives so users can navigate global interactions with confidence.

## Highlights

- Country + scenario advice with Do/Don't guidance and explanations
- Context-aware adjustments (formal/informal, business/casual, relationship)
- Risk meter and conflict detection from user notes
- Natural-language request parsing
- Simulation mode for decision practice
- Admin analytics + community tips
- Clean frontend-backend architecture

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI + PyMySQL
- Database: MySQL

## Project Structure

```
backend/
  main.py
  models/
  routes/
  services/
frontend/
  src/
    components/
    pages/
    services/api.js
```

## Getting Started (Windows)

### 1) Backend

Make sure MySQL is running, then update `start_ceas.bat` if your password differs.

```
cd c:\Users\DELL\Pictures\codee
.\start_ceas.bat
```

Backend runs on: `http://127.0.0.1:8001`

### 2) Frontend (dev)

```
cd c:\Users\DELL\Pictures\codee\frontend
npm install
npm run dev
```

Frontend runs on: `http://127.0.0.1:5173`

Vite proxies `/api` to the backend, so both services work together during development.

### 3) Frontend (production build served by backend)

```
cd c:\Users\DELL\Pictures\codee\frontend
npm run build
```

Then open: `http://127.0.0.1:8001`

## Admin Access

- Email: `admin@ceas.local`
- Password: `admin123`

## API Docs

FastAPI Swagger UI: `http://127.0.0.1:8001/docs`

## Screenshots

Add screenshots in `frontend/` and link them here:

```
![Dashboard](frontend/your-screenshot.png)
```

## Notes

- The database named by `MYSQL_DATABASE` is created automatically on first run if the configured user has permission.
- All countries are seeded into the `cultures` table with default rules for core scenarios.
- You can extend rules from the Admin page or through the API.
