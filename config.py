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

# Expanded Catalog Offerings for Every BYU GE Requirement
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