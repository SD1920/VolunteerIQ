import json
import os
import re
from math import asin, cos, radians, sin, sqrt

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from .database import SessionLocal, engine
from . import models


app = FastAPI()

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

models.Base.metadata.create_all(bind=engine)


CATEGORY_SKILL_MAP = {
    "medical": {"doctor"},
    "food": {"food distribution"},
    "rescue": {"driver", "logistics"},
    "shelter": {"logistics"},
}


CITY_COORDS = {
    "patna": (25.5941, 85.1376),
    "bihar rural": (25.5000, 85.0000),
    "guwahati": (26.1445, 91.7362),
    "chennai": (13.0827, 80.2707),
    "assam": (26.2006, 92.9376),
}


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def extract_json_from_text(text: str):
    if not isinstance(text, str):
        return None

    cleaned = text.strip()
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    c = 2 * asin(sqrt(a))
    return r * c


def build_cluster_sizes(needs):
    cluster_sizes = {}
    for need in needs:
        key = ((need.category or "").lower(), (need.location or "").lower())
        cluster_sizes[key] = cluster_sizes.get(key, 0) + 1
    return cluster_sizes


def detect_category_from_keywords(text: str) -> str:
    lowered = str(text or "").lower()

    category_keywords = {
        "medical": ["medical", "doctor", "hospital", "medicine", "injured"],
        "food": ["food", "hunger", "hungry", "ration", "water", "meal"],
        "shelter": ["shelter", "camp", "tent", "housing", "homeless"],
        "rescue": ["rescue", "trapped", "evacuate", "evacuation", "boat"],
    }

    for category, keywords in category_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            return category

    return "food"


@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/debug/status")
def debug_status():
    db = SessionLocal()
    try:
        total_needs = db.query(models.Need).count()
        total_volunteers = db.query(models.Volunteer).count()
        total_matches = db.query(models.Match).count()
        assigned_needs_count = (
            db.query(models.Need).filter(models.Need.status == "assigned").count()
        )

        return {
            "total_needs": total_needs,
            "total_volunteers": total_volunteers,
            "total_matches": total_matches,
            "assigned_needs_count": assigned_needs_count,
        }
    finally:
        db.close()


@app.get("/needs")
def get_needs():
    db = SessionLocal()
    try:
        needs = db.query(models.Need).all()
        cluster_sizes = build_cluster_sizes(needs)

        response_needs = [
            {
                "id": n.id,
                "source_text": n.source_text,
                "category": n.category,
                "location": n.location,
                "urgency_score": n.urgency_score,
                "cluster_size": cluster_sizes.get(
                    ((n.category or "").lower(), (n.location or "").lower()), 1
                ),
                "status": n.status,
                "created_at": n.created_at,
            }
            for n in needs
        ]

        response_needs.sort(
            key=lambda n: (
                n["urgency_score"] if n["urgency_score"] is not None else -1,
                n["cluster_size"],
            ),
            reverse=True,
        )

        return response_needs
    finally:
        db.close()


@app.get("/volunteers")
def get_volunteers():
    db = SessionLocal()
    try:
        volunteers = db.query(models.Volunteer).all()
        return [
            {
                "id": v.id,
                "name": v.name,
                "skills": v.skills,
                "location": v.location,
                "availability": v.availability,
                "contact": v.contact,
                "created_at": v.created_at,
            }
            for v in volunteers
        ]
    finally:
        db.close()


