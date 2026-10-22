import json
import os
import random
import time
from typing import Dict, List, Set
import requests

CATALOG_FILE = "byu_courses.json"
CACHE_FILE = "rmp_cache.json"

BYU_SCHOOL_ID = "U2Nob29sLTEzNQ=="
RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
RMP_AUTH_HEADER = "Basic dGVzdDp0ZXN0"

BATCH_SIZE = 50
THROTTLE_MIN = 0.4
THROTTLE_MAX = 0.8

GRAPHQL_HEADERS = {
    "Authorization": RMP_AUTH_HEADER,
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}

# Query 1: Initial Discovery / Search by Name
INITIAL_SEARCH_QUERY = """
query NewSearchTeachersQuery($text: String!, $schoolID: ID!) {
  newSearch {
    teachers(query: {text: $text, schoolID: $schoolID}) {
      edges {
        node {
          id
          firstName
          lastName
          avgRating
          numRatings
          avgDifficulty
          wouldTakeAgainPercent
          ratings(first: 20) {
            pageInfo {
              hasNextPage
              endCursor
            }
            edges {
              node {
                class
                comment
                difficultyRating
                helpfulRating
                clarityRating
                grade
                ratingTags
                date
              }
            }
          }
        }
      }
    }
  }
}
"""

# Query 2: Relay Pagination Cursor Query to Fetch Reviews Past 20
PAGINATE_REVIEWS_QUERY = """
query TeacherReviewsPageQuery($id: ID!, $count: Int!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      ratings(first: $count, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            class
            comment
            difficultyRating
            helpfulRating
            clarityRating
            grade
            ratingTags
            date
          }
        }
      }
    }
  }
}
"""


def load_catalog_data() -> Dict[str, list]:
    search_paths = [
        CATALOG_FILE,
        os.path.join("data", CATALOG_FILE),
        os.path.join("resources", CATALOG_FILE),
    ]
    for path in search_paths:
        if os.path.exists(path):
            print(f"[+] Loaded catalog data from '{path}'")
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    print(f"[-] Error: Could not locate '{CATALOG_FILE}'.")
    return {}


def load_existing_cache() -> Dict[str, dict]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[+] Loaded existing cache with {len(data)} faculty records.")
                return data
        except Exception as e:
            print(f"[-] Could not read existing cache file ({e}). Starting fresh.")
    return {}


def save_cache(cache_data: Dict[str, dict]) -> None:
    temp_file = f"{CACHE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, CACHE_FILE)


def normalize_name(name: str) -> str:
    if not name or name.strip().lower() in {"staff", "tba", "none"}:
        return ""
    clean = name.strip()
    if "," in clean:
        parts = clean.split(",")
        last = parts[0].strip()
        first_middle = parts[1].strip().split()
        first = first_middle[0] if first_middle else ""
        return f"{first} {last}".strip()
    return clean


def parse_review_node(r_node: dict) -> dict:
    tags_str = r_node.get("ratingTags", "") or ""
    tags = [t.strip() for t in tags_str.split("--") if t.strip()]
    return {
        "course": r_node.get("class", "General"),
        "comment": r_node.get("comment", ""),
        "difficulty": float(r_node.get("difficultyRating") or 0.0),
        "helpful": float(r_node.get("helpfulRating") or 0.0),
        "clarity": float(r_node.get("clarityRating") or 0.0),
        "grade": r_node.get("grade", "N/A"),
        "tags": tags,
        "date": r_node.get("date", ""),
    }


def extract_course_facts(reviews: List[dict]) -> dict:
    midterms = 0
    papers = 0
    extra_credit = 0
    mandatory_att = 0

    for r in reviews:
        c = r.get("comment", "").lower()
        if any(w in c for w in ["exam", "midterm", "test"]):
            midterms += 1
        if any(w in c for w in ["paper", "essay", "write"]):
            papers += 1
        if "extra credit" in c:
            extra_credit += 1
        if any(w in c for w in ["mandatory", "attendance"]):
            mandatory_att += 1

    total = max(1, len(reviews))
    return {
        "est_midterms": 2 if midterms >= 2 else (1 if midterms == 1 else 0),
        "est_papers": 2 if papers >= 2 else (1 if papers == 1 else 0),
        "has_extra_credit": extra_credit >= 1,
        "attendance_mandatory": (mandatory_att / total) >= 0.35,
        "exam_policy": "In-Person / Testing Center" if midterms > 0 else "Unspecified",
    }


def fetch_all_paginated_reviews(teacher_node_id: str, existing_reviews: List[dict], total_ratings: int, cursor: str = None) -> List[dict]:
    all_reviews = list(existing_reviews)
    seen_signatures = {f"{r.get('date')}_{r.get('comment')}" for r in all_reviews}

    has_next_page = True

    while has_next_page and len(all_reviews) < total_ratings:
        payload = {
            "query": PAGINATE_REVIEWS_QUERY,
            "variables": {
                "id": teacher_node_id,
                "count": BATCH_SIZE,
                "cursor": cursor,
            },
        }

        try:
            res = requests.post(RMP_GRAPHQL_URL, json=payload, headers=GRAPHQL_HEADERS, timeout=8)
            if res.status_code != 200:
                break

            data = res.json()
            t_node = data.get("data", {}).get("node", {})
            r_conn = t_node.get("ratings", {})
            edges = r_conn.get("edges", [])
            page_info = r_conn.get("pageInfo", {})

            if not edges:
                break

            for edge in edges:
                parsed = parse_review_node(edge.get("node", {}))
                sig = f"{parsed.get('date')}_{parsed.get('comment')}"
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    all_reviews.append(parsed)

            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            time.sleep(random.uniform(THROTTLE_MIN, THROTTLE_MAX))
        except Exception:
            break

    return all_reviews


