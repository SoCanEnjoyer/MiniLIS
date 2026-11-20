import sys
import os
import csv
import json
import random
import shutil
import sqlite3
import hashlib
from datetime import datetime

if sys.platform == "win32":
    import ctypes

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QPropertyAnimation, QEasingCurve,
    QVariantAnimation, Signal
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QRadialGradient,
    QFont, QKeySequence, QShortcut
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QSplitter,
    QFrame, QScrollArea, QStackedWidget, QDialog,
    QMessageBox, QFileDialog, QCheckBox, QAbstractItemView, QGraphicsDropShadowEffect,
    QSizePolicy
)
from fpdf import FPDF

APP_TITLE = "Monocytes Delegates LIS"
DB_NAME = "monocytes_delegates_lis_v4.db"

INITIAL_STAFF = [
    ("0001", "Carlyle Dioleste, RMT", "Medical Technologist (RMT)"),
    ("0002", "Ariech Legaspi, RMT", "Medical Technologist (RMT)"),
    ("0003", "Melody Bajande, RMT", "Medical Technologist (RMT)"),
    ("0004", "Christine Patani-e, RMT", "Medical Technologist (RMT)"),
    ("0005", "Chauncy Melvida, RMT", "Medical Technologist (RMT)"),
    ("0006", "Elaijeen Cordova, RMT", "Medical Technologist (RMT)"),
    ("0007", "Dianne Pastor, RMT", "Medical Technologist (RMT)"),
    ("0008", "Michael Malabago, RMT", "Medical Technologist (RMT)"),
    ("0009", "Nielmarc Pontioso, RMT", "Medical Technologist (RMT)"),
    ("0010", "Princess Aguilo, RMT", "Medical Technologist (RMT)"),
    ("0011", "Keturah Totisano, RMT", "Medical Technologist (RMT)"),
    ("0012", "Arthur Mana-ay, RMT", "Medical Technologist (RMT)"),
    ("1111", "Gaia Aubrey Manalo, MD", "Pathologist"),
]

# (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
DEFAULT_TESTS = [
    ("White Blood Cell Count (WBC)", "Hematology", "x10^9/L", 4.5, 11.0, 2.0, 30.0, 35.0, "Lavender (EDTA)", "4.5 - 11.0"),
    ("Red Blood Cell Count (RBC)", "Hematology", "x10^12/L", 4.2, 5.9, 2.5, 7.5, 20.0, "Lavender (EDTA)", "4.2 - 5.9"),
    ("Hemoglobin (Hgb)", "Hematology", "g/dL", 12.0, 17.5, 7.0, 20.0, 20.0, "Lavender (EDTA)", "12.0 - 17.5"),
    ("Hematocrit (Hct)", "Hematology", "%", 36.0, 50.0, 21.0, 60.0, 20.0, "Lavender (EDTA)", "36.0 - 50.0"),
    ("Platelet Count (PLT)", "Hematology", "x10^9/L", 150.0, 450.0, 40.0, 1000.0, 30.0, "Lavender (EDTA)", "150 - 450"),
    ("Peripheral Blood Smear (PBS)", "Hematology", "Morphology", None, None, None, None, 0.0, "Lavender (EDTA)", "Normocytic Normochromic"),
    ("Prothrombin Time (PT)", "Coagulation", "sec", 11.0, 13.5, None, 30.0, 25.0, "Light Blue (Citrate)", "11.0 - 13.5"),
    ("INR", "Coagulation", "ratio", 0.8, 1.2, None, 4.5, 30.0, "Light Blue (Citrate)", "0.8 - 1.2"),
    ("Activated Partial Thromboplastin Time (aPTT)", "Coagulation", "sec", 25.0, 35.0, None, 75.0, 25.0, "Light Blue (Citrate)", "25.0 - 35.0"),
    ("Fasting Blood Glucose (FBS)", "Clinical Chemistry", "mg/dL", 70.0, 99.0, 45.0, 400.0, 30.0, "Gold (SST)", "70 - 99"),
    ("Blood Urea Nitrogen (BUN)", "Clinical Chemistry", "mg/dL", 7.0, 20.0, None, 80.0, 35.0, "Gold (SST)", "7.0 - 20.0"),
    ("Creatinine", "Clinical Chemistry", "mg/dL", 0.6, 1.3, None, 5.0, 30.0, "Gold (SST)", "0.6 - 1.3"),
    ("Sodium (Na+)", "Clinical Chemistry", "mmol/L", 135.0, 145.0, 120.0, 160.0, 5.0, "Gold (SST)", "135 - 145"),
    ("Potassium (K+)", "Clinical Chemistry", "mmol/L", 3.5, 5.1, 2.8, 6.2, 15.0, "Gold (SST)", "3.5 - 5.1"),
    ("ALT (SGPT)", "Clinical Chemistry", "U/L", 7.0, 56.0, None, 500.0, 40.0, "Gold (SST)", "7 - 56"),
    ("AST (SGOT)", "Clinical Chemistry", "U/L", 10.0, 40.0, None, 500.0, 40.0, "Gold (SST)", "10 - 40"),
    ("Albumin", "Clinical Chemistry", "g/dL", 3.5, 5.0, 2.0, None, 20.0, "Gold (SST)", "3.5 - 5.0"),
    ("Total Calcium", "Clinical Chemistry", "mg/dL", 8.5, 10.5, 6.5, 13.0, 15.0, "Gold (SST)", "8.5 - 10.5"),
    ("Total Cholesterol", "Clinical Chemistry", "mg/dL", 0.0, 200.0, None, 400.0, 25.0, "Gold (SST)", "< 200"),
    ("Triglycerides", "Clinical Chemistry", "mg/dL", 0.0, 150.0, None, 500.0, 30.0, "Gold (SST)", "< 150"),
    ("HDL Cholesterol", "Clinical Chemistry", "mg/dL", 40.0, 90.0, None, None, 25.0, "Gold (SST)", "> 40"),
    ("Troponin I (hs-cTnI)", "Immunology", "ng/mL", 0.0, 0.04, None, 0.40, 50.0, "Gold (SST)", "< 0.04"),
    ("Dengue NS1 Antigen", "Serology", "Qualitative", None, None, None, None, 0.0, "Gold (SST)", "Non-Reactive"),
    ("Urinalysis (Complete)", "Clinical Microscopy", "Profile", None, None, None, None, 0.0, "Sterile Urine Cup", "Yellow / Clear / Neg"),
    ("Culture & Sensitivity (C&S)", "Microbiology", "Antibiogram", None, None, None, None, 0.0, "Sterile Container", "No Growth"),
]

PRESET_PANELS = {
    "Full CBC + PBS": [
        "White Blood Cell Count (WBC)", "Red Blood Cell Count (RBC)",
        "Hemoglobin (Hgb)", "Hematocrit (Hct)", "Platelet Count (PLT)",
        "Peripheral Blood Smear (PBS)"
    ],
    "Basic Metabolic (BMP)": [
        "Fasting Blood Glucose (FBS)", "Blood Urea Nitrogen (BUN)",
        "Creatinine", "Sodium (Na+)", "Potassium (K+)", "Total Calcium"
    ],
    "Hepatic Function": [
        "ALT (SGPT)", "AST (SGOT)", "Albumin"
    ],
    "Lipid Profile": [
        "Total Cholesterol", "Triglycerides", "HDL Cholesterol"
    ],
    "Coagulation Panel": [
        "Prothrombin Time (PT)", "INR", "Activated Partial Thromboplastin Time (aPTT)"
    ],
    "Dengue Workup": [
        "White Blood Cell Count (WBC)", "Hemoglobin (Hgb)",
        "Hematocrit (Hct)", "Platelet Count (PLT)", "Dengue NS1 Antigen"
    ],
}

DEFAULT_QC_TARGETS = [
    ("Hemoglobin (Hgb) | Level 1 (Normal)", "Hemoglobin (Hgb)", "Level 1", 13.8, 0.35, "g/dL"),
    ("Hemoglobin (Hgb) | Level 2 (Abnormal)", "Hemoglobin (Hgb)", "Level 2", 7.8, 0.25, "g/dL"),
    ("WBC | Level 1 (Normal)", "White Blood Cell Count (WBC)", "Level 1", 7.5, 0.40, "x10^9/L"),
    ("Platelet Count | Level 1 (Normal)", "Platelet Count (PLT)", "Level 1", 265.0, 14.0, "x10^9/L"),
    ("Fasting Blood Glucose | Level 1 (Normal)", "Fasting Blood Glucose (FBS)", "Level 1", 88.0, 3.00, "mg/dL"),
    ("Fasting Blood Glucose | Level 2 (High)", "Fasting Blood Glucose (FBS)", "Level 2", 245.0, 7.50, "mg/dL"),
]

PBS_MACROS = [
    "Normocytic, normochromic RBCs; adequate platelets; normal WBC morphology.",
    "Anisocytosis (+2), poikilocytosis (+1) with target cells and occasional microcytes.",
    "Neutrophilic leukocytosis with toxic granulation (+2) and Dohle bodies.",
    "Atypical / reactive lymphocytes (>15%) consistent with viral etiology.",
    "Marked thrombocytopenia confirmed on smear; occasional giant platelets noted.",
    "Schistocytes (+2) and polychromasia present — urgent clinical correlation advised.",
]

ANTIBIOTICS_LIST = [
    "Amoxicillin-Clavulanate",
    "Ceftriaxone",
    "Cefuroxime",
    "Ciprofloxacin",
    "Levofloxacin",
    "Gentamicin",
    "Amikacin",
    "Meropenem",
    "Piperacillin-Tazobactam",
    "Trimethoprim-Sulfamethoxazole",
    "Nitrofurantoin",
    "Vancomycin",
]

ORGANISMS_LIST = [
    "Escherichia coli",
    "Klebsiella pneumoniae",
    "Staphylococcus aureus (MSSA)",
    "Staphylococcus aureus (MRSA)",
    "Pseudomonas aeruginosa",
    "Enterococcus faecalis",
    "Proteus mirabilis",
    "Salmonella enterica",
    "No Pathogen Isolated / Normal Flora",
]

TUBE_COLORS = {
    "Lavender (EDTA)": ("#A855F7", "#F3E8FF"),
    "Gold (SST)": ("#EAB308", "#FEF9C3"),
    "Light Blue (Citrate)": ("#38BDF8", "#E0F2FE"),
    "Green (Heparin)": ("#10B981", "#D1FAE5"),
    "Sterile Urine Cup": ("#F97316", "#FFEDD5"),
    "Sterile Container": ("#F43F5E", "#FFE4E6"),
}

APP_QSS = """
QMainWindow, QWidget#RootCanvas {
    background-color: #070B14;
    color: #E2E8F0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}
QWidget {
    color: #E2E8F0;
    font-family: "Segoe UI", "Inter", sans-serif;
}
QFrame#SurfaceCard {
    background-color: #0D1322;
    border: 1px solid #1E293B;
    border-radius: 10px;
}
QFrame#SubPanel {
    background-color: #11192C;
    border: 1px solid #1E293B;
    border-radius: 8px;
}
QFrame#TopHeaderBar {
    background-color: #0B101D;
    border-bottom: 1px solid #1E293B;
}
QLabel#SectionHeader {
    font-size: 11pt;
    font-weight: 700;
    color: #F8FAFC;
}
QLabel#GroupTitle {
    font-size: 8.5pt;
    font-weight: 700;
    color: #94A3B8;
    letter-spacing: 0.6px;
}
QLabel#MutedLabel {
    color: #94A3B8;
    font-size: 9pt;
}
QLabel#MonoBadge {
    font-family: "Consolas", "JetBrains Mono", monospace;
    background-color: #111827;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 4px 10px;
    color: #CBD5E1;
    font-weight: 600;
}
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #090E1A;
    border: 1px solid #263348;
    border-radius: 7px;
    padding: 7px 10px;
    color: #F8FAFC;
    selection-background-color: #2563EB;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #38BDF8;
    background-color: #0C1424;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #0F172A;
    border: 1px solid #334155;
    color: #F8FAFC;
    selection-background-color: #1D4ED8;
}
QPushButton {
    background-color: #162033;
    border: 1px solid #29374F;
    border-radius: 7px;
    padding: 7px 13px;
    color: #E2E8F0;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #1E2B44;
    border-color: #475569;
    color: #FFFFFF;
}
QPushButton:pressed {
    background-color: #0F172A;
}
QPushButton#PrimaryBtn {
    background-color: #0284C7;
    border: 1px solid #38BDF8;
    color: #FFFFFF;
}
QPushButton#PrimaryBtn:hover {
    background-color: #0369A1;
}
QPushButton#SuccessBtn {
    background-color: #059669;
    border: 1px solid #34D399;
    color: #FFFFFF;
}
QPushButton#SuccessBtn:hover {
    background-color: #047857;
}
QPushButton#DangerBtn {
    background-color: #BE123C;
    border: 1px solid #FB7185;
    color: #FFFFFF;
}
QPushButton#DangerBtn:hover {
    background-color: #9F1239;
}
QPushButton#AccentBtn {
    background-color: #3730A3;
    border: 1px solid #6366F1;
    color: #FFFFFF;
}
QPushButton#AccentBtn:hover {
    background-color: #312E81;
}
QPushButton#KeypadBtn {
    background-color: #111827;
    border: 1px solid #263348;
    border-radius: 8px;
    font-family: "Consolas", monospace;
    font-size: 13pt;
    font-weight: 700;
    color: #F8FAFC;
    min-height: 44px;
}
QPushButton#KeypadBtn:hover {
    background-color: #1E293B;
    border-color: #38BDF8;
    color: #38BDF8;
}
QPushButton#KeypadBtn:pressed {
    background-color: #0284C7;
    color: #FFFFFF;
}
QTabWidget::pane {
    border: 1px solid #1E293B;
    border-radius: 9px;
    background-color: #070B14;
    top: -1px;
}
QTabBar::tab {
    background-color: #0B101D;
    border: 1px solid #1E293B;
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 9px 18px;
    margin-right: 4px;
    color: #94A3B8;
    font-weight: 600;
    font-size: 9.5pt;
}
QTabBar::tab:selected {
    background-color: #121B2E;
    border-color: #334155;
    border-top: 2px solid #38BDF8;
    color: #F8FAFC;
}
QTabBar::tab:hover:!selected {
    background-color: #0F172A;
    color: #E2E8F0;
}
QTableWidget {
    background-color: #090E1A;
    alternate-background-color: #0C1322;
    gridline-color: #172033;
    border: 1px solid #1E293B;
    border-radius: 8px;
    selection-background-color: #1D4ED8;
    selection-color: #FFFFFF;
}
QTableWidget::item {
    padding: 6px 8px;
}
QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    font-weight: 700;
    font-size: 9pt;
    border: none;
    border-bottom: 1px solid #263348;
    border-right: 1px solid #172033;
    padding: 7px 8px;
}
QScrollBar:vertical {
    background: #070B14;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #263348;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #38BDF8;
}
QScrollBar:horizontal {
    background: #070B14;
    height: 10px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #263348;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: #38BDF8;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}
QCheckBox {
    spacing: 8px;
    color: #E2E8F0;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #334155;
    background: #090E1A;
}
QCheckBox::indicator:checked {
    background: #0284C7;
    border-color: #38BDF8;
}
"""