@app.post("/upload-report")
def upload_report(payload: dict):
    raw_text = (payload or {}).get("raw_text")
    uploaded_by = (payload or {}).get("uploaded_by")

    if not isinstance(raw_text, str) or not raw_text.strip():
        raw_text = "Demo report"
    else:
        raw_text = raw_text.strip()

    api_key = os.getenv("GROQ_API_KEY")

    prompt = (
        "Extract structured information from this field report:\n\n"
        f"{raw_text}\n\n"
        "Return ONLY valid JSON with:\n"
        "- category (food/medical/shelter/rescue)\n"
        "- location (city or area name)\n"
        "- urgency_score (integer 1-10)\n"
        "- description (short summary)"
    )

    request_body = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
    }

    category = "food"
    location = "Chennai"
    urgency_score = 7
    description = (raw_text[:100] or "Demo report received").strip() or "Demo report received"

    lowered_text = raw_text.lower()
    high_priority_words = ["urgent", "dying", "critical", "immediate"]
    medium_priority_words = ["need", "help", "required"]
    keyword_weight = 0
    for word in high_priority_words:
        if word in lowered_text:
            keyword_weight += 2
    for word in medium_priority_words:
        if word in lowered_text:
            keyword_weight += 1

    extracted = None
    ai_success = False
    if api_key:
        try:
            import requests
        except ImportError:
            requests = None

        if requests is not None:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            groq_response = None

            for _ in range(2):
                try:
                    print("GROQ KEY LOADED:", api_key[:5])
                    candidate_response = requests.post(
                        GROQ_ENDPOINT,
                        headers=headers,
                        json=request_body,
                        timeout=20,
                    )
                    if candidate_response is not None and candidate_response.status_code == 200:
                        groq_response = candidate_response
                        break
                except requests.RequestException:
                    continue

            if groq_response is not None and groq_response.status_code == 200:
                try:
                    groq_json = groq_response.json()
                    ai_text = groq_json["choices"][0]["message"]["content"]
                    print("RAW AI RESPONSE:", ai_text)
                    extracted = extract_json_from_text(ai_text)
                except (ValueError, KeyError, IndexError, TypeError):
                    extracted = None

    if extracted:
        parsed_category = str(extracted.get("category", "")).strip().lower()
        parsed_location = str(extracted.get("location", "")).strip()
        parsed_description = str(extracted.get("description", "")).strip()

        raw_urgency = extracted.get("urgency_score")
        try:
            parsed_urgency = int(raw_urgency)
        except (TypeError, ValueError):
            parsed_urgency = None

        if (
            parsed_category in {"food", "medical", "shelter", "rescue"}
            and parsed_location
            and parsed_description
            and parsed_urgency is not None
            and (1 <= parsed_urgency <= 10)
        ):
            category = parsed_category
            location = parsed_location
            description = parsed_description
            urgency_score = parsed_urgency
            ai_success = True

    if not ai_success:
        category = detect_category_from_keywords(raw_text)
        location = "Chennai"
        urgency_score = 7
        description = (raw_text[:100] or "Demo report received").strip() or "Demo report received"
    else:
        recency_boost = 1
        final_score = urgency_score + keyword_weight + recency_boost
        final_score = max(1, min(10, final_score))
        urgency_score = final_score

    db = SessionLocal()
    try:
        report = models.Report(
            raw_text=raw_text,
            uploaded_by=uploaded_by,
            processed=True,
        )
        need = models.Need(
            source_text=description,
            category=category,
            location=location,
            urgency_score=urgency_score,
            status="open",
        )
        db.add(report)
        db.add(need)
        db.commit()
    except Exception:
        db.rollback()
        # Demo safety: never return an error response from this endpoint.
        pass
    finally:
        db.close()

    return {
        "category": category,
        "location": location,
        "urgency_score": urgency_score,
        "description": description,
    }


