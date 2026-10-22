import json
import os
import random
import time
from typing import Dict, List
import requests

CACHE_FILE = "rmp_cache.json"
BYU_SCHOOL_ID = "U2Nob29sLTEzNQ=="
RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
RMP_AUTH_HEADER = "Basic dGVzdDp0ZXN0"

BATCH_SIZE = 50
THROTTLE_MIN = 0.4
THROTTLE_MAX = 0.8

PAGINATED_QUERY = """
query TeacherReviewsPageQuery($id: ID!, $count: Int!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      ratings(first: $count, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          cursor
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


def load_cache() -> Dict[str, dict]:
    if not os.path.exists(CACHE_FILE):
        print(f"[-] '{CACHE_FILE}' not found. Run build_rmp_cache.py first.")
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache_data: Dict[str, dict]) -> None:
    temp_file = f"{CACHE_FILE}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, CACHE_FILE)


def fetch_all_reviews_for_node(teacher_node_id: str, existing_reviews: List[dict], total_ratings: int) -> List[dict]:
    headers = {
        "Authorization": RMP_AUTH_HEADER,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    all_reviews = list(existing_reviews)
    has_next_page = True
    cursor = None

    while has_next_page and len(all_reviews) < total_ratings:
        payload = {
            "query": PAGINATED_QUERY,
            "variables": {
                "id": teacher_node_id,
                "count": BATCH_SIZE,
                "cursor": cursor,
            },
        }

        res = requests.post(RMP_GRAPHQL_URL, json=payload, headers=headers, timeout=8)
        if res.status_code != 200:
            break

        data = res.json()
        teacher_node = data.get("data", {}).get("node", {})
        ratings_conn = teacher_node.get("ratings", {})
        edges = ratings_conn.get("edges", [])
        page_info = ratings_conn.get("pageInfo", {})

        if not edges:
            break

        for edge in edges:
            r_node = edge.get("node", {})
            tags_str = r_node.get("ratingTags", "") or ""
            tags = [t.strip() for t in tags_str.split("--") if t.strip()]

            review_entry = {
                "course": r_node.get("class", "General"),
                "comment": r_node.get("comment", ""),
                "difficulty": float(r_node.get("difficultyRating") or 0.0),
                "helpful": float(r_node.get("helpfulRating") or 0.0),
                "clarity": float(r_node.get("clarityRating") or 0.0),
                "grade": r_node.get("grade", "N/A"),
                "tags": tags,
                "date": r_node.get("date", ""),
            }

            # Avoid storing duplicate reviews if first batch overlaps
            if not any(
                r.get("date") == review_entry["date"] and r.get("comment") == review_entry["comment"]
                for r in all_reviews
            ):
                all_reviews.append(review_entry)

        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

        time.sleep(random.uniform(THROTTLE_MIN, THROTTLE_MAX))

    return all_reviews


def get_teacher_node_id(teacher_name: str) -> str:
    """Helper to locate the teacher's Base64 node ID if not already cached."""
    search_query = """
    query GetTeacherId($text: String!, $schoolID: ID!) {
      newSearch {
        teachers(query: {text: $text, schoolID: $schoolID}) {
          edges {
            node {
              id
            }
          }
        }
      }
    }
    """
    headers = {
        "Authorization": RMP_AUTH_HEADER,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }
    payload = {
        "query": search_query,
        "variables": {"text": teacher_name, "schoolID": BYU_SCHOOL_ID},
    }
    try:
        res = requests.post(RMP_GRAPHQL_URL, json=payload, headers=headers, timeout=6)
        if res.status_code == 200:
            edges = res.json().get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges", [])
            if edges:
                return edges[0]["node"]["id"]
    except Exception:
        pass
    return ""


def run_review_backfill():
    cache = load_cache()
    if not cache:
        return

    # Identify instructors where total reviews exceed current cached count
    professors_to_expand = []
    for prof_key, data in cache.items():
        num_ratings = data.get("num_ratings", 0)
        current_loaded = len(data.get("reviews", []))
        if num_ratings > current_loaded:
            professors_to_expand.append(prof_key)

    total_pending = len(professors_to_expand)
    print(f"[+] Found {total_pending} professors with additional comments to fetch.")

    if total_pending == 0:
        print("[✓] All available comments are already fully captured in rmp_cache.json!")
        return

    print("[*] Beginning backfill... Press Ctrl+C at any time to pause and save.")
    completed = 0

    try:
        for prof in professors_to_expand:
            data = cache[prof]
            total_ratings = data.get("num_ratings", 0)
            existing_reviews = data.get("reviews", [])

            # Check if teacher node ID is stored, otherwise query it
            node_id = data.get("node_id") or get_teacher_node_id(prof)
            if not node_id:
                continue

            data["node_id"] = node_id
            updated_reviews = fetch_all_reviews_for_node(node_id, existing_reviews, total_ratings)
            data["reviews"] = updated_reviews

            print(f"[{completed + 1}/{total_pending}] {prof}: {len(existing_reviews)} -> {len(updated_reviews)} reviews loaded")
            completed += 1

            if completed % 10 == 0:
                save_cache(cache)

    except KeyboardInterrupt:
        print("\n[!] Paused by user. Saving progress...")
    finally:
        save_cache(cache)
        print(f"\n[✓] Backfill complete. Updated cache saved to '{CACHE_FILE}'.")


if __name__ == "__main__":
    run_review_backfill()