def _pdf_safe(text) -> str:
    if text is None:
        return ""
    s = str(text)
    replacements = {
        "—": "-", "–": "-", "•": "*", "×": "x", "≥": ">=", "≤": "<=",
        "±": "+/-", "°": " deg", "’": "'", "‘": "'", "“": '"', "”": '"',
        "…": "...", "→": "->"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def apply_dark_titlebar(widget: QWidget):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
        )
    except Exception:
        pass


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(cur, table: str, col: str, definition: str):
    cur.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in cur.fetchall()}
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            pin TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrn TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            dob TEXT,
            sex TEXT,
            contact TEXT,
            physician TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            unit TEXT,
            low_val REAL,
            high_val REAL,
            crit_low REAL,
            crit_high REAL,
            delta_pct REAL DEFAULT 30.0,
            tube_type TEXT DEFAULT 'Gold (SST)',
            ref_range TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            specimen_id TEXT NOT NULL,
            patient_id INTEGER NOT NULL,
            test_name TEXT NOT NULL,
            department TEXT NOT NULL,
            priority TEXT DEFAULT 'Routine',
            status TEXT DEFAULT 'Ordered',
            result_value TEXT,
            flag TEXT,
            unit TEXT,
            ref_range TEXT,
            tube_type TEXT,
            notes TEXT,
            ordered_by TEXT,
            ordered_at TEXT,
            collected_at TEXT,
            verified_by TEXT,
            verified_at TEXT,
            amended_reason TEXT,
            panic_notified_to TEXT,
            delta_flag TEXT,
            critical_flag INTEGER DEFAULT 0,
            storage_slot TEXT,
            pathologist_note TEXT,
            pathologist_signed_by TEXT,
            pathologist_signed_at TEXT,
            antibiogram_json TEXT,
            diff_json TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS qc_targets (
            label TEXT PRIMARY KEY,
            test_name TEXT NOT NULL,
            level TEXT NOT NULL,
            target_mean REAL NOT NULL,
            sd REAL NOT NULL,
            unit TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS qc_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            measured REAL NOT NULL,
            z_score REAL NOT NULL,
            westgard_status TEXT NOT NULL,
            operator TEXT NOT NULL,
            logged_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            operator TEXT NOT NULL,
            action TEXT NOT NULL,
            specimen_id TEXT,
            details TEXT
        )
    """)

    order_upgrades = [
        ("collected_at", "TEXT"),
        ("verified_by", "TEXT"),
        ("verified_at", "TEXT"),
        ("amended_reason", "TEXT"),
        ("panic_notified_to", "TEXT"),
        ("delta_flag", "TEXT"),
        ("critical_flag", "INTEGER DEFAULT 0"),
        ("storage_slot", "TEXT"),
        ("pathologist_note", "TEXT"),
        ("pathologist_signed_by", "TEXT"),
        ("pathologist_signed_at", "TEXT"),
        ("antibiogram_json", "TEXT"),
        ("diff_json", "TEXT"),
        ("tube_type", "TEXT"),
        ("ref_range", "TEXT"),
        ("unit", "TEXT"),
    ]
    for col, col_def in order_upgrades:
        _ensure_column(cur, "orders", col, col_def)

    test_upgrades = [
        ("crit_low", "REAL"),
        ("crit_high", "REAL"),
        ("delta_pct", "REAL DEFAULT 30.0"),
        ("tube_type", "TEXT DEFAULT 'Gold (SST)'"),
        ("ref_range", "TEXT"),
    ]
    for col, col_def in test_upgrades:
        _ensure_column(cur, "tests", col, col_def)

    cur.execute("DELETE FROM staff WHERE pin IN ('1234', '9999') OR name LIKE '%Demo%'")

    for pin, name, role in INITIAL_STAFF:
        cur.execute("INSERT OR IGNORE INTO staff (pin, name, role) VALUES (?, ?, ?)", (pin, name, role))

    for t in DEFAULT_TESTS:
        cur.execute("""
            INSERT OR IGNORE INTO tests
            (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    for q in DEFAULT_QC_TARGETS:
        cur.execute("""
            INSERT OR IGNORE INTO qc_targets (label, test_name, level, target_mean, sd, unit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, q)

    conn.commit()
    conn.close()


def log_audit(operator: str, action: str, specimen_id: str = "-", details: str = ""):
    try:
        conn = get_conn()
        conn.execute(
            "INSERT INTO audit_log (timestamp, operator, action, specimen_id, details) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator, action, specimen_id, details)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ==============================================================================
# CLINICAL VISUAL INDICATORS (REFERENCE RANGE GAUGE, COLLECTION TUBE, CHARTS)
# ==============================================================================

class VectorRangeGauge(QWidget):
    """Clinical reference interval gauge showing where a numeric result sits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self.norm_pos = 0.5
        self.flag_text = "AWAITING RESULT"
        self.flag_color = QColor("#64748B")
        self.low_lbl = "-"
        self.high_lbl = "-"

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(380)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._on_step)

    def _on_step(self, v):
        self.norm_pos = float(v)
        self.update()

    def set_reading(self, val_str: str, low_val, high_val, crit_low, crit_high, flag: str):
        self.flag_text = flag or "PENDING"
        self.low_lbl = f"{low_val}" if low_val is not None else "-"
        self.high_lbl = f"{high_val}" if high_val is not None else "-"

        color_map = {
            "NORMAL": "#10B981",
            "LOW": "#F59E0B",
            "HIGH": "#F97316",
            "CRITICAL LOW": "#F43F5E",
            "CRITICAL HIGH": "#F43F5E",
            "ABNORMAL": "#F43F5E",
            "REJECTED": "#64748B",
        }
        self.flag_color = QColor(color_map.get(self.flag_text, "#38BDF8"))

        target = 0.5
        try:
            v = float(val_str)
            if low_val is not None and high_val is not None and high_val > low_val:
                span = high_val - low_val
                lo_bound = low_val - 0.5 * span
                hi_bound = high_val + 0.5 * span
                ratio = (v - lo_bound) / (hi_bound - lo_bound)
                target = max(0.05, min(0.95, ratio))
            elif high_val is not None and high_val > 0:
                target = max(0.05, min(0.95, (v / (high_val * 1.5)) * 0.75 + 0.1))
        except Exception:
            target = 0.5 if self.flag_text in ("NORMAL", "PENDING") else 0.85

        self.anim.stop()
        self.anim.setStartValue(self.norm_pos)
        self.anim.setEndValue(target)
        self.anim.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w = self.width()

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(self.flag_color)
        p.drawText(QRectF(2, 2, w - 4, 20), Qt.AlignLeft | Qt.AlignVCenter, f"Status: {self.flag_text}")

        bar_x, bar_y = 10.0, 28.0
        bar_w, bar_h = max(40.0, w - 20.0), 12.0

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E293B"))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 6, 6)

        p.setBrush(QColor(245, 158, 11, 130))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w * 0.26, bar_h), 6, 6)

        p.setBrush(QColor(244, 63, 94, 140))
        p.drawRoundedRect(QRectF(bar_x + bar_w * 0.74, bar_y, bar_w * 0.26, bar_h), 6, 6)

        p.setBrush(QColor(16, 185, 129, 200))
        p.drawRect(QRectF(bar_x + bar_w * 0.25, bar_y, bar_w * 0.50, bar_h))

        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor("#94A3B8"))
        x_lo = bar_x + bar_w * 0.25
        x_hi = bar_x + bar_w * 0.75
        p.drawLine(QPointF(x_lo, bar_y - 3), QPointF(x_lo, bar_y + bar_h + 3))
        p.drawLine(QPointF(x_hi, bar_y - 3), QPointF(x_hi, bar_y + bar_h + 3))
        p.drawText(QRectF(x_lo - 35, bar_y + bar_h + 3, 70, 16), Qt.AlignCenter, self.low_lbl)
        p.drawText(QRectF(x_hi - 35, bar_y + bar_h + 3, 70, 16), Qt.AlignCenter, self.high_lbl)

        nx = bar_x + self.norm_pos * bar_w
        ny = bar_y + bar_h * 0.5
        p.setBrush(QColor("#FFFFFF"))
        p.setPen(QPen(self.flag_color, 2.5))
        p.drawEllipse(QPointF(nx, ny), 6.0, 6.0)


