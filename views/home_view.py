import customtkinter as ctk

from config import (
    BG_LAYER_INSET,
    BG_SURFACE,
    BG_SURFACE_ALT,
    BG_SURFACE_HOVER,
    BORDER_SUBTLE,
    BYU_ROYAL,
    BYU_ROYAL_HOVER,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from scroll_engine import enable_smooth_scroll


class HomeView(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller
        enable_smooth_scroll(self)

        # ---------------------------------------------------------------------
        # 1. Hero Banner: Academic Planning Suite
        # ---------------------------------------------------------------------
        self.hero_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=BG_SURFACE,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        self.hero_card.pack(fill="x", pady=(0, 14))

        hero_inner = ctk.CTkFrame(self.hero_card, fg_color="transparent")
        hero_inner.pack(fill="x", padx=26, pady=20)

        top_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        top_row.pack(fill="x")

        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text="ACADEMIC PLANNING SUITE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=BYU_ROYAL,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            title_col,
            text="BYU Academic Course Suite & Schedule Solver",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(2, 4))

        ctk.CTkLabel(
            title_col,
            text="Automated Progress-to-Degree PDF extraction, course-specific RateMyProfessors rankings, multi-semester roadmaps, and conflict-free schedule generation.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x")

        # Right side of Hero: Catalog pill & Primary Upload CTA
        cta_col = ctk.CTkFrame(top_row, fg_color="transparent")
        cta_col.pack(side="right", padx=(16, 0))

        cat_len = len(getattr(self.app, "catalog", {}))
        self.catalog_badge = ctk.CTkLabel(
            cta_col,
            text=f"  {cat_len:,} Catalog Courses  ",
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            fg_color=BG_SURFACE_ALT,
            text_color=TEXT_SECONDARY,
            corner_radius=6,
            height=28,
        )
        self.catalog_badge.pack(side="left", padx=(0, 10))

        self.upload_btn = ctk.CTkButton(
            cta_col,
            text="Upload Progress Report",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            corner_radius=7,
            fg_color=BYU_ROYAL,
            hover_color=BYU_ROYAL_HOVER,
            text_color="#FFFFFF",
            command=self.app.prompt_upload_record,
        )
        self.upload_btn.pack(side="left")

        # ---------------------------------------------------------------------
        # 2. Student Audit Status & 4-Metric Dashboard Strip
        # ---------------------------------------------------------------------
        self.banner_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=BG_SURFACE,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        self.banner_frame.pack(fill="x", pady=(0, 18))

        self.student_summary_lbl = ctk.CTkLabel(
            self.banner_frame,
            text="● No Progress Report Loaded — Upload your BYU Progress-to-Degree PDF to unlock personalized GE, Major, and Roadmap planning.",
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
            padx=20,
            pady=12,
        )
        self.student_summary_lbl.pack(fill="x")

        # 4-Metric Apple Bento Strip (Populated when report is loaded)
        self.metrics_row = ctk.CTkFrame(self.banner_frame, fg_color="transparent")
        self._metric_cards = []
        metric_specs = [
            ("COMPLETED CREDITS", "0.0 cr", "Standing: Freshman"),
            ("IN PROGRESS", "0.0 cr", "Active Semester"),
            ("REMAINING TO 120 CR", "120.0 cr", "Graduation Goal"),
            ("CUMULATIVE GPA", "0.00", "Official Audit GPA"),
        ]
        for idx, (m_label, m_val, m_sub) in enumerate(metric_specs):
            self.metrics_row.grid_columnconfigure(idx, weight=1)
            m_box = ctk.CTkFrame(
                self.metrics_row,
                fg_color=BG_LAYER_INSET,
                corner_radius=8,
                border_color=BORDER_SUBTLE,
                border_width=1,
            )
            m_box.grid(row=0, column=idx, sticky="nsew", padx=5, pady=(0, 12))

            ctk.CTkLabel(
                m_box,
                text=m_label,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=TEXT_MUTED,
                anchor="w",
            ).pack(fill="x", padx=14, pady=(10, 0))

            v_lbl = ctk.CTkLabel(
                m_box,
                text=m_val,
                font=ctk.CTkFont(size=17, family="Menlo", weight="bold"),
                text_color=TEXT_PRIMARY,
                anchor="w",
            )
            v_lbl.pack(fill="x", padx=14, pady=(2, 0))

            s_lbl = ctk.CTkLabel(
                m_box,
                text=m_sub,
                font=ctk.CTkFont(size=10),
                text_color=TEXT_SECONDARY,
                anchor="w",
            )
            s_lbl.pack(fill="x", padx=14, pady=(0, 10))
            self._metric_cards.append((v_lbl, s_lbl))

        # ---------------------------------------------------------------------
        # 3. Planning & Solver Modules
        # ---------------------------------------------------------------------
        ctk.CTkLabel(
            self,
            text="PLANNING & SOLVER MODULES",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=TEXT_MUTED,
            anchor="w",
        ).pack(fill="x", padx=4, pady=(0, 8))

        self._build_module_card(
            tag="SECTION DIRECTORY & COURSE-SPECIFIC RMP RATINGS",
            title="Catalog Lookup & Professor Reviews",
            desc="Search all BYU courses by code, title, or instructor. Instantly view course-specific RateMyProfessors scores, section times, and verified student reviews.",
            btn_text="Open Catalog ›",
            command=self.app.show_lookup_view,
        )

        self._build_module_card(
            tag="WEEKLY TIMETABLE PERMUTATION SOLVER",
            title="Conflict-Free Schedule Builder",
            desc="Generates collision-free weekly schedules from your staged courses with time-window constraints, minimum RMP rating filters, No-Friday mode, and a visual weekly calendar.",
            btn_text="Schedule Builder ›",
            command=self.app.show_builder_view,
        )

        self._build_module_card(
            tag="DEGREE AUDIT & TOP-5 GE RECOMMENDER",
            title="Smart Course Recommender",
            desc="Mirrors your BYU Progress-to-Degree audit across General Education, Religion, and Major requirements with collapsible top-5 highest-rated classes for every needed GE.",
            btn_text="Recommender ›",
            command=self.app.show_smart_view,
        )

        self._build_module_card(
            tag="MULTI-SEMESTER GRADUATION SEQUENCER",
            title="Degree Roadmap & Milestone Planner",
            desc="Sequences remaining major core requirements, GE credits, and religion courses into balanced full-time semesters until all degree requirements and 120+ credits are met.",
            btn_text="Open Roadmap ›",
            command=self.app.show_roadmap_view,
        )

        self.update_summary_display()

    def _build_module_card(self, tag: str, title: str, desc: str, btn_text: str, command):
        card = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=BG_SURFACE,
            border_color=BORDER_SUBTLE,
            border_width=1,
        )
        card.pack(fill="x", pady=(0, 10))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=15)

        left_col = ctk.CTkFrame(inner, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left_col,
            text=tag,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=BYU_ROYAL,
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            left_col,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(2, 3))

        ctk.CTkLabel(
            left_col,
            text=desc,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
            wraplength=640,
            justify="left",
            anchor="w",
        ).pack(fill="x")

        right_col = ctk.CTkFrame(inner, fg_color="transparent")
        right_col.pack(side="right", padx=(16, 0))

        ctk.CTkButton(
            right_col,
            text=btn_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=30,
            width=152,
            corner_radius=7,
            fg_color=BG_SURFACE_ALT,
            hover_color=BG_SURFACE_HOVER,
            border_color=BORDER_SUBTLE,
            border_width=1,
            text_color=TEXT_PRIMARY,
            command=command,
        ).pack(anchor="e")

    def update_summary_display(self):
        cat_len = len(getattr(self.app, "catalog", {}))
        if hasattr(self, "catalog_badge"):
            self.catalog_badge.configure(text=f"  {cat_len:,} Catalog Courses  ")

        profile = getattr(self.app, "student_profile", None)
        if not profile:
            return

        name = profile.get("student_name", "Student")
        major = profile.get("major", "Undeclared")
        credits_val = float(profile.get("credits", 0.0))
        ip_val = float(profile.get("in_progress_credits", 0.0))
        rem_val = float(profile.get("remaining_credits", max(0.0, 120.0 - credits_val - ip_val)))
        req_val = float(profile.get("required_credits", 120.0))
        gpa_val = profile.get("gpa", "0.00")
        standing = profile.get("standing", "Freshman")

        summary_str = (
            f"✓ Active Student: {name} | Major: {major} | "
            f"Standing: {standing} | Credits Earned: {credits_val:.1f} cr | "
            f"Cumulative GPA: {gpa_val}"
        )
        if hasattr(self, "student_summary_lbl"):
            self.student_summary_lbl.configure(
                text=summary_str,
                text_color=STATUS_ONLINE,
            )

        if hasattr(self, "metrics_row") and len(self._metric_cards) == 4:
            self.metrics_row.pack(fill="x", padx=15)
            pct = int(round((credits_val / req_val) * 100)) if req_val > 0 else 0
            self._metric_cards[0][0].configure(text=f"{credits_val:.1f} cr", text_color=STATUS_ONLINE)
            self._metric_cards[0][1].configure(text=f"{standing} Standing ({pct}% Complete)")

            self._metric_cards[1][0].configure(text=f"{ip_val:.1f} cr", text_color=BYU_ROYAL)
            self._metric_cards[1][1].configure(text=f"{len(profile.get('in_progress_courses', []))} Enrolled Courses")

            self._metric_cards[2][0].configure(text=f"{rem_val:.1f} cr", text_color=STATUS_WARNING if rem_val > 0 else STATUS_ONLINE)
            self._metric_cards[2][1].configure(text=f"of {req_val:.1f} cr Degree Goal")

            self._metric_cards[3][0].configure(text=str(gpa_val), text_color=TEXT_PRIMARY)
            self._metric_cards[3][1].configure(text=major)