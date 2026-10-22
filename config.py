COURSES_FILE = "byu_courses.json"

# Apple macOS Dark Mode & BYU Accent Palette
BYU_ROYAL = "#0A84FF"
BYU_ROYAL_HOVER = "#0066CC"
BYU_ROYAL_SUBTLE = "#0A2540"

# Layered Dark Mode Surfaces (Elevated Hierarchy)
BG_CANVAS = "#090C12"
BG_LAYER_INSET = "#0D121B"
BG_SURFACE = "#121824"
BG_SURFACE_ALT = "#192131"
BG_SURFACE_HOVER = "#222D42"

# Hairline Micro-Borders
BORDER_SUBTLE = "#243046"
BORDER_ACTIVE = "#384B6E"

# Typographic Hierarchy
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"
TEXT_CODE = "#38BDF8"

# Apple Semantic Status Tones
STATUS_ONLINE = "#30D158"
STATUS_ONLINE_BG = "#083B22"
STATUS_WARNING = "#FF9F0A"
STATUS_WARNING_BG = "#3D2806"
STATUS_DANGER = "#FF453A"
STATUS_DANGER_BG = "#3B1219"

DEPT_DISPLAY_NAMES = {
    "ACC": "Accounting (ACC)",
    "A HTG": "American Heritage (A HTG)",
    "ANTHR": "Anthropology (ANTHR)",
    "ARTHC": "Art History (ARTHC)",
    "BIO": "Biology (BIO)",
    "CELL": "Cell Biology & Physiology (CELL)",
    "CE EN": "Civil & Construction Eng (CE EN)",
    "CH EN": "Chemical Engineering (CH EN)",
    "CHEM": "Chemistry & Biochem (CHEM)",
    "COMM": "Communications (COMM)",
    "C S": "Computer Science (C S)",
    "DANCE": "Dance (DANCE)",
    "DES": "Design (DES)",
    "EC EN": "Electrical & Computer Eng (EC EN)",
    "ECON": "Economics (ECON)",
    "ENGL": "English (ENGL)",
    "EXSC": "Exercise Sciences (EXSC)",
    "FIN": "Finance (FIN)",
    "GEOG": "Geography (GEOG)",
    "GEOL": "Geological Sciences (GEOL)",
    "HIST": "History (HIST)",
    "IHUM": "Interdisciplinary Humanities (IHUM)",
    "IS": "Information Systems (IS)",
    "IT&C": "Information Tech & Cyber (IT&C)",
    "MATH": "Mathematics (MATH)",
    "ME EN": "Mechanical Engineering (ME EN)",
    "MFG": "Manufacturing Engineering (MFG)",
    "MKTG": "Marketing (MKTG)",
    "MMBIO": "Microbiology & Mol Bio (MMBIO)",
    "MUSIC": "School of Music (MUSIC)",
    "NDFS": "Nutrition, Dietetics & Food (NDFS)",
    "NEURO": "Neuroscience (NEURO)",
    "NURS": "Nursing (NURS)",
    "PHIL": "Philosophy (PHIL)",
    "PHSCS": "Physics & Astronomy (PHSCS)",
    "POLI": "Political Science (POLI)",
    "PSYCH": "Psychology (PSYCH)",
    "REL A": "Religion - Ancient Scripture (REL A)",
    "REL C": "Religion - Church History (REL C)",
    "SFL": "School of Family Life (SFL)",
    "SOC": "Sociology (SOC)",
    "SPAN": "Spanish & Portuguese (SPAN)",
    "STAT": "Statistics (STAT)",
    "TMA": "Theatre & Media Arts (TMA)",
    "WRTG": "Writing & Rhetoric (WRTG)",
}

COURSE_COLORS = [
    "#0A84FF", "#0D9488", "#7C3AED", "#D97706",
    "#E11D48", "#059669", "#4F46E5", "#2563EB",
]

# Shared Prerequisite Dependency Map (Used by Recommender & Roadmap Sequencer)
PREREQ_MAP = {
    # Mathematics & Statistics
    "MATH 113": ["MATH 112"],
    "MATH 191": ["MATH 112"],
    "MATH 213": ["MATH 112"],
    "MATH 215": ["MATH 112"],
    "MATH 290": ["MATH 112"],
    "STAT 201": ["MATH 112"],
    "MATH 314": ["MATH 113"],
    "MATH 334": ["MATH 113", "MATH 213"],
    "MATH 341": ["MATH 314", "MATH 290"],
    "MATH 352": ["MATH 314", "MATH 290"],
    "MATH 371": ["MATH 290", "MATH 213"],
    "MATH 413": ["MATH 371"],
    "MATH 342": ["MATH 341"],
    "MATH 350": ["MATH 290"],
    "MATH 372": ["MATH 371"],
    "MATH 431": ["MATH 314"],
    "MATH 487": ["MATH 290"],
    "STAT 386": ["CS 111", "STAT 201"],
    # Computer Science
    "CS 142": ["CS 111"],
    "CS 235": ["CS 111"],
    "CS 270": ["CS 111"],
    "CS 224": ["CS 235"],
    "CS 240": ["CS 235"],
    "CS 252": ["CS 111"],
    "CS 260": ["CS 235"],
    "CS 312": ["CS 235"],
    # General Education Prereqs
    "WRTG 316": ["ENG 102", "WRTG 150"],
    "WRTG 315": ["ENG 102", "WRTG 150"],
    "WRTG 312": ["ENG 102", "WRTG 150"],
    "WRTG 311": ["ENG 102", "WRTG 150"],
    "WRTG 313": ["ENG 102", "WRTG 150"],
    "IHUM 311": ["ENG 102", "WRTG 150"],
    "BIO 316": ["ENG 102", "WRTG 150"],
    "PWS 316": ["ENG 102", "WRTG 150"],
    "ENGL 316": ["ENG 102", "WRTG 150"],
    "ECON 110": ["MATH 110"],
}