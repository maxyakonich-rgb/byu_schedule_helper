import json
import os
import re
from typing import Dict, List, Optional, Tuple

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(_BASE_DIR, "rmp_cache.json")

_LOCAL_CACHE: Optional[Dict[str, dict]] = None
_NORM_CACHE_MAP: Dict[str, dict] = {}
_COURSE_PROFILE_CACHE: Dict[Tuple[str, str], dict] = {}


def _normalize_name(name: str) -> str:
    """Normalizes university roster formatting like 'Smith, John D.' to 'John Smith'."""
    if not name or name.strip().lower() in {"staff", "tba", "none", "curriculum"}:
        return ""
    clean = name.strip()
    if "," in clean:
        parts = clean.split(",")
        last = parts[0].strip()
        first_middle = parts[1].strip().split()
        first = first_middle[0] if first_middle else ""
        return f"{first} {last}".strip()
    return clean


def _first_last_key(name: str) -> str:
    """Extracts a lowercase 'first last' key stripping middle initials/punctuation."""
    norm = _normalize_name(name)
    tokens = [re.sub(r"[^a-z]", "", t.lower()) for t in norm.split()]
    tokens = [t for t in tokens if t]
    if len(tokens) >= 2:
        return f"{tokens[0]} {tokens[-1]}"
    return tokens[0] if tokens else ""


def _load_cache() -> Dict[str, dict]:
    """Loads and indexes rmp_cache.json in memory once for O(1) instantaneous offline access."""
    global _LOCAL_CACHE, _NORM_CACHE_MAP
    if _LOCAL_CACHE is None:
        _LOCAL_CACHE = {}
        _NORM_CACHE_MAP = {}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    _LOCAL_CACHE = raw
                    for k, v in raw.items():
                        if not isinstance(v, dict) or not v:
                            continue
                        _NORM_CACHE_MAP[k.strip().lower()] = v
                        norm_k = _normalize_name(k).lower()
                        if norm_k:
                            _NORM_CACHE_MAP.setdefault(norm_k, v)
                        fl_k = _first_last_key(k)
                        if fl_k:
                            _NORM_CACHE_MAP.setdefault(fl_k, v)
            except Exception:
                _LOCAL_CACHE = {}
                _NORM_CACHE_MAP = {}
    return _LOCAL_CACHE


def _extract_course_facts(reviews: List[dict]) -> dict:
    """Consensus analyzer checking for exams, papers, attendance, and extra credit."""
    midterm_mentions = 0
    paper_mentions = 0
    extra_credit_count = 0
    mandatory_att_count = 0

    for r in reviews:
        comment = r.get("comment", "").lower()
        if "exam" in comment or "midterm" in comment or "test" in comment:
            midterm_mentions += 1
        if "paper" in comment or "essay" in comment or "write" in comment:
            paper_mentions += 1
        if "extra credit" in comment:
            extra_credit_count += 1
        if "mandatory" in comment or "attendance" in comment:
            mandatory_att_count += 1

    total = max(1, len(reviews))
    return {
        "est_midterms": 2 if midterm_mentions >= 2 else (1 if midterm_mentions == 1 else 0),
        "est_papers": 2 if paper_mentions >= 2 else (1 if paper_mentions == 1 else 0),
        "has_extra_credit": extra_credit_count >= 1,
        "attendance_mandatory": (mandatory_att_count / total) >= 0.35,
        "exam_policy": "In-Person / Testing Center" if midterm_mentions > 0 else "Unspecified",
    }


# Official BYU Department Code Aliases used by students on RateMyProfessors
_DEPT_ALIASES = {
    "RELA": {"RELA", "REL"},
    "RELC": {"RELC", "REL"},
    "RELE": {"RELE", "REL"},
    "WRTG": {"WRTG", "ENGL", "ENG", "WRIT", "WRITING", "WTRG"},
    "ENGL": {"ENGL", "ENG"},
    "IHUM": {"IHUM", "HUM"},
    "PHSCS": {"PHSCS", "PHYS", "PHSC"},
    "PHYS": {"PHYS", "PS", "PHSCS"},
    "POLI": {"POLI", "POL", "PLSC", "POLS", "POLISCI"},
    "PSYCH": {"PSYCH", "PSYC", "PSY", "PYCH", "PYSCH", "PSCYH"},
    "CELL": {"CELL", "PDBIO"},
    "COMM": {"COMM", "COMMS", "MCOM"},
    "COMMS": {"COMMS", "COMM", "MCOM"},
    "MUSIC": {"MUSIC", "MUS"},
    "GEOL": {"GEOL", "GEO", "GELO"},
    "GEOG": {"GEOG", "GEO"},
    "MEEN": {"MEEN", "ME"},
    "ECEN": {"ECEN", "EE", "ECE"},
    "CEEN": {"CEEN", "CE", "CCE"},
    "CHEN": {"CHEN", "CHE"},
    "ANTHR": {"ANTHR", "ANTH"},
    "ARTHC": {"ARTHC", "ARTH"},
    "CLCV": {"CLCV", "CL"},
    "AHTG": {"AHTG", "AH", "AMER", "AMHTG", "AMHER", "AMH", "AMHT", "AHGT", "AMHERTG"},
}


