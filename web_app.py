import io
import itertools
import json
import os
import re
import sys
import tempfile
import webbrowser
from typing import Any, Dict, List, Optional, Set, Tuple

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from audit_parser import parse_progress_report
from config import DEPT_DISPLAY_NAMES, PREREQ_MAP, GE_CATALOG_OPTIONS
from rmp_client import fetch_rmp_profile

from schedule_solver import is_conflict_free, parse_days, section_matches_preferences


# Initialize FastAPI App
app = FastAPI(
    title="BYU Academic Planning Suite & Schedule Solver",
    description="Web application for BYU course catalog, RateMyProfessors insights, schedule solving, and degree auditing.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSES_PATH = os.path.join(BASE_DIR, "byu_courses.json")
RMP_PATH = os.path.join(BASE_DIR, "rmp_cache.json")
WEB_DIR = os.path.join(BASE_DIR, "web")

# In-memory datasets
CATALOG: Dict[str, List[Dict[str, Any]]] = {}
DEPARTMENTS: List[str] = []
COURSE_CARD_CACHE: Dict[str, Dict[str, Any]] = {}


def load_catalog_data():
    global CATALOG, DEPARTMENTS, COURSE_CARD_CACHE
    if os.path.exists(COURSES_PATH):
        with open(COURSES_PATH, "r", encoding="utf-8") as f:
            CATALOG = json.load(f)
    else:
        CATALOG = {}

    depts_set = set()
    for course_key in CATALOG.keys():
        parts = course_key.split(" - ")[0].split()
        if len(parts) >= 2:
            dept = " ".join(parts[:-1]).upper()
            depts_set.add(dept)
    DEPARTMENTS = sorted(list(depts_set))

    # Precompute course card metadata (RMP average and ranked instructors)
    for course_key, sections in CATALOG.items():
        code = course_key.split(" - ")[0].strip()
        title = course_key.split(" - ", 1)[1].strip() if " - " in course_key else ""

        # Credit hours
        credits = 3.0
        if sections and "credit_hours" in sections[0]:
            try:
                credits = float(sections[0]["credit_hours"])
            except Exception:
                pass
        elif code.startswith("REL"):
            credits = 2.0
        elif any(c in code for c in ["112", "113"]):
            credits = 4.0

        # Instructors summary
        inst_sections: Dict[str, List[Dict[str, Any]]] = {}
        for s in sections:
            inst = s.get("instructor")
            if inst and inst.strip() and inst.lower() not in ["staff", "tba", "instructor"]:
                inst_sections.setdefault(inst.strip(), []).append(s)

        ranked_profs = []
        for inst, sec_list in inst_sections.items():
            prof_data = fetch_rmp_profile(inst, target_course=code)
            ranked_profs.append({
                "name": inst,
                "rating": prof_data.get("rating", "N/A"),
                "score_val": prof_data.get("score_val", 0.0),
                "num_ratings": prof_data.get("num_ratings", 0),
                "difficulty": prof_data.get("difficulty", "N/A"),
                "is_course_specific": prof_data.get("is_course_specific", False),
                "matched_course": prof_data.get("matched_course", ""),
                "section_count": len(sec_list),
            })

        ranked_profs.sort(key=lambda p: (p["score_val"], p["num_ratings"]), reverse=True)

        valid_scores = [p["score_val"] for p in ranked_profs if p["score_val"] > 0]
        avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

        COURSE_CARD_CACHE[course_key] = {
            "key": course_key,
            "code": code,
            "title": title,
            "credits": credits,
            "section_count": len(sections),
            "open_sections": sum(1 for s in sections if s.get("status", "").lower() == "open"),
            "professors": ranked_profs,
            "avg_rmp": avg_score,
            "sections": sections,
        }


load_catalog_data()


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "total_courses": len(CATALOG),
        "departments": DEPARTMENTS,
        "dept_display_names": DEPT_DISPLAY_NAMES,
    }


