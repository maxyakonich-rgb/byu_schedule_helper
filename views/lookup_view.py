import tkinter as tk
from typing import Dict, List
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
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from rmp_client import fetch_rmp_profile
from scroll_engine import enable_smooth_scroll, update_scrollbar_visibility
from views.modals import ReviewsModal


class LookupView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        self._search_timer = None
        self._matched_keys: List[str] = []
        self._displayed_count = 0
        self.PAGE_SIZE = 12

        # Memoized course rankings & course-wide avg score: { course_key: {"avg": float, "ranked": list} }
        self._course_rank_cache: Dict[str, dict] = {}
        self._expanded_prof_cards = set()

        # Cache available departments
        self._all_dept_options = ["All Departments"]
        if hasattr(self.app, "compute_dept_display_options"):
            try:
                for opt in self.app.compute_dept_display_options():
                    if opt and opt not in {"──────────", "No departments found"}:
                        self._all_dept_options.append(opt)
            except Exception:
                pass

        # ---------------------------------------------------------------------
        # Left Sidebar (Apple macOS Inspector Style)
        # ---------------------------------------------------------------------
        sidebar = ctk.CTkFrame(
            self, width=332, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="UNIVERSITY DIRECTORY",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=BYU_ROYAL
        ).pack(anchor="w", padx=20, pady=(20, 2))

        ctk.CTkLabel(
            sidebar, text="Catalog & RMP Lookup",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            sidebar,
            text="Search by course code, title, or instructor. Professors are automatically ranked using verified reviews strictly for each course.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=292, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # 1. Unified Search Bar (Course Code, Title, or Instructor) + Clear Button
        ctk.CTkLabel(
            sidebar, text="SEARCH COURSE OR PROFESSOR",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        search_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        search_row.pack(fill="x", padx=20, pady=(0, 12))

        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="e.g. MATH 290, Calculus, Smith...",
            textvariable=self.search_var, height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, border_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self._on_course_key_release)

        self.clear_search_btn = ctk.CTkButton(
            search_row, text="✕", width=32, height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
            border_color=BORDER_SUBTLE, border_width=1,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=11, weight="bold"),
            command=self.reset_filters
        )
        self.clear_search_btn.pack(side="right", padx=(6, 0))

        # 2. Department Filter
        ctk.CTkLabel(
            sidebar, text="ACADEMIC DEPARTMENT",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.dept_var = ctk.StringVar(value="All Departments")
        self.dept_menu = ctk.CTkOptionMenu(
            sidebar, values=self._all_dept_options, variable=self.dept_var,
            command=self._on_dropdown_picked, height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY,
            dynamic_resizing=False
        )
        self.dept_menu.pack(fill="x", padx=20, pady=(0, 12))

        # 3. Sort Order
        ctk.CTkLabel(
            sidebar, text="SORT COURSES BY",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.sort_var = ctk.StringVar(value="Course Code (A–Z)")
        self.sort_menu = ctk.CTkOptionMenu(
            sidebar,
            values=["Course Code (A–Z)", "Highest Course RMP Rating", "Most Open Sections"],
            variable=self.sort_var,
            command=lambda _: self.filter_courses(),
            height=34,
            corner_radius=7,
            fg_color=BG_SURFACE_ALT,
            button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY,
            dynamic_resizing=False,
        )
        self.sort_menu.pack(fill="x", padx=20, pady=(0, 14))

        # 4. Audit Deficient Major Courses Shortcut
        self.filter_missing_btn = ctk.CTkButton(
            sidebar, text="★ Show Needed Major Courses",
            font=ctk.CTkFont(size=11, weight="bold"), height=32, corner_radius=7,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER, border_color=BYU_ROYAL, border_width=1,
            text_color=TEXT_PRIMARY, command=self.show_deficient_major_courses
        )
        self.filter_missing_btn.pack(fill="x", padx=20, pady=(0, 16))

        # 5. Schedule Staging Card
        builder_box = ctk.CTkFrame(
            sidebar, fg_color=BG_SURFACE_ALT, corner_radius=8,
            border_color=BORDER_SUBTLE, border_width=1
        )
        builder_box.pack(fill="x", padx=20, pady=(0, 16))

        b_hdr = ctk.CTkFrame(builder_box, fg_color="transparent")
        b_hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            b_hdr, text="SCHEDULE STAGING",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=BYU_ROYAL
        ).pack(side="left")

        self.staged_count_lbl = ctk.CTkLabel(
            b_hdr, text="0 Staged",
            font=ctk.CTkFont(size=10, family="Menlo", weight="bold"), text_color=TEXT_MUTED
        )
        self.staged_count_lbl.pack(side="right")

        self.open_builder_btn = ctk.CTkButton(
            builder_box, text="Open Schedule Builder ›",
            font=ctk.CTkFont(size=11, weight="bold"), height=30, corner_radius=7,
            fg_color=BG_LAYER_INSET, hover_color=BG_SURFACE_HOVER, border_color=BORDER_SUBTLE, border_width=1,
            text_color=TEXT_SECONDARY, command=self.app.show_builder_view
        )
        self.open_builder_btn.pack(fill="x", padx=12, pady=(4, 10))

        self.status_lbl = ctk.CTkLabel(
            sidebar, text="Ready. Type to filter.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=292, justify="left"
        )
        self.status_lbl.pack(fill="x", padx=20)

        # ---------------------------------------------------------------------
        # Right Panel: Results Scroll Frame
        # ---------------------------------------------------------------------
        right_panel = ctk.CTkFrame(
            self, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        right_panel.pack(side="right", fill="both", expand=True)

        top_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        top_bar.pack(fill="x", padx=22, pady=(16, 8))

        self.results_title = ctk.CTkLabel(
            top_bar, text="Catalog Course Directory",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.results_title.pack(side="left")

        self.results_meta_lbl = ctk.CTkLabel(
            top_bar, text="",
            font=ctk.CTkFont(size=11, family="Menlo"), text_color=TEXT_MUTED
        )
        self.results_meta_lbl.pack(side="right")

        canvas_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        canvas_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.canvas = tk.Canvas(
            canvas_container,
            bg=BG_SURFACE,
            bd=0,
            highlightthickness=0,
            relief="flat",
            yscrollincrement=1,
        )
        self.scrollbar = ctk.CTkScrollbar(
            canvas_container, orientation="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_content = tk.Frame(
            self.canvas, bg=BG_SURFACE, bd=0, highlightthickness=0
        )
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_content, anchor="nw"
        )
        self._last_canvas_width = 0

        def _on_content_configure(e):
            bbox = self.canvas.bbox(self.canvas_window)
            if bbox:
                self.canvas.configure(scrollregion=bbox)

        def _on_canvas_configure(e):
            if e.width != self._last_canvas_width and e.width > 1:
                self._last_canvas_width = e.width
                self.canvas.itemconfig(self.canvas_window, width=e.width)
            update_scrollbar_visibility(self.canvas, self.scrollbar)

        self.scroll_content.bind("<Configure>", _on_content_configure)
        self.canvas.bind("<Configure>", _on_canvas_configure)

        enable_smooth_scroll(self.canvas, self.scrollbar)
        self.after(50, self.filter_courses)

    # -------------------------------------------------------------------------
    # Offline Course & Professor Ranking Helper
    # -------------------------------------------------------------------------
    def _get_course_ranking_data(self, course_key: str) -> dict:
        if course_key in self._course_rank_cache:
            return self._course_rank_cache[course_key]

        sections = self.app.catalog.get(course_key, [])
        teacher_dict: Dict[str, list] = {}
        for s in sections:
            inst = s.get("instructor", "Staff") or "Staff"
            teacher_dict.setdefault(inst, []).append(s)

        ranked_list = []
        valid_scores = []
        for inst, sec_list in teacher_dict.items():
            if inst != "Staff":
                rmp = fetch_rmp_profile(inst, target_course=course_key)
                score = float(rmp.get("score_val", 0.0))
                rev_cnt = len(rmp.get("reviews", []))
                if score > 0 and rev_cnt > 0:
                    valid_scores.append(score)
            else:
                rmp = {}
                score = 0.0
                rev_cnt = 0

            ranked_list.append({
                "instructor": inst,
                "score": score,
                "rev_count": rev_cnt,
                "sections": sec_list,
                "rmp_raw": rmp,
            })

        ranked_list.sort(key=lambda x: (x["score"], x["rev_count"], len(x["sections"])), reverse=True)
        avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

        data = {
            "avg": avg_score,
            "ranked": ranked_list,
            "rated_prof_count": len(valid_scores),
        }
        self._course_rank_cache[course_key] = data
        return data

    # -------------------------------------------------------------------------
    # Filtering & Sorting Logic
    # -------------------------------------------------------------------------
    def reset_filters(self):
        self.search_var.set("")
        self.dept_var.set("All Departments")
        self.sort_var.set("Course Code (A–Z)")
        self.filter_courses()

    def lookup_course(self, course_code: str):
        """Pre-fills the search bar with course_code and runs catalog filtering."""
        self.dept_var.set("All Departments")
        self.search_var.set(course_code.strip())
        self.filter_courses()

    def show_deficient_major_courses(self):
        """Filters the catalog directly to all deficient major courses from the student's audit."""
        profile = getattr(self.app, "student_profile", None)
        if not profile:
            self.status_lbl.configure(
                text="Upload a Progress Report first to filter needed major courses.",
                text_color=STATUS_WARNING
            )
            return

        missing_major = profile.get("missing_major", [])
        if not missing_major:
            self.status_lbl.configure(
                text="All major requirements are satisfied in your audit!",
                text_color=STATUS_ONLINE
            )
            return

        self.dept_var.set("All Departments")
        self.search_var.set("")

        matched = []
        for code, _, _ in missing_major:
            cat_key = self.app.match_catalog_key(code) if hasattr(self.app, "match_catalog_key") else ""
            if cat_key and cat_key not in matched:
                matched.append(cat_key)

        self._apply_sort(matched)
        self._matched_keys = matched
        self._displayed_count = 0
        for w in self.scroll_content.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0.0)
        self.update_staged_counter()

        self.results_title.configure(text=f"Needed Major Courses ({profile.get('major', 'Major')})")
        self.results_meta_lbl.configure(text=f"{len(matched)} Courses")
        self.status_lbl.configure(
            text=f"Showing {len(matched)} needed major course(s) from your audit.",
            text_color=STATUS_ONLINE
        )
        if matched:
            self.load_more_courses()
        else:
            ctk.CTkLabel(
                self.scroll_content, text="No matching major courses found in current catalog.",
                font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
            ).pack(pady=40)
            update_scrollbar_visibility(self.canvas, self.scrollbar)

    def _on_course_key_release(self, event=None):
        if self._search_timer:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(120, self.filter_courses)

    def _on_dropdown_picked(self, chosen: str):
        self.filter_courses()

    def update_staged_counter(self):
        staged_len = len(getattr(self.app, "builder_staged_courses", []))
        self.staged_count_lbl.configure(
            text=f"{staged_len} Staged",
            text_color=STATUS_ONLINE if staged_len > 0 else TEXT_MUTED,
        )

    def _apply_sort(self, keys: List[str]):
        mode = self.sort_var.get()
        if mode == "Highest Course RMP Rating":
            keys.sort(
                key=lambda k: (
                    self._get_course_ranking_data(k)["avg"],
                    self._get_course_ranking_data(k)["rated_prof_count"],
                ),
                reverse=True,
            )
        elif mode == "Most Open Sections":
            keys.sort(key=lambda k: len(self.app.catalog.get(k, [])), reverse=True)

    def filter_courses(self):
        catalog = getattr(self.app, "catalog", {})
        if not catalog:
            self.status_lbl.configure(text="Catalog is loading...", text_color=TEXT_MUTED)
            return

        query = self.search_var.get().strip().lower()
        query_comp = query.replace(" ", "")
        dept_sel = self.dept_var.get()
        dept_code = ""

        if dept_sel and dept_sel not in {"All Departments", "No Matching Departments"}:
            if hasattr(self.app, "display_to_code"):
                dept_code = self.app.display_to_code.get(dept_sel, "") or ""
            if not dept_code:
                dept_code = dept_sel.split(" - ")[0].strip()

        def _matches_query(k: str) -> bool:
            k_low = str(k).lower()
            if (query in k_low) or (query_comp in k_low.replace(" ", "")):
                return True
            for sec in catalog.get(k, []):
                inst_low = (sec.get("instructor") or "").lower()
                if query in inst_low:
                    return True
            return False

        all_keys = list(catalog.keys())
        filtered = []
        fell_back = False

        if dept_code:
            dept_keys = list(self.app.dept_to_courses.get(dept_code, [])) if hasattr(self.app, "dept_to_courses") else []
            if not dept_keys:
                dept_keys = [k for k in all_keys if str(k).upper().startswith(dept_code.upper())]
            if query:
                filtered = [k for k in dept_keys if _matches_query(k)]
            else:
                filtered = list(dept_keys)

            if query and not filtered:
                fell_back = True
                filtered = [k for k in all_keys if _matches_query(k)]
        else:
            if query:
                filtered = [k for k in all_keys if _matches_query(k)]
            else:
                filtered = list(all_keys)

        self._apply_sort(filtered)
        self._matched_keys = filtered
        self._displayed_count = 0

        for w in self.scroll_content.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0.0)
        self.update_staged_counter()

        self.results_title.configure(
            text=f"{dept_code} Courses" if (dept_code and not fell_back) else "Catalog Course Directory"
        )
        self.results_meta_lbl.configure(text=f"{len(filtered):,} Matching Courses")

        if fell_back:
            self.status_lbl.configure(
                text=f"No matches in {dept_code}. Showing {len(filtered)} result(s) across all departments.",
                text_color=STATUS_WARNING
            )
        else:
            self.status_lbl.configure(
                text=f"Showing {len(filtered):,} matching course(s).",
                text_color=STATUS_ONLINE if filtered else TEXT_MUTED
            )

        if not filtered:
            ctk.CTkLabel(
                self.scroll_content, text="No matching courses or instructors found in catalog.",
                font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
            ).pack(pady=40)
            update_scrollbar_visibility(self.canvas, self.scrollbar)
            return

        self.load_more_courses()

    def load_more_courses(self):
        if hasattr(self, "_load_more_btn") and self._load_more_btn:
            try:
                self._load_more_btn.destroy()
            except Exception:
                pass
            self._load_more_btn = None

        catalog = getattr(self.app, "catalog", {})
        staged_list = getattr(self.app, "builder_staged_courses", [])

        batch = self._matched_keys[self._displayed_count:self._displayed_count + self.PAGE_SIZE]
        self._displayed_count += len(batch)

        for k in batch:
            raw_sections = catalog.get(k, [])
            self._build_course_card(k, raw_sections, staged_list)

        if self._displayed_count < len(self._matched_keys):
            remaining = len(self._matched_keys) - self._displayed_count
            self._load_more_btn = ctk.CTkButton(
                self.scroll_content,
                text=f"Load More Courses ({remaining} remaining) ↓",
                font=ctk.CTkFont(size=11, weight="bold"), height=32, corner_radius=7,
                fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
                border_color=BORDER_SUBTLE, border_width=1, text_color=TEXT_PRIMARY,
                command=self.load_more_courses
            )
            self._load_more_btn.pack(fill="x", padx=6, pady=(8, 12))

        update_scrollbar_visibility(self.canvas, self.scrollbar)

    # -------------------------------------------------------------------------
    # Course Card & Immediate Course-Specific Professor Rankings
    # -------------------------------------------------------------------------
    def _build_course_card(self, course_key: str, sections: list, staged_list: list):
        card = ctk.CTkFrame(
            self.scroll_content, fg_color=BG_SURFACE_ALT, corner_radius=10,
            border_color=BORDER_SUBTLE, border_width=1
        )
        card.pack(fill="x", pady=5, padx=2)

        hdr = tk.Frame(card, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        hdr.pack(fill="x", padx=16, pady=(12, 6))

        parts = str(course_key).split(" - ")
        code_txt = parts[0]
        title_txt = parts[1] if len(parts) > 1 else ""
        comp_code = code_txt.replace(" ", "").upper()

        rank_info = self._get_course_ranking_data(course_key)
        avg_score = rank_info["avg"]
        ranked_profs = rank_info["ranked"]

        title_box = tk.Frame(hdr, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        title_box.pack(side="left", fill="x", expand=True)

        code_line = tk.Frame(title_box, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        code_line.pack(fill="x")

        # Course-wide Average RMP Badge
        if avg_score >= 4.0:
            avg_bg, avg_fg = STATUS_ONLINE_BG, STATUS_ONLINE
        elif avg_score >= 3.0:
            avg_bg, avg_fg = STATUS_WARNING_BG, STATUS_WARNING
        else:
            avg_bg, avg_fg = BG_LAYER_INSET, TEXT_MUTED

        avg_txt = f" {avg_score:.2f}★ Avg " if avg_score > 0 else " Unrated "
        ctk.CTkLabel(
            code_line, text=avg_txt,
            font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
            fg_color=avg_bg, text_color=avg_fg, corner_radius=5, height=20
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            code_line, text=code_txt,
            font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        if title_txt:
            ctk.CTkLabel(
                code_line, text=f"  •  {title_txt}",
                font=ctk.CTkFont(size=12), text_color=TEXT_SECONDARY
            ).pack(side="left")

        # Audit Status Badge (Completed / In Progress / Needed for Major)
        profile = getattr(self.app, "student_profile", None)
        is_completed = False
        is_in_progress = False
        is_missing_major = False
        if profile:
            comp_set = {str(c).split(" - ")[0].replace(" ", "").upper() for c in profile.get("completed_courses", [])}
            ip_set = {str(c).split(" - ")[0].replace(" ", "").upper() for c in profile.get("in_progress_courses", [])}
            maj_set = {str(c[0]).replace(" ", "").upper() for c in profile.get("missing_major", [])}
            is_completed = comp_code in comp_set
            is_in_progress = comp_code in ip_set
            is_missing_major = comp_code in maj_set

            if is_completed:
                ctk.CTkLabel(
                    code_line, text=" ✓ Completed ",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=STATUS_ONLINE_BG, text_color=STATUS_ONLINE, corner_radius=5, height=20
                ).pack(side="left", padx=(8, 0))
            elif is_in_progress:
                ctk.CTkLabel(
                    code_line, text=" ● In Progress ",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=BYU_ROYAL_SUBTLE, text_color=BYU_ROYAL, corner_radius=5, height=20
                ).pack(side="left", padx=(8, 0))
            elif is_missing_major:
                ctk.CTkLabel(
                    code_line, text=" ★ Major Requirement ",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=BG_LAYER_INSET, text_color=BYU_ROYAL, corner_radius=5, height=20
                ).pack(side="left", padx=(8, 0))

        cr_hours = sections[0].get("credit_hours", 3.0) if sections else 3.0
        inst_summary = f"{len(sections)} Section(s)  •  {len(ranked_profs)} Instructor(s)  •  {cr_hours} Credits"
        ctk.CTkLabel(
            title_box, text=inst_summary,
            font=ctk.CTkFont(size=10, family="Menlo"), text_color=TEXT_MUTED, anchor="w"
        ).pack(fill="x", pady=(2, 0))

        btn_box = tk.Frame(hdr, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
        btn_box.pack(side="right")

        if is_completed or is_in_progress:
            lbl_txt = "Already Completed" if is_completed else "Currently Enrolled"
            stage_btn = ctk.CTkButton(
                btn_box, text=lbl_txt, width=128, height=28, corner_radius=6,
                fg_color=BG_LAYER_INSET, border_color=BORDER_SUBTLE, border_width=1,
                text_color=TEXT_MUTED, font=ctk.CTkFont(size=10, weight="bold"),
                state="disabled"
            )
            stage_btn.pack(side="right", padx=(8, 0))
        else:
            is_staged = course_key in staged_list
            btn_txt = "✓ Staged" if is_staged else "+ Add to Schedule"
            btn_fg = STATUS_ONLINE_BG if is_staged else BYU_ROYAL
            btn_border = STATUS_ONLINE if is_staged else BYU_ROYAL
            btn_text_color = STATUS_ONLINE if is_staged else "#FFFFFF"

            stage_btn = ctk.CTkButton(
                btn_box, text=btn_txt, width=124, height=28, corner_radius=6,
                fg_color=btn_fg, hover_color=BYU_ROYAL_HOVER,
                border_color=btn_border, border_width=1,
                text_color=btn_text_color, font=ctk.CTkFont(size=11, weight="bold")
            )
            stage_btn.configure(command=lambda k=course_key, b=stage_btn: self.toggle_stage_course(k, b))
            stage_btn.pack(side="right", padx=(8, 0))

        # Inset Professor & Section Box (Rendered Immediately from Offline Cache)
        body_box = ctk.CTkFrame(
            card, fg_color=BG_LAYER_INSET, corner_radius=8,
            border_color=BORDER_SUBTLE, border_width=1
        )
        body_box.pack(fill="x", padx=12, pady=(2, 12))

        self._render_ranked_professors(body_box, course_key, ranked_profs)

    def _render_ranked_professors(self, body_box: ctk.CTkFrame, course_key: str, ranked_list: list):
        for w in body_box.winfo_children():
            w.destroy()

        course_code = str(course_key).split(" - ")[0]
        is_expanded = course_key in self._expanded_prof_cards
        visible_list = ranked_list if (is_expanded or len(ranked_list) <= 4) else ranked_list[:4]

        for rank_idx, t_data in enumerate(visible_list, start=1):
            row = tk.Frame(body_box, bg=BG_LAYER_INSET, bd=0, highlightthickness=0)
            row.pack(fill="x", padx=10, pady=3)

            ctk.CTkLabel(
                row, text=f"#{rank_idx}",
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                text_color=BYU_ROYAL if rank_idx == 1 else TEXT_MUTED,
                width=26, anchor="w"
            ).pack(side="left")

            score_val = t_data["score"]
            rmp_raw = t_data.get("rmp_raw") or {}
            rev_count = t_data.get("rev_count", 0)

            if score_val >= 4.0:
                badge_bg, badge_fg = STATUS_ONLINE_BG, STATUS_ONLINE
            elif score_val >= 3.0:
                badge_bg, badge_fg = STATUS_WARNING_BG, STATUS_WARNING
            else:
                badge_bg, badge_fg = BG_SURFACE_ALT, TEXT_MUTED

            score_text = f" {score_val:.1f}★ ({rev_count}) " if score_val > 0 else f" No {course_code} Ratings "
            ctk.CTkLabel(
                row, text=score_text,
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                fg_color=badge_bg, text_color=badge_fg, corner_radius=5, height=22
            ).pack(side="left", padx=(0, 10))

            inst_name = t_data["instructor"]
            ctk.CTkLabel(
                row, text=inst_name,
                font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY,
                width=150, anchor="w"
            ).pack(side="left")

            sec_items = t_data["sections"]
            first_sec = sec_items[0]
            loc = first_sec.get("location", "")
            loc_str = f" ({loc})" if loc and loc != "TBA" else ""
            time_info = f"Sec {first_sec.get('section', '001')} • {first_sec.get('days', 'TBA')} {first_sec.get('start_time', '')}–{first_sec.get('end_time', '')}{loc_str}"
            if len(sec_items) > 1:
                time_info += f" (+{len(sec_items) - 1} more)"

            ctk.CTkLabel(
                row, text=time_info,
                font=ctk.CTkFont(size=10, family="Menlo"), text_color=TEXT_MUTED, anchor="w"
            ).pack(side="left", fill="x", expand=True)

            if inst_name != "Staff" and rev_count > 0:
                rev_btn = ctk.CTkButton(
                    row, text=f"Reviews ({rev_count})", width=86, height=22, corner_radius=5,
                    fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
                    border_color=BORDER_SUBTLE, border_width=1,
                    text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=10, weight="bold"),
                    command=lambda inst=inst_name, raw=rmp_raw, c_key=course_key: ReviewsModal(
                        self, inst, raw, c_key
                    )
                )
                rev_btn.pack(side="right")

        if len(ranked_list) > 4:
            hidden_cnt = len(ranked_list) - 4
            toggle_txt = "v   Show Top 4 Professors Only" if is_expanded else f"^   Show All {len(ranked_list)} Professors (+{hidden_cnt} more)"

            def _toggle_more(ck=course_key, bb=body_box, rl=ranked_list):
                if ck in self._expanded_prof_cards:
                    self._expanded_prof_cards.remove(ck)
                else:
                    self._expanded_prof_cards.add(ck)
                self._render_ranked_professors(bb, ck, rl)

            more_btn = ctk.CTkButton(
                body_box,
                text=toggle_txt,
                height=24,
                corner_radius=5,
                fg_color=BG_SURFACE,
                hover_color=BG_SURFACE_HOVER,
                border_color=BORDER_ACTIVE if is_expanded else BORDER_SUBTLE,
                border_width=1,
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=_toggle_more,
            )
            more_btn.pack(fill="x", padx=10, pady=(4, 6))

        update_scrollbar_visibility(self.canvas, self.scrollbar)

    def toggle_stage_course(self, course_key: str, btn: ctk.CTkButton):
        if hasattr(self.app, "is_course_satisfied") and self.app.is_course_satisfied(course_key):
            self.status_lbl.configure(
                text=f"{str(course_key).split(' - ')[0]} is already completed or in progress.",
                text_color=STATUS_WARNING
            )
            return

        staged = getattr(self.app, "builder_staged_courses", None)
        if staged is None:
            self.app.builder_staged_courses = []
            staged = self.app.builder_staged_courses

        if course_key not in staged:
            staged.append(course_key)
            btn.configure(
                text="✓ Staged",
                fg_color=STATUS_ONLINE_BG,
                border_color=STATUS_ONLINE,
                text_color=STATUS_ONLINE
            )
            self.status_lbl.configure(
                text=f"Staged {str(course_key).split(' - ')[0]} to Schedule Builder.",
                text_color=STATUS_ONLINE
            )
        else:
            staged.remove(course_key)
            btn.configure(
                text="+ Add to Schedule",
                fg_color=BYU_ROYAL,
                border_color=BYU_ROYAL,
                text_color="#FFFFFF"
            )
            self.status_lbl.configure(
                text=f"Removed {str(course_key).split(' - ')[0]} from Schedule Builder.",
                text_color=TEXT_MUTED
            )

        if hasattr(self.app, "sync_staged_state"):
            self.app.sync_staged_state()