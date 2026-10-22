import threading
import tkinter as tk
from typing import Dict, List, Set, Tuple
import customtkinter as ctk
from config import (
    BG_LAYER_INSET,
    BG_SURFACE,
    BG_SURFACE_ALT,
    BG_SURFACE_HOVER,
    BORDER_ACTIVE,
    BORDER_SUBTLE,
    BYU_ROYAL,
    BYU_ROYAL_HOVER,
    BYU_ROYAL_SUBTLE,
    PREREQ_MAP,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from rmp_client import fetch_rmp_profile
from scroll_engine import enable_smooth_scroll
from views.modals import ReviewsModal

# Expanded Catalog Offerings for Every BYU GE Requirement (Evaluated & Sorted by Avg RMP for Top 5)
GE_CATALOG_OPTIONS = {
    "UNIV 101": [
        ("UNIV 101", "BYU Foundations for Student Success", 2.0),
        ("SFL 101", "Introduction to School of Family Life", 1.0),
        ("C S 191", "Exploring Computer Science", 0.5),
        ("STAT 130", "Introduction to Statistics Department", 0.5),
        ("CHEM 195", "Introduction to Chemistry & Biochemistry", 0.5),
    ],
    "WRTG 150": [
        ("WRTG 150", "Writing and Rhetoric", 3.0),
        ("ENGL 203", "Ways of Reading", 3.0),
        ("ENGL 218", "Creative Writing", 3.0),
        ("PHIL 205", "Introduction to Logic & Critical Thinking", 3.0),
        ("HIST 200", "The Historian's Craft", 3.0),
    ],
    "WRTG 316": [
        ("WRTG 316", "Technical Communication", 3.0),
        ("BIO 316", "Scientific Communication", 3.0),
        ("NEURO 316", "Neuroscience Advanced Writing", 3.0),
        ("PSYCH 307", "Writing Within Psychology", 3.0),
        ("POLI 200", "Political Inquiry & Writing", 3.0),
        ("HIST 200", "The Historian's Craft", 3.0),
        ("SFL 315", "Effective Writing & Presenting", 3.0),
        ("SOC 307", "Social Science Writing & Presentation", 3.0),
        ("ENGL 302", "Writing with Style", 3.0),
    ],
    "CIV 1 ELEC": [
        ("IHUM 201", "Western Humanities 1: Antiquity to Renaissance", 3.0),
        ("HIST 201", "World Civilization to 1500", 3.0),
        ("ENGL 201", "Masterpieces of World Literature 1", 3.0),
        ("ENGL 211", "Rhetoric & Civilization 1", 3.0),
        ("PHIL 201", "History of Philosophy 1", 3.0),
        ("POLI 201", "Western Political Heritage 1", 3.0),
        ("IHUM 261", "American Humanities 1: Colonial to 1876", 3.0),
        ("CL CV 246", "Golden Age of Rome", 3.0),
    ],
    "CIV 2 ELEC": [
        ("IHUM 202", "Western Humanities 2: Renaissance to Present", 3.0),
        ("HIST 202", "World Civilization from 1500", 3.0),
        ("ENGL 202", "Masterpieces of World Literature 2", 3.0),
        ("ENGL 212", "Rhetoric & Civilization 2", 3.0),
        ("PHIL 202", "History of Philosophy 2", 3.0),
        ("POLI 202", "Western Political Heritage 2", 3.0),
        ("IHUM 262", "American Humanities 2: 1877 to Present", 3.0),
        ("PHIL 211", "Science & Civilization 2", 3.0),
    ],
    "ARTS ELEC": [
        ("MUSIC 101", "Introduction to Music", 3.0),
        ("IHUM 101", "Introduction to the Humanities", 3.0),
        ("DANCE 180", "Social Dance, Beginning", 1.0),
        ("TMA 115", "Introduction to Performance Studies", 3.0),
        ("ART 133", "Introduction to 3D Art", 3.0),
        ("ART 260", "Photography Fundamentals", 3.0),
        ("TMA 294", "History of Animation", 3.0),
        ("DANCE 184", "International Ballroom Dance, Beginning", 1.0),
    ],
    "LETTERS ELEC": [
        ("PHIL 110", "Introduction to Philosophy", 3.0),
        ("IHUM 101", "Introduction to the Humanities", 3.0),
        ("ENGL 201", "Masterpieces of World Literature 1", 3.0),
        ("ENGL 203", "Ways of Reading", 3.0),
        ("ENGL 230", "Studies in Literature", 3.0),
        ("ENGL 232", "Shakespeare", 3.0),
        ("PHIL 205", "Introduction to Logic & Critical Thinking", 3.0),
        ("PHIL 213", "Introduction to Ethics", 3.0),
    ],
    "BIO 100": [
        ("BIO 100", "Principles of Biology", 3.0),
        ("PWS 150", "Environmental Biology", 3.0),
        ("MMBIO 121", "General Biology: Health & Disease", 3.0),
        ("CELL 120", "Science of Biology", 3.0),
        ("BIO 130", "General Biology", 4.0),
        ("BIO 250", "Evolutionary Medicine", 3.0),
        ("BIO 220", "Biological Diversity: Animals", 3.0),
        ("BIO 230", "Biological Diversity: Plants", 3.0),
    ],
    "PHY S 100": [
        ("CHEM 101", "Introductory General Chemistry", 3.0),
        ("PHSCS 127", "Descriptive Astronomy", 3.0),
        ("GEOL 101", "Introduction to Geology", 3.0),
        ("PHSCS 105", "General Physics 1", 3.0),
        ("PHSCS 121", "Introduction to Newtonian Mechanics", 3.0),
        ("PHSCS 167", "Descriptive Acoustics of Music & Speech", 3.0),
        ("GEOL 105", "Diamonds and Gems", 3.0),
        ("GEOL 107", "The Water Planet", 3.0),
    ],
    "GLOBAL ELEC": [
        ("IHUM 241", "Humanities of East Asia", 3.0),
        ("POLI 150", "Comparative Government & Politics", 3.0),
        ("POLI 170", "Introduction to International Politics", 3.0),
        ("HIST 202", "World Civilization from 1500", 3.0),
        ("SOC 113", "Multicultural America", 3.0),
        ("GEOG 285", "Africa South of the Sahara", 3.0),
        ("IHUM 242", "Introduction to Humanities of Islam", 3.0),
        ("IHUM 243", "Humanities of South Asia", 3.0),
    ],
    "SOC SCI ELEC": [
        ("PSYCH 111", "Psychological Science", 3.0),
        ("SOC 111", "Introductory Sociology", 3.0),
        ("ECON 110", "Economic Principles & Problems", 3.0),
        ("POLI 110", "American Government & Politics", 3.0),
        ("SFL 160", "Introduction to Family Processes", 3.0),
        ("SOC 112", "Current Social Problems", 3.0),
        ("SFL 210", "Human Development", 3.0),
        ("PSYCH 220", "Human Development: Life Span", 3.0),
    ],
    "A HTG 100": [
        ("A HTG 100", "American Heritage", 3.0),
        ("HIST 220", "United States Through 1877", 3.0),
        ("HIST 221", "United States Since 1877", 3.0),
        ("POLI 110", "American Government & Politics", 3.0),
        ("ECON 110", "Economic Principles & Problems", 3.0),
        ("IHUM 261", "American Humanities 1", 3.0),
        ("IHUM 262", "American Humanities 2", 3.0),
    ],
    "QUANT ELEC": [
        ("MATH 102", "Quantitative Reasoning", 3.0),
        ("STAT 121", "Introduction to Statistical Data Analysis", 3.0),
        ("MATH 112", "Calculus 1", 4.0),
        ("MATH 110", "College Algebra", 3.0),
        ("PHIL 205", "Introduction to Logic & Critical Thinking", 3.0),
    ],
    "LANG ELEC": [
        ("MATH 112", "Calculus 1", 4.0),
        ("C S 111", "Introduction to Computer Science", 3.0),
        ("C S 110", "How to Program", 3.0),
        ("STAT 121", "Introduction to Statistical Data Analysis", 3.0),
        ("MATH 113", "Calculus 2", 4.0),
    ],
}


class SmartScheduleView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self._stage_buttons: Dict[str, List[ctk.CTkButton]] = {}
        self._last_payload: dict = {}
        self._expanded_ge_keys: Set[str] = set()

        # Left Sidebar (Apple macOS Inspector Style)
        sidebar = ctk.CTkFrame(
            self, width=326, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="ADVISING & GE AUDIT",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=BYU_ROYAL
        ).pack(anchor="w", padx=20, pady=(20, 2))

        ctk.CTkLabel(
            sidebar, text="Smart Course Recommender",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            sidebar,
            text="Mirrors your BYU Progress-to-Degree audit. Click the ^ dropdown on any needed GE requirement to reveal its 5 highest average rated classes.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=286, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        self.scan_btn = ctk.CTkButton(
            sidebar, text="Scan Audit & Rank Courses",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            fg_color=BYU_ROYAL, hover_color=BYU_ROYAL_HOVER, text_color="#FFFFFF",
            command=self.run_advising_scan
        )
        self.scan_btn.pack(fill="x", padx=20, pady=(0, 8))

        self.auto_stage_btn = ctk.CTkButton(
            sidebar, text="⚡ Auto-Stage Balanced Semester (~15 cr)",
            font=ctk.CTkFont(size=11, weight="bold"), height=32, corner_radius=8,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
            border_color=BYU_ROYAL, border_width=1, text_color=TEXT_PRIMARY,
            command=self.auto_stage_recommended_block
        )
        self.auto_stage_btn.pack(fill="x", padx=20, pady=(0, 8))

        self.builder_shortcut_btn = ctk.CTkButton(
            sidebar, text="Open Schedule Builder ›",
            font=ctk.CTkFont(size=11, weight="bold"), height=30, corner_radius=8,
            fg_color=BG_LAYER_INSET, hover_color=BG_SURFACE_ALT,
            border_color=BORDER_SUBTLE, border_width=1, text_color=TEXT_SECONDARY,
            command=self.app.show_builder_view
        )
        self.builder_shortcut_btn.pack(fill="x", padx=20, pady=(0, 16))

        # Display Options Card
        filter_card = ctk.CTkFrame(
            sidebar, fg_color=BG_SURFACE_ALT, corner_radius=8,
            border_color=BORDER_SUBTLE, border_width=1
        )
        filter_card.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            filter_card, text="VIEW OPTIONS",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.show_completed_ge_var = ctk.BooleanVar(value=True)
        self.show_completed_ge_chk = ctk.CTkCheckBox(
            filter_card,
            text="Show Completed & In-Progress GEs",
            variable=self.show_completed_ge_var,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            fg_color=BYU_ROYAL,
            corner_radius=5,
            command=self._on_filter_toggle,
        )
        self.show_completed_ge_chk.pack(anchor="w", padx=12, pady=(2, 10))

        self.status = ctk.CTkLabel(
            sidebar, text="Ready. Upload a Progress Report to begin.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=286, justify="left"
        )
        self.status.pack(fill="x", padx=20)

        # Right Main Content Surface
        right_panel = ctk.CTkFrame(
            self, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        right_panel.pack(side="right", fill="both", expand=True)

        hdr_row = ctk.CTkFrame(right_panel, fg_color="transparent")
        hdr_row.pack(fill="x", padx=22, pady=(16, 8))

        self.results_title = ctk.CTkLabel(
            hdr_row, text="Degree Audit & Smart Course Recommendations",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.results_title.pack(side="left")

        self.scroll_area = ctk.CTkScrollableFrame(right_panel, corner_radius=8, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        enable_smooth_scroll(self.scroll_area)

        self._render_empty_prompt()

    def _render_empty_prompt(self):
        ctk.CTkLabel(
            self.scroll_area,
            text="Upload your BYU Progress-to-Degree PDF using the top-right 'Upload Audit PDF' button\nto inspect your General Education, Religion, and Major requirements with Top-5 RMP class rankings.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            justify="center",
        ).pack(pady=60)

    def _on_filter_toggle(self):
        if self._last_payload:
            self._render(self._last_payload)

    def _toggle_all_needed_ges(self, needed_names: List[str]):
        if all(n in self._expanded_ge_keys for n in needed_names):
            self._expanded_ge_keys.clear()
        else:
            for n in needed_names:
                self._expanded_ge_keys.add(n)
        if self._last_payload:
            self._render(self._last_payload)

    def _match_catalog_key(self, course_code: str) -> str:
        if hasattr(self.app, "match_catalog_key"):
            return self.app.match_catalog_key(course_code)
        clean = " ".join(course_code.split()).upper()
        for k in self.app.catalog.keys():
            if k.upper().startswith(clean):
                return k
        return ""

    def _enrich_candidate_with_rmp(self, cand: dict) -> dict:
        """Computes both the course-wide Average RMP Rating across instructors and the Top Instructor strictly for this course."""
        cat_key = cand.get("catalog_key", "")
        sections = self.app.catalog.get(cat_key, []) if cat_key else []
        best_instructor = "Staff"
        best_score = 0.0
        best_rmp_data = None
        instructor_scores: Dict[str, float] = {}
        seen_instructors: Set[str] = set()
        total_course_reviews = 0

        for s in sections:
            inst = s.get("instructor", "Staff")
            if inst and inst != "Staff" and inst not in seen_instructors:
                seen_instructors.add(inst)
                rmp = fetch_rmp_profile(inst, target_course=cat_key)
                score_val = float(rmp.get("score_val", 0.0))
                rev_cnt = len(rmp.get("reviews", []))
                total_course_reviews += rev_cnt
                if score_val > 0.0 and rev_cnt > 0:
                    instructor_scores[inst] = score_val
                if score_val > best_score and rev_cnt > 0:
                    best_score = score_val
                    best_instructor = inst
                    best_rmp_data = rmp

        avg_score = (
            round(sum(instructor_scores.values()) / len(instructor_scores), 2)
            if instructor_scores
            else 0.0
        )

        cand["avg_score"] = avg_score
        cand["rated_prof_count"] = len(instructor_scores)
        cand["total_course_reviews"] = total_course_reviews
        cand["best_inst"] = best_instructor
        cand["best_score"] = best_score
        cand["best_rmp_raw"] = best_rmp_data
        cand["num_sections"] = len(sections)
        return cand

    def run_advising_scan(self):
        profile = getattr(self.app, "student_profile", None)
        if not profile:
            if hasattr(self, "status"):
                self.status.configure(
                    text="Upload a Progress Report first to view recommendations.",
                    text_color=STATUS_WARNING
                )
            return

        for child in self.scroll_area.winfo_children():
            child.destroy()
        self._stage_buttons.clear()

        self.scan_btn.configure(state="disabled", text="Ranking Courses via RMP...")
        self.status.configure(
            text="Computing average RateMyProfessors ratings for GE, Religion, and Major courses...",
            text_color=BYU_ROYAL
        )

        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        profile = self.app.student_profile
        satisfied_compact: Set[str] = set()
        for c in profile.get("completed_courses", []):
            satisfied_compact.add(str(c).split(" - ")[0].replace(" ", "").upper())
        for c in profile.get("in_progress_courses", []):
            satisfied_compact.add(str(c).split(" - ")[0].replace(" ", "").upper())

        def _prereqs_met(course_code: str) -> Tuple[bool, List[str]]:
            comp = course_code.replace(" ", "").upper()
            prereqs = PREREQ_MAP.get(course_code, [])
            if not prereqs:
                for k, v in PREREQ_MAP.items():
                    if k.replace(" ", "").upper() == comp:
                        prereqs = v
                        break
            if not prereqs:
                return True, []
            if comp in {"WRTG316", "WRTG315", "WRTG312", "WRTG311", "WRTG313", "IHUM311", "BIO316", "PWS316", "ENGL316"}:
                if any(p.replace(" ", "").upper() in satisfied_compact for p in prereqs) or len(satisfied_compact) >= 4:
                    return True, []
            missing_p = [p for p in prereqs if p.replace(" ", "").upper() not in satisfied_compact]
            return len(missing_p) == 0, missing_p

        # ---------------------------------------------------------------------
        # 1. General Education Breakdown (Top 5 Highest Average Rated Classes per GE)
        # ---------------------------------------------------------------------
        ge_audit_rows = profile.get("ge_audit", [])
        enriched_ge_rows = []
        flat_ge_candidates = []

        for row in ge_audit_rows:
            row_copy = dict(row)
            recs = []
            if row_copy.get("status") == "Not Completed":
                placeholder = row_copy.get("placeholder", "")
                options = GE_CATALOG_OPTIONS.get(
                    placeholder,
                    [(placeholder, row_copy["name"], row_copy.get("credits", 3.0))]
                )
                for real_code, real_title, cr in options:
                    comp = real_code.replace(" ", "").upper()
                    met, _ = _prereqs_met(real_code)
                    if comp not in satisfied_compact and met:
                        cat_key = self._match_catalog_key(real_code)
                        if cat_key:
                            cat_parts = str(cat_key).split(" - ", 1)
                            display_title = cat_parts[1].strip() if len(cat_parts) > 1 and not real_title else real_title
                            cand = self._enrich_candidate_with_rmp({
                                "code": real_code,
                                "title": display_title,
                                "credits": cr,
                                "catalog_key": cat_key,
                                "ge_tag": f"Fulfills {row_copy['name']}",
                                "eligible": True,
                            })
                            recs.append(cand)

                recs.sort(
                    key=lambda x: (x.get("avg_score", 0.0), x.get("best_score", 0.0), x.get("num_sections", 0)),
                    reverse=True,
                )
                recs = recs[:5]

                if recs:
                    top_pick = recs[0]
                    if not any(g["code"] == top_pick["code"] for g in flat_ge_candidates):
                        flat_ge_candidates.append(top_pick)

            row_copy["recommendations"] = recs
            enriched_ge_rows.append(row_copy)

        # ---------------------------------------------------------------------
        # 2. Religion Requirements (Mirrors PDF Page 2)
        # ---------------------------------------------------------------------
        religion_candidates: List[dict] = []
        for item in profile.get("missing_religion", []):
            code = item[0]
            comp = code.replace(" ", "").upper()
            if not code.startswith("REL ELEC") and comp not in satisfied_compact:
                cat_key = self._match_catalog_key(code)
                if cat_key and not any(r["code"] == code for r in religion_candidates):
                    religion_candidates.append(
                        self._enrich_candidate_with_rmp({
                            "code": code,
                            "title": item[2],
                            "credits": item[1],
                            "catalog_key": cat_key,
                            "ge_tag": "BYU Cornerstone Requirement",
                            "eligible": True,
                        })
                    )

        elective_rels = [
            ("REL A 121", "The Book of Mormon 1", 2.0),
            ("REL A 122", "The Book of Mormon 2", 2.0),
            ("REL C 324", "The Doctrine and Covenants", 2.0),
            ("REL A 211", "The New Testament", 2.0),
        ]
        for code, title, cr in elective_rels:
            if len(religion_candidates) >= 5:
                break
            comp = code.replace(" ", "").upper()
            if comp not in satisfied_compact and not any(r["code"] == code for r in religion_candidates):
                cat_key = self._match_catalog_key(code)
                if cat_key:
                    religion_candidates.append(
                        self._enrich_candidate_with_rmp({
                            "code": code,
                            "title": title,
                            "credits": cr,
                            "catalog_key": cat_key,
                            "ge_tag": "Religion Elective (Toward 14.0 hrs)",
                            "eligible": True,
                        })
                    )

        religion_candidates.sort(key=lambda x: (x.get("avg_score", 0.0), x.get("best_score", 0.0)), reverse=True)

        # ---------------------------------------------------------------------
        # 3. Major Requirements (Eligible Next Term vs. Future Milestones)
        # ---------------------------------------------------------------------
        major_eligible: List[dict] = []
        major_future: List[dict] = []

        major_groups = profile.get("major_groups", [])
        if major_groups:
            for grp in major_groups:
                hdr = grp.get("header", "Major Requirement")
                short_hdr = hdr.split("—")[0].strip() if "—" in hdr else hdr[:25]
                is_hours = grp.get("is_hours", False)
                opts = grp.get("options", [])
                display_opts = opts[:6] if is_hours else opts

                for code, cr, title in display_opts:
                    comp = code.replace(" ", "").upper()
                    if comp in satisfied_compact:
                        continue
                    met, missing_p = _prereqs_met(code)
                    cat_key = self._match_catalog_key(code)
                    tag = f"{short_hdr} • Ready Next Term" if met else f"{short_hdr} • Needs: {', '.join(missing_p)}"

                    cand = self._enrich_candidate_with_rmp({
                        "code": code,
                        "title": title,
                        "credits": cr,
                        "catalog_key": cat_key,
                        "ge_tag": tag,
                        "eligible": met,
                    })
                    if met:
                        if not any(m["code"] == code for m in major_eligible):
                            major_eligible.append(cand)
                    else:
                        if not any(m["code"] == code for m in major_future):
                            major_future.append(cand)
        else:
            for code, cr, title in profile.get("missing_major", []):
                comp = code.replace(" ", "").upper()
                if comp in satisfied_compact:
                    continue
                met, missing_p = _prereqs_met(code)
                cat_key = self._match_catalog_key(code)
                tag = "Prerequisites Met • Ready Next Term" if met else f"Needs: {', '.join(missing_p)}"
                cand = self._enrich_candidate_with_rmp({
                    "code": code,
                    "title": title,
                    "credits": cr,
                    "catalog_key": cat_key,
                    "ge_tag": tag,
                    "eligible": met,
                })
                if met:
                    major_eligible.append(cand)
                else:
                    major_future.append(cand)

        major_eligible.sort(key=lambda x: (x.get("avg_score", 0.0), x.get("best_score", 0.0)), reverse=True)

        payload = {
            "profile": profile,
            "ge_rows": enriched_ge_rows,
            "flat_ge_candidates": flat_ge_candidates,
            "religion_candidates": religion_candidates,
            "major_eligible": major_eligible,
            "major_future": major_future,
        }
        self._last_payload = payload
        self.after(0, lambda: self._render(payload))

    def _render_candidate_row(
        self,
        parent,
        c: dict,
        bg_color: str = BG_SURFACE,
        rank_num: int = 0,
        indent_px: int = 10,
    ):
        """Renders a sleek Apple-styled course row inside a layered container."""
        row = tk.Frame(parent, bg=bg_color, bd=0, highlightthickness=0)
        row.pack(fill="x", padx=(indent_px, 12), pady=4)

        if rank_num > 0:
            ctk.CTkLabel(
                row,
                text=f"#{rank_num}",
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                text_color=BYU_ROYAL if rank_num == 1 else TEXT_MUTED,
                width=26,
                anchor="w",
            ).pack(side="left")

        avg_val = c.get("avg_score", 0.0)
        if avg_val >= 4.0:
            r_bg, r_fg = STATUS_ONLINE_BG, STATUS_ONLINE
        elif avg_val >= 3.0:
            r_bg, r_fg = STATUS_WARNING_BG, STATUS_WARNING
        else:
            r_bg, r_fg = BG_SURFACE_ALT, TEXT_MUTED

        r_txt = f" {avg_val:.2f}★ Avg " if avg_val > 0 else " Unrated "

        ctk.CTkLabel(
            row,
            text=r_txt,
            font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
            fg_color=r_bg,
            text_color=r_fg,
            corner_radius=5,
            width=78,
            height=22,
        ).pack(side="left", padx=(0, 10))

        code_lbl = ctk.CTkLabel(
            row,
            text=c["code"],
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=BYU_ROYAL if c.get("eligible", True) else TEXT_SECONDARY,
            width=84,
            anchor="w",
        )
        code_lbl.pack(side="left")

        info_box = tk.Frame(row, bg=bg_color, bd=0, highlightthickness=0)
        info_box.pack(side="left", fill="x", expand=True, padx=(4, 8))

        line_1 = f"{c['title']} ({c['credits']:.1f} cr)"
        ctk.CTkLabel(
            info_box,
            text=line_1,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        meta_parts = []
        best_revs = len(c["best_rmp_raw"].get("reviews", [])) if c.get("best_rmp_raw") else 0
        if c.get("best_inst") and c["best_inst"] != "Staff" and best_revs > 0:
            meta_parts.append(f"Top in {c['code']}: {c['best_inst']} ({c['best_score']:.1f}★, {best_revs} revs)")
        if c.get("catalog_key"):
            meta_parts.append(f"{c.get('num_sections', 0)} Sections")
        if c.get("ge_tag"):
            meta_parts.append(c["ge_tag"])

        line_2 = "  •  ".join(meta_parts)
        tag_color = "#F87171" if not c.get("eligible", True) else TEXT_MUTED
        ctk.CTkLabel(
            info_box,
            text=line_2,
            font=ctk.CTkFont(size=10),
            text_color=tag_color,
            anchor="w",
        ).pack(fill="x")

        cat_key = c.get("catalog_key", "")
        if cat_key:
            is_staged = cat_key in self.app.builder_staged_courses
            btn_txt = "✓ Staged" if is_staged else "+ Add"
            btn_fg = STATUS_ONLINE_BG if is_staged else BYU_ROYAL
            btn_border = STATUS_ONLINE if is_staged else BYU_ROYAL
            btn_text_col = STATUS_ONLINE if is_staged else "#FFFFFF"

            add_btn = ctk.CTkButton(
                row,
                text=btn_txt,
                width=74,
                height=24,
                corner_radius=6,
                fg_color=btn_fg,
                hover_color=BYU_ROYAL_HOVER,
                border_color=btn_border,
                border_width=1,
                text_color=btn_text_col,
                font=ctk.CTkFont(size=10, weight="bold"),
            )
            add_btn.configure(command=lambda k=cat_key, b=add_btn: self._stage_course_to_builder(k, b))
            add_btn.pack(side="right", padx=(5, 0))
            self._stage_buttons.setdefault(cat_key, []).append(add_btn)

            lookup_btn = ctk.CTkButton(
                row,
                text="Sections ↗",
                width=76,
                height=24,
                corner_radius=6,
                fg_color=BG_SURFACE_ALT,
                hover_color=BG_SURFACE_HOVER,
                border_color=BORDER_SUBTLE,
                border_width=1,
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda code=c["code"]: self.app.open_course_in_lookup(code),
            )
            lookup_btn.pack(side="right", padx=(5, 0))

        if best_revs > 0:
            rev_btn = ctk.CTkButton(
                row,
                text=f"Reviews ({best_revs})",
                width=82,
                height=24,
                corner_radius=6,
                fg_color=BG_SURFACE_ALT,
                hover_color=BG_SURFACE_HOVER,
                border_color=BORDER_SUBTLE,
                border_width=1,
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda item=c: ReviewsModal(
                    self, item["best_inst"], item["best_rmp_raw"], item["catalog_key"]
                ),
            )
            rev_btn.pack(side="right", padx=(5, 0))

    def _build_layered_ge_item(self, parent_group_box, r: dict):
        """
        Renders a single GE requirement inside its own self-contained layered card.
        If Not Completed, hides recommended courses initially and provides a '^' dropdown
        that reveals the 5 highest average rated classes inside an inset drawer.
        """
        st = r.get("status", "Not Completed")
        req_name = r.get("name", "GE Requirement")
        recs = r.get("recommendations", [])
        is_needed = st == "Not Completed"

        item_card = ctk.CTkFrame(
            parent_group_box,
            fg_color=BG_SURFACE_ALT if is_needed else BG_SURFACE,
            corner_radius=8,
            border_color=BORDER_ACTIVE if (is_needed and req_name in self._expanded_ge_keys) else BORDER_SUBTLE,
            border_width=1,
        )
        item_card.pack(fill="x", padx=10, pady=4)

        top_bg = BG_SURFACE_ALT if is_needed else BG_SURFACE
        header_row = tk.Frame(item_card, bg=top_bg, bd=0, highlightthickness=0)
        header_row.pack(fill="x", padx=12, pady=8)

        if st == "Completed":
            b_txt, b_bg, b_fg = " ✓ Completed ", STATUS_ONLINE_BG, STATUS_ONLINE
        elif st in {"In Progress", "Planned"}:
            b_txt, b_bg, b_fg = f" ● {st} ", BYU_ROYAL_SUBTLE, BYU_ROYAL
        else:
            b_txt, b_bg, b_fg = " ● Needed ", STATUS_WARNING_BG, STATUS_WARNING

        ctk.CTkLabel(
            header_row,
            text=b_txt,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=b_bg,
            text_color=b_fg,
            corner_radius=5,
            width=104,
            height=22,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            header_row,
            text=req_name,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_PRIMARY if is_needed else TEXT_SECONDARY,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header_row,
            text=f"  •  {r.get('credits', 3.0):.1f} cr",
            font=ctk.CTkFont(size=11, family="Menlo"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(side="left")

        if r.get("satisfied_by"):
            ctk.CTkLabel(
                header_row,
                text=f" {r['satisfied_by']} ",
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                fg_color=BG_LAYER_INSET,
                text_color=TEXT_SECONDARY,
                corner_radius=5,
                height=22,
            ).pack(side="right")
        elif is_needed and recs:
            drawer = ctk.CTkFrame(
                item_card,
                fg_color=BG_LAYER_INSET,
                corner_radius=7,
                border_color=BORDER_SUBTLE,
                border_width=1,
            )

            drawer_hdr = tk.Frame(drawer, bg=BG_LAYER_INSET, bd=0, highlightthickness=0)
            drawer_hdr.pack(fill="x", padx=12, pady=(8, 4))

            ctk.CTkLabel(
                drawer_hdr,
                text=f"TOP {len(recs)} HIGHEST AVERAGE RATED CLASSES FOR {req_name.upper()}",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=BYU_ROYAL,
            ).pack(side="left")

            ctk.CTkLabel(
                drawer_hdr,
                text="Ranked by Course-Wide Avg RMP Rating",
                font=ctk.CTkFont(size=9, family="Menlo"),
                text_color=TEXT_MUTED,
            ).pack(side="right")

            for idx, cand in enumerate(recs, start=1):
                self._render_candidate_row(
                    drawer,
                    cand,
                    bg_color=BG_LAYER_INSET,
                    rank_num=idx,
                    indent_px=12,
                )

            tk.Frame(drawer, bg=BG_LAYER_INSET, height=4).pack(fill="x")

            is_open = req_name in self._expanded_ge_keys
            top_avg = recs[0].get("avg_score", 0.0)
            avg_hint = f" (Top: {top_avg:.2f}★)" if top_avg > 0 else ""

            def _btn_label(expanded: bool) -> str:
                return f"v   Hide Top {len(recs)} Rated Classes" if expanded else f"^   Top {len(recs)} Rated Classes{avg_hint}"

            toggle_btn = ctk.CTkButton(
                header_row,
                text=_btn_label(is_open),
                width=205,
                height=26,
                corner_radius=6,
                fg_color=BYU_ROYAL if is_open else BG_LAYER_INSET,
                hover_color=BYU_ROYAL_HOVER if is_open else BG_SURFACE_HOVER,
                border_color=BYU_ROYAL if is_open else BORDER_ACTIVE,
                border_width=1,
                text_color="#FFFFFF" if is_open else TEXT_PRIMARY,
                font=ctk.CTkFont(size=11, weight="bold"),
            )

            def _toggle_drawer(
                k=req_name,
                d_frame=drawer,
                card_frame=item_card,
                btn=toggle_btn,
            ):
                if k in self._expanded_ge_keys:
                    self._expanded_ge_keys.remove(k)
                    d_frame.pack_forget()
                    card_frame.configure(border_color=BORDER_SUBTLE)
                    btn.configure(
                        text=_btn_label(False),
                        fg_color=BG_LAYER_INSET,
                        hover_color=BG_SURFACE_HOVER,
                        border_color=BORDER_ACTIVE,
                        text_color=TEXT_PRIMARY,
                    )
                else:
                    self._expanded_ge_keys.add(k)
                    d_frame.pack(fill="x", padx=10, pady=(0, 10))
                    card_frame.configure(border_color=BORDER_ACTIVE)
                    btn.configure(
                        text=_btn_label(True),
                        fg_color=BYU_ROYAL,
                        hover_color=BYU_ROYAL_HOVER,
                        border_color=BYU_ROYAL,
                        text_color="#FFFFFF",
                    )

            toggle_btn.configure(command=_toggle_drawer)
            toggle_btn.pack(side="right")

            if is_open:
                drawer.pack(fill="x", padx=10, pady=(0, 10))

    def _render(self, payload: dict):
        for child in self.scroll_area.winfo_children():
            child.destroy()
        self._stage_buttons.clear()

        self.scan_btn.configure(state="normal", text="Scan Audit & Rank Courses")
        profile = payload.get("profile", {})
        ge_rows = payload.get("ge_rows", [])
        rel_cands = payload.get("religion_candidates", [])
        maj_elig = payload.get("major_eligible", [])
        maj_fut = payload.get("major_future", [])

        comp_cr = float(profile.get("credits", 0.0))
        ip_cr = float(profile.get("in_progress_credits", 0.0))
        rem_cr = float(profile.get("remaining_credits", 0.0))
        req_cr = max(120.0, float(profile.get("required_credits", 120.0)))

        self.status.configure(
            text=f"Audit synced: {comp_cr:.1f} cr Completed • {ip_cr:.1f} cr In Progress.",
            text_color=STATUS_ONLINE,
        )

        # ---------------------------------------------------------------------
        # Top Card: Clean Apple Degree Progress Overview
        # ---------------------------------------------------------------------
        ha_card = ctk.CTkFrame(
            self.scroll_area,
            fg_color=BG_SURFACE_ALT,
            corner_radius=10,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        ha_card.pack(fill="x", pady=(2, 10), padx=2)

        ha_hdr = tk.Frame(ha_card, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        ha_hdr.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            ha_hdr,
            text=f"DEGREE PROGRESS — {profile.get('major', 'Declared Major').upper()}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=BYU_ROYAL,
        ).pack(side="left")

        tot_summary = (
            f"Completed: {comp_cr:.1f} cr   •   "
            f"In Progress: {ip_cr:.1f} cr   •   "
            f"Remaining: {rem_cr:.1f} cr   •   "
            f"Goal: {req_cr:.1f} cr"
        )
        ctk.CTkLabel(
            ha_hdr,
            text=tot_summary,
            font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
            text_color=STATUS_ONLINE,
        ).pack(side="right")

        prog_bar = ctk.CTkProgressBar(
            ha_card,
            height=8,
            corner_radius=4,
            fg_color=BG_LAYER_INSET,
            progress_color=STATUS_ONLINE,
        )
        prog_bar.pack(fill="x", padx=16, pady=(2, 12))
        prog_bar.set(min(1.0, max(0.02, (comp_cr + ip_cr) / req_cr)))

        # ---------------------------------------------------------------------
        # Section 1: General Education Requirements (Layered Boxes + '^' Top 5 Dropdowns)
        # ---------------------------------------------------------------------
        ge_card = ctk.CTkFrame(
            self.scroll_area,
            fg_color=BG_SURFACE_ALT,
            corner_radius=10,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        ge_card.pack(fill="x", pady=8, padx=2)

        ge_hdr = tk.Frame(ge_card, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        ge_hdr.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            ge_hdr,
            text="General Education Requirements",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        needed_ge_names = [r["name"] for r in ge_rows if r.get("status") == "Not Completed" and r.get("recommendations")]
        all_expanded = bool(needed_ge_names) and all(n in self._expanded_ge_keys for n in needed_ge_names)

        if needed_ge_names:
            ctk.CTkButton(
                ge_hdr,
                text="v Collapse All" if all_expanded else "^ Expand All Needed",
                width=136,
                height=24,
                corner_radius=6,
                fg_color=BG_LAYER_INSET,
                hover_color=BG_SURFACE_HOVER,
                border_color=BORDER_SUBTLE,
                border_width=1,
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda n_list=needed_ge_names: self._toggle_all_needed_ges(n_list),
            ).pack(side="right", padx=(10, 0))

        als_def = profile.get("als_deficient_count", 3)
        ctk.CTkLabel(
            ge_hdr,
            text=f"{als_def} Arts/Letters/Civ + 1 Skills Needed",
            font=ctk.CTkFont(size=10, family="Menlo"),
            text_color=STATUS_WARNING,
        ).pack(side="right")

        show_all_ge = self.show_completed_ge_var.get()
        grouped_ge: Dict[str, List[dict]] = {}
        for r in ge_rows:
            if not show_all_ge and r.get("status") != "Not Completed":
                continue
            grouped_ge.setdefault(r["group"], []).append(r)

        for grp_title, rows_in_grp in grouped_ge.items():
            grp_container = ctk.CTkFrame(
                ge_card,
                fg_color=BG_SURFACE,
                corner_radius=8,
                border_color=BORDER_SUBTLE,
                border_width=1,
            )
            grp_container.pack(fill="x", padx=14, pady=6)

            grp_hdr_bar = tk.Frame(grp_container, bg=BG_SURFACE, bd=0, highlightthickness=0)
            grp_hdr_bar.pack(fill="x", padx=12, pady=(8, 4))

            ctk.CTkLabel(
                grp_hdr_bar,
                text=grp_title.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=BYU_ROYAL,
                anchor="w",
            ).pack(side="left")

            for r in rows_in_grp:
                self._build_layered_ge_item(grp_container, r)

            tk.Frame(grp_container, bg=BG_SURFACE, height=4).pack(fill="x")

        tk.Frame(ge_card, bg=BG_SURFACE_ALT, height=6).pack(fill="x")

        # ---------------------------------------------------------------------
        # Section 2: Major Requirements (Eligible Next Term)
        # ---------------------------------------------------------------------
        self._render_standard_section(
            title=f"Major Requirements — Eligible Next Term ({profile.get('major', 'Major')})",
            color=BYU_ROYAL,
            courses=maj_elig,
            empty_msg="All prerequisite-ready major courses are satisfied or in progress.",
        )

        # ---------------------------------------------------------------------
        # Section 3: Religion Requirements (Cornerstones & 14.0 Hr Requirement)
        # ---------------------------------------------------------------------
        self._render_standard_section(
            title="Religion Requirements — Cornerstones & Electives",
            color="#38BDF8",
            courses=rel_cands,
            empty_msg="All Religion requirements are satisfied.",
        )

        # ---------------------------------------------------------------------
        # Section 4: Future Major Milestones (Prerequisites Pending)
        # ---------------------------------------------------------------------
        if maj_fut:
            self._render_standard_section(
                title="Future Major Milestones & Upper-Division Electives (Prerequisites Pending)",
                color=TEXT_SECONDARY,
                courses=maj_fut,
                empty_msg="",
            )

    def _render_standard_section(self, title: str, color: str, courses: List[dict], empty_msg: str):
        cat_frame = ctk.CTkFrame(
            self.scroll_area,
            fg_color=BG_SURFACE_ALT,
            corner_radius=10,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        cat_frame.pack(fill="x", pady=8, padx=2)

        cat_hdr = tk.Frame(cat_frame, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        cat_hdr.pack(fill="x", padx=16, pady=(10, 6))

        ctk.CTkLabel(
            cat_hdr,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=color,
        ).pack(side="left")

        count_txt = f"{len(courses)} Options" if courses else "Fulfilled"
        ctk.CTkLabel(
            cat_hdr,
            text=count_txt,
            font=ctk.CTkFont(size=10, family="Menlo"),
            text_color=TEXT_MUTED,
        ).pack(side="right")

        list_box = ctk.CTkFrame(
            cat_frame,
            fg_color=BG_SURFACE,
            corner_radius=8,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        list_box.pack(fill="x", padx=14, pady=(2, 12))

        if not courses:
            ctk.CTkLabel(
                list_box,
                text=empty_msg,
                font=ctk.CTkFont(size=11),
                text_color=TEXT_MUTED,
            ).pack(padx=12, pady=8, anchor="w")
            return

        for c in courses:
            self._render_candidate_row(list_box, c, bg_color=BG_SURFACE, indent_px=12)

    def refresh_staged_buttons(self):
        """Synchronizes '+ Add' / '✓ Staged' buttons with app.builder_staged_courses."""
        for cat_key, btn_list in list(self._stage_buttons.items()):
            is_staged = cat_key in self.app.builder_staged_courses
            for btn in btn_list:
                if not btn.winfo_exists():
                    continue
                if is_staged:
                    btn.configure(
                        text="✓ Staged",
                        fg_color=STATUS_ONLINE_BG,
                        border_color=STATUS_ONLINE,
                        text_color=STATUS_ONLINE,
                    )
                else:
                    btn.configure(
                        text="+ Add",
                        fg_color=BYU_ROYAL,
                        border_color=BYU_ROYAL,
                        text_color="#FFFFFF",
                    )

    def auto_stage_recommended_block(self):
        """Automatically stages a ~14-16 credit balanced semester from top recommendations."""
        if not self._last_payload:
            if getattr(self.app, "student_profile", None):
                self.run_advising_scan()
                self.after(400, self._perform_auto_stage)
            else:
                self.status.configure(
                    text="Upload a Progress Report first to auto-stage courses.",
                    text_color=STATUS_WARNING,
                )
            return
        self._perform_auto_stage()

    def _perform_auto_stage(self):
        if not self._last_payload:
            return
        self.app.builder_staged_courses.clear()
        total_cr = 0.0
        target_cap = 15.5

        rel_list = self._last_payload.get("religion_candidates", [])
        maj_list = self._last_payload.get("major_eligible", [])
        ge_list = self._last_payload.get("flat_ge_candidates", [])

        # 1 Religion course (2.0 cr)
        for r in rel_list[:1]:
            if r.get("catalog_key"):
                self.app.builder_staged_courses.append(r["catalog_key"])
                total_cr += r.get("credits", 2.0)

        # Up to 3 eligible Major courses
        for m in maj_list[:3]:
            if m.get("catalog_key") and total_cr + m.get("credits", 3.0) <= target_cap:
                if m["catalog_key"] not in self.app.builder_staged_courses:
                    self.app.builder_staged_courses.append(m["catalog_key"])
                    total_cr += m.get("credits", 3.0)

        # Fill remaining credits up to ~15 cr with top-rated GE courses
        for g in ge_list:
            if total_cr >= 14.0:
                break
            if g.get("catalog_key") and total_cr + g.get("credits", 3.0) <= target_cap:
                if g["catalog_key"] not in self.app.builder_staged_courses:
                    self.app.builder_staged_courses.append(g["catalog_key"])
                    total_cr += g.get("credits", 3.0)

        if hasattr(self.app, "sync_staged_state"):
            self.app.sync_staged_state()

        count = len(self.app.builder_staged_courses)
        self.status.configure(
            text=f"Auto-staged {count} courses ({total_cr:.1f} cr) to Schedule Builder!",
            text_color=STATUS_ONLINE,
        )

    def _stage_course_to_builder(self, catalog_key: str, btn: ctk.CTkButton):
        if self.app.is_course_satisfied(catalog_key):
            self.status.configure(
                text=f"{catalog_key.split(' - ')[0]} is already completed or in progress.",
                text_color=STATUS_WARNING,
            )
            return

        if catalog_key not in self.app.builder_staged_courses:
            self.app.builder_staged_courses.append(catalog_key)
            self.status.configure(
                text=f"Staged {catalog_key.split(' - ')[0]} to Schedule Builder.",
                text_color=STATUS_ONLINE,
            )
        else:
            self.app.builder_staged_courses.remove(catalog_key)
            self.status.configure(
                text=f"Removed {catalog_key.split(' - ')[0]} from Builder.",
                text_color=TEXT_MUTED,
            )

        if hasattr(self.app, "sync_staged_state"):
            self.app.sync_staged_state()