@app.post("/api/upload-audit")
async def upload_degree_audit(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT BYU Progress Reports are supported.")

    contents = await file.read()
    suffix = ".pdf" if file.filename.lower().endswith(".pdf") else ".txt"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        profile = parse_progress_report(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse report: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return profile


@app.get("/api/catalog")
def search_catalog(
    q: str = "",
    dept: str = "",
    sort: str = "code",
    offset: int = 0,
    limit: int = 50,
):
    q_norm = str(q).strip().lower()
    dept_norm = str(dept).strip().upper()


    results = []
    for course_key, card in COURSE_CARD_CACHE.items():
        # Department filter
        if dept_norm and dept_norm != "ALL":
            code_dept = " ".join(card["code"].split()[:-1]).upper()
            if code_dept != dept_norm:
                continue

        # Text query filter (matches code, title, or instructor name)
        if q_norm:
            matches_code = q_norm in card["code"].lower()
            matches_title = q_norm in card["title"].lower()
            matches_prof = any(q_norm in p["name"].lower() for p in card["professors"])
            if not (matches_code or matches_title or matches_prof):
                continue

        results.append(card)

    # Sort results
    if sort == "rating":
        results.sort(key=lambda x: (x["avg_rmp"], len(x["professors"])), reverse=True)
    elif sort == "sections":
        results.sort(key=lambda x: x["section_count"], reverse=True)
    else:
        results.sort(key=lambda x: x["code"])

    total_matches = len(results)
    paged = results[offset : offset + limit]

    # Return card summary (excluding heavy raw sections in list mode for speed)
    summaries = []
    for item in paged:
        c = dict(item)
        # Keep lightweight section previews
        summaries.append(c)

    return {
        "total": total_matches,
        "offset": offset,
        "limit": limit,
        "results": summaries,
    }


def match_catalog_card(course_str: str) -> Optional[Dict[str, Any]]:
    if not course_str:
        return None
    if course_str in COURSE_CARD_CACHE:
        return COURSE_CARD_CACHE[course_str]
    clean = " ".join(course_str.split()).upper()
    code_only = clean.split(" - ")[0]
    for k, card in COURSE_CARD_CACHE.items():
        k_up = k.upper()
        if k_up.startswith(clean) or k_up.startswith(code_only):
            return card
    return None


@app.get("/api/reviews")
def get_instructor_reviews(
    instructor: str = "",
    course_code: str = "",
):
    clean_code = course_code.split(" - ")[0].strip() if course_code else ""
    card = match_catalog_card(clean_code) if clean_code else None

    # If instructor is not specified, pick the highest-rated instructor for this course
    if (not instructor or instructor.strip().lower() in ["staff", "tba", "none"]) and card:
        if card.get("professors"):
            instructor = card["professors"][0]["name"]

    prof_data = fetch_rmp_profile(instructor, target_course=clean_code)
    if card:
        prof_data["all_course_instructors"] = card.get("professors", [])
        prof_data["course_title"] = card.get("title", "")
        prof_data["course_code"] = card.get("code", "")
    return prof_data



class ScheduleSolveRequest(BaseModel):
    staged_courses: List[str]
    min_rmp: float = 0.0
    min_start_m: int = -1
    max_end_m: int = -1
    no_fridays: bool = False


@app.post("/api/solve-schedules")
def solve_schedules(req: ScheduleSolveRequest):

    staged = req.staged_courses
    if not staged:
        return {"schedules": [], "total_credits": 0.0, "message": "No courses staged."}

    # Resolve cards
    resolved_cards = []
    for c in staged:
        card = match_catalog_card(c)
        if card:
            resolved_cards.append(card)

    if not resolved_cards:
        return {"schedules": [], "total_credits": 0.0, "message": "None of the staged courses matched the catalog."}

    # Calculate total credits
    total_sched_credits = sum(card["credits"] for card in resolved_cards)

    # Build instructor profiles cache
    profiles_map = {}
    for card in resolved_cards:
        for s in card.get("sections", []):
            inst = s.get("instructor")
            key = f"{inst}::{card['code']}"
            if inst and key not in profiles_map:
                profiles_map[key] = fetch_rmp_profile(inst, target_course=card["code"])

    pools = []
    for card in resolved_cards:
        raw_secs = card.get("sections", [])
        valid_secs = []


        for s in raw_secs:
            inst = s.get("instructor", "")
            prof_data = profiles_map.get(f"{inst}::{card['code']}", {})
            copy_s = dict(s)
            copy_s["course"] = c
            copy_s["course_code"] = card["code"]
            copy_s["course_title"] = card["title"]
            copy_s["score"] = float(prof_data.get("score_val", 0.0))
            copy_s["rmp_rating"] = prof_data.get("rating", "N/A")
            copy_s["rmp_difficulty"] = prof_data.get("difficulty", "N/A")
            copy_s["rmp_raw"] = prof_data

            if section_matches_preferences(
                copy_s, req.min_start_m, req.max_end_m, req.no_fridays, req.min_rmp
            ):
                valid_secs.append(copy_s)

        # Sort sections by RMP score descending and keep diverse slots
        valid_secs.sort(key=lambda x: x["score"], reverse=True)
        unique_slots = []
        seen_slots = set()
        for v in valid_secs:
            sig = f"{v.get('days')}_{v.get('start_time')}_{v.get('instructor')}"
            if sig not in seen_slots:
                seen_slots.add(sig)
                unique_slots.append(v)
            if len(unique_slots) >= 4:
                break

        if unique_slots:
            pools.append(unique_slots)

    if len(pools) < len(resolved_cards):
        return {
            "schedules": [],
            "total_credits": total_sched_credits,
            "message": "One or more staged courses have no sections meeting your time or rating filters.",
        }

    valid_permutations = []
    for combo in itertools.product(*pools):
        if is_conflict_free(combo):
            rated_scores = [item["score"] for item in combo if item["score"] > 0]
            avg_r = round(sum(rated_scores) / len(rated_scores), 2) if rated_scores else 0.0
            valid_permutations.append({
                "sections": combo,
                "avg_score": avg_r,
                "total_credits": total_sched_credits,
            })

    valid_permutations.sort(key=lambda x: x["avg_score"], reverse=True)
    return {
        "schedules": valid_permutations[:10],
        "total_credits": total_sched_credits,
        "message": f"Found {len(valid_permutations)} conflict-free schedule(s).",
    }


@app.get("/api/ge-options")
def get_ge_options():
    ge_data = {}
    for req_title, options in GE_CATALOG_OPTIONS.items():
        evaluated_options = []
        for code, title, credits in options:
            # Look up RMP score for this course
            matching_key = None
            for k in COURSE_CARD_CACHE.keys():
                if k.startswith(code):
                    matching_key = k
                    break

            avg_score = 0.0
            professors = []
            if matching_key:
                card = COURSE_CARD_CACHE[matching_key]
                avg_score = card["avg_rmp"]
                professors = card["professors"][:3]

            evaluated_options.append({
                "code": code,
                "title": title,
                "credits": credits,
                "avg_rmp": avg_score,
                "professors": professors,
                "catalog_key": matching_key or f"{code} - {title}",
            })

        # Sort options by avg_rmp descending
        evaluated_options.sort(key=lambda x: x["avg_rmp"], reverse=True)
        ge_data[req_title] = evaluated_options

    return ge_data


class RoadmapRequest(BaseModel):
    profile: Dict[str, Any]
    starting_term: str = "Winter 2027"
    target_credits_per_term: float = 15.0
    include_summer: bool = False


@app.post("/api/roadmap")
def compute_roadmap(req: RoadmapRequest):
    profile = req.profile
    rel_pool = list(profile.get("missing_religion", []))
    ge_pool = list(profile.get("missing_ge", []))
    major_pool = list(profile.get("missing_major", []))

    simulated_history: Set[str] = set()
    for c in profile.get("completed_courses", []):
        simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())
    for c in profile.get("in_progress_courses", []):
        simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())
    for c in profile.get("planned_courses", []):
        simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())

    def prereqs_met(code_str: str) -> bool:
        comp = code_str.replace(" ", "").upper()
        prereqs = PREREQ_MAP.get(code_str, [])
        if not prereqs:
            for k, v in PREREQ_MAP.items():
                if k.replace(" ", "").upper() == comp:
                    prereqs = v
                    break
        if not prereqs:
            return True
        if comp in {"WRTG316", "WRTG315", "ENGL316"}:
            return True
        return all(p.replace(" ", "").upper() in simulated_history for p in prereqs)

    earned = float(profile.get("credits", 0.0))
    in_progress = float(profile.get("in_progress_credits", 0.0))
    simulated_cumulative = earned + in_progress

    # Term names generator
    term_seq = []
    parts = req.starting_term.split()
    season = parts[0] if parts else "Winter"
    year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2027

    for _ in range(12):
        term_seq.append(f"{season} {year}")
        if season == "Winter":
            season = "Spring/Summer" if req.include_summer else "Fall"
        elif season == "Spring/Summer":
            season = "Fall"
        elif season == "Fall":
            season = "Winter"
            year += 1

    semesters = []
    term_idx = 0

    while (rel_pool or ge_pool or major_pool or simulated_cumulative < 120.0) and term_idx < len(term_seq):
        term_name = term_seq[term_idx]
        term_idx += 1
        term_courses = []
        term_credits = 0.0
        max_term_credits = req.target_credits_per_term

        # 1 Religion course per semester
        if rel_pool and term_credits < max_term_credits:
            chosen = rel_pool.pop(0)
            term_courses.append({"code": chosen[0], "credits": chosen[1], "title": chosen[2], "type": "Religion"})
            term_credits += chosen[1]
            simulated_history.add(chosen[0].replace(" ", "").upper())

        # Major courses that meet prerequisites
        deferred_major = []
        while major_pool and term_credits + 3.0 <= max_term_credits + 1.0:
            cand = major_pool.pop(0)
            if prereqs_met(cand[0]):
                term_courses.append({"code": cand[0], "credits": cand[1], "title": cand[2], "type": "Major"})
                term_credits += cand[1]
                simulated_history.add(cand[0].replace(" ", "").upper())
            else:
                deferred_major.append(cand)
        major_pool = deferred_major + major_pool

        # GE courses
        while ge_pool and term_credits + 3.0 <= max_term_credits + 0.5:
            cand = ge_pool.pop(0)
            term_courses.append({"code": cand[0], "credits": cand[1], "title": cand[2], "type": "GE"})
            term_credits += cand[1]
            simulated_history.add(cand[0].replace(" ", "").upper())

        # General Electives if under target
        while term_credits + 3.0 <= max_term_credits and simulated_cumulative + term_credits < 120.0:
            term_courses.append({"code": "ELECTIVE", "credits": 3.0, "title": "General College Elective", "type": "Elective"})
            term_credits += 3.0

        simulated_cumulative += term_credits
        semesters.append({
            "term": term_name,
            "term_credits": term_credits,
            "cumulative_credits": min(round(simulated_cumulative, 1), 120.0),
            "courses": term_courses,
        })

    return {
        "semesters": semesters,
        "graduation_term": semesters[-1]["term"] if semesters else req.starting_term,
        "final_credits": min(round(simulated_cumulative, 1), 120.0),
    }


# Serve the Web App Frontend
os.makedirs(WEB_DIR, exist_ok=True)


@app.get("/")
def get_index():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>BYU Academic Planning Suite Web Server</h1><p>Building frontend...</p>")


def run_server(port: int = 8000, open_browser: bool = True):
    url = f"http://localhost:{port}"
    print(f"\n========================================================")
    print(f"🚀 BYU Academic Planning Suite & Schedule Solver Web App")
    print(f"👉 Local Web URL: {url}")
    print(f"========================================================\n")
    if open_browser:
        webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")


if __name__ == "__main__":
    run_server()
