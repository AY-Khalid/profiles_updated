# Profile Intelligence Service

A RESTful API that accepts a name, enriches it with demographic data from three external APIs (Genderize, Agify, Nationalize), stores the result in a PostgreSQL database, and exposes endpoints to query, filter, sort, paginate, and search profiles using natural language.

Built with FastAPI, SQLAlchemy, and PostgreSQL.

---

## Live API

**Base URL:** `https://profilesupdated-production.up.railway.app/`

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
backend/
├── app/
│   ├── init.py
│   ├── main.py              # App entry point, CORS, startup
│   ├── database.py          # DB engine and session
│   ├── models.py            # SQLAlchemy Profile model
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── seed.py              # Database seeder (2026 profiles)
│   ├── routes/
│   │   ├── init.py
│   │   └── profiles.py      # All /api/profiles endpoints
│   └── services/
│       ├── init.py
│       └── external_apis.py # Genderize, Agify, Nationalize integration
├── seed_profiles.json        # Seed data (2026 names)
├── requirements.txt
└── .env

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

Auto-generated docs: `http://localhost:8000/docs`

### 6. Seed the database

```bash
python -m app.seed
```

This loads all 2026 profiles from `seed_profiles.json`, enriches each name via the external APIs, and inserts them into the database. Re-running is safe — existing profiles are skipped.

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
    "country_name": "Denmark",
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

Returns paginated profiles with optional filtering and sorting.

**Filter params:**

| Param | Type | Description |
|---|---|---|
| `gender` | string | `male` or `female` |
| `age_group` | string | `child`, `teenager`, `adult`, `senior` |
| `country_id` | string | ISO 2-letter code e.g. `NG` |
| `min_age` | int | Minimum age (inclusive) |
| `max_age` | int | Maximum age (inclusive) |
| `min_gender_probability` | float | 0.0 – 1.0 |
| `min_country_probability` | float | 0.0 – 1.0 |

**Sort params:**

| Param | Values | Default |
|---|---|---|
| `sort_by` | `age`, `created_at`, `gender_probability` | none |
| `order` | `asc`, `desc` | `asc` |

**Pagination params:**

| Param | Default | Max |
|---|---|---|
| `page` | `1` | — |
| `limit` | `10` | `50` |

**Example:** `/api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&page=1&limit=20`

**Success response (200):**
```json
{
  "status": "success",
  "page": 1,
  "limit": 20,
  "total": 312,
  "data": [
    {
      "id": "b3f9c1e2-...",
      "name": "chukwuemeka",
      "gender": "male",
      "age": 48,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria"
    }
  ]
}
```

---

### GET `/api/profiles/search`

Interprets a plain English query and returns matching profiles. Supports the same `page` and `limit` params as the list endpoint.

**Query param:** `q` — natural language string

**Example:** `/api/profiles/search?q=young males from nigeria`

**Success response (200):**
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 45,
  "data": [ "..." ]
}
```

**If the query can't be interpreted:**
```json
{ "status": "error", "message": "Unable to interpret query" }
```

#### Natural Language Query Examples

| Query | Interpreted As |
|---|---|
| `young males` | `gender=male` + `min_age=16` + `max_age=24` |
| `females above 30` | `gender=female` + `min_age=30` |
| `people from angola` | `country_id=AO` |
| `adult males from kenya` | `gender=male` + `age_group=adult` + `country_id=KE` |
| `male and female teenagers above 17` | `age_group=teenager` + `min_age=17` |

> Parsing is rule-based only — no AI or LLMs involved.

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
    "country_name": "Denmark",
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
|---|---|
| 400 | Missing, empty, or uninterpretable parameter |
| 404 | Profile not found |
| 422 | Invalid parameter type |
| 502 | External API returned invalid data |
| 500 | Internal server error |

---

## External APIs Used

| API | Purpose |
|---|---|
| [Genderize](https://api.genderize.io) | Predicts gender from name |
| [Agify](https://api.agify.io) | Predicts age from name |
| [Nationalize](https://api.nationalize.io) | Predicts nationality from name |

All three are free and require no API key.

---

## Age Group Classification

| Age Range | Group |
|---|---|
| 0 – 12 | child |
| 13 – 19 | teenager |
| 20 – 64 | adult |
| 65+ | senior |

> "young" in natural language queries maps to ages 16–24 for parsing only — it is not a stored age group.

---

## Database Schema

| Field | Type | Notes |
|---|---|---|
| `id` | UUID v7 | Primary key |
| `name` | VARCHAR (unique) | Lowercased |
| `gender` | VARCHAR | `male` or `female` |
| `gender_probability` | FLOAT | Confidence score |
| `sample_size` | INT | From Genderize |
| `age` | INT | Predicted age |
| `age_group` | VARCHAR | `child`, `teenager`, `adult`, `senior` |
| `country_id` | VARCHAR(2) | ISO code e.g. `NG` |
| `country_name` | VARCHAR | Full country name e.g. `Nigeria` |
| `country_probability` | FLOAT | Confidence score |
| `created_at` | TIMESTAMP | UTC, auto-generated |

---

## Deployment (Railway)

1. Push the repo to GitHub
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**
3. Add a **PostgreSQL** plugin inside the project
4. In your app's **Variables** tab, link `DATABASE_URL` from the Postgres service
5. Set the start command:
uvicorn app.main:app --host 0.0.0.0 --port $PORT
6. After deploy, open the Railway shell and run:
```bash
python -m app.seed
```
7. Railway redeploys automatically on every push to `main`

---

## Notes

- All IDs are **UUID v7**
- All timestamps are **UTC ISO 8601**
- CORS is open (`*`) to allow the grading script to reach the API
- Filters are combinable — all conditions must match (AND logic)
- Pagination is enforced on all list endpoints (`limit` max: 50)
- Submitting the same name twice returns the existing profile — no duplicates created