def _matches_target_course(rev_course: str, target_code: str) -> bool:
    """
    Strictly checks whether a RateMyProfessors review course tag belongs to target_code.
    Handles whitespace/hyphen variations and BYU department renames without allowing
    other course numbers from the same professor to leak through.
    """
    rc = re.sub(r"[^A-Z0-9&]", "", (rev_course or "").upper())
    tc = re.sub(r"[^A-Z0-9&]", "", (target_code or "").upper())
    if not rc or not tc:
        return False
    if rc == tc:
        return True

    m_t = re.match(r"^([A-Z&]+)(\d{3}[A-Z]?)$", tc)
    if not m_t:
        return tc in rc
    t_dept, t_num = m_t.group(1), m_t.group(2)
    t_num_base = t_num.rstrip("R")

    # Case 1: Student entered only the 3-digit course number (e.g. '316' or '290') under this professor
    if rc == t_num or rc == t_num_base:
        return True

    # Case 2: Standard '<DEPT><NUM>' review tag
    m_r = re.match(r"^([A-Z&]+)(\d{3}[A-Z]?)$", rc)
    if m_r:
        r_dept, r_num = m_r.group(1), m_r.group(2)
        if r_num.rstrip("R") != t_num_base:
            return False
        allowed = _DEPT_ALIASES.get(t_dept, {t_dept})
        if r_dept in allowed or t_dept.startswith(r_dept) or r_dept.startswith(t_dept):
            return True
        return False

    # Case 3: Combined multi-section tag where the exact dept+number token appears
    allowed = _DEPT_ALIASES.get(t_dept, {t_dept})
    for alias in allowed:
        if re.search(rf"(?:^|[^A-Z]){re.escape(alias)}{re.escape(t_num_base)}(?:[^0-9]|$)", rc):
            return True
    return False


def fetch_rmp_profile(instructor: str, target_course: str = "") -> dict:
    """
    Primary entry point. Reads 100% from local rmp_cache.json in memory (never hits the network).
    When target_course is provided, strictly filters reviews and recomputes rating,
    score_val, difficulty, num_ratings, and course_facts ONLY from that specific course's
    reviews (never falling back to other courses the professor teaches).
    """
    clean_name = _normalize_name(instructor)
    target_code = target_course.split(" - ")[0].strip().upper() if target_course else ""

    cache_key = (instructor.strip() if instructor else "", target_code)
    if cache_key in _COURSE_PROFILE_CACHE:
        return _COURSE_PROFILE_CACHE[cache_key]

    empty_profile = {
        "instructor": instructor or "Staff",
        "rating": "N/A",
        "score_val": 0.0,
        "difficulty": "N/A",
        "take_again": "N/A",
        "num_ratings": 0,
        "reviews": [],
        "course_facts": _extract_course_facts([]),
        "is_course_specific": bool(target_code),
        "target_course_label": target_code,
    }

    if not clean_name:
        _COURSE_PROFILE_CACHE[cache_key] = empty_profile
        return empty_profile

    cache = _load_cache()

    # 1. Exact, normalized, or first+last local cache hit (never queries the web)
    profile_data = (
        cache.get(instructor)
        or cache.get(clean_name)
        or _NORM_CACHE_MAP.get(instructor.strip().lower())
        or _NORM_CACHE_MAP.get(clean_name.lower())
        or _NORM_CACHE_MAP.get(_first_last_key(instructor))
    )

    if not profile_data:
        _COURSE_PROFILE_CACHE[cache_key] = empty_profile
        return empty_profile

    result = dict(profile_data)
    all_reviews = result.get("reviews", [])

    # 2. Strict Course-Specific Filtering & Score Recalculation
    if target_code:
        specific = [
            r for r in all_reviews
            if _matches_target_course(r.get("course", ""), target_code)
        ]
        result["is_course_specific"] = True
        result["target_course_label"] = target_code

        if specific:
            q_scores = []
            d_scores = []
            for r in specific:
                h_val = float(r.get("helpful") or 0.0)
                c_val = float(r.get("clarity") or 0.0)
                if h_val > 0 and c_val > 0:
                    q_scores.append((h_val + c_val) / 2.0)
                elif h_val > 0 or c_val > 0:
                    q_scores.append(max(h_val, c_val))

                diff_val = float(r.get("difficulty") or 0.0)
                if diff_val > 0:
                    d_scores.append(diff_val)

            course_score = round(sum(q_scores) / len(q_scores), 2) if q_scores else 0.0
            course_diff = round(sum(d_scores) / len(d_scores), 1) if d_scores else 0.0

            result["reviews"] = specific
            result["score_val"] = course_score
            result["rating"] = f"{course_score:.1f}" if course_score > 0 else "N/A"
            result["difficulty"] = f"{course_diff:.1f}" if course_diff > 0 else "N/A"
            result["num_ratings"] = len(specific)
            result["course_facts"] = _extract_course_facts(specific)
        else:
            # Professor has no reviews for this specific course — do not use other courses' data
            result["reviews"] = []
            result["score_val"] = 0.0
            result["rating"] = "N/A"
            result["difficulty"] = "N/A"
            result["take_again"] = "N/A"
            result["num_ratings"] = 0
            result["course_facts"] = _extract_course_facts([])
    else:
        result["is_course_specific"] = False
        result["target_course_label"] = ""

    _COURSE_PROFILE_CACHE[cache_key] = result
    return result