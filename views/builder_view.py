import itertools
import threading
import tkinter as tk
from typing import List
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
    STATUS_DANGER,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from rmp_client import fetch_rmp_profile
from schedule_solver import is_conflict_free, section_matches_preferences
from scroll_engine import enable_smooth_scroll
from views.modals import CalendarModal, ReviewsModal


def _parse_time_str_to_min(time_str: str) -> int:
    """Converts strings like '8:00 AM' or '2:30 PM' to minutes from midnight."""
    if not time_str or time_str == "Any Time":
        return -1
    try:
        parts = time_str.strip().split()
        if len(parts) != 2:
            return -1
        hm, ampm = parts[0], parts[1].upper()
        h, m = map(int, hm.split(":"))
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
        return h * 60 + m
    except Exception:
        return -1


def _parse_min_rating(rating_str: str) -> float:
    if not rating_str or rating_str == "Any Rating":
        return 0.0
    try:
        return float(rating_str.split("★")[0].strip())
    except Exception:
        return 0.0


class BuilderView(ctk.CTkFrame):
    def __init__(self, master, app_controller):
        super().__init__(master, fg_color="transparent")
        self.app = app_controller

        # Left Sidebar (Apple macOS Inspector Style)
        sidebar = ctk.CTkFrame(
            self, width=368, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="TIMETABLE SOLVER",
            font=ctk.CTkFont(size=10, weight="bold"), text_color=BYU_ROYAL
        ).pack(anchor="w", padx=20, pady=(20, 2))

        ctk.CTkLabel(
            sidebar, text="Schedule Configuration",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Staged Courses Title, Credit Counter & Clear All Button
        staged_hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        staged_hdr.pack(fill="x", padx=20, pady=(0, 4))

        ctk.CTkLabel(
            staged_hdr, text="STAGED COURSES",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(side="left")

        self.clear_all_btn = ctk.CTkButton(
            staged_hdr, text="Clear All", width=58, height=20, corner_radius=5,
            fg_color="transparent", hover_color=BG_SURFACE_HOVER,
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=10, weight="bold"),
            command=self.clear_staged_courses
        )
        self.clear_all_btn.pack(side="right", padx=(6, 0))

        self.staged_credits_lbl = ctk.CTkLabel(
            staged_hdr, text="0.0 cr Total",
            font=ctk.CTkFont(size=10, family="Menlo", weight="bold"), text_color=BYU_ROYAL
        )
        self.staged_credits_lbl.pack(side="right")

        # Staged Course List Frame
        self.staged_frame = ctk.CTkFrame(
            sidebar, height=136, corner_radius=8,
            fg_color=BG_LAYER_INSET, border_color=BORDER_SUBTLE, border_width=1
        )
        self.staged_frame.pack(fill="x", padx=20, pady=(0, 14))
        self.staged_frame.pack_propagate(False)

        self.staged_scroll = ctk.CTkScrollableFrame(self.staged_frame, fg_color="transparent")
        self.staged_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        enable_smooth_scroll(self.staged_scroll)

        # Department & Course Selection
        ctk.CTkLabel(
            sidebar, text="ADD COURSE MANUALLY",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        self.dept_dropdown = ctk.CTkOptionMenu(
            sidebar, values=self.app.compute_dept_display_options(), command=self._on_dept_selected,
            height=32, corner_radius=7, fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, dynamic_resizing=False
        )
        self.dept_dropdown.pack(fill="x", padx=20, pady=(0, 6))

        self.course_dropdown = ctk.CTkOptionMenu(
            sidebar, values=["Select Department"], command=self._on_course_selected,
            height=32, corner_radius=7, fg_color=BG_SURFACE_ALT, button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, dynamic_resizing=False
        )
        self.course_dropdown.pack(fill="x", padx=20, pady=(0, 8))

        self.add_btn = ctk.CTkButton(
            sidebar, text="+ Add Course to Builder",
            font=ctk.CTkFont(size=11, weight="bold"), height=32, corner_radius=7,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER, border_color=BORDER_SUBTLE, border_width=1,
            text_color=TEXT_PRIMARY, command=self.add_course
        )
        self.add_btn.pack(fill="x", padx=20, pady=(0, 14))

        # Constraints & Preferences
        ctk.CTkLabel(
            sidebar, text="CONSTRAINTS & PREFERENCES",
            font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_MUTED
        ).pack(anchor="w", padx=20, pady=(0, 4))

        time_box = ctk.CTkFrame(
            sidebar, fg_color=BG_SURFACE_ALT, corner_radius=8,
            border_color=BORDER_SUBTLE, border_width=1
        )
        time_box.pack(fill="x", padx=20, pady=(0, 12))

        time_inner = ctk.CTkFrame(time_box, fg_color="transparent")
        time_inner.pack(fill="x", padx=12, pady=8)
        time_inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(time_inner, text="Earliest class:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=3)
        self.start_time_menu = ctk.CTkOptionMenu(
            time_inner, values=["Any Time", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM"],
            height=26, width=132, corner_radius=6, fg_color=BG_LAYER_INSET, button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY
        )
        self.start_time_menu.grid(row=0, column=1, sticky="e", pady=3)

        ctk.CTkLabel(time_inner, text="Latest class:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(row=1, column=0, sticky="w", pady=3)
        self.end_time_menu = ctk.CTkOptionMenu(
            time_inner, values=["Any Time", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"],
            height=26, width=132, corner_radius=6, fg_color=BG_LAYER_INSET, button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY
        )
        self.end_time_menu.grid(row=1, column=1, sticky="e", pady=3)

        ctk.CTkLabel(time_inner, text="Min RMP rating:", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=3)
        self.min_rating_menu = ctk.CTkOptionMenu(
            time_inner, values=["Any Rating", "3.0★+", "3.5★+", "4.0★+"],
            height=26, width=132, corner_radius=6, fg_color=BG_LAYER_INSET, button_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY
        )
        self.min_rating_menu.grid(row=2, column=1, sticky="e", pady=3)

        self.no_friday_var = ctk.BooleanVar(value=False)
        self.no_friday_check = ctk.CTkCheckBox(
            sidebar, text="No Friday Classes (3-day weekend)",
            variable=self.no_friday_var, font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY, fg_color=BYU_ROYAL, corner_radius=5
        )
        self.no_friday_check.pack(anchor="w", padx=20, pady=(0, 14))

        # Solve Action
        self.solve_btn = ctk.CTkButton(
            sidebar, text="Solve Non-Conflicting Schedules",
            font=ctk.CTkFont(size=12, weight="bold"), height=36, corner_radius=8,
            fg_color=BYU_ROYAL, hover_color=BYU_ROYAL_HOVER,
            command=self.start_schedule_solving
        )
        self.solve_btn.pack(fill="x", padx=20, pady=(0, 8))

        self.builder_status = ctk.CTkLabel(
            sidebar, text="Stage at least 2 courses to solve.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED, wraplength=328, justify="left"
        )
        self.builder_status.pack(fill="x", padx=20)

        # Right Panel (Permutations)
        right_panel = ctk.CTkFrame(
            self, corner_radius=12,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        right_panel.pack(side="right", fill="both", expand=True)

        hdr_bar = ctk.CTkFrame(right_panel, fg_color="transparent")
        hdr_bar.pack(fill="x", padx=24, pady=(18, 10))

        self.results_title = ctk.CTkLabel(
            hdr_bar, text="Optimal Schedule Permutations",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_PRIMARY
        )
        self.results_title.pack(side="left")

        self.scroll_area = ctk.CTkScrollableFrame(right_panel, corner_radius=8, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        enable_smooth_scroll(self.scroll_area)

        # Sync staged list from controller
        self.render_staged_courses()
        self._render_empty_prompt()

        initial = self.app.compute_dept_display_options()
        if initial and initial[0] != "No departments found":
            first_choice = initial[0] if initial[0] != "──────────" else initial[1]
            self.dept_dropdown.set(first_choice)
            self._on_dept_selected(first_choice)

    def _render_empty_prompt(self):
        if self.scroll_area.winfo_children():
            return
        ctk.CTkLabel(
            self.scroll_area,
            text="Stage 2 or more courses from the Recommender, Roadmap, or Catalog Lookup,\nthen click 'Solve Non-Conflicting Schedules' to generate ranked weekly timetables.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED,
            justify="center",
        ).pack(pady=60)

    def _estimate_credits(self, course_key: str) -> float:
        sections = self.app.catalog.get(course_key, [])
        if sections and "credit_hours" in sections[0]:
            try:
                return float(sections[0]["credit_hours"])
            except Exception:
                pass
        code = course_key.split(" - ")[0]
        if code.startswith("REL"):
            return 2.0
        if "191" in code or "215" in code:
            return 1.0
        if any(c in code for c in ["112", "113"]):
            return 4.0
        return 3.0

    def clear_staged_courses(self):
        if not self.app.builder_staged_courses:
            return
        self.app.builder_staged_courses.clear()
        self.builder_status.configure(text="Cleared all staged courses.", text_color=TEXT_MUTED)
        if hasattr(self.app, "sync_staged_state"):
            self.app.sync_staged_state()

    def render_staged_courses(self):
        if hasattr(self.app, "is_course_satisfied") and self.app.student_profile:
            filtered_staged = [
                k for k in self.app.builder_staged_courses if not self.app.is_course_satisfied(k)
            ]
            if len(filtered_staged) != len(self.app.builder_staged_courses):
                self.app.builder_staged_courses = filtered_staged
                self.builder_status.configure(
                    text="Filtered out completed/in-progress courses from staged list.",
                    text_color=STATUS_WARNING
                )

        for w in self.staged_scroll.winfo_children():
            w.destroy()

        total_staged_credits = sum(self._estimate_credits(k) for k in self.app.builder_staged_courses)
        self.staged_credits_lbl.configure(
            text=f"{total_staged_credits:.1f} cr Total",
            text_color=STATUS_ONLINE if total_staged_credits >= 12.0 else BYU_ROYAL
        )

        if not self.app.builder_staged_courses:
            ctk.CTkLabel(
                self.staged_scroll, text="No courses staged yet. Add courses below or from the Recommender.",
                font=ctk.CTkFont(size=10), text_color=TEXT_MUTED, wraplength=290, justify="left"
            ).pack(padx=6, pady=10, anchor="w")
            return

        for course_key in self.app.builder_staged_courses:
            row = ctk.CTkFrame(self.staged_scroll, fg_color=BG_SURFACE_ALT, corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            cr_val = self._estimate_credits(course_key)
            parts = course_key.split(" - ")
            short_name = parts[0]
            sub_title = parts[1][:22] + ("…" if len(parts[1]) > 22 else "") if len(parts) > 1 else ""

            ctk.CTkLabel(
                row, text=f" {short_name}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY
            ).pack(side="left", padx=(6, 4), pady=4)

            if sub_title:
                ctk.CTkLabel(
                    row, text=sub_title,
                    font=ctk.CTkFont(size=10), text_color=TEXT_MUTED
                ).pack(side="left")

            ctk.CTkButton(
                row, text="✕", width=22, height=20, corner_radius=4,
                fg_color="transparent", hover_color=BG_SURFACE_HOVER, text_color=STATUS_DANGER,
                font=ctk.CTkFont(size=10, weight="bold"),
                command=lambda k=course_key: self.remove_course(k)
            ).pack(side="right", padx=(2, 4))

            ctk.CTkLabel(
                row, text=f"{cr_val:.1f} cr",
                font=ctk.CTkFont(size=10, family="Menlo"), text_color=TEXT_SECONDARY
            ).pack(side="right", padx=4)

    def add_course(self):
        key = self.app.builder_course_key
        if not key or key in {"No matching courses", "All courses completed/enrolled"}:
            return
        if hasattr(self.app, "is_course_satisfied") and self.app.is_course_satisfied(key):
            self.builder_status.configure(
                text=f"{key.split(' - ')[0]} is already completed or in progress.",
                text_color=STATUS_WARNING
            )
            return
        if key not in self.app.builder_staged_courses:
            self.app.builder_staged_courses.append(key)
            self.builder_status.configure(
                text=f"Added {key.split(' - ')[0]} to staged courses.",
                text_color=STATUS_ONLINE
            )
            if hasattr(self.app, "sync_staged_state"):
                self.app.sync_staged_state()

    def remove_course(self, key: str):
        if key in self.app.builder_staged_courses:
            self.app.builder_staged_courses.remove(key)
            if hasattr(self.app, "sync_staged_state"):
                self.app.sync_staged_state()

    def refresh_department_courses(self):
        """Refreshes the course dropdown for the currently selected department, excluding satisfied courses."""
        current_dept = self.dept_dropdown.get()
        if current_dept:
            self._on_dept_selected(current_dept)

    def _on_dept_selected(self, chosen: str):
        if chosen in {"──────────", "No departments found"}:
            return
        code = self.app.display_to_code.get(chosen)
        if not code:
            return
        self.app.builder_dept_code = code
        raw_courses = self.app.dept_to_courses.get(code, [])
        if hasattr(self.app, "is_course_satisfied") and self.app.student_profile:
            courses = [c for c in raw_courses if not self.app.is_course_satisfied(c)]
        else:
            courses = list(raw_courses)

        if courses:
            self.course_dropdown.configure(values=courses, state="normal")
            self.course_dropdown.set(courses[0])
            self.app.builder_course_key = courses[0]
        else:
            msg = "All courses completed/enrolled" if raw_courses else "No matching courses"
            self.course_dropdown.configure(values=[msg], state="disabled")
            self.course_dropdown.set(msg)
            self.app.builder_course_key = None

    def _on_course_selected(self, chosen: str):
        if chosen not in {"No matching courses", "All courses completed/enrolled"}:
            self.app.builder_course_key = chosen

    def start_schedule_solving(self):
        if len(self.app.builder_staged_courses) < 2:
            self.builder_status.configure(text="Please stage at least 2 courses.", text_color=STATUS_DANGER)
            return

        self.solve_btn.configure(state="disabled", text="Solving Constraints...")
        self.builder_status.configure(text="Resolving interval overlaps & course-specific ratings...", text_color=BYU_ROYAL)

        for w in self.scroll_area.winfo_children():
            w.destroy()

        start_sel = self.start_time_menu.get()
        end_sel = self.end_time_menu.get()
        min_start_m = _parse_time_str_to_min(start_sel)
        max_end_m = _parse_time_str_to_min(end_sel)
        min_score = _parse_min_rating(self.min_rating_menu.get())
        no_fridays = self.no_friday_var.get()

        threading.Thread(
            target=self._worker,
            args=(min_start_m, max_end_m, no_fridays, min_score),
            daemon=True
        ).start()

    def _worker(self, min_start_m: int, max_end_m: int, no_fridays: bool, min_score: float):
        staged = list(self.app.builder_staged_courses)
        total_sched_credits = sum(self._estimate_credits(c) for c in staged)

        profiles_map = {}
        for c in staged:
            for s in self.app.catalog.get(c, []):
                inst = s.get("instructor")
                key = f"{inst}::{c}"
                if inst and key not in profiles_map:
                    profiles_map[key] = fetch_rmp_profile(inst, target_course=c)

        pools = []
        for c in staged:
            raw_secs = self.app.catalog.get(c, [])
            valid_secs = []
            for s in raw_secs:
                prof_data = profiles_map.get(f"{s.get('instructor', '')}::{c}", {})
                copy_s = dict(s)
                copy_s["course"] = c
                copy_s["score"] = float(prof_data.get("score_val", 0.0))
                copy_s["rmp_raw"] = prof_data
                if section_matches_preferences(copy_s, min_start_m, max_end_m, no_fridays, min_score):
                    valid_secs.append(copy_s)

            valid_secs.sort(key=lambda x: x["score"], reverse=True)
            unique_slots = []
            seen_slots = set()
            for v in valid_secs:
                sig = f"{v.get('days')}_{v.get('start_time')}_{v.get('instructor')}"
                if sig not in seen_slots:
                    seen_slots.add(sig)
                    unique_slots.append(v)
                if len(unique_slots) >= 4:
                    break

            if unique_slots:
                pools.append(unique_slots)

        if len(pools) < len(staged):
            self.after(0, lambda: self._render([], total_sched_credits,
                                               "One or more staged courses have no sections meeting your time or rating filters."))
            return

        valid_permutations = []
        for combo in itertools.product(*pools):
            if is_conflict_free(combo):
                rated_scores = [item["score"] for item in combo if item["score"] > 0]
                avg_r = round(sum(rated_scores) / len(rated_scores), 2) if rated_scores else 0.0
                valid_permutations.append({
                    "sections": combo,
                    "avg_score": avg_r,
                    "total_credits": total_sched_credits
                })

        valid_permutations.sort(key=lambda x: x["avg_score"], reverse=True)
        self.after(0, lambda: self._render(valid_permutations[:10], total_sched_credits))

    def _render(self, schedules: List[dict], total_credits: float, error_msg: str = ""):
        self.solve_btn.configure(state="normal", text="Solve Non-Conflicting Schedules")

        if not schedules:
            self.builder_status.configure(text="No collision-free permutations.", text_color=STATUS_DANGER)
            ctk.CTkLabel(
                self.scroll_area,
                text=error_msg or "All section combinations had overlapping times. Try relaxing your time or rating constraints.",
                font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, wraplength=480, justify="center"
            ).pack(pady=40)
            return

        self.builder_status.configure(
            text=f"Found {len(schedules)} conflict-free schedule(s) ({total_credits:.1f} cr).",
            text_color=STATUS_ONLINE
        )

        for rank, sched in enumerate(schedules, start=1):
            card = ctk.CTkFrame(
                self.scroll_area, corner_radius=10,
                fg_color=BG_SURFACE_ALT, border_color=BORDER_SUBTLE, border_width=1
            )
            card.pack(fill="x", pady=6, padx=2)

            hdr = tk.Frame(card, bg=BG_SURFACE_ALT, bd=0, highlightthickness=0)
            hdr.pack(fill="x", padx=16, pady=(12, 6))

            ctk.CTkLabel(
                hdr, text=f"Option #{rank}",
                font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT_PRIMARY
            ).pack(side="left")

            ft_label = " (Full-Time)" if sched["total_credits"] >= 12.0 else ""
            cr_pill = ctk.CTkLabel(
                hdr, text=f"  {sched['total_credits']:.1f} Credits{ft_label}  ",
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                fg_color=BYU_ROYAL_SUBTLE, text_color=BYU_ROYAL, corner_radius=5, height=22
            )
            cr_pill.pack(side="left", padx=10)

            score_val = sched["avg_score"]
            if score_val >= 4.0:
                badge_bg, badge_fg = STATUS_ONLINE_BG, STATUS_ONLINE
            elif score_val >= 3.0:
                badge_bg, badge_fg = STATUS_WARNING_BG, STATUS_WARNING
            else:
                badge_bg, badge_fg = BG_LAYER_INSET, TEXT_MUTED

            score_txt = f"  {score_val:.2f}★ Avg RMP  " if score_val > 0 else "  Unrated  "
            ctk.CTkLabel(
                hdr, text=score_txt,
                font=ctk.CTkFont(size=10, family="Menlo", weight="bold"),
                fg_color=badge_bg, text_color=badge_fg, corner_radius=5, height=22
            ).pack(side="right")

            cal_btn = ctk.CTkButton(
                hdr, text="Weekly Calendar ↗", width=124, height=24, corner_radius=6,
                fg_color=BG_LAYER_INSET, hover_color=BG_SURFACE_HOVER, border_color=BORDER_SUBTLE, border_width=1,
                font=ctk.CTkFont(size=10, weight="bold"), text_color=TEXT_PRIMARY,
                command=lambda s=sched, r=rank: CalendarModal(self, s, r)
            )
            cal_btn.pack(side="right", padx=(0, 8))

            grid_box = ctk.CTkFrame(
                card, fg_color=BG_LAYER_INSET, corner_radius=8,
                border_color=BORDER_SUBTLE, border_width=1
            )
            grid_box.pack(fill="x", padx=14, pady=(4, 12))

            for s in sched["sections"]:
                row = tk.Frame(grid_box, bg=BG_LAYER_INSET, bd=0, highlightthickness=0)
                row.pack(fill="x", padx=12, pady=4)

                c_code = s["course"].split(" - ")[0]
                ctk.CTkLabel(
                    row, text=c_code,
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=BYU_ROYAL,
                    width=88, anchor="w"
                ).pack(side="left")

                inst_name = s.get("instructor", "Staff")
                sc = s.get("score", 0.0)
                sc_str = f"{sc:.1f}★" if sc > 0 else "Unrated"
                ctk.CTkLabel(
                    row, text=f"{inst_name} ({sc_str})",
                    font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY,
                    width=185, anchor="w"
                ).pack(side="left")

                loc = s.get("location", "")
                loc_str = f" ({loc})" if loc and loc != "TBA" else ""
                time_str = f"Sec {s.get('section', '001')} • {s.get('days', 'TBA')} {s.get('start_time', '')}–{s.get('end_time', '')}{loc_str}"
                if s.get("lab"):
                    lab = s["lab"]
                    time_str += f"  |  Lab {lab.get('days', '')} {lab.get('start_time', '')}–{lab.get('end_time', '')}"

                ctk.CTkLabel(
                    row, text=time_str,
                    font=ctk.CTkFont(size=10, family="Menlo"), text_color=TEXT_MUTED,
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)

                rmp_raw = s.get("rmp_raw") or {}
                revs = rmp_raw.get("reviews", [])
                if inst_name != "Staff" and revs:
                    ctk.CTkButton(
                        row, text=f"Reviews ({len(revs)})", width=82, height=22, corner_radius=5,
                        fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
                        border_color=BORDER_SUBTLE, border_width=1,
                        text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=10, weight="bold"),
                        command=lambda i=inst_name, r_data=rmp_raw, ck=s["course"]: ReviewsModal(self, i, r_data, ck)
                    ).pack(side="right")