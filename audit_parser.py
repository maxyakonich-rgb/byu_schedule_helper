import os
import re
from typing import Any, Dict, List, Set, Tuple

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    try:
        import PyPDF2 as pypdf
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False


def _extract_pages_from_file(file_path: str) -> List[str]:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return [f.read()]

    if ext == ".pdf":
        if not HAS_PYPDF:
            raise ImportError("pypdf is required to read PDF progress reports. Install with: pip install pypdf")
        pages_text = []
        reader = pypdf.PdfReader(file_path)
        for page in reader.pages:
            t = page.extract_text()
            pages_text.append(t if t else "")
        return pages_text

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [f.read()]


def _clean_name(raw_name: str) -> str:
    if not raw_name:
        return ""
    cleaned = re.sub(r"\bTRN\b", "", raw_name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = " ".join(cleaned.strip().split())
    cleaned = re.sub(r"\b([A-Za-z])\s+([a-z]{2,})\b", r"\1\2", cleaned)
    if "," in cleaned:
        parts = [p.strip() for p in cleaned.split(",", 1)]
        cleaned = f"{parts[1]} {parts[0]}".strip()
    return " ".join(w.capitalize() for w in cleaned.split() if w)


def parse_progress_report(file_path: str) -> Dict[str, Any]:
    pages = _extract_pages_from_file(file_path)
    full_text = "\n".join(pages)
    page_1 = pages[0] if pages else full_text

    profile: Dict[str, Any] = {
        "student_name": "Student",
        "byu_id": "",
        "major": "Undeclared",
        "standing": "Freshman",
        "credits": 0.0,
        "in_progress_credits": 0.0,
        "remaining_credits": 0.0,
        "required_credits": 120.0,
        "gpa": "0.00",
        "hours_analysis": [],
        "ge_audit": [],
        "religion_audit": [],
        "major_groups": [],
        "completed_courses": [],
        "in_progress_courses": [],
        "planned_courses": [],
        "missing_major": [],
        "missing_ge": [],
        "missing_religion": [],
    }

    # -------------------------------------------------------------------------
    # 1. Header Metadata Extraction
    # -------------------------------------------------------------------------
    name_m = re.search(r"(?:^|\n)[ \t]*([A-Za-z ,\.\-]+(?:\([A-Za-z]+\))?)[ \t]*\(\d{8,10}\)", page_1)
    if not name_m:
        # Fallback: line immediately following the report date on Page 1
        name_m = re.search(
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*\n\s*([A-Za-z ,\.\-]+(?:\([A-Za-z]+\))?)",
            page_1,
        )
    if name_m:
        cand = _clean_name(name_m.group(1))
        if cand and not any(k in cand.lower() for k in ["brigham", "university", "page", "degree"]):
            profile["student_name"] = cand

    id_m = re.search(r"\b(\d{2}-\d{3}-\d{4})\b|\((\d{8,10})\)", page_1)
    if id_m:
        profile["byu_id"] = id_m.group(1) or id_m.group(2)

    major_m = re.search(r"Program:\s*(?:PRIMARY\s+)?([A-Za-z\s&/\-]+(?:\([A-Za-z]+\))?)", page_1, re.IGNORECASE)
    if major_m:
        cand_major = major_m.group(1).splitlines()[0].strip()
        cand_major = re.sub(r"\b(Entered|Academic|Major Code|Hours Analysis).*$", "", cand_major, flags=re.IGNORECASE).strip()
        if cand_major:
            profile["major"] = cand_major

    # -------------------------------------------------------------------------
    # 2. Credits, Hours Analysis Table & Cumulative GPA
    # -------------------------------------------------------------------------
    flat_p1 = " ".join(page_1.replace("|", " ").split())
    last_page = pages[-1] if len(pages) > 1 else full_text
    flat_last = " ".join(last_page.replace("|", " ").split())

    # Strategy A: Page 1 'Total Hours <Required> <Completed> <Pct>% <InProgress> <Planned> <Remaining>'
    m_total_hours = re.search(
        r"Total\s+Hours\s+([\d\.]+)\s+([\d\.]+)(?:\s+([\d\.]+%)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+))?",
        flat_p1,
        re.IGNORECASE,
    )
    if m_total_hours:
        try:
            req_val = float(m_total_hours.group(1))
            comp_val = float(m_total_hours.group(2))
            if req_val >= 100.0 and comp_val < req_val:
                profile["required_credits"] = req_val
                profile["credits"] = comp_val
                if m_total_hours.group(4):
                    profile["in_progress_credits"] = float(m_total_hours.group(4))
                if m_total_hours.group(6):
                    profile["remaining_credits"] = float(m_total_hours.group(6))
        except ValueError:
            pass

    # Strategy B: Page 11 Academic Summary 'Total <Earned> <Graded> <Points> <GPA>' (row or column layout)
    m_summary_total = re.search(
        r"Summary\s+of\s+College\s+Credits.*?\bTotal(?:\s+BYU)?\s+([\d\.]+)\s+(?:0\.00\s+)?([\d\.]+)\s+(?:0\.00\s+)?([\d\.]+)\s+(?:0\.00\s+)?([\d]\.[\d]{2})",
        flat_last,
        re.IGNORECASE,
    )
    if not m_summary_total:
        m_summary_total = re.search(
            r"\bTotal\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d]\.[\d]{2})\b",
            flat_last,
            re.IGNORECASE,
        )
    if m_summary_total:
        try:
            earned_val = float(m_summary_total.group(1))
            if (profile["credits"] == 0.0 or profile["credits"] >= 120.0) and 0.0 < earned_val < 120.0:
                profile["credits"] = earned_val
            gpa_cand = m_summary_total.group(4)
            if float(gpa_cand) <= 4.0:
                profile["gpa"] = gpa_cand
        except ValueError:
            pass

    # Strategy C: Column-flattened Page 1 Hours Analysis (where 6 numbers appear per column before the % column)
    if profile["credits"] == 0.0 and "Hours Analysis" in flat_p1:
        ha_slice = flat_p1.split("Hours Analysis", 1)[1].split("GPA", 1)[0]
        # Look for the number immediately preceding the Total Hours percentage (e.g., 26.2%) or the last Completed column entry
        floats_before_pct = re.findall(r"\b(\d+\.\d+)\b(?<!%)", ha_slice.split("%")[0])
        if len(floats_before_pct) >= 2:
            # In row layout: [..., 122.0, 32.0] before 26.2%; in column layout: Completed column ends with Total Completed
            cand_last = float(floats_before_pct[-1])
            if 0.0 < cand_last < 120.0:
                profile["credits"] = cand_last

    # Strategy D: Sum 'Hours Earned: X.X' and 'In Process: X.X' across transcript semester banners (Pages 8-10)
    # These horizontal semester banners never get scrambled by pypdf table column ordering!
    transcript_only = full_text
    if "Classes" in full_text:
        transcript_only = full_text.split("Classes", 1)[1]
    if "Academic Summary" in transcript_only:
        transcript_only = transcript_only.split("Academic Summary", 1)[0]

    earned_banners = [float(x) for x in re.findall(r"Hours\s*Earned:\s*([\d\.]+)", transcript_only, re.IGNORECASE)]
    in_proc_banners = [float(x) for x in re.findall(r"In\s*Process:\s*([\d\.]+)", transcript_only, re.IGNORECASE)]

    if earned_banners:
        banner_earned_sum = round(sum(earned_banners), 2)
        if profile["credits"] == 0.0 or profile["credits"] >= 120.0:
            profile["credits"] = banner_earned_sum
    if in_proc_banners and profile["in_progress_credits"] == 0.0:
        profile["in_progress_credits"] = round(sum(in_proc_banners), 2)

    # Extract full Hours Analysis rows from Page 1
    ha_pattern = re.compile(
        r"(Religion\s+Hours|General\s+Ed\s+Hours|Elective\s+Hours|Additional\s+Hours|Total\s+Hours|[A-Za-z&/\-]+(?:\s+[A-Za-z&/\-]+)?\s+Hours)\s+"
        r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+%)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)",
        re.IGNORECASE,
    )
    hours_analysis_Block = page_1
    if "Hours Analysis" in page_1 and "GPA" in page_1:
        try:
            hours_analysis_Block = page_1[page_1.index("Hours Analysis"):page_1.index("GPA")]
        except ValueError:
            pass
    flat_ha = " ".join(hours_analysis_Block.replace("|", " ").split())
    flat_ha = re.sub(
        r"^.*?Remaining\s+",
        "",
        flat_ha,
        count=1,
        flags=re.IGNORECASE,
    )
    for hm in ha_pattern.finditer(flat_ha):
        cat_label = " ".join(hm.group(1).split())
        profile["hours_analysis"].append({
            "category": cat_label,
            "required": float(hm.group(2)),
            "completed": float(hm.group(3)),
            "percent": hm.group(4),
            "in_progress": float(hm.group(5)),
            "planned": float(hm.group(6)),
            "remaining": float(hm.group(7)),
        })

    # Cumulative GPA on Page 1
    if profile["gpa"] == "0.00":
        gpa_match_p1 = re.search(
            r"Cumulative\s+GPA\s+BYU\s+GPA\s+Major\s+GPA\s+([\d]\.[\d]{2})",
            flat_p1,
            re.IGNORECASE,
        )
        if gpa_match_p1:
            profile["gpa"] = gpa_match_p1.group(1).strip()

    cr = profile["credits"]
    if cr >= 90.0:
        profile["standing"] = "Senior"
    elif cr >= 60.0:
        profile["standing"] = "Junior"
    elif cr >= 30.0:
        profile["standing"] = "Sophomore"
    else:
        profile["standing"] = "Freshman"

    # -------------------------------------------------------------------------
    # 3. Dynamic Course Classification (Transcript Section)
    # -------------------------------------------------------------------------
    multi_word_depts = (
        r"A\s+HTG|C\s+S|CL\s+CV|EC\s+EN|EL\s+ED|ME\s+EN|CE\s+EN|CH\s+EN|"
        r"PHY\s+S|REL\s+A|REL\s+C|REL\s+E|SC\s+ED|SOC\s+W|T\s+ED|G\s+E|IP&T|IT&C"
    )
    course_pattern = re.compile(rf"\b((?:{multi_word_depts}|[A-Z]{{2,6}})\s+\d{{3}}[A-Z]?)\b")

    stopwords = {
        "IN", "OF", "TO", "OR", "AT", "BY", "ON", "NO", "AS", "IF", "UP", "SO",
        "DO", "GO", "AN", "BE", "WE", "HE", "ME", "MY", "US", "AM", "PM", "ID",
        "HR", "CR", "YR", "PT", "ST", "ND", "RD", "TH", "PAGE", "TERM", "FALL",
        "YEAR", "CODE", "FROM", "WITH", "OVER", "PLUS", "NEED", "TAKE", "EARN",
        "LESS", "MORE", "LAST", "NEXT", "EACH", "BOTH", "SOME", "SUCH", "THAN",
        "THEN", "THEM", "THEY", "THIS", "THAT", "WHEN", "WHAT", "WERE", "WILL",
        "HAVE", "BEEN", "INTO", "ONLY", "ALSO", "MUST", "GRAD", "HOURS", "TOTAL",
        "COMPLETE", "DEFICIENT", "PROGRESS", "PROCESS", "SEMESTER", "WINTER",
        "SPRING", "SUMMER", "PROGRAM", "ENTERED", "OPTION", "OPTIONS", "COURSES",
    }

    def _is_valid_course_code(raw_code: str) -> str:
        norm = " ".join(raw_code.strip().upper().split())
        dept_part = re.sub(r"\s+\d{3}[A-Z]?$", "", norm).strip()
        if dept_part in stopwords:
            return ""
        return norm

    completed_set: Set[str] = set()
    in_progress_set: Set[str] = set()
    planned_set: Set[str] = set()

    # The transcript starts at 'Classes' on Page 8 and ends at 'Academic Summary'
    transcript_text = full_text
    classes_m = re.search(r"\bClasses\s*\n", full_text)
    if classes_m:
        transcript_text = full_text[classes_m.start():]
    elif "Classes" in full_text:
        transcript_text = full_text.split("Classes", 1)[1]

    if "Academic Summary" in transcript_text:
        transcript_text = transcript_text.split("Academic Summary", 1)[0]

    semester_blocks = re.split(
        r"((?:Winter|Fall|Spring|Summer)\s+(?:Semester|Term)\s+\d{4}|Transfer/exam\s+credits(?:\s+\d{4})?)",
        transcript_text,
        flags=re.IGNORECASE,
    )

    for i in range(1, len(semester_blocks), 2):
        sem_hdr = semester_blocks[i]
        sem_content = semester_blocks[i + 1] if i + 1 < len(semester_blocks) else ""
        header_line = (sem_hdr + " " + sem_content[:120]).upper()

        is_planned = "PLANNED" in header_line and "IN PROCESS" not in header_line
        is_in_progress = "IN PROCESS" in header_line or "IN PROGRESS" in header_line

        for match in course_pattern.finditer(sem_content):
            c_code = _is_valid_course_code(match.group(1))
            if not c_code:
                continue
            if is_planned:
                planned_set.add(c_code)
            elif is_in_progress:
                in_progress_set.add(c_code)
            else:
                completed_set.add(c_code)

    profile["completed_courses"] = sorted(list(completed_set))
    profile["in_progress_courses"] = sorted(list(in_progress_set))
    profile["planned_courses"] = sorted(list(planned_set))

    taken_or_planned = completed_set.union(in_progress_set).union(planned_set)
    taken_compact = {c.replace(" ", "") for c in taken_or_planned}

    # -------------------------------------------------------------------------
    # 4. General Education Audit Extraction (Mirrors PDF Pages 1-2)
    # -------------------------------------------------------------------------
    ge_text = ""
    if "General Education Requirements" in full_text:
        ge_start = full_text.index("General Education Requirements")
        ge_end = full_text.index("Religion Requirements", ge_start) if "Religion Requirements" in full_text[ge_start:] else len(full_text)
        ge_text = full_text[ge_start:ge_end]
    flat_ge = " ".join(ge_text.split())

    # Extract Arts, Letters and Sciences 'Complete 6 of 7 Options — (Completed: X — In Progress: Y — Deficient: Z)'
    als_rule_label = "Arts, Letters and Sciences — Complete 6 of 7 Options"
    als_deficient_count = 3
    als_m = re.search(
        r"Arts,\s*Letters\s*and\s*Sciences\s*[—\-]+\s*Complete\s+(\d+\s+of\s+\d+\s+Options)\s*[—\-]+\s*\(([^)]+)\)",
        flat_ge,
        re.IGNORECASE,
    )
    if als_m:
        als_rule_label = f"Arts, Letters and Sciences — Complete {als_m.group(1)} ({als_m.group(2).strip()})"
        def_m = re.search(r"Deficient:\s*(\d+)", als_m.group(2), re.IGNORECASE)
        if def_m:
            als_deficient_count = int(def_m.group(1))

    ge_items_spec = [
        # (Section Group, PDF Requirement Name, Placeholder Key, Default Credits, Satisfying Compact Codes)
        ("BYU Foundations for Student Success", "BYU Foundations for Student Success", "UNIV 101", 2.0, {"UNIV101"}),
        ("The Individual and Society", "American Heritage", "A HTG 100", 3.0, {"AHTG100", "HIST102", "PSC101", "HIST220", "POLI150"}),
        ("The Individual and Society", "Global and Cultural Awareness", "GLOBAL ELEC", 3.0, {"GEOG130", "ANTHR101", "HIST200", "POLI200", "IAS101"}),
        ("Skills", "First-Year Writing", "WRTG 150", 3.0, {"WRTG150", "ENG102", "ENG101"}),
        ("Skills", "Adv Written & Oral Communication", "WRTG 316", 3.0, {"WRTG316", "WRTG315", "ENGL316", "WRTG312"}),
        ("Skills", "Quantitative Reasoning", "QUANT ELEC", 3.0, {"GE106", "MATH112", "MATH110", "STAT121"}),
        ("Skills", "Languages of Learning", "LANG ELEC", 4.0, {"MATH112", "MATH113", "CS111", "SPAN201", "FREN201"}),
        (als_rule_label, "Civilization 1", "CIV 1 ELEC", 3.0, {"ARTHC201", "HIST201", "CLCV241", "IHUM201", "PHIL201"}),
        (als_rule_label, "Civilization 2", "CIV 2 ELEC", 3.0, {"ARTHC202", "HIST202", "IHUM202", "MUSIC202", "PHIL202"}),
        (als_rule_label, "Arts", "ARTS ELEC", 3.0, {"ART101", "DANCE180", "MUSIC101", "TMA102", "DES110"}),
        (als_rule_label, "Letters", "LETTERS ELEC", 3.0, {"PHIL110", "ENGL251", "CLCV110", "IHUM101", "PHIL201"}),
        (als_rule_label, "Biological Science", "BIO 100", 3.0, {"BIO100", "BIO130", "PWS150", "MMBIO121", "CELL120"}),
        (als_rule_label, "Physical Science", "PHY S 100", 3.0, {"PHYS100", "ASTRON127", "GEOL101", "CHEM101", "CHEM105", "PHSCS121"}),
        (als_rule_label, "Social Science", "SOC SCI ELEC", 3.0, {"PSC101", "PSYCH111", "SOC111", "ECON110", "POLI110", "SFL160"}),
    ]

    comp_compact = {c.replace(" ", ""): c for c in completed_set}
    ip_compact = {c.replace(" ", ""): c for c in in_progress_set}
    plan_compact = {c.replace(" ", ""): c for c in planned_set}

    als_not_completed_items: List[Tuple[str, float, str]] = []

    for sec_group, req_name, placeholder_key, cr_val, sat_codes in ge_items_spec:
        # Check status directly in PDF GE text first, then fallback to transcript sets
        status = "Not Completed"
        satisfied_by = ""

        esc_name = re.escape(req_name).replace(r"\ ", r"\s+")
        m_ge_row = re.search(
            rf"{esc_name}\s+(Completed|In\s+Progress|Not\s+Completed)(.*?)(?=(?:American\s+Heritage|Global\s+and\s+Cultural|Skills|First-Year\s+Writing|Adv\s+Written|Quantitative|Languages\s+of\s+Learning|Arts,\s*Letters|Civilization\s+1|Civilization\s+2|Arts\s+|Letters\s+|Biological\s+Science|Physical\s+Science|Social\s+Science|Religion\s+Requirements|$))",
            flat_ge,
            re.IGNORECASE,
        )
        if m_ge_row:
            raw_st = " ".join(m_ge_row.group(1).split()).title()
            status = raw_st
            tail = m_ge_row.group(2).strip()
            found_courses = []
            for cm in course_pattern.finditer(tail):
                cc = _is_valid_course_code(cm.group(1))
                if cc and cc not in found_courses:
                    found_courses.append(cc)
            if found_courses:
                satisfied_by = ", ".join(found_courses)
                if "AP EXAM" in tail.upper():
                    satisfied_by += " (AP Exam)"
                elif "TWV" in tail.upper():
                    satisfied_by += " (TWV)"
                elif "TRN" in tail.upper():
                    satisfied_by += " (TRN)"
        else:
            # Fallback to transcript sets
            matched_comp = [comp_compact[sc] for sc in sat_codes if sc in comp_compact]
            matched_ip = [ip_compact[sc] for sc in sat_codes if sc in ip_compact]
            matched_pl = [plan_compact[sc] for sc in sat_codes if sc in plan_compact]
            if matched_comp:
                status = "Completed"
                satisfied_by = ", ".join(matched_comp)
            elif matched_ip:
                status = "In Progress"
                satisfied_by = ", ".join(matched_ip)
            elif matched_pl:
                status = "Planned"
                satisfied_by = ", ".join(matched_pl)

        profile["ge_audit"].append({
            "group": sec_group,
            "name": req_name,
            "placeholder": placeholder_key,
            "credits": cr_val,
            "status": status,
            "satisfied_by": satisfied_by,
        })

        if status == "Not Completed":
            if sec_group == als_rule_label:
                als_not_completed_items.append((placeholder_key, cr_val, req_name))
            else:
                profile["missing_ge"].append((placeholder_key, cr_val, req_name))

    # For Arts, Letters and Sciences (Complete 6 of 7 Options):
    # In SmartScheduleView we can show all uncompleted options so the student can pick any 3 of the 4,
    # while in missing_ge we store the exact deficient count needed for graduation credit math!
    profile["als_uncompleted_options"] = list(als_not_completed_items)
    profile["als_deficient_count"] = als_deficient_count
    for item in als_not_completed_items[:als_deficient_count]:
        profile["missing_ge"].append(item)

    # -------------------------------------------------------------------------
    # 5. Religion Audit Extraction (Mirrors PDF Page 2)
    # -------------------------------------------------------------------------
    rel_text = ""
    if "Religion Requirements" in full_text:
        r_start = full_text.index("Religion Requirements")
        r_end_m = re.search(r"PRIMARY\s+.*?\s+Requirements", full_text[r_start:], re.IGNORECASE)
        r_end = r_start + r_end_m.start() if r_end_m else len(full_text)
        rel_text = full_text[r_start:r_end]

    cornerstone_specs = [
        ("Requirement 1", "REL A 275", 2.0, "Teachings & Doctrine of Book of Mormon"),
        ("Requirement 2", "REL A 250", 2.0, "Jesus Christ & the Everlasting Gospel"),
        ("Requirement 3", "REL C 225", 2.0, "Foundations of the Restoration"),
        ("Requirement 4", "REL C 200", 2.0, "The Eternal Family"),
    ]
    missing_religion: List[Tuple[str, float, str]] = []
    for req_lbl, r_code, r_cr, r_title in cornerstone_specs:
        comp = r_code.replace(" ", "")
        if comp in comp_compact:
            st = "Completed"
        elif comp in ip_compact:
            st = "In Progress"
        elif comp in plan_compact:
            st = "Planned"
        else:
            st = "Not Completed"
            missing_religion.append((r_code, r_cr, r_title))
        profile["religion_audit"].append({
            "req": req_lbl,
            "code": r_code,
            "credits": r_cr,
            "title": r_title,
            "status": st,
        })

    # Check total religion hours needed (14.0 hrs total)
    rel_hours_remaining = 12.0
    for h_row in profile["hours_analysis"]:
        if "RELIGION" in h_row["category"].upper():
            rel_hours_remaining = h_row["remaining"]
            break
    else:
        rel_taken = sum(2.0 for c in taken_or_planned if c.startswith("REL"))
        rel_hours_remaining = max(0.0, 14.0 - rel_taken)

    cornerstone_missing_hrs = sum(c[1] for c in missing_religion)
    elective_rel_hrs = max(0.0, rel_hours_remaining - cornerstone_missing_hrs)
    num_rel_electives = int(round(elective_rel_hrs / 2.0))
    for i in range(1, num_rel_electives + 1):
        missing_religion.append((f"REL ELEC {i}", 2.0, "BYU Religion Elective (Toward 14.0 hrs)"))

    profile["missing_religion"] = missing_religion

    # -------------------------------------------------------------------------
    # 6. Major Requirements Extraction (Mirrors PDF Pages 4-6)
    # -------------------------------------------------------------------------
    major_req_text = full_text
    m_maj_start = re.search(r"PRIMARY\s+.*?\s+Requirements", full_text, re.IGNORECASE)
    if m_maj_start:
        m_start = m_maj_start.start()
        m_end = classes_m.start() if classes_m else len(full_text)
        major_req_text = full_text[m_start:m_end]
    elif "Requirements" in full_text and "Classes" in full_text:
        try:
            start_idx = full_text.index("Requirements")
            end_idx = full_text.index("Classes", start_idx)
            major_req_text = full_text[start_idx:end_idx]
        except ValueError:
            pass

    req_sections = re.split(
        r"(Requirement\s+\d+\s*[—\-]+[^\n]*\([^)]*Deficient:\s*[1-9][\d\.]*[^)]*\))",
        major_req_text,
        flags=re.IGNORECASE,
    )

    missing_major: List[Tuple[str, float, str]] = []
    seen_major_compact: Set[str] = set()

    for idx in range(1, len(req_sections), 2):
        sec_header = " ".join(req_sections[idx].split())
        sec_body = req_sections[idx + 1] if idx + 1 < len(req_sections) else ""
        # Stop scanning if Requirement 5 (exit exam/confirmation text) begins inside sec_body
        if "Obtain confirmation" in sec_body:
            sec_body = sec_body.split("Obtain confirmation", 1)[0]

        # Determine how many courses/hours are deficient in this specific requirement group
        def_m = re.search(r"Deficient:\s*([\d\.]+)", sec_header, re.IGNORECASE)
        def_val = float(def_m.group(1)) if def_m else 1.0
        is_hours_req = bool(re.search(r"Complete\s+\d+\s+hours", sec_header, re.IGNORECASE))

        group_courses: List[Tuple[str, float, str]] = []

        for cm in course_pattern.finditer(sec_body):
            code = _is_valid_course_code(cm.group(1))
            if not code or code.startswith("REL"):
                continue
            comp = code.replace(" ", "")
            if comp in taken_compact:
                continue

            start_pos = cm.end()
            # Slice up to the next course match or 120 chars
            window = sec_body[start_pos:start_pos + 120]
            flat_win = " ".join(window.replace("|", " ").split())

            # Skip if forward window shows course was completed/in-progress in a specific term
            if any(
                term in flat_win.upper()
                for term in ["FALL SEMESTER", "WINTER SEMESTER", "SPRING TERM", "SUMMER TERM", "PLANNED"]
            ):
                continue

            # Extract title and credits before the credit float (e.g. 'Calculus 2 4.0' or 'Readings in Math 0.5v')
            tc_m = re.match(r"^([A-Za-z0-9\s&,\.\-/]+?)\s+(\d+\.\d+)v?\b", flat_win)
            if tc_m:
                title = " ".join(tc_m.group(1).strip(" |-").split())
                creds = float(tc_m.group(2))
            else:
                cred_m = re.search(r"\b([0-5]\.\d+)v?\b", flat_win)
                creds = float(cred_m.group(1)) if cred_m else 3.0
                title = "Major Requirement"

            if not any(g[0].replace(" ", "") == comp for g in group_courses):
                group_courses.append((code, creds, title))

        if group_courses:
            profile["major_groups"].append({
                "header": sec_header,
                "deficient": def_val,
                "is_hours": is_hours_req,
                "options": group_courses,
            })

            # Add needed count/hours to missing_major for accurate roadmap sequencing
            if is_hours_req:
                hrs_acc = 0.0
                for c_code, c_cr, c_title in group_courses:
                    comp = c_code.replace(" ", "")
                    if comp not in seen_major_compact and c_cr >= 1.0:
                        seen_major_compact.add(comp)
                        missing_major.append((c_code, c_cr, f"{c_title} (Major Elective)"))
                        hrs_acc += c_cr
                        if hrs_acc >= def_val:
                            break
            else:
                needed_count = int(round(def_val))
                added = 0
                for c_code, c_cr, c_title in group_courses:
                    comp = c_code.replace(" ", "")
                    if comp not in seen_major_compact:
                        seen_major_compact.add(comp)
                        suffix = "" if needed_count == len(group_courses) else f" (Option Group)"
                        missing_major.append((c_code, c_cr, f"{c_title}{suffix}"))
                        added += 1
                        if added >= needed_count:
                            break

    profile["missing_major"] = missing_major
    return profile