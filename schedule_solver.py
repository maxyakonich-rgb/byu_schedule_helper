import itertools
from typing import List


def parse_days(day_str: str) -> List[str]:
    if not day_str or day_str.upper() == "TBA":
        return []
    days = []
    i = 0
    s = day_str.strip()
    while i < len(s):
        if s[i:i+2] == "Th":
            days.append("Th")
            i += 2
        elif s[i:i+2] == "Sa":
            days.append("Sa")
            i += 2
        elif s[i] in ["M", "T", "W", "F", "S"]:
            days.append(s[i])
            i += 1
        else:
            i += 1
    return days


def slots_overlap(days_a_str: str, s_min_a: int, e_min_a: int,
                  days_b_str: str, s_min_b: int, e_min_b: int) -> bool:
    days_a = set(parse_days(days_a_str))
    days_b = set(parse_days(days_b_str))
    if not days_a.intersection(days_b):
        return False
    if s_min_a == -1 or e_min_a == -1 or s_min_b == -1 or e_min_b == -1:
        return False
    return (s_min_a < e_min_b) and (s_min_b < e_min_a)


def sections_overlap(sec_a: dict, sec_b: dict) -> bool:
    slots_a = []
    if sec_a.get("lecture") and sec_a["lecture"].get("days") != "TBA":
        slots_a.append(sec_a["lecture"])
    elif sec_a.get("days") != "TBA":
        slots_a.append(sec_a)
    if sec_a.get("lab") and sec_a["lab"].get("days") != "TBA":
        slots_a.append(sec_a["lab"])

    slots_b = []
    if sec_b.get("lecture") and sec_b["lecture"].get("days") != "TBA":
        slots_b.append(sec_b["lecture"])
    elif sec_b.get("days") != "TBA":
        slots_b.append(sec_b)
    if sec_b.get("lab") and sec_b["lab"].get("days") != "TBA":
        slots_b.append(sec_b["lab"])

    for sa in slots_a:
        for sb in slots_b:
            if slots_overlap(
                sa.get("days", ""), sa.get("start_min", -1), sa.get("end_min", -1),
                sb.get("days", ""), sb.get("start_min", -1), sb.get("end_min", -1)
            ):
                return True
    return False


def is_conflict_free(schedule: List[dict]) -> bool:
    for a, b in itertools.combinations(schedule, 2):
        if sections_overlap(a, b):
            return False
    return True


def section_matches_preferences(section: dict, min_start_m: int, max_end_m: int,
                                no_fridays: bool, min_score: float) -> bool:
    if min_score > 0.0 and section.get("score", 0.0) < min_score:
        return False

    slots = []
    if section.get("lecture") and section["lecture"].get("days") != "TBA":
        slots.append(section["lecture"])
    elif section.get("days") != "TBA":
        slots.append(section)
    if section.get("lab") and section["lab"].get("days") != "TBA":
        slots.append(section["lab"])

    for slot in slots:
        s_m = slot.get("start_min", -1)
        e_m = slot.get("end_min", -1)
        days = slot.get("days", "")

        if no_fridays and "F" in parse_days(days):
            return False
        if min_start_m != -1 and s_m != -1 and s_m < min_start_m:
            return False
        if max_end_m != -1 and e_m != -1 and e_m > max_end_m:
            return False

    return True