@app.post("/match/{need_id}")
def match_volunteers(need_id: int):
    db = SessionLocal()
    try:
        need = db.query(models.Need).filter(models.Need.id == need_id).first()
        if not need:
            raise HTTPException(status_code=404, detail="Need not found")

        target_skills = CATEGORY_SKILL_MAP.get((need.category or "").lower(), set())
        need_coords = CITY_COORDS.get((need.location or "").lower())
        volunteers = db.query(models.Volunteer).all()

        scored = []
        for volunteer in volunteers:
            score = 0

            volunteer_skills = {str(skill).lower() for skill in (volunteer.skills or [])}
            if target_skills and volunteer_skills.intersection(target_skills):
                score += 5

            availability = (volunteer.availability or "").lower()
            if "full-time" in availability:
                score += 3

            volunteer_coords = CITY_COORDS.get((volunteer.location or "").lower())
            distance_km = -1
            distance_label = "unknown"
            if need_coords and volunteer_coords:
                distance_km = haversine_km(
                    need_coords[0],
                    need_coords[1],
                    volunteer_coords[0],
                    volunteer_coords[1],
                )
                if distance_km == 0:
                    distance_label = "same city"
                elif distance_km < 50:
                    distance_label = "nearby"
                else:
                    distance_label = "far"

                if distance_km < 50:
                    score += 2
                elif distance_km < 200:
                    score += 1

            if distance_km == 0:
                distance_km_out = 0.0
            elif distance_km == -1:
                distance_km_out = -1
            else:
                distance_km_out = round(distance_km, 2)

            scored.append(
                {
                    "id": volunteer.id,
                    "name": volunteer.name,
                    "skills": volunteer.skills,
                    "location": volunteer.location,
                    "availability": volunteer.availability,
                    "contact": volunteer.contact,
                    "created_at": volunteer.created_at,
                    "distance_km": distance_km_out,
                    "distance_label": distance_label,
                    "match_score": score,
                }
            )

        top_3 = sorted(scored, key=lambda x: x["match_score"], reverse=True)[:3]
        return {"need_id": need.id, "category": need.category, "matches": top_3}
    finally:
        db.close()


@app.post("/assign")
def assign_volunteer(payload: dict):
    need_id = (payload or {}).get("need_id")
    volunteer_id = (payload or {}).get("volunteer_id")

    db = SessionLocal()
    try:
        need = db.query(models.Need).filter(models.Need.id == need_id).first()
        if not need:
            raise HTTPException(status_code=404, detail="Need not found")
        if need.status == "assigned":
            return JSONResponse(status_code=400, content={"error": "Need already assigned"})

        volunteer = (
            db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()
        )
        if not volunteer:
            raise HTTPException(status_code=404, detail="Volunteer not found")

        existing_need_assignment = (
            db.query(models.Match).filter(models.Match.need_id == need_id).first()
        )
        if existing_need_assignment:
            return JSONResponse(status_code=400, content={"error": "Need already assigned"})

        existing_match = (
            db.query(models.Match)
            .filter(
                models.Match.need_id == need_id,
                models.Match.volunteer_id == volunteer_id,
            )
            .first()
        )
        if existing_match:
            return JSONResponse(status_code=400, content={"error": "Already assigned"})

        match = models.Match(
            need_id=need_id,
            volunteer_id=volunteer_id,
            status="assigned",
            match_score=0.0,
        )
        need.status = "assigned"

        db.add(match)
        db.commit()

        return {
            "need_id": need.id,
            "volunteer_id": volunteer.id,
            "volunteer_name": volunteer.name,
            "status": "assigned",
        }
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        return JSONResponse(status_code=500, content={"error": "Failed to assign volunteer"})
    finally:
        db.close()


@app.get("/insights")
def get_insights():
    db = SessionLocal()
    try:
        open_needs = db.query(models.Need).filter(models.Need.status == "open").all()

        if len(open_needs) < 2:
            return {"clusters": [], "top_urgent": []}

        texts = [str(need.source_text or "") for need in open_needs]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        n_clusters = min(4, len(open_needs))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(tfidf_matrix)

        clusters_map = {}
        for need, label in zip(open_needs, labels):
            cluster_id = int(label)
            if cluster_id not in clusters_map:
                clusters_map[cluster_id] = []
            clusters_map[cluster_id].append(
                {
                    "id": need.id,
                    "category": need.category,
                    "location": need.location,
                    "urgency_score": need.urgency_score,
                    "source_text": need.source_text,
                }
            )

        clusters = [
            {"cluster_id": cluster_id, "needs": needs}
            for cluster_id, needs in sorted(clusters_map.items(), key=lambda x: x[0])
        ]

        top_urgent = [
            {
                "id": need.id,
                "category": need.category,
                "location": need.location,
                "urgency_score": need.urgency_score,
                "source_text": need.source_text,
            }
            for need in sorted(
                open_needs,
                key=lambda n: n.urgency_score if n.urgency_score is not None else -1,
                reverse=True,
            )[:5]
        ]

        return {"clusters": clusters, "top_urgent": top_urgent}
    finally:
        db.close()