def build_full_profile(prof_name: str) -> dict:
    clean = normalize_name(prof_name)
    payload = {
        "query": INITIAL_SEARCH_QUERY,
        "variables": {
            "text": clean,
            "schoolID": BYU_SCHOOL_ID,
        },
    }

    res = requests.post(RMP_GRAPHQL_URL, json=payload, headers=GRAPHQL_HEADERS, timeout=8)
    if res.status_code != 200:
        return {}

    data = res.json()
    teachers = data.get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges", [])
    if not teachers:
        return {}

    node = teachers[0]["node"]
    teacher_id = node.get("id")
    num_ratings = int(node.get("numRatings") or 0)
    avg_score = float(node.get("avgRating") or 0.0)
    avg_diff = float(node.get("avgDifficulty") or 0.0)

    # Initial 20 reviews
    ratings_conn = node.get("ratings", {})
    edges = ratings_conn.get("edges", [])
    page_info = ratings_conn.get("pageInfo", {})

    initial_reviews = [parse_review_node(e["node"]) for e in edges]

    # Fetch remaining reviews if total exceeds 20
    if num_ratings > len(initial_reviews) and page_info.get("hasNextPage") and teacher_id:
        cursor = page_info.get("endCursor")
        all_reviews = fetch_all_paginated_reviews(teacher_id, initial_reviews, num_ratings, cursor)
    else:
        all_reviews = initial_reviews

    return {
        "node_id": teacher_id,
        "instructor": f"{node.get('firstName', '')} {node.get('lastName', '')}".strip() or prof_name,
        "rating": f"{avg_score:.1f}" if avg_score > 0 else "N/A",
        "score_val": avg_score,
        "difficulty": f"{avg_diff:.1f}" if avg_diff > 0 else "N/A",
        "take_again": f"{node.get('wouldTakeAgainPercent', 0):.0f}%" if node.get("wouldTakeAgainPercent") != -1 else "N/A",
        "num_ratings": num_ratings,
        "reviews": all_reviews,
        "course_facts": extract_course_facts(all_reviews),
        "is_course_specific": False,
        "target_course_label": "",
    }


def run_full_review_cache():
    catalog = load_catalog_data()
    cache = load_existing_cache()

    # 1. Collect all instructors from catalog
    instructors = set()
    for _, sections in catalog.items():
        if isinstance(sections, list):
            for sec in sections:
                if isinstance(sec, dict):
                    inst = sec.get("instructor")
                    if inst and str(inst).strip() not in {"Staff", "TBA", "None", ""}:
                        instructors.add(str(inst).strip())

    total_profs = len(instructors)
    print(f"[+] Total unique instructors in catalog: {total_profs}")

    # 2. Find profiles that either do not exist or need additional reviews past 20
    candidates = []
    for prof in sorted(list(instructors)):
        data = cache.get(prof)
        if not data:
            candidates.append((prof, "new"))
        else:
            num_ratings = data.get("num_ratings", 0)
            current_loaded = len(data.get("reviews", []))
            if num_ratings > current_loaded:
                candidates.append((prof, "expand"))

    print(f"[+] Professors requiring review updates/expansion: {len(candidates)}")
    if not candidates:
        print("[✓] All professors are already fully cached with 100% of reviews!")
        return

    print("[*] Processing reviews... Press Ctrl+C at any time to pause safely.")
    processed = 0

    try:
        for prof, mode in candidates:
            start_t = time.time()

            if mode == "new":
                profile = build_full_profile(prof)
                if profile:
                    cache[prof] = profile
                    print(f"[NEW] {prof} -> {len(profile.get('reviews', []))}/{profile.get('num_ratings', 0)} reviews captured.")
            else:
                data = cache[prof]
                node_id = data.get("node_id")
                num_ratings = data.get("num_ratings", 0)
                current_reviews = data.get("reviews", [])

                if not node_id:
                    # Refresh to obtain Base64 node_id if missing
                    fresh = build_full_profile(prof)
                    if fresh:
                        cache[prof] = fresh
                        print(f"[PAGINATED] {prof} -> {len(fresh.get('reviews', []))}/{num_ratings} reviews complete.")
                else:
                    updated = fetch_all_paginated_reviews(node_id, current_reviews, num_ratings)
                    data["reviews"] = updated
                    data["course_facts"] = extract_course_facts(updated)
                    print(f"[PAGINATED] {prof} -> Expanded from {len(current_reviews)} to {len(updated)} reviews.")

            processed += 1
            if processed % 5 == 0:
                save_cache(cache)

            elapsed = time.time() - start_t
            sleep_t = random.uniform(THROTTLE_MIN, THROTTLE_MAX)
            if elapsed < sleep_t:
                time.sleep(sleep_t - elapsed)

    except KeyboardInterrupt:
        print("\n[!] Paused by user. Saving progress to cache...")
    finally:
        save_cache(cache)
        print(f"\n[✓] Finished. All reviews saved to '{CACHE_FILE}'.")


if __name__ == "__main__":
    run_full_review_cache()