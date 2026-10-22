import json
import os
import re
from tkinter import filedialog
import customtkinter as ctk

from audit_parser import parse_progress_report
from config import (
    BG_CANVAS,
    BG_SURFACE,
    BG_SURFACE_ALT,
    BORDER_SUBTLE,
    BYU_ROYAL,
    BYU_ROYAL_HOVER,
    BYU_ROYAL_SUBTLE,
    DEPT_DISPLAY_NAMES,
    STATUS_DANGER,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from views.builder_view import BuilderView
from views.home_view import HomeView
from views.lookup_view import LookupView
from views.roadmap_view import RoadmapView
from views.smart_view import SmartScheduleView


class BYUApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance & Window Configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("BYU Academic Course Suite & Schedule Solver")
        self.geometry("1280x820")
        self.minsize(1080, 700)
        self.configure(fg_color=BG_CANVAS)

        # Application State
        self.student_profile = None
        self.builder_staged_courses = []
        self.builder_dept_code = None
        self.builder_course_key = None

        # Load Course Catalog
        self.catalog = self._load_catalog()
        self.dept_to_courses = {}
        self.display_to_code = {}
        self.compact_to_catalog_key = {}
        self._build_department_mappings()

        # Build UI Layout
        self._create_header()
        self._create_main_container()

        # Instantiate View Singletons
        self.home_view = HomeView(self.container, self)
        self.lookup_view = LookupView(self.container, self)
        self.builder_view = BuilderView(self.container, self)
        self.smart_view = SmartScheduleView(self.container, self)
        self.roadmap_view = RoadmapView(self.container, self)

        # Set default view
        self.show_home_view()

    # -------------------------------------------------------------------------
    # Catalog & Department Indexing
    # -------------------------------------------------------------------------
    def _load_catalog(self) -> dict:
        candidates = [
            "byu_courses.json",
            "catalog.json",
            "data/byu_courses.json",
            "data/catalog.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return {}

    def _build_department_mappings(self):
        for course_key in self.catalog.keys():
            code = str(course_key).split(" - ")[0].strip()
            comp = code.replace(" ", "").upper()
            if comp and comp not in self.compact_to_catalog_key:
                self.compact_to_catalog_key[comp] = course_key

            m_dept = re.match(r"^([A-Z&\s]+?)\s+\d", code.upper())
            if m_dept:
                dept = " ".join(m_dept.group(1).split())
            else:
                dept = code.split()[0].upper() if code else "GENERAL"

            self.dept_to_courses.setdefault(dept, []).append(course_key)

        for dept in sorted(self.dept_to_courses.keys()):
            friendly = DEPT_DISPLAY_NAMES.get(dept, dept)
            display_label = f"{friendly} ({len(self.dept_to_courses[dept])} courses)"
            self.display_to_code[display_label] = dept

    def match_catalog_key(self, course_code: str) -> str:
        """Resolves a course code (e.g. 'CS 111', 'C S 111', 'MATH 290') to its exact catalog key."""
        if not course_code:
            return ""
        if course_code in self.catalog:
            return course_code
        comp = course_code.split(" - ")[0].replace(" ", "").upper()
        if comp in self.compact_to_catalog_key:
            return self.compact_to_catalog_key[comp]
        clean = " ".join(course_code.split()).upper()
        for k in self.catalog.keys():
            if k.upper().startswith(clean):
                return k
        return ""

    def get_satisfied_compact_codes(self) -> set:
        """Returns compact codes (e.g. 'CS111', 'MATH112') of completed and in-progress courses."""
        if not self.student_profile:
            return set()
        codes = set()
        for c in self.student_profile.get("completed_courses", []):
            codes.add(str(c).split(" - ")[0].replace(" ", "").upper())
        for c in self.student_profile.get("in_progress_courses", []):
            codes.add(str(c).split(" - ")[0].replace(" ", "").upper())
        return codes

    def is_course_satisfied(self, course_code_or_key: str) -> bool:
        """Checks if a course is already completed or currently in-progress."""
        if not course_code_or_key or not self.student_profile:
            return False
        comp = str(course_code_or_key).split(" - ")[0].replace(" ", "").upper()
        return comp in self.get_satisfied_compact_codes()

    def compute_dept_display_options(self) -> list:
        if not self.display_to_code:
            return ["No departments found"]
        return list(self.display_to_code.keys())

    def sync_staged_state(self):
        """Synchronizes staged course counters and button states across all views and the top nav."""
        cnt = len(self.builder_staged_courses)
        if hasattr(self, "nav_builder_btn"):
            lbl = f"Schedule Builder ({cnt})" if cnt > 0 else "Schedule Builder"
            self.nav_builder_btn.configure(text=lbl)
        if hasattr(self, "lookup_view"):
            self.lookup_view.update_staged_counter()
        if hasattr(self, "builder_view"):
            self.builder_view.render_staged_courses()
        if hasattr(self, "smart_view"):
            self.smart_view.refresh_staged_buttons()

    # -------------------------------------------------------------------------
    # Top Navigation Header (Apple macOS Segmented Pill Toolbar)
    # -------------------------------------------------------------------------
    def _create_header(self):
        self.header_frame = ctk.CTkFrame(
            self, height=60, corner_radius=0,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        self.header_frame.pack(side="top", fill="x")
        self.header_frame.pack_propagate(False)

        # Brand / Title
        brand_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        brand_box.pack(side="left", padx=(22, 24))

        brand_pill = ctk.CTkLabel(
            brand_box, text=" BYU ",
            font=ctk.CTkFont(size=12, family="Menlo", weight="bold"),
            fg_color=BYU_ROYAL_SUBTLE, text_color=BYU_ROYAL, corner_radius=6, height=26
        )
        brand_pill.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            brand_box, text="Academic Suite",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        # Segmented Pill Navigation Bar
        nav_pill_tray = ctk.CTkFrame(
            self.header_frame, fg_color=BG_CANVAS, corner_radius=9,
            border_color=BORDER_SUBTLE, border_width=1
        )
        nav_pill_tray.pack(side="left", pady=11)

        nav_inner = ctk.CTkFrame(nav_pill_tray, fg_color="transparent")
        nav_inner.pack(padx=3, pady=3)

        self.nav_home_btn = self._make_nav_btn(nav_inner, "Home", self.show_home_view, width=96)
        self.nav_lookup_btn = self._make_nav_btn(nav_inner, "Catalog Lookup", self.show_lookup_view, width=124)
        self.nav_builder_btn = self._make_nav_btn(nav_inner, "Schedule Builder", self.show_builder_view, width=142)
        self.nav_smart_btn = self._make_nav_btn(nav_inner, "Recommender", self.show_smart_view, width=118)
        self.nav_roadmap_btn = self._make_nav_btn(nav_inner, "Roadmap", self.show_roadmap_view, width=104)

        # Top-Right Actions & Upload Status Pill
        right_actions = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        right_actions.pack(side="right", padx=(0, 20))

        self.header_report_status_lbl = ctk.CTkLabel(
            right_actions, text=" ● No Report ",
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            fg_color=STATUS_WARNING_BG, text_color=STATUS_WARNING,
            corner_radius=6, height=28
        )
        self.header_report_status_lbl.pack(side="left", padx=(0, 10))

        self.header_upload_btn = ctk.CTkButton(
            right_actions, text="Upload Audit PDF",
            font=ctk.CTkFont(size=11, weight="bold"), height=30, width=132, corner_radius=7,
            fg_color=BYU_ROYAL, hover_color=BYU_ROYAL_HOVER,
            text_color="#FFFFFF", command=self.prompt_upload_record
        )
        self.header_upload_btn.pack(side="left")

    def _make_nav_btn(self, parent, text: str, command, width: int = 116):
        btn = ctk.CTkButton(
            parent, text=text, width=width, height=30, corner_radius=6,
            fg_color="transparent", hover_color=BG_SURFACE_ALT,
            text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=11, weight="bold"),
            command=command
        )
        btn.pack(side="left", padx=2)
        return btn

    def _highlight_nav_tab(self, active_btn):
        for btn in [
            self.nav_home_btn,
            self.nav_lookup_btn,
            self.nav_builder_btn,
            self.nav_smart_btn,
            self.nav_roadmap_btn,
        ]:
            if btn == active_btn:
                btn.configure(text_color=TEXT_PRIMARY, fg_color=BG_SURFACE_ALT)
            else:
                btn.configure(text_color=TEXT_SECONDARY, fg_color="transparent")

    # -------------------------------------------------------------------------
    # Main Content Area & View Router
    # -------------------------------------------------------------------------
    def _create_main_container(self):
        self.container = ctk.CTkFrame(self, fg_color=BG_CANVAS, corner_radius=0)
        self.container.pack(fill="both", expand=True, padx=18, pady=16)

    def _switch_view(self, target_view, nav_btn):
        for child in self.container.winfo_children():
            child.pack_forget()
        target_view.pack(fill="both", expand=True)
        self._highlight_nav_tab(nav_btn)

    def show_home_view(self):
        self._switch_view(self.home_view, self.nav_home_btn)

    def show_lookup_view(self):
        if hasattr(self, "lookup_view"):
            self.lookup_view.update_staged_counter()
        self._switch_view(self.lookup_view, self.nav_lookup_btn)

    def open_course_in_lookup(self, course_code: str):
        """Navigates to Catalog Lookup and immediately filters for the given course code."""
        self.show_lookup_view()
        if hasattr(self, "lookup_view"):
            self.lookup_view.lookup_course(course_code)

    def show_builder_view(self):
        if hasattr(self, "builder_view"):
            self.builder_view.refresh_department_courses()
            self.builder_view.render_staged_courses()
        self._switch_view(self.builder_view, self.nav_builder_btn)

    def show_smart_view(self):
        if hasattr(self, "smart_view"):
            self.smart_view.refresh_staged_buttons()
        self._switch_view(self.smart_view, self.nav_smart_btn)

    def show_roadmap_view(self):
        self._switch_view(self.roadmap_view, self.nav_roadmap_btn)

    # -------------------------------------------------------------------------
    # Unified Progress Report Handler
    # -------------------------------------------------------------------------
    def prompt_upload_record(self, file_path: str = None):
        """Unified audit report loader. Can be invoked directly or with a file_path."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select BYU Progress to Degree Report",
                filetypes=[
                    ("Degree Audit Files", "*.pdf *.txt"),
                    ("PDF Documents", "*.pdf"),
                    ("Text Files", "*.txt"),
                ],
            )

        if not file_path:
            return

        try:
            parsed = parse_progress_report(file_path)
            self.student_profile = parsed
            name = parsed.get("student_name", "Student")

            # Purge any staged courses that the student already completed or is currently taking
            self.builder_staged_courses = [
                k for k in self.builder_staged_courses if not self.is_course_satisfied(k)
            ]

            # Update top-right header status
            self.header_report_status_lbl.configure(
                text=f" ✓ {name} ", fg_color=STATUS_ONLINE_BG, text_color=STATUS_ONLINE
            )

            # Synchronize all views
            if hasattr(self, "home_view"):
                self.home_view.update_summary_display()
            if hasattr(self, "lookup_view"):
                self.lookup_view.filter_courses()
            if hasattr(self, "smart_view"):
                self.smart_view.run_advising_scan()
            if hasattr(self, "builder_view"):
                self.builder_view.refresh_department_courses()
            if hasattr(self, "roadmap_view"):
                self.roadmap_view.generate_roadmap()

            self.sync_staged_state()

        except Exception as e:
            print(f"[-] Failed to parse progress report: {e}")
            self.header_report_status_lbl.configure(
                text=" ● Parse Error ", text_color=STATUS_DANGER
            )


if __name__ == "__main__":
    app = BYUApp()
    app.mainloop()