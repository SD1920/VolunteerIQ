# VolunteerIQ Backend/ML

> Smart resource allocation system for NGO volunteer coordination.

---

## Tech Stack

- **FastAPI** (Python)
- **SQLAlchemy** (ORM)
- **SQLite** (local database)
- **Gemini API** (AI-based extraction)

---

## Setup

```bash
git clone https://github.com/SD1920/VolunteerIQ.git
cd VolunteerIQ/backend
pip install -r requirements.txt
```

Create `.env` file:

```
DATABASE_URL=sqlite:///./test.db
GEMINI_API_KEY=your_api_key_here
```

Run:

```bash
python -m backend.seed
uvicorn backend.main:app --reload
```

Base URL: `http://127.0.0.1:8000`

---

## API Routes

### Needs

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/needs` | Get all needs (sorted by urgency) |

### Volunteers

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/volunteers` | Get all volunteers |

### AI Report Processing

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/upload-report` | Convert raw text → structured need |

**Input:**
```json
{
  "raw_text": "people need food in chennai urgently",
  "uploaded_by": "field_worker"
}
```

**Output:**
```json
{
  "category": "food",
  "location": "Chennai",
  "urgency_score": 9,
  "description": "People need urgent food support in Chennai"
}
```

### Matching

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/match/{need_id}` | Get best volunteers for a need |

**Output:**
```json
{
  "need_id": 5,
  "category": "food",
  "matches": [
    {
      "id": 7,
      "name": "Lalita Devi",
      "match_score": 8,
      "distance_km": 0.0,
      "distance_label": "same city"
    }
  ]
}
```

### Assignment

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/assign` | Assign volunteer to need |

**Input:**
```json
{
  "need_id": 5,
  "volunteer_id": 7
}
```

**Output:**
```json
{
  "need_id": 5,
  "volunteer_id": 7,
  "volunteer_name": "Lalita Devi",
  "status": "assigned"
}
```

---

## Matching Algorithm

Score = Skill + Availability + Distance

| Condition | Points |
|-----------|--------|
| Skill match | +5 |
| Full-time availability | +3 |
| Distance < 50 km | +2 |
| Distance < 200 km | +1 |

Distance calculated using the **Haversine formula**.

---

## Data Models

- `volunteers`
- `needs`
- `matches`
- `reports`

---

## Flow

```
Upload Report → AI Extraction → Stored as Need
       ↓
Match Volunteers → Assign → Status Updated
```
