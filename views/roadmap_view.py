import math
import tkinter as tk
from typing import Dict, List, Set, Tuple
import customtkinter as ctk
from config import (
    BG_LAYER_INSET,
    BG_SURFACE,
    BG_SURFACE_ALT,
    BG_SURFACE_HOVER,
    BORDER_SUBTLE,
    BYU_ROYAL,
    BYU_ROYAL_HOVER,
    BYU_ROYAL_SUBTLE,
    PREREQ_MAP,
    STATUS_DANGER,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from scroll_engine import enable_smooth_scroll


class RoadmapView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller

        sidebar = ctk.CTkFrame(
            self, width=350, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="DEGREE SEQUENCER",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=BYU_ROYAL
        ).pack(anchor="w", padx=20, pady=(20, 2))

        ctk.CTkLabel(
            sidebar, text="Graduation Roadmap Planner",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            sidebar,
            text="Distributes remaining Major, GE, Religion, and graduation credits into balanced full-time semesters.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=310, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # 1. Target Runway Selection
        ctk.CTkLabel(
            sidebar, text="MAX SEMESTERS PLANNED",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.terms_var = ctk.StringVar(value="5 Semesters")
        self.terms_menu = ctk.CTkOptionMenu(
            sidebar, values=[f"{i} Semesters" for i in range(3, 9)],
            variable=self.terms_var, command=self._on_terms_changed,
            height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY
        )
        self.terms_menu.pack(fill="x", padx=20, pady=(0, 12))

        # 2. Finish GE Target Term Selector
        ctk.CTkLabel(
            sidebar, text="FINISH GE COURSES BY",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.ge_target_var = ctk.StringVar(value="By Term 3")
        self.ge_target_menu = ctk.CTkOptionMenu(
            sidebar, values=self._compute_ge_options(5),
            variable=self.ge_target_var, command=lambda _: self._auto_recompute(),
            height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY
        )
        self.ge_target_menu.pack(fill="x", padx=20, pady=(0, 12))

        # 3. Full-Time Pacing
        ctk.CTkLabel(
            sidebar, text="FULL-TIME PACING",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.load_var = ctk.StringVar(value="14-15 Credits (Standard)")
        self.load_menu = ctk.CTkOptionMenu(
            sidebar, values=["12-13 Credits (Minimum FT)", "14-15 Credits (Standard)", "16-17 Credits (Accelerated)"],
            variable=self.load_var, command=lambda _: self._auto_recompute(),
            height=34, corner_radius=7,
            fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE, text_color=TEXT_PRIMARY
        )
        self.load_menu.pack(fill="x", padx=20, pady=(0, 18))

        # Actions
        self.gen_btn = ctk.CTkButton(
            sidebar, text="Compute Balanced Roadmap",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            fg_color=BYU_ROYAL, hover_color=BYU_ROYAL_HOVER, text_color="#FFFFFF",
            command=self.generate_roadmap
        )
        self.gen_btn.pack(fill="x", padx=20, pady=(0, 8))

        self.open_builder_btn = ctk.CTkButton(
            sidebar, text="Open Schedule Builder ›",
            font=ctk.CTkFont(size=11, weight="bold"), height=30, corner_radius=8,
            fg_color=BG_LAYER_INSET, hover_color=BG_SURFACE_ALT,
            border_color=BORDER_SUBTLE, border_width=1, text_color=TEXT_SECONDARY,
            command=self.app.show_builder_view
        )
        self.open_builder_btn.pack(fill="x", padx=20, pady=(0, 14))

        self.status = ctk.CTkLabel(
            sidebar, text="Ready. Load progress report to compute.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=310, justify="left"
        )
        self.status.pack(fill="x", padx=20)

        # Right Display Area
        right_panel = ctk.CTkFrame(
            self, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        right_panel.pack(side="right", fill="both", expand=True)

        self.results_title = ctk.CTkLabel(
            right_panel, text="Multi-Semester Graduation Sequence",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.results_title.pack(anchor="w", padx=24, pady=(18, 12))

        self.scroll_area = ctk.CTkScrollableFrame(right_panel, corner_radius=8, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        enable_smooth_scroll(self.scroll_area)

        self._render_empty_prompt()

    def _render_empty_prompt(self):
        ctk.CTkLabel(
            self.scroll_area,
            text="Upload your BYU Progress-to-Degree PDF using the top-right 'Upload Audit PDF' button\nto automatically sequence your remaining requirements into a graduation roadmap.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            justify="center",
        ).pack(pady=60)

    def _compute_ge_options(self, num_terms: int) -> List[str]:
        opts = [f"By Term {i}" for i in range(1, min(num_terms, 5) + 1)]
        opts.append("Spread Across All Terms")
        return opts

    def _on_terms_changed(self, chosen: str):
        terms_num = int(chosen.split()[0])
        new_opts = self._compute_ge_options(terms_num)
        self.ge_target_menu.configure(values=new_opts)
        if self.ge_target_var.get() not in new_opts:
            self.ge_target_var.set(new_opts[min(2, len(new_opts) - 1)])
        self._auto_recompute()

    def _auto_recompute(self):
        if getattr(self.app, "student_profile", None):
            self.generate_roadmap()

    def _estimate_course_credits(self, code: str) -> float:
        c_up = code.upper()
        if c_up.startswith("REL"):
            return 2.0
        if any(x in c_up for x in ["191", "215", "UNIV 101", "DANCE 180"]):
            return 1.0
        if any(x in c_up for x in ["112", "113"]):
            return 4.0
        return 3.0

    def _stage_term_to_builder(self, term_courses: List[Tuple[str, float, str]], term_num: int):
        staged_count = 0
        self.app.builder_staged_courses.clear()
        from views.smart_view import GE_CATALOG_OPTIONS

        for code, _, _ in term_courses:
            cat_key = self.app.match_catalog_key(code) if hasattr(self.app, "match_catalog_key") else ""
            if not cat_key or code in GE_CATALOG_OPTIONS:
                opts = GE_CATALOG_OPTIONS.get(code, [])
                for opt_code, _, _ in opts:
                    cand_key = self.app.match_catalog_key(opt_code) if hasattr(self.app, "match_catalog_key") else ""
                    if cand_key and not self.app.is_course_satisfied(cand_key) and cand_key not in self.app.builder_staged_courses:
                        cat_key = cand_key
                        break
            if not cat_key and code.startswith("REL ELEC"):
                for r_code in ["REL A 121", "REL A 122", "REL C 324", "REL A 211"]:
                    cand_key = self.app.match_catalog_key(r_code)
                    if cand_key and not self.app.is_course_satisfied(cand_key) and cand_key not in self.app.builder_staged_courses:
                        cat_key = cand_key
                        break

            if cat_key and not self.app.is_course_satisfied(cat_key):
                if cat_key not in self.app.builder_staged_courses:
                    self.app.builder_staged_courses.append(cat_key)
                    staged_count += 1

        if hasattr(self.app, "sync_staged_state"):
            self.app.sync_staged_state()

        self.status.configure(
            text=f"Staged {staged_count} courses from Term {term_num} to Schedule Builder!",
            text_color=STATUS_ONLINE
        )

    def generate_roadmap(self):
        profile = self.app.student_profile
        if not profile:
            self.status.configure(text="Please load your Progress Report first.", text_color=STATUS_DANGER)
            return

        for w in self.scroll_area.winfo_children():
            w.destroy()

        rel_pool: List[Tuple[str, float, str]] = list(profile.get("missing_religion", []))
        ge_pool: List[Tuple[str, float, str]] = list(profile.get("missing_ge", []))
        major_pool: List[Tuple[str, float, str]] = list(profile.get("missing_major", []))

        simulated_history: Set[str] = set()
        for c in profile.get("completed_courses", []):
            simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())
        for c in profile.get("in_progress_courses", []):
            simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())
        for c in profile.get("planned_courses", []):
            simulated_history.add(str(c).split(" - ")[0].replace(" ", "").upper())

        def _prereqs_met(code_str: str) -> bool:
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

        # Calculate starting credits (Earned + In-Progress + Planned)
        earned_credits = float(profile.get("credits", 0.0))
        parsed_ip = float(profile.get("in_progress_credits", 0.0))
        in_progress_credits = (
            parsed_ip
            if parsed_ip > 0.0
            else sum(self._estimate_course_credits(c) for c in profile.get("in_progress_courses", []))
        )
        planned_credits = sum(self._estimate_course_credits(c) for c in profile.get("planned_courses", []))
        baseline_credits = earned_credits + in_progress_credits + planned_credits

        # Calculate total credits in pools vs graduation requirement (120.0+ cr)
        GRADUATION_GOAL = max(120.0, float(profile.get("required_credits", 120.0)))
        pool_credits = (
            sum(c[1] for c in rel_pool)
            + sum(c[1] for c in ge_pool)
            + sum(c[1] for c in major_pool)
        )
        elective_deficit = max(0.0, GRADUATION_GOAL - (baseline_credits + pool_credits))
        elective_pool: List[Tuple[str, float, str]] = []
        elec_idx = 1
        while elective_deficit > 0.0:
            chunk = 3.0 if elective_deficit >= 3.0 else round(elective_deficit, 1)
            if chunk > 0:
                elective_pool.append((f"ELECTIVE {elec_idx}", chunk, "General / Upper-Division Graduation Elective"))
                elective_deficit = round(elective_deficit - chunk, 1)
                elec_idx += 1

        MIN_CREDITS = 12.0
        if "12-13" in self.load_var.get():
            desired_cap = 13.0
        elif "16-17" in self.load_var.get():
            desired_cap = 16.5
        else:
            desired_cap = 15.0

        selected_terms = int(self.terms_var.get().split()[0])
        total_remaining_credits = pool_credits + sum(e[1] for e in elective_pool)
        min_terms_for_credits = math.ceil(total_remaining_credits / desired_cap) if desired_cap > 0 else selected_terms
        max_allowed_terms = max(selected_terms, min_terms_for_credits)

        rel_schedule_slots: Dict[int, Tuple[str, float, str]] = {}
        if rel_pool:
            interval = max(1, max_allowed_terms // len(rel_pool))
            term_idx = 1
            for r_course in list(rel_pool):
                if term_idx <= max_allowed_terms:
                    rel_schedule_slots[term_idx] = r_course
                    rel_pool.remove(r_course)
                    term_idx += interval

        ge_selection = self.ge_target_var.get()
        if "Spread Across" in ge_selection:
            ge_target_terms = max_allowed_terms
        else:
            try:
                ge_target_terms = min(int(ge_selection.replace("By Term", "").strip()), max_allowed_terms)
            except ValueError:
                ge_target_terms = min(3, max_allowed_terms)

        total_ge_count = len(ge_pool)
        ge_slots_per_term = math.ceil(total_ge_count / ge_target_terms) if ge_target_terms > 0 else 0

        terms_plan = []
        running_credits = baseline_credits

        for term_num in range(1, max_allowed_terms + 1):
            has_assigned_religion = term_num in rel_schedule_slots
            has_pending_religion = bool(rel_pool or any(k >= term_num for k in rel_schedule_slots))
            has_pending_ge = bool(ge_pool)
            has_pending_major = bool(major_pool)
            has_pending_electives = bool(elective_pool)

            if not has_pending_religion and not has_pending_ge and not has_pending_major and not has_pending_electives:
                break

            term_courses: List[Tuple[str, float, str]] = []
            term_credits = 0.0

            # Step 1: Assign Religion (Max 1 per term)
            if has_assigned_religion:
                assigned_rel = rel_schedule_slots.pop(term_num)
                term_courses.append(assigned_rel)
                term_credits += assigned_rel[1]
            elif rel_pool and term_credits < desired_cap:
                assigned_rel = rel_pool.pop(0)
                term_courses.append(assigned_rel)
                term_credits += assigned_rel[1]

            # Step 2: GE Courses within target window
            if term_num <= ge_target_terms and ge_pool:
                ge_added = 0
                while ge_pool and ge_added < ge_slots_per_term and (term_credits < desired_cap + 1.5):
                    ge_item = ge_pool.pop(0)
                    term_courses.append(ge_item)
                    term_credits += ge_item[1]
                    ge_added += 1

            # Step 3: Major Requirements (Prerequisite-ordered)
            remaining_major = list(major_pool)
            for course_item in remaining_major:
                if term_credits >= desired_cap:
                    break
                code, creds, title = course_item
                if _prereqs_met(code):
                    if term_credits + creds <= desired_cap + 1.5:
                        term_courses.append(course_item)
                        term_credits += creds
                        major_pool.remove(course_item)

            if major_pool and not any(c in major_pool for c in term_courses) and term_credits + 3.0 <= desired_cap + 1.5:
                m_item = major_pool.pop(0)
                term_courses.append(m_item)
                term_credits += m_item[1]

            # Step 4: Overflow GEs
            while term_credits < desired_cap and ge_pool:
                ge_item = ge_pool.pop(0)
                term_courses.append(ge_item)
                term_credits += ge_item[1]

            # Step 5: Graduation Electives toward 120.0+ credit requirement
            while term_credits < desired_cap and elective_pool:
                el_item = elective_pool.pop(0)
                term_courses.append(el_item)
                term_credits += el_item[1]

            # Step 6: Full-Time Floor
            more_terms_needed = bool(rel_pool or ge_pool or major_pool or elective_pool or rel_schedule_slots)
            if term_credits < MIN_CREDITS and more_terms_needed:
                for m_course in list(major_pool):
                    code, creds, title = m_course
                    if _prereqs_met(code):
                        term_courses.append(m_course)
                        term_credits += creds
                        major_pool.remove(m_course)
                        if term_credits >= MIN_CREDITS:
                            break
                while term_credits < MIN_CREDITS and elective_pool:
                    el_item = elective_pool.pop(0)
                    term_courses.append(el_item)
                    term_credits += el_item[1]

            for c in term_courses:
                simulated_history.add(c[0].replace(" ", "").upper())

            if term_courses:
                running_credits += term_credits
                terms_plan.append({
                    "term": term_num,
                    "courses": term_courses,
                    "credits": term_credits,
                    "cumulative_credits": running_credits,
                })

        actual_terms_needed = len(terms_plan)
        major_title = profile.get("major", "Declared Major")

        self.results_title.configure(
            text=f"Roadmap: {major_title} ({actual_terms_needed} Terms • {running_credits:.1f} / {GRADUATION_GOAL:.1f} cr)"
        )
        self.status.configure(
            text=f"Degree & {GRADUATION_GOAL:.1f} cr requirement complete in {actual_terms_needed} terms ({running_credits:.1f} total cr).",
            text_color=STATUS_ONLINE
        )

        # Baseline Summary Card
        base_card = ctk.CTkFrame(
            self.scroll_area, corner_radius=8,
            fg_color=BG_SURFACE_ALT, border_color=BORDER_SUBTLE, border_width=1
        )
        base_card.pack(fill="x", pady=(2, 8), padx=2)
        base_txt = (
            f"Starting Credit Baseline: {earned_credits:.1f} cr Earned  +  "
            f"{in_progress_credits:.1f} cr In-Progress  +  {planned_credits:.1f} cr Planned  =  "
            f"{baseline_credits:.1f} cr Prior to Roadmap"
        )
        ctk.CTkLabel(
            base_card, text=base_txt,
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            text_color=BYU_ROYAL
        ).pack(padx=16, pady=10, anchor="w")

        for term_data in terms_plan:
            card = ctk.CTkFrame(
                self.scroll_area, corner_radius=10,
                fg_color=BG_SURFACE_ALT, border_color=BORDER_SUBTLE, border_width=1
            )
            card.pack(fill="x", pady=6, padx=2)

            hdr = tk.Frame(card, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
            hdr.pack(fill="x", padx=16, pady=(12, 4))

            ctk.CTkLabel(
                hdr, text=f"Term {term_data['term']}",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY
            ).pack(side="left")

            cr_val = term_data["credits"]
            cum_val = term_data["cumulative_credits"]
            ft_str = " (Full-Time)" if cr_val >= 12.0 else ""
            badge_text = f"  {cr_val:.1f} cr{ft_str}  •  {cum_val:.1f} / {GRADUATION_GOAL:.1f} cr Total  "

            ctk.CTkLabel(
                hdr, text=badge_text,
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                fg_color=BYU_ROYAL_SUBTLE, text_color=BYU_ROYAL, corner_radius=5, height=22
            ).pack(side="right")

            stage_term_btn = ctk.CTkButton(
                hdr, text="Stage Term to Builder ›", width=152, height=24, corner_radius=6,
                fg_color=BG_LAYER_INSET, hover_color=BG_SURFACE_HOVER, border_color=BORDER_SUBTLE, border_width=1,
                font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_PRIMARY,
                command=lambda tc=term_data["courses"], tn=term_data["term"]: self._stage_term_to_builder(tc, tn)
            )
            stage_term_btn.pack(side="right", padx=(0, 8))

            grid_box = ctk.CTkFrame(
                card, fg_color=BG_LAYER_INSET, corner_radius=8,
                border_color=BORDER_SUBTLE, border_width=1
            )
            grid_box.pack(fill="x", padx=14, pady=(6, 12))

            for code, cred, title in term_data["courses"]:
                row = tk.Frame(grid_box, bg=BG_LAYER_INSET, bd=0, highlightthickness=0)
                row.pack(fill="x", padx=12, pady=4)

                if code.startswith("REL"):
                    tag_color = "#38BDF8"
                elif code.startswith("ELECTIVE"):
                    tag_color = STATUS_ONLINE
                elif any(ge_key in code for ge_key in ["WRTG", "BIO", "PHY S", "ARTHC", "CIV", "ARTS", "LETTERS", "A HTG", "GLOBAL", "SOC SCI"]):
                    tag_color = STATUS_WARNING
                else:
                    tag_color = BYU_ROYAL

                ctk.CTkLabel(
                    row, text=code,
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=tag_color,
                    width=112, anchor="w"
                ).pack(side="left")

                ctk.CTkLabel(
                    row, text=title,
                    font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY,
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)

                has_catalog = bool(self.app.match_catalog_key(code)) if hasattr(self.app, "match_catalog_key") else False
                if has_catalog:
                    ctk.CTkButton(
                        row, text="Sections ↗", width=72, height=20, corner_radius=5,
                        fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
                        border_color=BORDER_SUBTLE, border_width=1,
                        text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=10, weight="bold"),
                        command=lambda c=code: self.app.open_course_in_lookup(c)
                    ).pack(side="right", padx=(8, 0))

                ctk.CTkLabel(
                    row, text=f"{cred:.1f} cr",
                    font=ctk.CTkFont(size=10, family="Menlo"), text_color=TEXT_MUTED
                ).pack(side="right")

        # Graduation Milestone Banner
        if running_credits >= GRADUATION_GOAL and not rel_pool and not ge_pool and not major_pool:
            grad_card = ctk.CTkFrame(
                self.scroll_area, corner_radius=10,
                fg_color=STATUS_ONLINE_BG, border_color=STATUS_ONLINE, border_width=1
            )
            grad_card.pack(fill="x", pady=(12, 8), padx=2)

            grad_body = ctk.CTkFrame(grad_card, fg_color="transparent")
            grad_body.pack(fill="x", padx=18, pady=14)

            ctk.CTkLabel(
                grad_body, text=f"🎓 ALL DEGREE REQUIREMENTS MET ({running_credits:.1f} / {GRADUATION_GOAL:.1f} CREDITS) — READY TO GRADUATE",
                font=ctk.CTkFont(size=13, weight="bold"), text_color=STATUS_ONLINE
            ).pack(anchor="w")

            ctk.CTkLabel(
                grad_body,
                text=f"All Major Core, General Education, Religion milestones, and the {GRADUATION_GOAL:.1f} credit graduation threshold are 100% satisfied by the end of Term {actual_terms_needed}.",
                font=ctk.CTkFont(size=11), text_color=TEXT_PRIMARY
            ).pack(anchor="w", pady=(4, 0))