class TubeBadgeWidget(QWidget):
    """Crisp vacutainer collection tube icon + label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tube_name = "Gold (SST)"
        self.setMinimumHeight(30)

    def set_tube(self, tube_name: str):
        self.tube_name = tube_name or "Gold (SST)"
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        cap_hex, _ = TUBE_COLORS.get(self.tube_name, ("#38BDF8", "#E0F2FE"))
        cap_col = QColor(cap_hex)

        p.setPen(QPen(QColor("#64748B"), 1.2))
        p.setBrush(QColor("#1E293B"))
        p.drawRoundedRect(QRectF(10, 8, 26, 12), 5, 5)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(225, 29, 72, 180))
        p.drawRoundedRect(QRectF(12, 10, 14, 8), 3, 3)

        p.setBrush(cap_col)
        p.drawRoundedRect(QRectF(2, 7, 9, 14), 2, 2)

        p.setPen(QColor("#CBD5E1"))
        p.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        p.drawText(QRectF(44, 3, self.width() - 48, 24), Qt.AlignLeft | Qt.AlignVCenter, f"Container: {self.tube_name}")


class MplCanvas(FigureCanvas):
    """Dark-theme Matplotlib canvas for QC Levey-Jennings and Patient Trends."""

    def __init__(self, width=5.5, height=3.4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor="#090E1A")
        self.ax = self.fig.add_subplot(111)
        self._style_ax(self.ax)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _style_ax(self, ax):
        ax.set_facecolor("#0D1322")
        ax.tick_params(colors="#94A3B8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#263348")
        ax.title.set_color("#F8FAFC")
        ax.xaxis.label.set_color("#94A3B8")
        ax.yaxis.label.set_color("#94A3B8")


# ==============================================================================
# CLEAN STAFF PIN LOGIN SCREEN
# ==============================================================================

class CleanLoginBackdrop(QWidget):
    """Clean, static obsidian-slate backdrop with subtle grid lines."""

    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()

        bg = QRadialGradient(w * 0.5, h * 0.45, max(w, h) * 0.72)
        bg.setColorAt(0.0, QColor("#0E1526"))
        bg.setColorAt(0.65, QColor("#080C16"))
        bg.setColorAt(1.0, QColor("#05080F"))
        p.fillRect(0, 0, w, h, bg)

        p.setPen(QPen(QColor(30, 41, 59, 32), 1))
        step = 56
        for gx in range(0, w, step):
            p.drawLine(gx, 0, gx, h)
        for gy in range(0, h, step):
            p.drawLine(0, gy, w, gy)


class StaffLoginScreen(QWidget):
    authenticated = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pin_buffer = ""
        self.locked_transition = False

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.bg_canvas = CleanLoginBackdrop(self)
        root.addWidget(self.bg_canvas, 0, 0)

        center_wrap = QWidget(self)
        center_wrap.setAttribute(Qt.WA_TranslucentBackground)
        c_lay = QVBoxLayout(center_wrap)
        c_lay.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedWidth(400)
        self.card.setStyleSheet("""
            QFrame {
                background-color: #0D1322;
                border: 1px solid #1E293B;
                border-radius: 14px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(28, 28, 28, 24)
        card_lay.setSpacing(14)

        # Clean clinical emblem badge
        badge = QLabel("MDL")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(48, 48)
        badge.setStyleSheet("""
            background-color: #111C33;
            border: 1px solid #2563EB;
            border-radius: 12px;
            color: #38BDF8;
            font-size: 13pt;
            font-weight: 800;
            letter-spacing: 1px;
        """)
        badge_row = QHBoxLayout()
        badge_row.setAlignment(Qt.AlignCenter)
        badge_row.addWidget(badge)
        card_lay.addLayout(badge_row)

        lbl_brand = QLabel("Monocytes Delegates LIS")
        lbl_brand.setAlignment(Qt.AlignCenter)
        lbl_brand.setStyleSheet("color: #F8FAFC; font-size: 15pt; font-weight: 700; border: none; background: transparent;")
        card_lay.addWidget(lbl_brand)

        lbl_sub = QLabel("Clinical Laboratory Information System")
        lbl_sub.setAlignment(Qt.AlignCenter)
        lbl_sub.setStyleSheet("color: #94A3B8; font-size: 9pt; border: none; background: transparent;")
        card_lay.addWidget(lbl_sub)

        # 4 PIN Slots
        slot_row = QHBoxLayout()
        slot_row.setSpacing(12)
        slot_row.setAlignment(Qt.AlignCenter)
        self.pin_slots = []
        for _ in range(4):
            box = QLabel("•")
            box.setAlignment(Qt.AlignCenter)
            box.setFixedSize(54, 54)
            box.setStyleSheet("""
                background-color: #080C16;
                border: 1px solid #263348;
                border-radius: 10px;
                color: #475569;
                font-family: 'Consolas', monospace;
                font-size: 19pt;
                font-weight: 700;
            """)
            self.pin_slots.append(box)
            slot_row.addWidget(box)
        card_lay.addLayout(slot_row)

        self.lbl_status = QLabel("Enter 4-digit staff PIN")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 9pt; border: none; background: transparent;")
        card_lay.addWidget(self.lbl_status)

        # Keypad Grid
        grid = QGridLayout()
        grid.setSpacing(8)
        keys = [
            ("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
            ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
            ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
            ("CLR", 3, 0), ("0", 3, 1), ("⌫", 3, 2),
        ]
        for label, r, c in keys:
            btn = QPushButton(label)
            btn.setObjectName("KeypadBtn")
            btn.setFocusPolicy(Qt.NoFocus)
            btn.clicked.connect(lambda checked=False, k=label: self._on_key(k))
            grid.addWidget(btn, r, c)
        card_lay.addLayout(grid)

        self.btn_unlock = QPushButton("Sign In")
        self.btn_unlock.setObjectName("PrimaryBtn")
        self.btn_unlock.setMinimumHeight(42)
        self.btn_unlock.setFocusPolicy(Qt.NoFocus)
        self.btn_unlock.clicked.connect(self._verify_pin)
        card_lay.addWidget(self.btn_unlock)

        lbl_hint = QLabel("Keyboard number pad supported")
        lbl_hint.setAlignment(Qt.AlignCenter)
        lbl_hint.setStyleSheet("color: #64748B; font-size: 8pt; border: none; background: transparent;")
        card_lay.addWidget(lbl_hint)

        c_lay.addWidget(self.card)
        root.addWidget(center_wrap, 0, 0)
        self.setFocusPolicy(Qt.StrongFocus)

    def reset_gate(self):
        self.pin_buffer = ""
        self.locked_transition = False
        self.lbl_status.setText("Enter 4-digit staff PIN")
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 9pt; border: none; background: transparent;")
        self._refresh_slots("#263348")
        self.setFocus()

    def _refresh_slots(self, border_hex="#38BDF8"):
        for i, slot in enumerate(self.pin_slots):
            if i < len(self.pin_buffer):
                slot.setText("●")
                slot.setStyleSheet(f"""
                    background-color: #0B1426;
                    border: 2px solid {border_hex};
                    border-radius: 10px;
                    color: {border_hex};
                    font-family: 'Consolas', monospace;
                    font-size: 19pt;
                    font-weight: 700;
                """)
            else:
                slot.setText("•")
                slot.setStyleSheet("""
                    background-color: #080C16;
                    border: 1px solid #263348;
                    border-radius: 10px;
                    color: #475569;
                    font-family: 'Consolas', monospace;
                    font-size: 19pt;
                    font-weight: 700;
                """)

    def keyPressEvent(self, event):
        if self.locked_transition:
            return
        k = event.key()
        txt = event.text()
        if txt in "0123456789" and len(txt) == 1:
            self._on_key(txt)
        elif k in (Qt.Key_Backspace, Qt.Key_Delete):
            self._on_key("⌫")
        elif k == Qt.Key_Escape:
            self._on_key("CLR")
        elif k in (Qt.Key_Return, Qt.Key_Enter):
            self._verify_pin()

    def _on_key(self, k: str):
        if self.locked_transition:
            return
        if k == "CLR":
            self.pin_buffer = ""
            self._refresh_slots("#263348")
            self.lbl_status.setText("Enter 4-digit staff PIN")
            self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 9pt; border: none; background: transparent;")
        elif k == "⌫":
            self.pin_buffer = self.pin_buffer[:-1]
            self._refresh_slots("#38BDF8")
        else:
            if len(self.pin_buffer) < 4:
                self.pin_buffer += k
                self._refresh_slots("#38BDF8")
                if len(self.pin_buffer) == 4:
                    QTimer.singleShot(90, self._verify_pin)

    def _shake_card(self):
        orig = self.card.pos()
        anim = QPropertyAnimation(self.card, b"pos", self)
        anim.setDuration(260)
        anim.setKeyValueAt(0.0, orig)
        anim.setKeyValueAt(0.2, orig + QPointF(-10, 0).toPoint())
        anim.setKeyValueAt(0.4, orig + QPointF(10, 0).toPoint())
        anim.setKeyValueAt(0.6, orig + QPointF(-7, 0).toPoint())
        anim.setKeyValueAt(0.8, orig + QPointF(7, 0).toPoint())
        anim.setKeyValueAt(1.0, orig)
        anim.start()

    def _verify_pin(self):
        if self.locked_transition:
            return
        conn = get_conn()
        row = conn.execute("SELECT pin, name, role FROM staff WHERE pin = ?", (self.pin_buffer,)).fetchone()
        conn.close()

        if not row:
            self._refresh_slots("#F43F5E")
            self.lbl_status.setText("Invalid PIN — please try again")
            self.lbl_status.setStyleSheet("color: #FB7185; font-size: 9pt; font-weight: 600; border: none; background: transparent;")
            self._shake_card()
            self.pin_buffer = ""
            return

        self.locked_transition = True
        self._refresh_slots("#10B981")
        user = {"pin": row["pin"], "name": row["name"], "role": row["role"]}
        self.lbl_status.setText(f"Welcome, {user['name']}")
        self.lbl_status.setStyleSheet("color: #34D399; font-size: 9.5pt; font-weight: 700; border: none; background: transparent;")
        log_audit(f"{user['name']} ({user['pin']})", "SESSION_UNLOCK", "-", f"Role: {user['role']}")
        QTimer.singleShot(320, lambda: self.authenticated.emit(user))


# ==============================================================================
# CLINICAL INTERACTIVE DIALOGS (CALCULATORS, 100-CELL WBC DIFF, ANTIBIOGRAM, HISTORY)
# ==============================================================================

class RmtCalculatorDialog(QDialog):
    """Hematology & Clinical Chemistry derived indices calculator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clinical Indices Calculator")
        self.resize(520, 440)
        self.setStyleSheet(APP_QSS)
        apply_dark_titlebar(self)
        self.generated_summary = ""

        lay = QVBoxLayout(self)
        tabs = QTabWidget()

        hem = QWidget()
        h_lay = QGridLayout(hem)
        self.in_rbc = QLineEdit(); self.in_rbc.setPlaceholderText("e.g. 4.8")
        self.in_hgb = QLineEdit(); self.in_hgb.setPlaceholderText("e.g. 14.2")
        self.in_hct = QLineEdit(); self.in_hct.setPlaceholderText("e.g. 42.5")
        self.in_wbc = QLineEdit(); self.in_wbc.setPlaceholderText("e.g. 12.4")
        self.in_nrbc = QLineEdit(); self.in_nrbc.setPlaceholderText("nRBC / 100 WBC (e.g. 0)")
        self.in_neut = QLineEdit(); self.in_neut.setPlaceholderText("Neutrophils % (e.g. 68)")
        self.in_lymph = QLineEdit(); self.in_lymph.setPlaceholderText("Lymphocytes % (e.g. 24)")

        fields_h = [
            ("RBC (x10^12/L):", self.in_rbc),
            ("Hemoglobin (g/dL):", self.in_hgb),
            ("Hematocrit (%):", self.in_hct),
            ("Uncorrected WBC (x10^9/L):", self.in_wbc),
            ("Nucleated RBCs (/100 WBC):", self.in_nrbc),
            ("Neutrophils (%):", self.in_neut),
            ("Lymphocytes (%):", self.in_lymph),
        ]
        for idx, (lbl, w) in enumerate(fields_h):
            h_lay.addWidget(QLabel(lbl), idx, 0)
            h_lay.addWidget(w, idx, 1)

        btn_calc_h = QPushButton("Compute Hematology Indices")
        btn_calc_h.setObjectName("PrimaryBtn")
        btn_calc_h.clicked.connect(self._calc_hem)
        h_lay.addWidget(btn_calc_h, len(fields_h), 0, 1, 2)
        tabs.addTab(hem, "Hematology")

        chem = QWidget()
        c_lay = QGridLayout(chem)
        self.in_tc = QLineEdit(); self.in_tc.setPlaceholderText("Total Chol mg/dL (e.g. 210)")
        self.in_tg = QLineEdit(); self.in_tg.setPlaceholderText("Triglycerides mg/dL (e.g. 140)")
        self.in_hdl = QLineEdit(); self.in_hdl.setPlaceholderText("HDL mg/dL (e.g. 48)")
        self.in_bun = QLineEdit(); self.in_bun.setPlaceholderText("BUN mg/dL (e.g. 18)")
        self.in_cr = QLineEdit(); self.in_cr.setPlaceholderText("Creatinine mg/dL (e.g. 1.0)")
        self.in_ca = QLineEdit(); self.in_ca.setPlaceholderText("Measured Ca mg/dL (e.g. 8.2)")
        self.in_alb = QLineEdit(); self.in_alb.setPlaceholderText("Albumin g/dL (e.g. 2.8)")

        fields_c = [
            ("Total Cholesterol (mg/dL):", self.in_tc),
            ("Triglycerides (mg/dL):", self.in_tg),
            ("HDL Cholesterol (mg/dL):", self.in_hdl),
            ("BUN (mg/dL):", self.in_bun),
            ("Creatinine (mg/dL):", self.in_cr),
            ("Total Calcium (mg/dL):", self.in_ca),
            ("Serum Albumin (g/dL):", self.in_alb),
        ]
        for idx, (lbl, w) in enumerate(fields_c):
            c_lay.addWidget(QLabel(lbl), idx, 0)
            c_lay.addWidget(w, idx, 1)

        btn_calc_c = QPushButton("Compute Chemistry Indices")
        btn_calc_c.setObjectName("PrimaryBtn")
        btn_calc_c.clicked.connect(self._calc_chem)
        c_lay.addWidget(btn_calc_c, len(fields_c), 0, 1, 2)
        tabs.addTab(chem, "Chemistry")

        lay.addWidget(tabs)

        self.out_box = QPlainTextEdit()
        self.out_box.setReadOnly(True)
        self.out_box.setFixedHeight(100)
        self.out_box.setPlaceholderText("Computed values will appear here...")
        lay.addWidget(self.out_box)

        btn_row = QHBoxLayout()
        btn_inject = QPushButton("Add to Specimen Note")
        btn_inject.setObjectName("SuccessBtn")
        btn_inject.clicked.connect(self.accept)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_inject)
        btn_row.addWidget(btn_close)
        lay.addLayout(btn_row)

    def _f(self, widget):
        try:
            return float(widget.text().strip())
        except Exception:
            return None

    def _calc_hem(self):
        lines = []
        rbc, hgb, hct = self._f(self.in_rbc), self._f(self.in_hgb), self._f(self.in_hct)
        if rbc and hct and rbc > 0:
            lines.append(f"MCV: {(hct * 10.0) / rbc:.1f} fL")
        if rbc and hgb and rbc > 0:
            lines.append(f"MCH: {(hgb * 10.0) / rbc:.1f} pg")
        if hct and hgb and hct > 0:
            lines.append(f"MCHC: {(hgb * 100.0) / hct:.1f} g/dL")
        wbc, nrbc = self._f(self.in_wbc), self._f(self.in_nrbc)
        eff_wbc = wbc
        if wbc is not None and nrbc is not None and nrbc > 0:
            eff_wbc = (wbc * 100.0) / (100.0 + nrbc)
            lines.append(f"Corrected WBC: {eff_wbc:.2f} x10^9/L ({nrbc:.0f} nRBC/100 WBC)")
        neut, lymph = self._f(self.in_neut), self._f(self.in_lymph)
        if eff_wbc is not None and neut is not None:
            lines.append(f"ANC: {eff_wbc * (neut / 100.0):.2f} x10^9/L")
        if neut is not None and lymph is not None and lymph > 0:
            lines.append(f"NLR: {neut / lymph:.2f}")
        self.generated_summary = " | ".join(lines) if lines else "Enter valid numeric inputs."
        self.out_box.setPlainText(self.generated_summary)

    def _calc_chem(self):
        lines = []
        tc, tg, hdl = self._f(self.in_tc), self._f(self.in_tg), self._f(self.in_hdl)
        if tc is not None and tg is not None and hdl is not None:
            if tg < 400:
                ldl = tc - hdl - (tg / 5.0)
                lines.append(f"Calculated LDL: {ldl:.1f} mg/dL")
            else:
                lines.append("Calculated LDL: Invalid (TG >= 400 mg/dL)")
        bun, cr = self._f(self.in_bun), self._f(self.in_cr)
        if bun is not None and cr is not None and cr > 0:
            lines.append(f"BUN/Cr Ratio: {bun / cr:.1f}:1")
        ca, alb = self._f(self.in_ca), self._f(self.in_alb)
        if ca is not None and alb is not None:
            corr_ca = ca + 0.8 * (4.0 - alb)
            lines.append(f"Corrected Ca: {corr_ca:.2f} mg/dL")
        self.generated_summary = " | ".join(lines) if lines else "Enter valid numeric inputs."
        self.out_box.setPlainText(self.generated_summary)


class WbcDiffCounterDialog(QDialog):
    """Keyboard-driven 100-cell Manual WBC Differential Counter & PBS Morphology Builder."""

    def __init__(self, existing_json: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("100-Cell WBC Differential & Smear Morphology")
        self.resize(600, 500)
        self.setStyleSheet(APP_QSS)
        apply_dark_titlebar(self)

        self.counts = {"Neutrophils": 0, "Lymphocytes": 0, "Monocytes": 0, "Eosinophils": 0, "Basophils": 0, "nRBC": 0}
        if existing_json:
            try:
                data = json.loads(existing_json)
                self.counts.update(data.get("counts", {}))
            except Exception:
                pass

        lay = QVBoxLayout(self)
        hdr = QLabel("Keys: [N] Neutrophil   [L] Lymphocyte   [M] Monocyte   [E] Eosinophil   [B] Basophil   [R] nRBC")
        hdr.setObjectName("MonoBadge")
        hdr.setAlignment(Qt.AlignCenter)
        lay.addWidget(hdr)

        self.lbl_total = QLabel("WBC Counted: 0 / 100")
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setStyleSheet("font-size: 15pt; font-weight: 700; color: #38BDF8; padding: 6px;")
        lay.addWidget(self.lbl_total)

        grid = QGridLayout()
        self.cell_labels = {}
        specs = [
            ("Neutrophils", "N", "#38BDF8"),
            ("Lymphocytes", "L", "#818CF8"),
            ("Monocytes", "M", "#10B981"),
            ("Eosinophils", "E", "#F59E0B"),
            ("Basophils", "B", "#EC4899"),
            ("nRBC", "R / 100 WBC", "#F43F5E"),
        ]
        for idx, (cell, key_hint, col) in enumerate(specs):
            r, c = divmod(idx, 3)
            card = QFrame()
            card.setObjectName("SubPanel")
            cl = QVBoxLayout(card)
            t = QLabel(f"{cell} [{key_hint}]")
            t.setStyleSheet(f"color: {col}; font-weight: 700;")
            val_lbl = QLabel("0 (0%)")
            val_lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 13pt; font-weight: 700;")
            btn_add = QPushButton(f"+1 {cell}")
            btn_add.setFocusPolicy(Qt.NoFocus)
            btn_add.clicked.connect(lambda checked=False, name=cell: self._inc(name))
            cl.addWidget(t)
            cl.addWidget(val_lbl)
            cl.addWidget(btn_add)
            grid.addWidget(card, r, c)
            self.cell_labels[cell] = val_lbl
        lay.addLayout(grid)

        lay.addWidget(QLabel("Peripheral Blood Smear (PBS) Morphology Preset:"))
        self.cmb_macro = QComboBox()
        self.cmb_macro.addItems(PBS_MACROS)
        lay.addWidget(self.cmb_macro)

        self.txt_morph = QPlainTextEdit()
        self.txt_morph.setFixedHeight(72)
        self.txt_morph.setPlainText(PBS_MACROS[0])
        self.cmb_macro.currentTextChanged.connect(self.txt_morph.setPlainText)
        lay.addWidget(self.txt_morph)

        btns = QHBoxLayout()
        btn_reset = QPushButton("Reset")
        btn_reset.setFocusPolicy(Qt.NoFocus)
        btn_reset.clicked.connect(self._reset)
        btn_save = QPushButton("Save to Specimen")
        btn_save.setObjectName("SuccessBtn")
        btn_save.setFocusPolicy(Qt.NoFocus)
        btn_save.clicked.connect(self.accept)
        btns.addWidget(btn_reset)
        btns.addStretch()
        btns.addWidget(btn_save)
        lay.addLayout(btns)

        self._refresh()

    def keyPressEvent(self, event):
        t = event.text().upper()
        mapping = {"N": "Neutrophils", "L": "Lymphocytes", "M": "Monocytes", "E": "Eosinophils", "B": "Basophils", "R": "nRBC"}
        if t in mapping:
            self._inc(mapping[t])
        else:
            super().keyPressEvent(event)

    def _wbc_sum(self):
        return sum(self.counts[k] for k in ("Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils"))

    def _inc(self, cell: str):
        if cell != "nRBC" and self._wbc_sum() >= 100:
            return
        self.counts[cell] += 1
        self._refresh()

    def _reset(self):
        for k in self.counts:
            self.counts[k] = 0
        self._refresh()

    def _refresh(self):
        tot = self._wbc_sum()
        self.lbl_total.setText(f"WBC Counted: {tot} / 100  {'(Complete)' if tot == 100 else ''}")
        self.lbl_total.setStyleSheet(
            f"font-size: 15pt; font-weight: 700; color: {'#10B981' if tot == 100 else '#38BDF8'}; padding: 6px;"
        )
        for cell, lbl in self.cell_labels.items():
            c = self.counts[cell]
            if cell == "nRBC":
                lbl.setText(f"{c} / 100 WBC")
            else:
                pct = (c / tot * 100.0) if tot > 0 else 0.0
                lbl.setText(f"{c} ({pct:.0f}%)")

    def export_payload(self):
        summary_parts = [
            f"Neut:{self.counts['Neutrophils']}%",
            f"Lymph:{self.counts['Lymphocytes']}%",
            f"Mono:{self.counts['Monocytes']}%",
            f"Eos:{self.counts['Eosinophils']}%",
            f"Baso:{self.counts['Basophils']}%",
        ]
        if self.counts["nRBC"] > 0:
            summary_parts.append(f"nRBC:{self.counts['nRBC']}/100")
        payload = {"counts": self.counts, "morphology": self.txt_morph.toPlainText().strip()}
        return json.dumps(payload), " ".join(summary_parts), payload["morphology"]


class AntibiogramDialog(QDialog):
    """Microbiology Organism & S/I/R Susceptibility Matrix Builder."""

    def __init__(self, existing_json: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Culture & Antibiogram (S / I / R)")
        self.resize(540, 520)
        self.setStyleSheet(APP_QSS)
        apply_dark_titlebar(self)

        saved = {}
        if existing_json:
            try:
                saved = json.loads(existing_json)
            except Exception:
                saved = {}

        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Isolated Organism:"))
        self.cmb_org = QComboBox()
        self.cmb_org.setEditable(True)
        self.cmb_org.addItems(ORGANISMS_LIST)
        if saved.get("organism"):
            self.cmb_org.setCurrentText(saved["organism"])
        lay.addWidget(self.cmb_org)

        lay.addWidget(QLabel("Colony Count / Source Note:"))
        self.in_colony = QLineEdit(saved.get("colony", "> 100,000 CFU/mL Pure Growth"))
        lay.addWidget(self.in_colony)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        grid = QGridLayout(inner)
        grid.setSpacing(8)
        self.abx_combos = {}
        saved_panel = saved.get("panel", {})

        for idx, abx in enumerate(ANTIBIOTICS_LIST):
            grid.addWidget(QLabel(abx), idx, 0)
            cmb = QComboBox()
            cmb.addItems(["Not Tested (-)", "S (Susceptible)", "I (Intermediate)", "R (Resistant)"])
            prev = saved_panel.get(abx, "Not Tested (-)")
            cmb.setCurrentText(prev)
            grid.addWidget(cmb, idx, 1)
            self.abx_combos[abx] = cmb

        scroll.setWidget(inner)
        lay.addWidget(scroll)

        btn_save = QPushButton("Save Antibiogram")
        btn_save.setObjectName("SuccessBtn")
        btn_save.clicked.connect(self.accept)
        lay.addWidget(btn_save)

    def export_payload(self):
        panel = {}
        tested = []
        for abx, cmb in self.abx_combos.items():
            val = cmb.currentText()
            if not val.startswith("Not Tested"):
                panel[abx] = val
                code = val.split(" ")[0]
                tested.append(f"{abx}:{code}")
        data = {
            "organism": self.cmb_org.currentText().strip(),
            "colony": self.in_colony.text().strip(),
            "panel": panel,
        }
        short_res = f"{data['organism']} ({len(tested)} Abx)"
        return json.dumps(data), short_res


class PatientHistoryDialog(QDialog):
    """Cumulative Patient Lab Ledger + Serial Trend Chart."""

    def __init__(self, patient_id: int, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.resize(920, 600)
        self.setStyleSheet(APP_QSS)
        apply_dark_titlebar(self)

        conn = get_conn()
        pt = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
        self.rows = conn.execute("""
            SELECT o.*, t.low_val, t.high_val
            FROM orders o
            LEFT JOIN tests t ON o.test_name = t.test_name
            WHERE o.patient_id = ?
            ORDER BY COALESCE(o.verified_at, o.ordered_at) DESC
        """, (patient_id,)).fetchall()
        conn.close()

        pt_name = pt["full_name"] if pt else "Unknown Patient"
        pt_mrn = pt["mrn"] if pt else "-"
        self.setWindowTitle(f"Lab History — {pt_name} ({pt_mrn})")

        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        lbl = QLabel(f"{pt_name}  |  MRN: {pt_mrn}  |  Sex: {pt['sex'] if pt else '-'}  |  DOB: {pt['dob'] if pt else '-'}")
        lbl.setObjectName("SectionHeader")
        top.addWidget(lbl)
        top.addStretch()

        top.addWidget(QLabel("Trend Chart:"))
        self.cmb_analyte = QComboBox()
        numeric_tests = sorted({
            r["test_name"] for r in self.rows
            if r["result_value"] is not None and self._is_float(r["result_value"])
        })
        self.cmb_analyte.addItems(numeric_tests if numeric_tests else ["No Numeric History"])
        self.cmb_analyte.currentTextChanged.connect(self._plot_trend)
        top.addWidget(self.cmb_analyte)
        lay.addLayout(top)

        self.canvas = MplCanvas(width=8.5, height=2.6, dpi=100)
        lay.addWidget(self.canvas)

        self.tbl = QTableWidget(len(self.rows), 7)
        self.tbl.setHorizontalHeaderLabels(["Timestamp", "Specimen ID", "Assay", "Result", "Unit", "Flag", "Verified By"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for i, r in enumerate(self.rows):
            ts = r["verified_at"] or r["ordered_at"] or "-"
            self.tbl.setItem(i, 0, QTableWidgetItem(ts))
            self.tbl.setItem(i, 1, QTableWidgetItem(r["specimen_id"]))
            self.tbl.setItem(i, 2, QTableWidgetItem(r["test_name"]))
            self.tbl.setItem(i, 3, QTableWidgetItem(r["result_value"] or "Pending"))
            self.tbl.setItem(i, 4, QTableWidgetItem(r["unit"] or ""))
            fl = QTableWidgetItem(r["flag"] or r["status"])
            if r["flag"] in ("HIGH", "CRITICAL HIGH", "CRITICAL LOW", "ABNORMAL"):
                fl.setForeground(QColor("#FB7185"))
            elif r["flag"] == "LOW":
                fl.setForeground(QColor("#FBBF24"))
            elif r["flag"] == "NORMAL":
                fl.setForeground(QColor("#34D399"))
            self.tbl.setItem(i, 5, fl)
            self.tbl.setItem(i, 6, QTableWidgetItem(r["verified_by"] or "-"))
        lay.addWidget(self.tbl)

        self._plot_trend(self.cmb_analyte.currentText())

    @staticmethod
    def _is_float(v):
        try:
            float(v)
            return True
        except Exception:
            return False

    def _plot_trend(self, test_name: str):
        ax = self.canvas.ax
        ax.clear()
        self.canvas._style_ax(ax)

        pts = [
            r for r in reversed(self.rows)
            if r["test_name"] == test_name and self._is_float(r["result_value"])
        ]
        if not pts:
            ax.set_title("Select a numeric assay with verified history to view serial trend", fontsize=10)
            self.canvas.draw()
            return

        xs = [(r["verified_at"] or r["ordered_at"] or "")[5:16] for r in pts]
        ys = [float(r["result_value"]) for r in pts]
        lo, hi = pts[-1]["low_val"], pts[-1]["high_val"]
        unit = pts[-1]["unit"] or ""

        if lo is not None and hi is not None:
            ax.axhspan(lo, hi, color="#10B981", alpha=0.14, label=f"Normal Ref ({lo} - {hi})")
            ax.axhline(lo, color="#10B981", linestyle="--", linewidth=0.9, alpha=0.6)
            ax.axhline(hi, color="#10B981", linestyle="--", linewidth=0.9, alpha=0.6)

        ax.plot(xs, ys, color="#38BDF8", marker="o", linewidth=2.0, markersize=6, label=test_name)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:g}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", color="#F8FAFC", fontsize=8)

        ax.set_title(f"Serial Trend: {test_name} ({unit})", fontsize=10, fontweight="bold")
        ax.grid(True, color="#1E293B", linestyle=":", linewidth=0.8)
        ax.legend(loc="upper left", facecolor="#090E1A", edgecolor="#263348", labelcolor="#E2E8F0", fontsize=8)
        self.canvas.fig.tight_layout()
        self.canvas.draw()


# ==============================================================================
# PDF REPORT GENERATORS (CONSOLIDATED REPORT, BARCODE TUBE LABEL, SHIFT HANDOVER)
# ==============================================================================

def generate_specimen_pdf(patient: dict, specimen_id: str, orders: list, out_path: str):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_fill_color(11, 17, 32)
    pdf.rect(0, 0, 210, 34, style="F")
    pdf.set_text_color(56, 189, 248)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(12, 8)
    pdf.cell(130, 8, _pdf_safe("MONOCYTES DELEGATES CLINICAL LABORATORY"))
    pdf.set_text_color(203, 213, 225)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_xy(12, 16)
    pdf.cell(130, 5, _pdf_safe("ISO 15189 Accredited Diagnostic Center  |  Hematology, Chemistry & Microbiology"))
    pdf.set_xy(12, 21)
    pdf.cell(130, 5, _pdf_safe(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"))

    doc_hash = hashlib.sha256(f"{specimen_id}|{patient.get('mrn','')}|{len(orders)}".encode()).hexdigest()[:12].upper()
    pdf.set_xy(145, 9)
    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(52, 211, 153)
    pdf.cell(53, 6, _pdf_safe(f"SPECIMEN: {specimen_id}"), align="R")
    pdf.set_xy(145, 16)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(53, 5, _pdf_safe(f"AUTH HASH: #{doc_hash}"), align="R")

    pdf.set_xy(12, 39)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(12, 39, 186, 24, style="DF")

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_xy(15, 42)
    pdf.cell(95, 5, _pdf_safe(f"Patient Name: {patient.get('full_name', 'N/A')}"))
    pdf.set_xy(115, 42)
    pdf.cell(80, 5, _pdf_safe(f"MRN: {patient.get('mrn', 'N/A')}"))

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(15, 48)
    pdf.cell(95, 5, _pdf_safe(f"DOB / Sex: {patient.get('dob', '-')}  /  {patient.get('sex', '-')}"))
    pdf.set_xy(115, 48)
    pdf.cell(80, 5, _pdf_safe(f"Requesting MD: {patient.get('physician', 'Walk-In / OPD')}"))

    priority = orders[0].get("priority", "Routine") if orders else "Routine"
    collected = orders[0].get("collected_at") or orders[0].get("ordered_at") or "-"
    pdf.set_xy(15, 54)
    pdf.cell(95, 5, _pdf_safe(f"Collected / Received: {collected}"))
    pdf.set_xy(115, 54)
    pdf.cell(80, 5, _pdf_safe(f"Priority: {priority}  |  Storage: {orders[0].get('storage_slot') or 'Bench'}"))

    y = 68
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8.5)
    headers = [("TEST / ASSAY", 58), ("RESULT", 26), ("FLAG", 24), ("UNIT", 22), ("REF. RANGE", 30), ("PRIOR", 26)]
    x = 12
    for title, w_col in headers:
        pdf.set_xy(x, y)
        pdf.cell(w_col, 7, _pdf_safe(title), border=1, fill=True, align="C" if title != "TEST / ASSAY" else "L")
        x += w_col
    y += 7

    conn = get_conn()
    verifiers = set()
    pathologist_sig = ""
    pathologist_notes = []
    antibiograms = []
    diffs = []

    for idx, o in enumerate(orders):
        if y > 245:
            pdf.add_page()
            y = 18

        if o.get("verified_by"):
            verifiers.add(o["verified_by"])
        if o.get("pathologist_signed_by"):
            pathologist_sig = f"{o['pathologist_signed_by']} ({o.get('pathologist_signed_at', '')})"
        if o.get("pathologist_note"):
            pathologist_notes.append(f"[{o['test_name']}] {o['pathologist_note']}")
        if o.get("antibiogram_json"):
            try:
                antibiograms.append((o["test_name"], json.loads(o["antibiogram_json"])))
            except Exception:
                pass
        if o.get("diff_json"):
            try:
                diffs.append((o["test_name"], json.loads(o["diff_json"])))
            except Exception:
                pass

        prior_row = conn.execute("""
            SELECT result_value FROM orders
            WHERE patient_id = ? AND test_name = ? AND id < ? AND result_value IS NOT NULL AND result_value != ''
            ORDER BY id DESC LIMIT 1
        """, (patient["id"], o["test_name"], o["id"])).fetchone()
        prior_val = prior_row["result_value"] if prior_row else "-"

        flag = o.get("flag") or o.get("status") or "-"
        is_crit = "CRITICAL" in flag or flag in ("HIGH", "ABNORMAL")
        is_low = flag == "LOW"

        pdf.set_fill_color(255, 255, 255) if idx % 2 == 0 else pdf.set_fill_color(248, 250, 252)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B" if is_crit else "", 8.5)

        vals = [
            (o["test_name"], 58, "L"),
            (o.get("result_value") or "Pending", 26, "C"),
            (flag, 24, "C"),
            (o.get("unit") or "-", 22, "C"),
            (o.get("ref_range") or "-", 30, "C"),
            (prior_val, 26, "C"),
        ]
        x = 12
        for col_idx, (val, w_col, al) in enumerate(vals):
            if col_idx in (1, 2) and is_crit:
                pdf.set_text_color(190, 18, 60)
            elif col_idx in (1, 2) and is_low:
                pdf.set_text_color(180, 83, 9)
            else:
                pdf.set_text_color(15, 23, 42)
            pdf.set_xy(x, y)
            pdf.cell(w_col, 6.5, _pdf_safe(val), border=1, fill=True, align=al)
            x += w_col
        y += 6.5

        note_bits = []
        if o.get("panic_notified_to"):
            note_bits.append(f"PANIC READ-BACK: Notified {o['panic_notified_to']}")
        if o.get("delta_flag"):
            note_bits.append(f"DELTA ALERT: {o['delta_flag']}")
        if o.get("amended_reason"):
            note_bits.append(f"AMENDED: {o['amended_reason']}")
        if o.get("notes"):
            note_bits.append(f"Note: {o['notes']}")
        if note_bits:
            pdf.set_text_color(71, 85, 105)
            pdf.set_font("Helvetica", "I", 7.8)
            pdf.set_xy(14, y)
            pdf.multi_cell(182, 4.5, _pdf_safe("  |  ".join(note_bits)))
            y = pdf.get_y() + 1

    conn.close()

    for t_name, d_obj in diffs:
        y += 3
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(12, y)
        pdf.cell(186, 5, _pdf_safe(f"Manual 100-Cell WBC Differential & Smear Morphology ({t_name}):"))
        y += 5
        c = d_obj.get("counts", {})
        line = (
            f"Neutrophils: {c.get('Neutrophils', 0)}%   |   Lymphocytes: {c.get('Lymphocytes', 0)}%   |   "
            f"Monocytes: {c.get('Monocytes', 0)}%   |   Eosinophils: {c.get('Eosinophils', 0)}%   |   "
            f"Basophils: {c.get('Basophils', 0)}%   |   nRBC: {c.get('nRBC', 0)}/100 WBC"
        )
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_xy(14, y)
        pdf.cell(184, 5, _pdf_safe(line))
        y += 5
        if d_obj.get("morphology"):
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_xy(14, y)
            pdf.multi_cell(184, 4.5, _pdf_safe(f"Morphology: {d_obj['morphology']}"))
            y = pdf.get_y() + 2

    for t_name, abg in antibiograms:
        y += 3
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(12, y)
        pdf.cell(186, 5, _pdf_safe(f"Microbiology Antibiogram — Organism: {abg.get('organism', '-')} ({abg.get('colony', '')})"))
        y += 5.5
        panel = abg.get("panel", {})
        pdf.set_font("Helvetica", "", 8)
        for abx, interp in panel.items():
            pdf.set_xy(14, y)
            pdf.cell(85, 5, _pdf_safe(abx), border=1)
            pdf.cell(45, 5, _pdf_safe(interp), border=1, align="C")
            y += 5

    if pathologist_notes:
        y += 4
        pdf.set_fill_color(239, 246, 255)
        pdf.set_draw_color(59, 130, 246)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(30, 58, 138)
        pdf.set_xy(12, y)
        pdf.cell(186, 6, _pdf_safe("PATHOLOGIST CLINICAL IMPRESSION / INTERPRETATION"), border=1, fill=True)
        y += 6
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(12, y)
        pdf.multi_cell(186, 5, _pdf_safe("\n".join(pathologist_notes)), border=1)
        y = pdf.get_y() + 2

    y = max(y + 12, 248)
    if y > 268:
        pdf.add_page()
        y = 240

    rmt_line = ", ".join(sorted(verifiers)) if verifiers else "Pending RMT Verification"
    pdf.set_draw_color(100, 116, 139)
    pdf.line(15, y, 95, y)
    pdf.line(115, y, 195, y)

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.set_xy(15, y + 1.5)
    pdf.cell(80, 4.5, _pdf_safe(rmt_line), align="C")
    pdf.set_xy(115, y + 1.5)
    pdf.cell(80, 4.5, _pdf_safe("Gaia Aubrey Manalo, MD"), align="C")

    pdf.set_font("Helvetica", "", 7.8)
    pdf.set_text_color(71, 85, 105)
    pdf.set_xy(15, y + 6)
    pdf.cell(80, 4, _pdf_safe("Performing Medical Technologist (RMT)"), align="C")
    pdf.set_xy(115, y + 6)
    pdf.cell(80, 4, _pdf_safe(f"Anatomic & Clinical Pathologist  {pathologist_sig}"), align="C")

    pdf.output(out_path)


def generate_barcode_label_pdf(patient: dict, specimen_id: str, order: dict, out_path: str):
    """Generates a 3.0 x 1.5 inch (76.2 x 38.1 mm) thermal tube barcode label."""
    pdf = FPDF(orientation="L", unit="mm", format=(38.1, 76.2))
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(3, 2.5)
    pdf.cell(70, 4, _pdf_safe(f"{patient.get('full_name', '')[:28]}  ({patient.get('sex', '-')})"))

    pdf.set_font("Courier", "B", 7.5)
    pdf.set_xy(3, 6.5)
    pdf.cell(70, 3.5, _pdf_safe(f"MRN: {patient.get('mrn', '-')}  |  {order.get('priority', 'Routine').upper()}"))

    digest = hashlib.sha256(specimen_id.encode()).hexdigest()
    bx = 5.0
    pdf.set_fill_color(0, 0, 0)
    for i, ch in enumerate(digest[:42]):
        val = int(ch, 16)
        bar_w = 0.45 if (val % 3 == 0) else 0.85
        gap_w = 0.45 if (val % 2 == 0) else 0.75
        if bx + bar_w < 71.0:
            pdf.rect(bx, 11.0, bar_w, 13.0, style="F")
        bx += bar_w + gap_w

    pdf.set_font("Courier", "B", 8.5)
    pdf.set_xy(3, 24.5)
    pdf.cell(70, 4, _pdf_safe(specimen_id), align="C")

    pdf.set_font("Helvetica", "B", 7)
    pdf.set_xy(3, 29.0)
    tube = order.get("tube_type") or "Gold (SST)"
    pdf.cell(70, 3.5, _pdf_safe(f"{order.get('test_name', '')[:24]} | {tube}"), align="C")

    pdf.output(out_path)


def generate_shift_handover_pdf(operator_name: str, shift_label: str, out_path: str):
    conn = get_conn()
    pending = conn.execute("""
        SELECT o.specimen_id, p.full_name, o.test_name, o.priority, o.ordered_at, o.storage_slot
        FROM orders o JOIN patients p ON o.patient_id = p.id
        WHERE o.status NOT IN ('Verified', 'Amended', 'Rejected')
        ORDER BY CASE WHEN o.priority='STAT' THEN 0 ELSE 1 END, o.ordered_at ASC
    """).fetchall()
    criticals = conn.execute("""
        SELECT o.specimen_id, p.full_name, o.test_name, o.result_value, o.panic_notified_to, o.verified_at
        FROM orders o JOIN patients p ON o.patient_id = p.id
        WHERE o.critical_flag = 1 OR o.flag LIKE 'CRITICAL%'
        ORDER BY o.verified_at DESC LIMIT 25
    """).fetchall()
    total_cnt = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    ver_cnt = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Verified', 'Amended')").fetchone()[0]
    conn.close()

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_fill_color(11, 17, 32)
    pdf.rect(0, 0, 210, 28, style="F")
    pdf.set_text_color(56, 189, 248)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(12, 7)
    pdf.cell(186, 7, _pdf_safe(f"MONOCYTES DELEGATES LIS — SHIFT ENDORSEMENT ({shift_label})"))
    pdf.set_text_color(226, 232, 240)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(12, 16)
    pdf.cell(186, 5, _pdf_safe(f"Endorsing RMT: {operator_name}  |  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Verified: {ver_cnt}/{total_cnt}"))

    y = 34
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(12, y)
    pdf.cell(186, 6, _pdf_safe(f"1. Pending Carry-Over Specimens ({len(pending)})"))
    y += 7
    pdf.set_font("Helvetica", "", 8.5)
    if not pending:
        pdf.set_xy(14, y)
        pdf.cell(180, 5, _pdf_safe("Zero pending carry-over orders. All bench queues clear."))
        y += 7
    else:
        for r in pending[:30]:
            pdf.set_xy(14, y)
            pdf.cell(182, 5, _pdf_safe(f"[{r['priority']}] {r['specimen_id']} | {r['full_name']} | {r['test_name']} | Slot: {r['storage_slot'] or 'Bench'}"), border="B")
            y += 5.5

    y += 6
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(12, y)
    pdf.cell(186, 6, _pdf_safe(f"2. Critical Panic Value Read-Backs ({len(criticals)})"))
    y += 7
    pdf.set_font("Helvetica", "", 8.5)
    for r in criticals[:20]:
        pdf.set_xy(14, y)
        pdf.cell(182, 5, _pdf_safe(f"{r['specimen_id']} | {r['full_name']} | {r['test_name']} = {r['result_value']} | Notified: {r['panic_notified_to'] or 'Logged'}"), border="B")
        y += 5.5

    pdf.output(out_path)


# ==============================================================================
# MAIN WORKSPACE
# ==============================================================================

class MainWorkspace(QWidget):
    lock_requested = Signal()

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.user = current_user
        self.selected_order_id = None
        self.qc_lockout_enabled = False
        self.failed_qc_tests = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Clean Top Header Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopHeaderBar")
        top_bar.setFixedHeight(52)
        tb_lay = QHBoxLayout(top_bar)
        tb_lay.setContentsMargins(16, 6, 16, 6)
        tb_lay.setSpacing(12)

        lbl_logo = QLabel("Monocytes Delegates LIS")
        lbl_logo.setStyleSheet("color: #F8FAFC; font-size: 12pt; font-weight: 700;")
        tb_lay.addWidget(lbl_logo)

        self.lbl_qc_pill = QLabel("QC: In Control")
        self.lbl_qc_pill.setStyleSheet(
            "background-color: rgba(16,185,129,0.14); border: 1px solid #10B981; "
            "color: #34D399; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 8.5pt;"
        )
        tb_lay.addWidget(self.lbl_qc_pill)

        tb_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setObjectName("MonoBadge")
        tb_lay.addWidget(self.lbl_clock)

        role_short = "Pathologist" if "Pathologist" in self.user["role"] else "RMT"
        lbl_op = QLabel(f"{self.user['name']}  •  {role_short}")
        lbl_op.setStyleSheet(
            "background-color: #131C31; border: 1px solid #334155; color: #E2E8F0; "
            "border-radius: 6px; padding: 4px 12px; font-weight: 600;"
        )
        tb_lay.addWidget(lbl_op)

        btn_lock = QPushButton("Lock / Switch User")
        btn_lock.setObjectName("DangerBtn")
        btn_lock.clicked.connect(self.lock_requested.emit)
        tb_lay.addWidget(btn_lock)

        root.addWidget(top_bar)

        # Main Tabbed Workspace (No sparkline KPI cards cluttering the workbench)
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(12, 10, 12, 12)
        body_lay.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_worklist_tab(), "Worklist")
        self.tabs.addTab(self._build_requisition_tab(), "New Order")
        self.tabs.addTab(self._build_pathologist_tab(), "Pathologist Review")
        self.tabs.addTab(self._build_qc_tab(), "Quality Control")
        self.tabs.addTab(self._build_patients_tab(), "Patients")
        self.tabs.addTab(self._build_catalog_tab(), "Test Catalog")
        self.tabs.addTab(self._build_admin_tab(), "Admin & Handover")
        body_lay.addWidget(self.tabs, 1)

        root.addWidget(body, 1)

        sc = QShortcut(QKeySequence("Ctrl+F"), self)
        sc.activated.connect(self._focus_search)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self.refresh_all()

    def _update_clock(self):
        self.lbl_clock.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _focus_search(self):
        self.tabs.setCurrentIndex(0)
        self.in_search.setFocus()
        self.in_search.selectAll()

    # --------------------------------------------------------------------------
    # TAB 1: WORKLIST & CLINICAL INSPECTOR
    # --------------------------------------------------------------------------
    def _build_worklist_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        # Clean Filter, Quick Counter & New Order Bar
        flt = QHBoxLayout()
        flt.setSpacing(8)

        self.in_search = QLineEdit()
        self.in_search.setPlaceholderText("Search specimen ID, patient name, MRN, or test (Ctrl+F)...")
        self.in_search.textChanged.connect(self.refresh_worklist)
        flt.addWidget(self.in_search, 3)

        self.cmb_dept_filter = QComboBox()
        self.cmb_dept_filter.addItems([
            "All Departments", "Hematology", "Clinical Chemistry", "Coagulation",
            "Immunology", "Serology", "Clinical Microscopy", "Microbiology"
        ])
        self.cmb_dept_filter.currentTextChanged.connect(self.refresh_worklist)
        flt.addWidget(self.cmb_dept_filter, 1)

        self.cmb_status_filter = QComboBox()
        self.cmb_status_filter.addItems([
            "All Statuses", "Pending / Active", "STAT Only",
            "Critical / Abnormal", "Verified / Amended", "Rejected"
        ])
        self.cmb_status_filter.currentTextChanged.connect(self.refresh_worklist)
        flt.addWidget(self.cmb_status_filter, 1)

        self.lbl_queue_counts = QLabel("Total: 0  |  Pending: 0  |  STAT: 0  |  Verified: 0")
        self.lbl_queue_counts.setObjectName("MonoBadge")
        flt.addWidget(self.lbl_queue_counts)

        btn_new = QPushButton("+ New Order")
        btn_new.setObjectName("PrimaryBtn")
        btn_new.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        flt.addWidget(btn_new)

        lay.addLayout(flt)

        splitter = QSplitter(Qt.Horizontal)

        # Left: Live Worklist Table
        self.tbl_worklist = QTableWidget(0, 9)
        self.tbl_worklist.setHorizontalHeaderLabels([
            "ID", "Specimen ID", "Patient Name", "Test / Assay", "Department", "Priority", "TAT", "Result", "Status"
        ])
        self.tbl_worklist.setColumnHidden(0, True)
        hdr = self.tbl_worklist.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(True)
        self.tbl_worklist.setColumnWidth(1, 130)
        self.tbl_worklist.setColumnWidth(2, 165)
        self.tbl_worklist.setColumnWidth(3, 195)
        self.tbl_worklist.setColumnWidth(4, 125)
        self.tbl_worklist.setColumnWidth(5, 72)
        self.tbl_worklist.setColumnWidth(6, 78)
        self.tbl_worklist.setColumnWidth(7, 105)
        self.tbl_worklist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_worklist.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_worklist.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_worklist.setAlternatingRowColors(True)
        self.tbl_worklist.itemSelectionChanged.connect(self._on_worklist_select)
        self.tbl_worklist.doubleClicked.connect(lambda: self.in_result.setFocus())
        splitter.addWidget(self.tbl_worklist)

        # Right: Clean Result Entry & Specimen Inspector
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)
        insp = QFrame()
        insp.setObjectName("SurfaceCard")
        il = QVBoxLayout(insp)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(10)

        self.lbl_insp_spec = QLabel("Select a specimen row")
        self.lbl_insp_spec.setObjectName("SectionHeader")
        self.lbl_insp_spec.setWordWrap(True)
        il.addWidget(self.lbl_insp_spec)

        self.lbl_insp_meta = QLabel("Click any row on the left to enter results, inspect reference ranges, or print reports.")
        self.lbl_insp_meta.setObjectName("MutedLabel")
        self.lbl_insp_meta.setWordWrap(True)
        il.addWidget(self.lbl_insp_meta)

        self.tube_badge = TubeBadgeWidget()
        il.addWidget(self.tube_badge)

        self.range_gauge = VectorRangeGauge()
        il.addWidget(self.range_gauge)

        # Section 1: Result Verification
        grp_res = QLabel("RESULT ENTRY & VERIFICATION")
        grp_res.setObjectName("GroupTitle")
        il.addWidget(grp_res)

        self.in_result = QLineEdit()
        self.in_result.setPlaceholderText("Enter numeric or qualitative result (Press Enter to verify)...")
        self.in_result.returnPressed.connect(self._verify_selected_order)
        il.addWidget(self.in_result)

        self.in_notes = QLineEdit()
        self.in_notes.setPlaceholderText("Optional clinical or bench note...")
        il.addWidget(self.in_notes)

        act_row = QHBoxLayout()
        self.btn_verify = QPushButton("Verify & Release")
        self.btn_verify.setObjectName("SuccessBtn")
        self.btn_verify.setMinimumHeight(38)
        self.btn_verify.clicked.connect(self._verify_selected_order)
        act_row.addWidget(self.btn_verify, 2)

        btn_reject = QPushButton("Reject")
        btn_reject.setObjectName("DangerBtn")
        btn_reject.setMinimumHeight(38)
        btn_reject.clicked.connect(self._reject_selected_order)
        act_row.addWidget(btn_reject, 1)
        il.addLayout(act_row)

        # Section 2: Specimen Handling & Clinical Tools
        grp_tools = QLabel("SPECIMEN HANDLING & BENCH TOOLS")
        grp_tools.setObjectName("GroupTitle")
        il.addWidget(grp_tools)

        stage_row = QHBoxLayout()
        btn_collect = QPushButton("Collected")
        btn_collect.clicked.connect(lambda: self._advance_stage("Collected"))
        btn_proc = QPushButton("In-Process")
        btn_proc.clicked.connect(lambda: self._advance_stage("In-Process"))
        btn_store = QPushButton("Storage Slot")
        btn_store.clicked.connect(self._assign_storage_slot)
        stage_row.addWidget(btn_collect)
        stage_row.addWidget(btn_proc)
        stage_row.addWidget(btn_store)
        il.addLayout(stage_row)

        tools_row = QHBoxLayout()
        btn_calc = QPushButton("Calculators")
        btn_calc.clicked.connect(self._open_calculators)
        btn_diff = QPushButton("100-Cell Diff")
        btn_diff.clicked.connect(self._open_wbc_diff)
        btn_abx = QPushButton("Antibiogram")
        btn_abx.clicked.connect(self._open_antibiogram)
        tools_row.addWidget(btn_calc)
        tools_row.addWidget(btn_diff)
        tools_row.addWidget(btn_abx)
        il.addLayout(tools_row)

        # Section 3: Reports & History
        grp_rep = QLabel("REPORTS & PATIENT RECORD")
        grp_rep.setObjectName("GroupTitle")
        il.addWidget(grp_rep)

        exp_row = QHBoxLayout()
        btn_pdf = QPushButton("Print Report (PDF)")
        btn_pdf.setObjectName("PrimaryBtn")
        btn_pdf.clicked.connect(self._print_consolidated_pdf)
        btn_lbl = QPushButton("Tube Label")
        btn_lbl.clicked.connect(self._print_tube_label)
        btn_hist = QPushButton("History")
        btn_hist.clicked.connect(self._open_selected_patient_history)
        exp_row.addWidget(btn_pdf)
        exp_row.addWidget(btn_lbl)
        exp_row.addWidget(btn_hist)
        il.addLayout(exp_row)

        il.addStretch()
        scroll.setWidget(insp)
        splitter.addWidget(scroll)
        splitter.setSizes([860, 420])

        lay.addWidget(splitter, 1)
        return w

    def _on_worklist_select(self):
        rows = self.tbl_worklist.selectionModel().selectedRows()
        if not rows:
            return
        order_id = int(self.tbl_worklist.item(rows[0].row(), 0).text())
        self.selected_order_id = order_id

        conn = get_conn()
        o = conn.execute("""
            SELECT o.*, p.full_name, p.mrn, p.sex, p.dob, t.low_val, t.high_val, t.crit_low, t.crit_high
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            LEFT JOIN tests t ON o.test_name = t.test_name
            WHERE o.id = ?
        """, (order_id,)).fetchone()
        conn.close()
        if not o:
            return

        self.lbl_insp_spec.setText(f"{o['specimen_id']}  •  {o['test_name']}")
        slot_txt = o["storage_slot"] or "Unassigned"
        self.lbl_insp_meta.setText(
            f"Patient: {o['full_name']} ({o['mrn']})  |  {o['sex'] or '-'} / {o['dob'] or '-'}\n"
            f"Priority: {o['priority']}  |  Stage: {o['status']}  |  Storage: {slot_txt}\n"
            f"Reference Range: {o['ref_range'] or '-'} {o['unit'] or ''}"
        )
        self.tube_badge.set_tube(o["tube_type"])
        self.in_result.setText(o["result_value"] or "")
        self.in_notes.setText(o["notes"] or "")
        self.range_gauge.set_reading(
            o["result_value"] or "", o["low_val"], o["high_val"], o["crit_low"], o["crit_high"],
            o["flag"] or o["status"]
        )

    def _advance_stage(self, stage: str):
        if not self.selected_order_id:
            return
        conn = get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if stage == "Collected":
            conn.execute("UPDATE orders SET status = ?, collected_at = COALESCE(collected_at, ?) WHERE id = ?", (stage, now, self.selected_order_id))
        else:
            conn.execute("UPDATE orders SET status = ? WHERE id = ?", (stage, self.selected_order_id))
        row = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
        conn.commit()
        conn.close()
        log_audit(self.user["name"], f"STAGE_{stage.upper()}", row["specimen_id"] if row else "-", f"Order #{self.selected_order_id}")
        self.refresh_all()

    def _assign_storage_slot(self):
        if not self.selected_order_id:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Assign Specimen Storage Slot")
        dlg.setStyleSheet(APP_QSS)
        apply_dark_titlebar(dlg)
        l = QVBoxLayout(dlg)
        l.addWidget(QLabel("Storage Unit & Rack Slot:"))
        cmb_u = QComboBox()
        cmb_u.addItems(["Fridge A (2-8°C)", "Fridge B (2-8°C)", "Freezer (-20°C)", "Hematology Rack 1", "Chemistry Rack 2"])
        in_pos = QLineEdit("Rack 1 - Slot A1")
        l.addWidget(cmb_u)
        l.addWidget(in_pos)
        b = QPushButton("Save Location")
        b.setObjectName("PrimaryBtn")
        b.clicked.connect(dlg.accept)
        l.addWidget(b)
        if dlg.exec() == QDialog.Accepted:
            slot = f"{cmb_u.currentText()} ({in_pos.text().strip()})"
            conn = get_conn()
            conn.execute("UPDATE orders SET storage_slot = ? WHERE id = ?", (slot, self.selected_order_id))
            conn.commit()
            conn.close()
            self.refresh_all()

    def _open_calculators(self):
        dlg = RmtCalculatorDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.generated_summary:
            cur = self.in_notes.text().strip()
            self.in_notes.setText(f"{cur} | {dlg.generated_summary}".strip(" |"))

    def _open_wbc_diff(self):
        if not self.selected_order_id:
            QMessageBox.information(self, "Select Specimen", "Select a Hematology / CBC / PBS order first.")
            return
        conn = get_conn()
        o = conn.execute("SELECT diff_json, specimen_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
        conn.close()
        dlg = WbcDiffCounterDialog(o["diff_json"] or "", self)
        if dlg.exec() == QDialog.Accepted:
            raw_json, summary, morph = dlg.export_payload()
            conn = get_conn()
            conn.execute("UPDATE orders SET diff_json = ? WHERE id = ?", (raw_json, self.selected_order_id))
            conn.commit()
            conn.close()
            if not self.in_result.text().strip():
                self.in_result.setText(summary)
            self.in_notes.setText(morph)
            log_audit(self.user["name"], "WBC_DIFF_SAVED", o["specimen_id"], summary)
            self.refresh_all()

    def _open_antibiogram(self):
        if not self.selected_order_id:
            QMessageBox.information(self, "Select Specimen", "Select a Microbiology / Culture order first.")
            return
        conn = get_conn()
        o = conn.execute("SELECT antibiogram_json, specimen_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
        conn.close()
        dlg = AntibiogramDialog(o["antibiogram_json"] or "", self)
        if dlg.exec() == QDialog.Accepted:
            raw_json, short_res = dlg.export_payload()
            conn = get_conn()
            conn.execute("UPDATE orders SET antibiogram_json = ? WHERE id = ?", (raw_json, self.selected_order_id))
            conn.commit()
            conn.close()
            self.in_result.setText(short_res)
            log_audit(self.user["name"], "ANTIBIOGRAM_SAVED", o["specimen_id"], short_res)
            self.refresh_all()

    def _verify_selected_order(self):
        if not self.selected_order_id:
            QMessageBox.information(self, "No Selection", "Please select a specimen order from the worklist first.")
            return
        val_str = self.in_result.text().strip()
        if not val_str:
            QMessageBox.warning(self, "Missing Result", "Enter a result value before verifying.")
            return

        conn = get_conn()
        o = conn.execute("""
            SELECT o.*, t.low_val, t.high_val, t.crit_low, t.crit_high, t.delta_pct
            FROM orders o
            LEFT JOIN tests t ON o.test_name = t.test_name
            WHERE o.id = ?
        """, (self.selected_order_id,)).fetchone()
        if not o:
            conn.close()
            return

        if self.qc_lockout_enabled and o["test_name"] in self.failed_qc_tests:
            conn.close()
            QMessageBox.critical(
                self, "QC Lockout Active",
                f"Verification blocked for {o['test_name']}.\nResolve the active Westgard 1-3s QC failure first."
            )
            return

        flag = "NORMAL"
        is_crit = 0
        try:
            v = float(val_str)
            if o["crit_low"] is not None and v <= o["crit_low"]:
                flag = "CRITICAL LOW"
                is_crit = 1
            elif o["crit_high"] is not None and v >= o["crit_high"]:
                flag = "CRITICAL HIGH"
                is_crit = 1
            elif o["low_val"] is not None and v < o["low_val"]:
                flag = "LOW"
            elif o["high_val"] is not None and v > o["high_val"]:
                flag = "HIGH"
        except Exception:
            upper_v = val_str.upper()
            if any(k in upper_v for k in ("REACTIVE", "POSITIVE", "MRSA", "SCHISTOCYTE", "ABNORMAL")):
                flag = "ABNORMAL"

        delta_msg = ""
        prior = conn.execute("""
            SELECT result_value FROM orders
            WHERE patient_id = ? AND test_name = ? AND id != ? AND result_value IS NOT NULL AND result_value != ''
            ORDER BY id DESC LIMIT 1
        """, (o["patient_id"], o["test_name"], o["id"])).fetchone()
        if prior and o["delta_pct"]:
            try:
                v_now = float(val_str)
                v_old = float(prior["result_value"])
                if v_old != 0:
                    pct_diff = abs((v_now - v_old) / v_old) * 100.0
                    if pct_diff >= float(o["delta_pct"]):
                        delta_msg = f"{pct_diff:.0f}% shift vs prior ({v_old:g})"
                        ans = QMessageBox.warning(
                            self, "Delta Check Alert",
                            f"Result shifted {pct_diff:.1f}% from prior value ({v_old:g} -> {v_now:g}).\n"
                            f"Confirm specimen identity and proceed with release?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if ans != QMessageBox.Yes:
                            conn.close()
                            return
            except Exception:
                pass

        panic_notified = o["panic_notified_to"] or ""
        if is_crit:
            dlg = QDialog(self)
            dlg.setWindowTitle("Critical Value — Read-Back Log")
            dlg.setStyleSheet(APP_QSS)
            apply_dark_titlebar(dlg)
            dl = QVBoxLayout(dlg)
            warn = QLabel(f"CRITICAL VALUE: {o['test_name']} = {val_str} ({flag})\nRecord physician/nurse notified and read-back confirmation:")
            warn.setStyleSheet("color: #FB7185; font-weight: 700;")
            dl.addWidget(warn)
            in_md = QLineEdit()
            in_md.setPlaceholderText("e.g., Dr. Santos / Nurse Cruz — Read-back confirmed")
            dl.addWidget(in_md)
            b_ok = QPushButton("Confirm Read-Back & Release")
            b_ok.setObjectName("DangerBtn")
            b_ok.clicked.connect(dlg.accept)
            dl.addWidget(b_ok)
            if dlg.exec() != QDialog.Accepted or not in_md.text().strip():
                conn.close()
                return
            panic_notified = f"{in_md.text().strip()} @ {datetime.now().strftime('%H:%M')}"

        new_status = "Verified"
        amend_reason = o["amended_reason"] or ""
        if o["status"] in ("Verified", "Amended") and o["result_value"] != val_str:
            dlg_am = QDialog(self)
            dlg_am.setWindowTitle("Result Amendment Reason")
            dlg_am.setStyleSheet(APP_QSS)
            apply_dark_titlebar(dlg_am)
            al = QVBoxLayout(dlg_am)
            al.addWidget(QLabel(f"Amending verified result ({o['result_value']} -> {val_str}). Enter reason:"))
            in_am = QLineEdit()
            in_am.setPlaceholderText("e.g., Repeat dilution check / Clerical correction")
            al.addWidget(in_am)
            b_am = QPushButton("Record Amendment")
            b_am.setObjectName("PrimaryBtn")
            b_am.clicked.connect(dlg_am.accept)
            al.addWidget(b_am)
            if dlg_am.exec() != QDialog.Accepted or not in_am.text().strip():
                conn.close()
                return
            new_status = "Amended"
            amend_reason = f"{in_am.text().strip()} (was {o['result_value']})"

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE orders SET
                result_value = ?, flag = ?, status = ?, notes = ?,
                verified_by = ?, verified_at = ?, amended_reason = ?,
                panic_notified_to = ?, delta_flag = ?, critical_flag = ?
            WHERE id = ?
        """, (
            val_str, flag, new_status, self.in_notes.text().strip(),
            self.user["name"], now, amend_reason,
            panic_notified, delta_msg, is_crit, self.selected_order_id
        ))
        conn.commit()
        conn.close()

        log_audit(self.user["name"], f"RESULT_{new_status.upper()}", o["specimen_id"], f"{o['test_name']} = {val_str} [{flag}]")
        self.refresh_all()

    def _reject_selected_order(self):
        if not self.selected_order_id:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Reject Specimen")
        dlg.setStyleSheet(APP_QSS)
        apply_dark_titlebar(dlg)
        l = QVBoxLayout(dlg)
        l.addWidget(QLabel("Select Rejection Reason:"))
        cmb = QComboBox()
        cmb.addItems([
            "Grossly Hemolyzed", "Quantity Not Sufficient (QNS)", "Clotted EDTA Sample",
            "Unlabeled / Mislabeled Tube", "Lipemic / Icteric Interference", "Improper Container / Expired Tube"
        ])
        l.addWidget(cmb)
        b = QPushButton("Confirm Rejection")
        b.setObjectName("DangerBtn")
        b.clicked.connect(dlg.accept)
        l.addWidget(b)
        if dlg.exec() == QDialog.Accepted:
            reason = cmb.currentText()
            conn = get_conn()
            row = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
            conn.execute("""
                UPDATE orders SET status = 'Rejected', flag = 'REJECTED', notes = ?, verified_by = ?, verified_at = ?
                WHERE id = ?
            """, (f"REJECTED: {reason}", self.user["name"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.selected_order_id))
            conn.commit()
            conn.close()
            log_audit(self.user["name"], "SPECIMEN_REJECTED", row["specimen_id"] if row else "-", reason)
            self.refresh_all()

    def _print_consolidated_pdf(self):
        if not self.selected_order_id:
            QMessageBox.information(self, "Select Specimen", "Select an order from the worklist to print its report.")
            return
        conn = get_conn()
        sel = conn.execute("SELECT specimen_id, patient_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
        if not sel:
            conn.close()
            return
        pt = dict(conn.execute("SELECT * FROM patients WHERE id = ?", (sel["patient_id"],)).fetchone())
        orders = [dict(r) for r in conn.execute("SELECT * FROM orders WHERE specimen_id = ? ORDER BY id ASC", (sel["specimen_id"],)).fetchall()]
        conn.close()

        default_name = f"{sel['specimen_id']}_Report.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save Lab Report PDF", default_name, "PDF Files (*.pdf)")
        if path:
            try:
                generate_specimen_pdf(pt, sel["specimen_id"], orders, path)
                log_audit(self.user["name"], "PDF_REPORT_PRINTED", sel["specimen_id"], path)
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    QMessageBox.information(self, "PDF Saved", f"Saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "PDF Error", str(e))

    def _print_tube_label(self):
        if not self.selected_order_id:
            return
        conn = get_conn()
        o = dict(conn.execute("SELECT * FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone())
        pt = dict(conn.execute("SELECT * FROM patients WHERE id = ?", (o["patient_id"],)).fetchone())
        conn.close()

        path, _ = QFileDialog.getSaveFileName(self, "Save Tube Barcode Label", f"{o['specimen_id']}_Label.pdf", "PDF Files (*.pdf)")
        if path:
            generate_barcode_label_pdf(pt, o["specimen_id"], o, path)
            if sys.platform == "win32":
                os.startfile(path)

    def _open_selected_patient_history(self):
        if not self.selected_order_id:
            return
        conn = get_conn()
        o = conn.execute("SELECT patient_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
        conn.close()
        if o:
            PatientHistoryDialog(o["patient_id"], self).exec()

    # --------------------------------------------------------------------------
    # TAB 2: NEW ORDER & ACCESSIONING
    # --------------------------------------------------------------------------
    def _build_requisition_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(14)

        # Left: Patient Details
        left = QFrame()
        left.setObjectName("SurfaceCard")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(16, 16, 16, 16)
        ll.setSpacing(10)

        lbl = QLabel("1. Patient & Order Details")
        lbl.setObjectName("SectionHeader")
        ll.addWidget(lbl)

        ll.addWidget(QLabel("Existing Patient (or leave as New Patient):"))
        self.cmb_req_patient = QComboBox()
        self.cmb_req_patient.currentIndexChanged.connect(self._on_req_patient_pick)
        ll.addWidget(self.cmb_req_patient)

        self.in_pt_name = QLineEdit(); self.in_pt_name.setPlaceholderText("Full Name (Last, First MI)")
        self.in_pt_mrn = QLineEdit(); self.in_pt_mrn.setPlaceholderText("MRN (auto-generated if blank)")
        self.in_pt_dob = QLineEdit(); self.in_pt_dob.setPlaceholderText("DOB (YYYY-MM-DD) or Age")
        self.cmb_pt_sex = QComboBox(); self.cmb_pt_sex.addItems(["Female", "Male", "Other"])
        self.in_pt_md = QLineEdit(); self.in_pt_md.setPlaceholderText("Requesting Physician (e.g., Dr. Santos)")

        ll.addWidget(QLabel("Patient Full Name:")); ll.addWidget(self.in_pt_name)
        ll.addWidget(QLabel("Medical Record Number (MRN):")); ll.addWidget(self.in_pt_mrn)
        r_ds = QHBoxLayout()
        r_ds.addWidget(self.in_pt_dob); r_ds.addWidget(self.cmb_pt_sex)
        ll.addLayout(r_ds)
        ll.addWidget(QLabel("Requesting Physician:")); ll.addWidget(self.in_pt_md)

        r_pr = QHBoxLayout()
        self.cmb_req_priority = QComboBox(); self.cmb_req_priority.addItems(["Routine", "STAT", "Urgent"])
        self.in_req_slot = QLineEdit("Bench Rack A1")
        r_pr.addWidget(QLabel("Priority:")); r_pr.addWidget(self.cmb_req_priority)
        r_pr.addWidget(QLabel("Rack Slot:")); r_pr.addWidget(self.in_req_slot)
        ll.addLayout(r_pr)

        self.btn_submit_req = QPushButton("Create Order (0 Assays)")
        self.btn_submit_req.setObjectName("SuccessBtn")
        self.btn_submit_req.setMinimumHeight(42)
        self.btn_submit_req.clicked.connect(self._submit_requisition)
        ll.addWidget(self.btn_submit_req)
        ll.addStretch()

        # Right: Preset Panels + Assay Selection
        right = QFrame()
        right.setObjectName("SurfaceCard")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(16, 16, 16, 16)
        rl.setSpacing(10)

        lbl2 = QLabel("2. Preset Panels & Assays")
        lbl2.setObjectName("SectionHeader")
        rl.addWidget(lbl2)

        panel_grid = QGridLayout()
        for idx, (p_name, tests_list) in enumerate(PRESET_PANELS.items()):
            b = QPushButton(f"+ {p_name}")
            b.clicked.connect(lambda checked=False, tl=tests_list: self._apply_preset_panel(tl))
            panel_grid.addWidget(b, idx // 3, idx % 3)
        btn_clr = QPushButton("Clear Selection")
        btn_clr.clicked.connect(self._clear_test_checks)
        panel_grid.addWidget(btn_clr, 2, 0, 1, 3)
        rl.addLayout(panel_grid)

        self.in_assay_filter = QLineEdit()
        self.in_assay_filter.setPlaceholderText("Filter assays by name or tube type...")
        self.in_assay_filter.textChanged.connect(self._filter_assay_checkboxes)
        rl.addWidget(self.in_assay_filter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        chk_container = QWidget()
        self.chk_grid = QGridLayout(chk_container)
        self.test_checkboxes = {}
        scroll.setWidget(chk_container)
        rl.addWidget(scroll, 1)

        lay.addWidget(left, 2)
        lay.addWidget(right, 3)
        return w

    def _on_req_patient_pick(self):
        pid = self.cmb_req_patient.currentData()
        if not pid:
            self.in_pt_name.clear(); self.in_pt_mrn.clear(); self.in_pt_dob.clear(); self.in_pt_md.clear()
            return
        conn = get_conn()
        pt = conn.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
        conn.close()
        if pt:
            self.in_pt_name.setText(pt["full_name"])
            self.in_pt_mrn.setText(pt["mrn"])
            self.in_pt_dob.setText(pt["dob"] or "")
            self.cmb_pt_sex.setCurrentText(pt["sex"] or "Female")
            self.in_pt_md.setText(pt["physician"] or "")

    def _update_selected_assay_count(self):
        cnt = sum(1 for cb in self.test_checkboxes.values() if cb.isChecked())
        self.btn_submit_req.setText(f"Create Order ({cnt} Assay{'s' if cnt != 1 else ''})")

    def _filter_assay_checkboxes(self, text: str):
        q = text.strip().lower()
        for t_name, cb in self.test_checkboxes.items():
            cb.setVisible(not q or q in cb.text().lower())

    def _apply_preset_panel(self, test_names: list):
        for t in test_names:
            if t in self.test_checkboxes:
                self.test_checkboxes[t].setChecked(True)
        self._update_selected_assay_count()

    def _clear_test_checks(self):
        for cb in self.test_checkboxes.values():
            cb.setChecked(False)
        self._update_selected_assay_count()

    def _submit_requisition(self):
        name = self.in_pt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Patient Name", "Enter or select a patient name.")
            return
        selected_tests = [t for t, cb in self.test_checkboxes.items() if cb.isChecked()]
        if not selected_tests:
            QMessageBox.warning(self, "No Assays Selected", "Select at least one test or preset panel.")
            return

        mrn = self.in_pt_mrn.text().strip() or f"MRN-{random.randint(100000, 999999)}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spec_id = f"MDL-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"

        conn = get_conn()
        cur = conn.cursor()
        existing = cur.execute("SELECT id FROM patients WHERE mrn = ?", (mrn,)).fetchone()
        if existing:
            pid = existing["id"]
            cur.execute("UPDATE patients SET full_name=?, dob=?, sex=?, physician=? WHERE id=?",
                        (name, self.in_pt_dob.text().strip(), self.cmb_pt_sex.currentText(), self.in_pt_md.text().strip(), pid))
        else:
            cur.execute("INSERT INTO patients (mrn, full_name, dob, sex, physician, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                        (mrn, name, self.in_pt_dob.text().strip(), self.cmb_pt_sex.currentText(), self.in_pt_md.text().strip(), now))
            pid = cur.lastrowid

        for t_name in selected_tests:
            t_info = cur.execute("SELECT * FROM tests WHERE test_name = ?", (t_name,)).fetchone()
            cur.execute("""
                INSERT INTO orders (
                    specimen_id, patient_id, test_name, department, priority, status,
                    unit, ref_range, tube_type, ordered_by, ordered_at, storage_slot
                ) VALUES (?, ?, ?, ?, ?, 'Ordered', ?, ?, ?, ?, ?, ?)
            """, (
                spec_id, pid, t_name, t_info["department"], self.cmb_req_priority.currentText(),
                t_info["unit"], t_info["ref_range"], t_info["tube_type"],
                self.user["name"], now, self.in_req_slot.text().strip()
            ))

        conn.commit()
        conn.close()
        log_audit(self.user["name"], "REQUISITION_CREATED", spec_id, f"{name} ({len(selected_tests)} assays)")
        self._clear_test_checks()
        self.refresh_all()
        self.tabs.setCurrentIndex(0)
        QMessageBox.information(self, "Order Created", f"Specimen ID: {spec_id}\nPatient: {name}\nAssays Queued: {len(selected_tests)}")

    # --------------------------------------------------------------------------
    # TAB 3: PATHOLOGIST REVIEW & CO-SIGN
    # --------------------------------------------------------------------------
    def _build_pathologist_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        banner = QFrame()
        banner.setObjectName("SurfaceCard")
        bl = QHBoxLayout(banner)
        info = QLabel("Pathologist Review Queue — Gaia Aubrey Manalo, MD (Critical values, amended results, blood smears, and cultures)")
        info.setStyleSheet("color: #CBD5E1; font-weight: 600;")
        bl.addWidget(info)
        lay.addWidget(banner)

        self.tbl_path = QTableWidget(0, 7)
        self.tbl_path.setHorizontalHeaderLabels(["ID", "Specimen ID", "Patient", "Assay", "Result", "Flag / Trigger", "Co-Sign Status"])
        self.tbl_path.setColumnHidden(0, True)
        self.tbl_path.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_path.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_path.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(self.tbl_path, 1)

        sign_box = QFrame()
        sign_box.setObjectName("SurfaceCard")
        sl = QVBoxLayout(sign_box)
        sl.addWidget(QLabel("Pathologist Clinical Impression:"))
        self.in_path_note = QPlainTextEdit()
        self.in_path_note.setFixedHeight(75)
        self.in_path_note.setPlaceholderText("Enter clinical interpretation or peripheral smear impression...")
        sl.addWidget(self.in_path_note)

        btn_sign = QPushButton("Apply Pathologist Signature (Gaia Aubrey Manalo, MD)")
        btn_sign.setObjectName("PrimaryBtn")
        btn_sign.setMinimumHeight(38)
        btn_sign.clicked.connect(self._pathologist_cosign)
        sl.addWidget(btn_sign)
        lay.addWidget(sign_box)
        return w

    def _pathologist_cosign(self):
        rows = self.tbl_path.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "Select Case", "Select a specimen row to co-sign.")
            return
        if self.user["pin"] != "1111" and "Pathologist" not in self.user["role"]:
            ans = QMessageBox.question(
                self, "Pathologist Signature",
                "You are logged in as RMT. Record co-signature for Gaia Aubrey Manalo, MD?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans != QMessageBox.Yes:
                return

        oid = int(self.tbl_path.item(rows[0].row(), 0).text())
        note = self.in_path_note.toPlainText().strip() or "Reviewed and clinically correlated."
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = get_conn()
        row = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (oid,)).fetchone()
        conn.execute("""
            UPDATE orders SET pathologist_note = ?, pathologist_signed_by = 'Gaia Aubrey Manalo, MD', pathologist_signed_at = ?
            WHERE id = ?
        """, (note, now, oid))
        conn.commit()
        conn.close()
        log_audit("Gaia Aubrey Manalo, MD (1111)", "PATHOLOGIST_COSIGN", row["specimen_id"] if row else "-", note)
        self.in_path_note.clear()
        self.refresh_all()

    # --------------------------------------------------------------------------
    # TAB 4: QUALITY CONTROL (LEVEY-JENNINGS)
    # --------------------------------------------------------------------------
    def _build_qc_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        ctrl_bar = QFrame()
        ctrl_bar.setObjectName("SurfaceCard")
        cl = QHBoxLayout(ctrl_bar)

        cl.addWidget(QLabel("Control Lot:"))
        self.cmb_qc_target = QComboBox()
        self.cmb_qc_target.currentTextChanged.connect(self.refresh_qc)
        cl.addWidget(self.cmb_qc_target, 2)

        cl.addWidget(QLabel("Measured Value:"))
        self.in_qc_val = QLineEdit()
        self.in_qc_val.setPlaceholderText("e.g. 13.8")
        self.in_qc_val.returnPressed.connect(self._log_qc_run)
        cl.addWidget(self.in_qc_val, 1)

        btn_log_qc = QPushButton("Log QC Run")
        btn_log_qc.setObjectName("PrimaryBtn")
        btn_log_qc.clicked.connect(self._log_qc_run)
        cl.addWidget(btn_log_qc)

        self.chk_qc_lock = QCheckBox("Block Release on 1-3s Failure")
        self.chk_qc_lock.toggled.connect(self._toggle_qc_lockout)
        cl.addWidget(self.chk_qc_lock)

        lay.addWidget(ctrl_bar)

        self.qc_canvas = MplCanvas(width=8.5, height=3.1, dpi=100)
        lay.addWidget(self.qc_canvas, 2)

        self.tbl_qc = QTableWidget(0, 6)
        self.tbl_qc.setHorizontalHeaderLabels(["Timestamp", "Control Lot", "Measured", "Z-Score", "Westgard Status", "Operator"])
        self.tbl_qc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_qc.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(self.tbl_qc, 1)
        return w

    def _toggle_qc_lockout(self, state: bool):
        self.qc_lockout_enabled = state
        self._update_qc_pill()

    def _update_qc_pill(self):
        if self.qc_lockout_enabled and self.failed_qc_tests:
            self.lbl_qc_pill.setText(f"QC Lockout: {len(self.failed_qc_tests)} Assay(s)")
            self.lbl_qc_pill.setStyleSheet(
                "background-color: rgba(244,63,94,0.18); border: 1px solid #F43F5E; "
                "color: #FB7185; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 8.5pt;"
            )
        else:
            self.lbl_qc_pill.setText("QC: In Control")
            self.lbl_qc_pill.setStyleSheet(
                "background-color: rgba(16,185,129,0.14); border: 1px solid #10B981; "
                "color: #34D399; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 8.5pt;"
            )

    def _log_qc_run(self):
        label = self.cmb_qc_target.currentText()
        try:
            measured = float(self.in_qc_val.text().strip())
        except Exception:
            QMessageBox.warning(self, "Invalid Number", "Enter a valid numeric QC measurement.")
            return

        conn = get_conn()
        t = conn.execute("SELECT * FROM qc_targets WHERE label = ?", (label,)).fetchone()
        if not t:
            conn.close()
            return

        z = (measured - t["target_mean"]) / t["sd"]
        abs_z = abs(z)
        if abs_z > 3.0:
            status = "FAIL (1-3s Violation)"
            self.failed_qc_tests.add(t["test_name"])
        elif abs_z > 2.0:
            status = "WARN (1-2s Warning)"
        else:
            status = "PASS (In Control)"
            self.failed_qc_tests.discard(t["test_name"])

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO qc_logs (label, measured, z_score, westgard_status, operator, logged_at) VALUES (?, ?, ?, ?, ?, ?)",
            (label, measured, round(z, 2), status, self.user["name"], now)
        )
        conn.commit()
        conn.close()

        log_audit(self.user["name"], "QC_RUN_LOGGED", "-", f"{label}: {measured} (Z={z:+.2f} -> {status})")
        self.in_qc_val.clear()
        self._update_qc_pill()
        self.refresh_qc()

        if abs_z > 3.0:
            QMessageBox.critical(
                self, "Westgard 1-3s Violation",
                f"Control: {label}\nMeasured: {measured} {t['unit']} (Z = {z:+.2f} SD)\n\n"
                f"Exceeds +/- 3 SD limits. Recalibrate before releasing patient results."
            )

    def refresh_qc(self):
        label = self.cmb_qc_target.currentText()
        conn = get_conn()
        target = conn.execute("SELECT * FROM qc_targets WHERE label = ?", (label,)).fetchone()
        logs = conn.execute("SELECT * FROM qc_logs WHERE label = ? ORDER BY id DESC LIMIT 20", (label,)).fetchall()
        conn.close()

        self.tbl_qc.setRowCount(len(logs))
        for i, r in enumerate(logs):
            self.tbl_qc.setItem(i, 0, QTableWidgetItem(r["logged_at"]))
            self.tbl_qc.setItem(i, 1, QTableWidgetItem(r["label"]))
            self.tbl_qc.setItem(i, 2, QTableWidgetItem(f"{r['measured']:g}"))
            self.tbl_qc.setItem(i, 3, QTableWidgetItem(f"{r['z_score']:+.2f} SD"))
            st = QTableWidgetItem(r["westgard_status"])
            if "FAIL" in r["westgard_status"]:
                st.setForeground(QColor("#FB7185"))
            elif "WARN" in r["westgard_status"]:
                st.setForeground(QColor("#FBBF24"))
            else:
                st.setForeground(QColor("#34D399"))
            self.tbl_qc.setItem(i, 4, st)
            self.tbl_qc.setItem(i, 5, QTableWidgetItem(r["operator"]))

        ax = self.qc_canvas.ax
        ax.clear()
        self.qc_canvas._style_ax(ax)

        if target:
            mean, sd = target["target_mean"], target["sd"]
            ax.axhspan(mean - sd, mean + sd, color="#10B981", alpha=0.14)
            ax.axhline(mean, color="#10B981", linewidth=1.6, label=f"Mean ({mean:g})")
            for mult, col, ls in [(2, "#F59E0B", "--"), (-2, "#F59E0B", "--"), (3, "#F43F5E", ":"), (-3, "#F43F5E", ":")]:
                ax.axhline(mean + mult * sd, color=col, linestyle=ls, linewidth=1.0)
            ax.set_ylim(mean - 4.0 * sd, mean + 4.0 * sd)

        ordered = list(reversed(logs))
        if ordered:
            xs = [f"#{i+1}" for i in range(len(ordered))]
            ys = [r["measured"] for r in ordered]
            ax.plot(xs, ys, color="#38BDF8", linewidth=1.8, zorder=3)
            for x, y, r in zip(xs, ys, ordered):
                c = "#F43F5E" if "FAIL" in r["westgard_status"] else ("#F59E0B" if "WARN" in r["westgard_status"] else "#10B981")
                ax.scatter([x], [y], color=c, s=55, zorder=4, edgecolors="#FFFFFF", linewidths=0.8)

        ax.set_title(f"Levey-Jennings Chart — {label}", fontsize=10, fontweight="bold")
        ax.set_ylabel(target["unit"] if target else "Value")
        ax.grid(True, color="#1E293B", linestyle=":", linewidth=0.7)
        self.qc_canvas.fig.tight_layout()
        self.qc_canvas.draw()

    # --------------------------------------------------------------------------
    # TAB 5: PATIENTS REGISTRY
    # --------------------------------------------------------------------------
    def _build_patients_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        top = QHBoxLayout()
        self.in_pt_search = QLineEdit()
        self.in_pt_search.setPlaceholderText("Search patient name or MRN (Double-click any row to view cumulative lab history)...")
        self.in_pt_search.textChanged.connect(self.refresh_patients)
        top.addWidget(self.in_pt_search)
        lay.addLayout(top)

        self.tbl_patients = QTableWidget(0, 6)
        self.tbl_patients.setHorizontalHeaderLabels(["ID", "MRN", "Full Patient Name", "DOB / Age", "Sex", "Requesting Physician"])
        self.tbl_patients.setColumnHidden(0, True)
        self.tbl_patients.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_patients.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_patients.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_patients.doubleClicked.connect(self._on_patient_double_click)
        lay.addWidget(self.tbl_patients, 1)
        return w

    def _on_patient_double_click(self, idx):
        pid = int(self.tbl_patients.item(idx.row(), 0).text())
        PatientHistoryDialog(pid, self).exec()

    # --------------------------------------------------------------------------
    # TAB 6: TEST CATALOG & REFERENCE RANGES
    # --------------------------------------------------------------------------
    def _build_catalog_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        form = QFrame()
        form.setObjectName("SurfaceCard")
        fl = QHBoxLayout(form)
        self.cat_name = QLineEdit(); self.cat_name.setPlaceholderText("Assay Name")
        self.cat_dept = QComboBox(); self.cat_dept.addItems([
            "Hematology", "Clinical Chemistry", "Coagulation",
            "Immunology", "Serology", "Clinical Microscopy", "Microbiology"
        ])
        self.cat_unit = QLineEdit(); self.cat_unit.setPlaceholderText("Unit (e.g. mg/dL)")
        self.cat_lo = QLineEdit(); self.cat_lo.setPlaceholderText("Low")
        self.cat_hi = QLineEdit(); self.cat_hi.setPlaceholderText("High")
        self.cat_tube = QComboBox(); self.cat_tube.addItems(list(TUBE_COLORS.keys()))
        btn_add_t = QPushButton("Save Assay")
        btn_add_t.setObjectName("PrimaryBtn")
        btn_add_t.clicked.connect(self._save_catalog_test)

        for widget in (self.cat_name, self.cat_dept, self.cat_unit, self.cat_lo, self.cat_hi, self.cat_tube, btn_add_t):
            fl.addWidget(widget)
        lay.addWidget(form)

        self.tbl_catalog = QTableWidget(0, 7)
        self.tbl_catalog.setHorizontalHeaderLabels(["Test Name", "Department", "Unit", "Low", "High", "Critical Cutoffs", "Container"])
        self.tbl_catalog.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_catalog.setEditTriggers(QAbstractItemView.NoEditTriggers)
        lay.addWidget(self.tbl_catalog, 1)
        return w

    def _save_catalog_test(self):
        name = self.cat_name.text().strip()
        if not name:
            return
        try:
            lo = float(self.cat_lo.text()) if self.cat_lo.text().strip() else None
            hi = float(self.cat_hi.text()) if self.cat_hi.text().strip() else None
        except Exception:
            QMessageBox.warning(self, "Invalid Range", "Low and High must be numeric (or blank).")
            return
        ref = f"{lo:g} - {hi:g}" if (lo is not None and hi is not None) else "Qualitative"
        conn = get_conn()
        conn.execute("""
            INSERT INTO tests (test_name, department, unit, low_val, high_val, tube_type, ref_range)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(test_name) DO UPDATE SET
                department=excluded.department, unit=excluded.unit, low_val=excluded.low_val,
                high_val=excluded.high_val, tube_type=excluded.tube_type, ref_range=excluded.ref_range
        """, (name, self.cat_dept.currentText(), self.cat_unit.text().strip(), lo, hi, self.cat_tube.currentText(), ref))
        conn.commit()
        conn.close()
        self.cat_name.clear(); self.cat_lo.clear(); self.cat_hi.clear()
        self.refresh_all()

    # --------------------------------------------------------------------------
    # TAB 7: ADMIN, SHIFT HANDOVER & SYSTEM
    # --------------------------------------------------------------------------
    def _build_admin_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)

        sub_tabs = QTabWidget()

        # Sub-tab 1: Shift Handover & Workload Summary
        ho_w = QWidget()
        ho_l = QVBoxLayout(ho_w)
        ho_l.setContentsMargins(10, 10, 10, 10)
        ho_l.setSpacing(10)

        top_ho = QFrame()
        top_ho.setObjectName("SurfaceCard")
        tl = QHBoxLayout(top_ho)
        tl.addWidget(QLabel("Shift:"))
        self.cmb_shift = QComboBox()
        self.cmb_shift.addItems(["AM Shift (06:00 - 14:00)", "PM Shift (14:00 - 22:00)", "Night Shift (22:00 - 06:00)"])
        tl.addWidget(self.cmb_shift)
        btn_ho = QPushButton("Export Shift Handover PDF")
        btn_ho.setObjectName("PrimaryBtn")
        btn_ho.clicked.connect(self._export_shift_handover)
        tl.addWidget(btn_ho)
        tl.addStretch()

        btn_csv = QPushButton("Export Worklist CSV")
        btn_csv.clicked.connect(self._export_csv)
        btn_bak = QPushButton("Backup Database (.db)")
        btn_bak.setObjectName("SuccessBtn")
        btn_bak.clicked.connect(self._backup_db)
        tl.addWidget(btn_csv)
        tl.addWidget(btn_bak)
        ho_l.addWidget(top_ho)

        self.analytics_canvas = MplCanvas(width=9.0, height=4.2, dpi=100)
        ho_l.addWidget(self.analytics_canvas, 1)
        sub_tabs.addTab(ho_w, "Shift Handover & Summary")

        # Sub-tab 2: Staff Roster
        st_w = QWidget()
        st_l = QVBoxLayout(st_w)
        st_l.setContentsMargins(10, 10, 10, 10)
        st_l.setSpacing(10)

        add_card = QFrame()
        add_card.setObjectName("SurfaceCard")
        add_r = QHBoxLayout(add_card)
        self.st_pin = QLineEdit(); self.st_pin.setPlaceholderText("4-Digit PIN")
        self.st_name = QLineEdit(); self.st_name.setPlaceholderText("Full Name & Credentials")
        self.st_role = QComboBox(); self.st_role.addItems(["Medical Technologist (RMT)", "Pathologist"])
        btn_st = QPushButton("Save Staff")
        btn_st.setObjectName("PrimaryBtn")
        btn_st.clicked.connect(self._save_staff)
        add_r.addWidget(self.st_pin)
        add_r.addWidget(self.st_name, 2)
        add_r.addWidget(self.st_role, 1)
        add_r.addWidget(btn_st)
        st_l.addWidget(add_card)

        self.tbl_staff = QTableWidget(0, 3)
        self.tbl_staff.setHorizontalHeaderLabels(["PIN", "Operator Name", "Role"])
        self.tbl_staff.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_staff.setEditTriggers(QAbstractItemView.NoEditTriggers)
        st_l.addWidget(self.tbl_staff, 1)
        sub_tabs.addTab(st_w, "Staff Roster")

        # Sub-tab 3: Audit Log
        aud_w = QWidget()
        aud_l = QVBoxLayout(aud_w)
        aud_l.setContentsMargins(10, 10, 10, 10)
        self.tbl_audit = QTableWidget(0, 5)
        self.tbl_audit.setHorizontalHeaderLabels(["Timestamp", "Operator", "Action", "Specimen ID", "Details"])
        self.tbl_audit.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_audit.setEditTriggers(QAbstractItemView.NoEditTriggers)
        aud_l.addWidget(self.tbl_audit, 1)
        sub_tabs.addTab(aud_w, "Audit Log")

        lay.addWidget(sub_tabs)
        return w

    def _export_shift_handover(self):
        shift = self.cmb_shift.currentText()
        path, _ = QFileDialog.getSaveFileName(self, "Save Shift Handover Report", f"Shift_Handover_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF Files (*.pdf)")
        if path:
            generate_shift_handover_pdf(self.user["name"], shift, path)
            log_audit(self.user["name"], "SHIFT_HANDOVER_PDF", "-", shift)
            if sys.platform == "win32":
                os.startfile(path)

    def refresh_analytics(self):
        conn = get_conn()
        dept_rows = conn.execute("SELECT department, COUNT(*) as cnt FROM orders GROUP BY department ORDER BY cnt DESC").fetchall()
        flag_rows = conn.execute("SELECT COALESCE(flag, status) as flg, COUNT(*) as cnt FROM orders GROUP BY flg").fetchall()
        conn.close()

        fig = self.analytics_canvas.fig
        fig.clear()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        self.analytics_canvas._style_ax(ax1)
        self.analytics_canvas._style_ax(ax2)

        if dept_rows:
            depts = [r["department"][:16] for r in dept_rows]
            cnts = [r["cnt"] for r in dept_rows]
            bars = ax1.barh(depts[::-1], cnts[::-1], color="#38BDF8", height=0.55)
            ax1.bar_label(bars, padding=4, color="#E2E8F0", fontsize=8)
        ax1.set_title("Orders by Section", fontsize=10, fontweight="bold")

        if flag_rows:
            labels = [r["flg"] for r in flag_rows]
            vals = [r["cnt"] for r in flag_rows]
            palette = ["#10B981", "#38BDF8", "#F59E0B", "#F43F5E", "#818CF8", "#64748B"]
            ax2.pie(vals, labels=labels, autopct="%1.0f%%", colors=palette[:len(vals)], textprops={"color": "#E2E8F0", "fontsize": 8})
        ax2.set_title("Order Status & Flags", fontsize=10, fontweight="bold")

        fig.tight_layout()
        self.analytics_canvas.draw()

    def _save_staff(self):
        pin = self.st_pin.text().strip()
        name = self.st_name.text().strip()
        if len(pin) != 4 or not pin.isdigit() or not name:
            QMessageBox.warning(self, "Invalid Staff Entry", "PIN must be 4 digits and Name cannot be empty.")
            return
        conn = get_conn()
        conn.execute("""
            INSERT INTO staff (pin, name, role) VALUES (?, ?, ?)
            ON CONFLICT(pin) DO UPDATE SET name=excluded.name, role=excluded.role
        """, (pin, name, self.st_role.currentText()))
        conn.commit()
        conn.close()
        log_audit(self.user["name"], "STAFF_UPDATED", "-", f"{name} (PIN {pin})")
        self.st_pin.clear(); self.st_name.clear()
        self.refresh_all()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Worklist CSV", f"MDL_Worklist_{datetime.now().strftime('%Y%m%d')}.csv", "CSV (*.csv)")
        if not path:
            return
        conn = get_conn()
        rows = conn.execute("""
            SELECT o.specimen_id, p.mrn, p.full_name, o.test_name, o.department, o.priority, o.status, o.result_value, o.unit, o.flag, o.verified_by, o.verified_at
            FROM orders o JOIN patients p ON o.patient_id = p.id ORDER BY o.id DESC
        """).fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Specimen ID", "MRN", "Patient", "Assay", "Department", "Priority", "Status", "Result", "Unit", "Flag", "Verified By", "Verified At"])
            for r in rows:
                writer.writerow(list(r))
        QMessageBox.information(self, "CSV Exported", f"Worklist exported to:\n{path}")

    def _backup_db(self):
        path, _ = QFileDialog.getSaveFileName(self, "Backup SQLite Database", f"monocytes_lis_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db", "SQLite DB (*.db)")
        if path:
            shutil.copy2(DB_NAME, path)
            log_audit(self.user["name"], "DB_BACKUP", "-", path)
            QMessageBox.information(self, "Backup Complete", f"Database backed up to:\n{path}")

    # --------------------------------------------------------------------------
    # MASTER DATA REFRESHERS
    # --------------------------------------------------------------------------
    def refresh_all(self):
        self.refresh_kpis()
        self.refresh_worklist()
        self.refresh_requisition_catalog()
        self.refresh_pathologist_queue()
        self.refresh_qc_targets()
        self.refresh_qc()
        self.refresh_analytics()
        self.refresh_patients()
        self.refresh_system()

    def refresh_kpis(self):
        conn = get_conn()
        tot = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pend = conn.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Verified', 'Amended', 'Rejected')").fetchone()[0]
        stat = conn.execute("SELECT COUNT(*) FROM orders WHERE priority = 'STAT' OR critical_flag = 1 OR flag LIKE 'CRITICAL%'").fetchone()[0]
        ver = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Verified', 'Amended')").fetchone()[0]
        conn.close()

        self.lbl_queue_counts.setText(f"Total: {tot}  |  Pending: {pend}  |  STAT: {stat}  |  Verified: {ver}")

    def refresh_worklist(self):
        q = self.in_search.text().strip().lower()
        dept = self.cmb_dept_filter.currentText()
        st_f = self.cmb_status_filter.currentText()

        conn = get_conn()
        rows = conn.execute("""
            SELECT o.*, p.full_name, p.mrn
            FROM orders o JOIN patients p ON o.patient_id = p.id
            ORDER BY CASE WHEN o.priority='STAT' AND o.status NOT IN ('Verified','Amended') THEN 0 ELSE 1 END, o.id DESC
        """).fetchall()
        conn.close()

        filtered = []
        for r in rows:
            if q and q not in r["specimen_id"].lower() and q not in r["full_name"].lower() and q not in r["mrn"].lower() and q not in r["test_name"].lower():
                continue
            if dept != "All Departments" and r["department"] != dept:
                continue
            if st_f == "Pending / Active" and r["status"] in ("Verified", "Amended", "Rejected"):
                continue
            elif st_f == "STAT Only" and r["priority"] != "STAT":
                continue
            elif st_f == "Critical / Abnormal" and (r["flag"] or "") not in ("HIGH", "LOW", "CRITICAL HIGH", "CRITICAL LOW", "ABNORMAL"):
                continue
            elif st_f == "Verified / Amended" and r["status"] not in ("Verified", "Amended"):
                continue
            elif st_f == "Rejected" and r["status"] != "Rejected":
                continue
            filtered.append(r)

        self.tbl_worklist.setRowCount(len(filtered))
        now_dt = datetime.now()
        for i, r in enumerate(filtered):
            self.tbl_worklist.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.tbl_worklist.setItem(i, 1, QTableWidgetItem(r["specimen_id"]))
            self.tbl_worklist.setItem(i, 2, QTableWidgetItem(r["full_name"]))
            self.tbl_worklist.setItem(i, 3, QTableWidgetItem(r["test_name"]))
            self.tbl_worklist.setItem(i, 4, QTableWidgetItem(r["department"]))

            pr_item = QTableWidgetItem(r["priority"])
            if r["priority"] == "STAT":
                pr_item.setForeground(QColor("#FB7185"))
            self.tbl_worklist.setItem(i, 5, pr_item)

            tat_str = "Done"
            if r["status"] not in ("Verified", "Amended", "Rejected") and r["ordered_at"]:
                try:
                    odt = datetime.strptime(r["ordered_at"], "%Y-%m-%d %H:%M:%S")
                    mins = int((now_dt - odt).total_seconds() // 60)
                    sla = 60 if r["priority"] == "STAT" else 240
                    tat_str = f"{mins}m / {sla}m"
                except Exception:
                    tat_str = "-"
            self.tbl_worklist.setItem(i, 6, QTableWidgetItem(tat_str))

            res_txt = f"{r['result_value']} {r['unit'] or ''}".strip() if r["result_value"] else "-"
            self.tbl_worklist.setItem(i, 7, QTableWidgetItem(res_txt))

            badge = r["flag"] if r["flag"] else r["status"]
            st_item = QTableWidgetItem(badge)
            if badge in ("HIGH", "CRITICAL HIGH", "CRITICAL LOW", "ABNORMAL"):
                st_item.setForeground(QColor("#FB7185"))
            elif badge == "LOW":
                st_item.setForeground(QColor("#FBBF24"))
            elif badge == "NORMAL":
                st_item.setForeground(QColor("#34D399"))
            elif badge == "REJECTED":
                st_item.setForeground(QColor("#94A3B8"))
            else:
                st_item.setForeground(QColor("#38BDF8"))
            self.tbl_worklist.setItem(i, 8, st_item)

    def refresh_requisition_catalog(self):
        conn = get_conn()
        pts = conn.execute("SELECT id, mrn, full_name FROM patients ORDER BY full_name ASC").fetchall()
        tests = conn.execute("SELECT * FROM tests ORDER BY department, test_name").fetchall()
        conn.close()

        cur_pid = self.cmb_req_patient.currentData()
        self.cmb_req_patient.blockSignals(True)
        self.cmb_req_patient.clear()
        self.cmb_req_patient.addItem("-- Register New Patient --", None)
        for p in pts:
            self.cmb_req_patient.addItem(f"{p['full_name']} ({p['mrn']})", p["id"])
        if cur_pid:
            idx = self.cmb_req_patient.findData(cur_pid)
            if idx >= 0:
                self.cmb_req_patient.setCurrentIndex(idx)
        self.cmb_req_patient.blockSignals(False)

        if not self.test_checkboxes:
            for idx, t in enumerate(tests):
                cb = QCheckBox(f"{t['test_name']}  [{t['tube_type']}]")
                cb.stateChanged.connect(self._update_selected_assay_count)
                self.chk_grid.addWidget(cb, idx // 2, idx % 2)
                self.test_checkboxes[t["test_name"]] = cb

        self.tbl_catalog.setRowCount(len(tests))
        for i, t in enumerate(tests):
            self.tbl_catalog.setItem(i, 0, QTableWidgetItem(t["test_name"]))
            self.tbl_catalog.setItem(i, 1, QTableWidgetItem(t["department"]))
            self.tbl_catalog.setItem(i, 2, QTableWidgetItem(t["unit"] or "-"))
            self.tbl_catalog.setItem(i, 3, QTableWidgetItem(str(t["low_val"]) if t["low_val"] is not None else "-"))
            self.tbl_catalog.setItem(i, 4, QTableWidgetItem(str(t["high_val"]) if t["high_val"] is not None else "-"))
            crit = f"<{t['crit_low']} or >{t['crit_high']}" if (t["crit_low"] is not None or t["crit_high"] is not None) else "-"
            self.tbl_catalog.setItem(i, 5, QTableWidgetItem(crit))
            self.tbl_catalog.setItem(i, 6, QTableWidgetItem(t["tube_type"] or "-"))

    def refresh_pathologist_queue(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT o.*, p.full_name
            FROM orders o JOIN patients p ON o.patient_id = p.id
            WHERE o.critical_flag = 1
               OR o.flag IN ('CRITICAL HIGH', 'CRITICAL LOW', 'ABNORMAL')
               OR o.status = 'Amended'
               OR o.test_name LIKE '%Smear%'
               OR o.test_name LIKE '%Culture%'
            ORDER BY o.id DESC
        """).fetchall()
        conn.close()

        unsigned_cnt = sum(1 for r in rows if not r["pathologist_signed_by"])
        tab_label = f"Pathologist Review ({unsigned_cnt})" if unsigned_cnt > 0 else "Pathologist Review"
        self.tabs.setTabText(2, tab_label)

        self.tbl_path.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tbl_path.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.tbl_path.setItem(i, 1, QTableWidgetItem(r["specimen_id"]))
            self.tbl_path.setItem(i, 2, QTableWidgetItem(r["full_name"]))
            self.tbl_path.setItem(i, 3, QTableWidgetItem(r["test_name"]))
            self.tbl_path.setItem(i, 4, QTableWidgetItem(r["result_value"] or "Pending"))
            self.tbl_path.setItem(i, 5, QTableWidgetItem(r["flag"] or r["status"]))
            cs = f"Signed ({r['pathologist_signed_at']})" if r["pathologist_signed_by"] else "Awaiting MD Co-Sign"
            item_cs = QTableWidgetItem(cs)
            item_cs.setForeground(QColor("#34D399") if r["pathologist_signed_by"] else QColor("#FBBF24"))
            self.tbl_path.setItem(i, 6, item_cs)

    def refresh_qc_targets(self):
        conn = get_conn()
        targets = conn.execute("SELECT label FROM qc_targets ORDER BY label").fetchall()
        conn.close()
        cur = self.cmb_qc_target.currentText()
        self.cmb_qc_target.blockSignals(True)
        self.cmb_qc_target.clear()
        for t in targets:
            self.cmb_qc_target.addItem(t["label"])
        if cur:
            self.cmb_qc_target.setCurrentText(cur)
        self.cmb_qc_target.blockSignals(False)

    def refresh_patients(self):
        q = self.in_pt_search.text().strip().lower()
        conn = get_conn()
        rows = conn.execute("SELECT * FROM patients ORDER BY full_name ASC").fetchall()
        conn.close()

        filtered = [r for r in rows if not q or q in r["full_name"].lower() or q in r["mrn"].lower()]
        self.tbl_patients.setRowCount(len(filtered))
        for i, r in enumerate(filtered):
            self.tbl_patients.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.tbl_patients.setItem(i, 1, QTableWidgetItem(r["mrn"]))
            self.tbl_patients.setItem(i, 2, QTableWidgetItem(r["full_name"]))
            self.tbl_patients.setItem(i, 3, QTableWidgetItem(r["dob"] or "-"))
            self.tbl_patients.setItem(i, 4, QTableWidgetItem(r["sex"] or "-"))
            self.tbl_patients.setItem(i, 5, QTableWidgetItem(r["physician"] or "-"))

    def refresh_system(self):
        conn = get_conn()
        staff = conn.execute("SELECT * FROM staff ORDER BY pin ASC").fetchall()
        audits = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 100").fetchall()
        conn.close()

        self.tbl_staff.setRowCount(len(staff))
        for i, s in enumerate(staff):
            self.tbl_staff.setItem(i, 0, QTableWidgetItem(s["pin"]))
            self.tbl_staff.setItem(i, 1, QTableWidgetItem(s["name"]))
            self.tbl_staff.setItem(i, 2, QTableWidgetItem(s["role"]))

        self.tbl_audit.setRowCount(len(audits))
        for i, a in enumerate(audits):
            self.tbl_audit.setItem(i, 0, QTableWidgetItem(a["timestamp"]))
            self.tbl_audit.setItem(i, 1, QTableWidgetItem(a["operator"]))
            self.tbl_audit.setItem(i, 2, QTableWidgetItem(a["action"]))
            self.tbl_audit.setItem(i, 3, QTableWidgetItem(a["specimen_id"] or "-"))
            self.tbl_audit.setItem(i, 4, QTableWidgetItem(a["details"] or ""))


# ==============================================================================
# MAIN SHELL WINDOW
# ==============================================================================

class MonocytesLisApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1380, 860)
        self.setMinimumSize(1120, 720)
        apply_dark_titlebar(self)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_gate = StaffLoginScreen(self)
        self.login_gate.authenticated.connect(self._on_authenticated)
        self.stack.addWidget(self.login_gate)
        self.workspace = None

    def _on_authenticated(self, user: dict):
        if self.workspace is not None:
            self.stack.removeWidget(self.workspace)
            self.workspace.deleteLater()
            self.workspace = None

        self.workspace = MainWorkspace(user, self)
        self.workspace.lock_requested.connect(self._on_lock)
        self.stack.addWidget(self.workspace)
        self.stack.setCurrentWidget(self.workspace)

    def _on_lock(self):
        if self.workspace is not None:
            log_audit(self.workspace.user["name"], "SESSION_LOCKED", "-", "Operator locked workstation")
            self.stack.removeWidget(self.workspace)
            self.workspace.deleteLater()
            self.workspace = None
        self.login_gate.reset_gate()
        self.stack.setCurrentWidget(self.login_gate)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_QSS)

    init_db()
    win = MonocytesLisApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
