import customtkinter as ctk
from config import (
    BG_CANVAS,
    BG_LAYER_INSET,
    BG_SURFACE,
    BG_SURFACE_ALT,
    BG_SURFACE_HOVER,
    BORDER_SUBTLE,
    BYU_ROYAL,
    BYU_ROYAL_SUBTLE,
    COURSE_COLORS,
    STATUS_ONLINE,
    STATUS_ONLINE_BG,
    STATUS_WARNING,
    STATUS_WARNING_BG,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from schedule_solver import parse_days
from scroll_engine import enable_smooth_scroll


class CalendarModal(ctk.CTkToplevel):
    def __init__(self, master, schedule_data: dict, schedule_number: int):
        super().__init__(master)
        self.title(f"Weekly Grid — Option #{schedule_number}")
        self.geometry("1000x740")
        self.minsize(860, 600)
        self.configure(fg_color=BG_CANVAS)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(16, 10))

        ctk.CTkLabel(
            hdr, text=f"Weekly Calendar — Schedule Option #{schedule_number}",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_PRIMARY
        ).pack(side="left")

        total_cr = schedule_data.get("total_credits", 0.0)
        if total_cr > 0:
            ctk.CTkLabel(
                hdr, text=f"  {total_cr:.1f} Credits  ",
                font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
                fg_color=BYU_ROYAL_SUBTLE, text_color=BYU_ROYAL, corner_radius=5, height=24
            ).pack(side="left", padx=12)

        ctk.CTkButton(
            hdr, text="Done", width=68, height=26, corner_radius=6,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
            border_color=BORDER_SUBTLE, border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY,
            command=self.destroy
        ).pack(side="right", padx=(10, 0))

        score_val = float(schedule_data.get("avg_score", 0.0))
        if score_val >= 4.0:
            badge_bg, badge_fg = STATUS_ONLINE_BG, STATUS_ONLINE
        elif score_val >= 3.0:
            badge_bg, badge_fg = STATUS_WARNING_BG, STATUS_WARNING
        else:
            badge_bg, badge_fg = BG_SURFACE_ALT, TEXT_MUTED

        score_txt = f"  {score_val:.2f}★ Avg Rating  " if score_val > 0 else "  Unrated  "
        ctk.CTkLabel(
            hdr, text=score_txt,
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            fg_color=badge_bg, text_color=badge_fg, corner_radius=5, height=24
        ).pack(side="right")

        canvas_card = ctk.CTkFrame(
            self, corner_radius=10,
            fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        canvas_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = ctk.CTkCanvas(canvas_card, bg=BG_SURFACE, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=12)

        self.schedule_sections = schedule_data.get("sections", [])
        self.color_map = {}
        for sec in self.schedule_sections:
            c_name = sec.get("course", "")
            if c_name not in self.color_map:
                self.color_map[c_name] = COURSE_COLORS[len(self.color_map) % len(COURSE_COLORS)]

        self.canvas.bind("<Configure>", lambda e: self.draw_calendar())

    def draw_calendar(self):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 200 or h < 200:
            return

        time_col_w, header_h = 68, 36
        days = [("M", "Monday"), ("T", "Tuesday"), ("W", "Wednesday"), ("Th", "Thursday"), ("F", "Friday")]
        col_w = (w - time_col_w - 16) / len(days)

        # Dynamically adjust end hour if any class/lab extends past 6:00 PM
        max_end_min = 18 * 60
        min_start_min = 8 * 60
        for sec in self.schedule_sections:
            for slot in [sec, sec.get("lecture") or {}, sec.get("lab") or {}]:
                em = slot.get("end_min", -1)
                sm = slot.get("start_min", -1)
                if em > max_end_min:
                    max_end_min = em
                if 0 < sm < min_start_min:
                    min_start_min = sm

        start_hr = max(7, min(8, min_start_min // 60))
        end_hr = max(18, min(22, (max_end_min + 59) // 60))
        total_mins = (end_hr - start_hr) * 60
        grid_h = h - header_h - 18

        # Day Headers
        for i, (_, day_name) in enumerate(days):
            x1 = time_col_w + i * col_w
            x2 = x1 + col_w
            self.canvas.create_rectangle(x1, 0, x2, header_h, fill=BG_SURFACE_ALT, outline=BORDER_SUBTLE)
            self.canvas.create_text(
                (x1 + x2) / 2, header_h / 2,
                text=day_name, fill=TEXT_PRIMARY, font=("SF Pro Text", 11, "bold")
            )

        # Hourly Grid Lines
        for hr in range(start_hr, end_hr + 1):
            min_offset = (hr - start_hr) * 60
            y = header_h + (min_offset / total_mins) * grid_h
            time_str = f"{12 if hr == 12 else (hr % 12)}:00 {'AM' if hr < 12 else 'PM'}"
            self.canvas.create_text(time_col_w / 2, y, text=time_str, fill=TEXT_MUTED, font=("Menlo", 9))
            self.canvas.create_line(time_col_w, y, w - 10, y, fill=BORDER_SUBTLE, width=1)

        # Vertical Column Lines
        for i in range(len(days) + 1):
            x = time_col_w + i * col_w
            self.canvas.create_line(x, header_h, x, header_h + grid_h, fill=BORDER_SUBTLE, width=1)

        # Course Blocks
        day_to_idx = {"M": 0, "T": 1, "W": 2, "Th": 3, "F": 4}
        for sec in self.schedule_sections:
            course = sec.get("course", "Course")
            short_title = course.split(" - ")[0] if " - " in course else course
            inst = sec.get("instructor", "")
            fill_color = self.color_map.get(course, BYU_ROYAL)

            active_slots = []
            lec = sec.get("lecture")
            if lec and lec.get("days") != "TBA":
                active_slots.append((lec, short_title))
            elif sec.get("days") != "TBA":
                active_slots.append((sec, short_title))

            lab = sec.get("lab")
            if lab and lab.get("days") != "TBA":
                active_slots.append((lab, f"{short_title} Lab"))

            for slot_info, title_label in active_slots:
                start_m, end_m = slot_info.get("start_min", -1), slot_info.get("end_min", -1)
                loc = slot_info.get("location", "")
                t_range = f"{slot_info.get('start_time', '')}–{slot_info.get('end_time', '')}"
                if start_m == -1 or end_m == -1:
                    continue

                y1 = header_h + ((start_m - start_hr * 60) / total_mins) * grid_h
                y2 = header_h + ((end_m - start_hr * 60) / total_mins) * grid_h

                for d in parse_days(slot_info.get("days", "")):
                    if d in day_to_idx:
                        d_idx = day_to_idx[d]
                        x1 = time_col_w + d_idx * col_w + 4
                        x2 = x1 + col_w - 8
                        self.canvas.create_rectangle(
                            x1, y1, x2, y2,
                            fill=fill_color, outline="#FFFFFF", width=1
                        )
                        mid_x = (x1 + x2) / 2
                        block_h = y2 - y1
                        if block_h >= 28:
                            self.canvas.create_text(
                                mid_x, y1 + 11, text=title_label,
                                fill="#FFFFFF", font=("SF Pro Text", 10, "bold")
                            )
                        if block_h >= 42:
                            sub_meta = f"{loc}" if loc and loc != "TBA" else t_range
                            self.canvas.create_text(
                                mid_x, y1 + 24, text=sub_meta,
                                fill="#E2E8F0", font=("Menlo", 8)
                            )
                        if block_h >= 56 and inst:
                            self.canvas.create_text(
                                mid_x, y1 + 37, text=inst,
                                fill="#F1F5F9", font=("SF Pro Text", 8)
                            )


class ReviewsModal(ctk.CTkToplevel):
    def __init__(self, master, instructor_name: str, rmp_data: dict, current_course: str):
        super().__init__(master)
        target_code = rmp_data.get("target_course_label") or current_course.split(" - ")[0]
        self.title(f"{target_code} Reviews — {instructor_name}")
        self.geometry("760x640")
        self.minsize(640, 480)
        self.configure(fg_color=BG_CANVAS)
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 6))

        ctk.CTkLabel(
            hdr,
            text=f"{instructor_name}  •  {target_code}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="Done", width=64, height=26, corner_radius=6,
            fg_color=BG_SURFACE_ALT, hover_color=BG_SURFACE_HOVER,
            border_color=BORDER_SUBTLE, border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_PRIMARY,
            command=self.destroy
        ).pack(side="right", padx=(10, 0))

        score_val = float(rmp_data.get("score_val", 0.0))
        badge_bg = STATUS_ONLINE_BG if score_val >= 4.0 else (STATUS_WARNING_BG if score_val >= 3.0 else BG_SURFACE_ALT)
        badge_fg = STATUS_ONLINE if score_val >= 4.0 else (STATUS_WARNING if score_val >= 3.0 else TEXT_MUTED)

        score_badge = ctk.CTkLabel(
            hdr,
            text=f"  {rmp_data.get('rating', 'N/A')} / 5.0 ({target_code} Only)  ",
            font=ctk.CTkFont(size=11, family="Menlo", weight="bold"),
            fg_color=badge_bg,
            text_color=badge_fg,
            corner_radius=6,
            height=26,
        )
        score_badge.pack(side="right")

        displayed_reviews = rmp_data.get("reviews", [])

        sub_bar = ctk.CTkFrame(self, fg_color="transparent")
        sub_bar.pack(fill="x", padx=24, pady=(0, 12))

        scope_text = f"✓ {len(displayed_reviews)} verified student review(s) strictly for {target_code} (Offline Cache)"
        ctk.CTkLabel(sub_bar, text=scope_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=STATUS_ONLINE).pack(side="left")
        ctk.CTkLabel(
            sub_bar,
            text=f"{target_code} Difficulty: {rmp_data.get('difficulty', 'N/A')} / 5.0",
            font=ctk.CTkFont(size=11, family="Menlo"),
            text_color=TEXT_MUTED,
        ).pack(side="right")

        facts = rmp_data.get("course_facts", {})
        summary_box = ctk.CTkFrame(
            self, fg_color=BG_SURFACE, corner_radius=8, border_color=BORDER_SUBTLE, border_width=1
        )
        summary_box.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            summary_box,
            text=f"Course-Specific Syllabus Consensus ({target_code}):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w", padx=14, pady=(10, 4))
        m_str = f"~{facts.get('est_midterms')} exams" if facts.get("est_midterms") else "Not mentioned"
        p_str = f"~{facts.get('est_papers')} papers" if facts.get("est_papers") else "Not mentioned"
        ec_str = "Yes" if facts.get("has_extra_credit") else "None mentioned"
        att_str = "Mandatory" if facts.get("attendance_mandatory") else "Flexible / Unspecified"
        fact_line = f"Midterms: {m_str}   •   Papers: {p_str}   •   Exam Policy: {facts.get('exam_policy', 'Unspecified')}\nExtra Credit: {ec_str}   •   Attendance: {att_str}"
        ctk.CTkLabel(
            summary_box,
            text=fact_line,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 10))

        reviews_scroll = ctk.CTkScrollableFrame(
            self, corner_radius=8, fg_color=BG_SURFACE, border_color=BORDER_SUBTLE, border_width=1
        )
        reviews_scroll.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        enable_smooth_scroll(reviews_scroll)

        if not displayed_reviews:
            ctk.CTkLabel(
                reviews_scroll,
                text=f"No written student reviews on record for {instructor_name} in {target_code}.",
                font=ctk.CTkFont(size=12),
                text_color=TEXT_MUTED,
            ).pack(pady=40)
            return

        for rev in displayed_reviews:
            card = ctk.CTkFrame(reviews_scroll, fg_color=BG_LAYER_INSET, corner_radius=8, border_color=BORDER_SUBTLE, border_width=1)
            card.pack(fill="x", pady=5, padx=4)

            top_meta = ctk.CTkFrame(card, fg_color="transparent")
            top_meta.pack(fill="x", padx=12, pady=(8, 2))
            q_val = round((float(rev.get("helpful", 0)) + float(rev.get("clarity", 0))) / 2.0, 1)
            ctk.CTkLabel(
                top_meta,
                text=f"{target_code}  ({rev.get('course', target_code)})  •  {q_val:.1f}★",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=TEXT_PRIMARY,
            ).pack(side="left")

            date_raw = (rev.get("date") or "")[:10]
            date_part = f"  •  {date_raw}" if date_raw else ""
            ctk.CTkLabel(
                top_meta,
                text=f"Grade: {rev.get('grade') or 'N/A'}  •  Diff: {rev.get('difficulty', 0.0):.1f}{date_part}",
                font=ctk.CTkFont(size=10, family="Menlo"),
                text_color=TEXT_MUTED,
            ).pack(side="right")

            if rev.get("tags"):
                ctk.CTkLabel(
                    card,
                    text=f"Tags: {' • '.join(rev['tags'])}",
                    font=ctk.CTkFont(size=10),
                    text_color=BYU_ROYAL,
                    anchor="w",
                ).pack(fill="x", padx=12, pady=(0, 4))
            ctk.CTkLabel(
                card,
                text=rev.get("comment", ""),
                font=ctk.CTkFont(size=12),
                text_color=TEXT_SECONDARY,
                wraplength=650,
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=12, pady=(0, 10))