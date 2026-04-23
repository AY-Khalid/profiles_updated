# Profile Intelligence Service

A RESTful API that accepts a name, enriches it with data from three external APIs (Genderize, Agify, Nationalize), stores the result in a PostgreSQL database, and exposes endpoints to retrieve, filter, and delete profiles.

Built with FastAPI, SQLAlchemy, and PostgreSQL.

---

## Live API

**Base URL:** `https://your-deployed-url.up.railway.app`

---

## Tech Stack

- **FastAPI** — API framework
- **PostgreSQL** — database
- **SQLAlchemy** — async ORM
- **httpx** — async HTTP client for external API calls
- **uuid6** — UUID v7 generation
- **Railway** — deployment platform

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # App entry point, CORS, startup
│   ├── database.py          # DB engine and session
│   ├── models.py            # SQLAlchemy Profile model
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   └── profiles.py      # All /api/profiles endpoints
│   └── services/
│       ├── __init__.py
│       └── external_apis.py # Genderize, Agify, Nationalize integration
├── requirements.txt
└── .env
```

---

## Getting Started Locally

### 1. Clone the repo

```bash
git clone https://github.com/your-username/profile-intelligence.git
cd profile-intelligence/backend
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your environment variables

Create a `.env` file in the `backend/` folder:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/profiles_db
```

> Make sure PostgreSQL is running locally and the database `profiles_db` exists.
> Create it with: `CREATE DATABASE profiles_db;` in your PostgreSQL shell.

### 5. Run the server

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

You can explore the auto-generated docs at `http://localhost:8000/docs`

---

## API Endpoints

### POST `/api/profiles`

Accepts a name, fetches enriched data from external APIs, and stores the result.

**Request body:**
```json
{ "name": "ella" }
```

**Success response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-7d4a-4c91-9c2a-1f0a8e5b6d12",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DK",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

**If the name already exists (idempotency):**
```json
{
  "status": "success",
  "message": "Profile already exists",
  "data": { "...existing profile..." }
}
```

---

### GET `/api/profiles`

Returns all stored profiles. Supports optional case-insensitive filters.

**Query params:** `gender`, `country_id`, `age_group`

**Example:** `/api/profiles?gender=female&country_id=NG`

**Success response (200):**
```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "id": "b3f9c1e2-...",
      "name": "ella",
      "gender": "female",
      "age": 46,
      "age_group": "adult",
      "country_id": "DK"
    }
  ]
}
```

---

### GET `/api/profiles/{id}`

Returns a single profile by its UUID.

**Success response (200):**
```json
{
  "status": "success",
  "data": {
    "id": "b3f9c1e2-...",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "DK",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

---

### DELETE `/api/profiles/{id}`

Deletes a profile by its UUID. Returns `204 No Content` on success.

---

## Error Responses

All errors follow this structure:

```json
{ "status": "error", "message": "<error message>" }
```

| Status | Meaning |
|--------|---------|
| 400 | Missing or empty name |
| 404 | Profile not found |
| 502 | External API returned invalid data |
| 500 | Internal server error |

---

## External APIs Used

| API | Purpose |
|-----|---------|
| [Genderize](https://api.genderize.io) | Predicts gender from name |
| [Agify](https://api.agify.io) | Predicts age from name |
| [Nationalize](https://api.nationalize.io) | Predicts nationality from name |

All three are free and require no API key.

---

## Age Group Classification

| Age Range | Group |
|-----------|-------|
| 0 – 12 | child |
| 13 – 19 | teenager |
| 20 – 59 | adult |
| 60+ | senior |

---

## Deployment (Railway)

1. Push the repo to GitHub (must be public)
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add a **PostgreSQL** plugin inside the project
4. In your app's **Variables** tab, set:
```
DATABASE_URL=postgresql+asyncpg://<railway-provided-url>
```
> Make sure to change `postgresql://` to `postgresql+asyncpg://`

5. Set the start command:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
6. Railway deploys automatically on every push to main

---

## Notes

- All IDs are **UUID v7**
- All timestamps are **UTC ISO 8601**
- CORS is open (`*`) to allow the grading script to reach the server
- Submitting the same name twice returns the existing profile — no duplicate records are created
