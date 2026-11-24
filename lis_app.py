import sys
import os
import json
import math
import random
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QSize, QMarginsF, Signal, Property
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QFont, QPainterPath, QLinearGradient,
    QPolygonF, QPageSize, QPageLayout, QAction, QKeySequence, QShortcut,
    QFontDatabase, QTransform, QWheelEvent
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea,
    QFrame, QSplitter, QGroupBox, QCheckBox, QTextEdit, QPlainTextEdit,
    QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QSizePolicy, QToolButton, QMenu, QStatusBar, QStackedWidget, QSlider
)
from PySide6.QtPrintSupport import QPrinter

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False


# ==============================================================================
# APPLICATION CONSTANTS & CLINICAL REFERENCE RANGES
# ==============================================================================
APP_TITLE = "Monocytes Delegates LIS"
APP_VERSION = "v8.0 TITAN"
DB_FILENAME = "monocytes_delegates_lis.db"

STAFF_ROLES = {
    "0001": ("Ariech Legaspi, RMT", "RMT"),
    "0002": ("Melody Bajande, RMT", "RMT"),
    "0003": ("Christine Patani-e, RMT", "RMT"),
    "0004": ("Chauncy Melvida, RMT", "RMT"),
    "0005": ("Elaijeen Cordova, RMT", "RMT"),
    "0006": ("Dianne Pastor, RMT", "RMT"),
    "0007": ("Michael Malabago, RMT", "RMT"),
    "0008": ("Nielmarc Pontioso, RMT", "RMT"),
    "0009": ("Princess Aguilo, RMT", "RMT"),
    "0010": ("Keturah Totisano, RMT", "RMT"),
    "0011": ("Arthur Mana-ay, RMT", "RMT"),
    "0012": ("Carlyle Theodore Dioleste, RMT", "RMT"),
    "1111": ("Gaia Aubrey Manalo, MD, FPSP", "Pathologist"),
}

REQUESTING_PHYSICIANS = [
    "Dr. Shaun Bautista",
    "Dr. Ramelin David",
    "Dr. Raan Feril",
    "Dr. Marinelle Garcia",
]

MALE_PATIENT_LASTNAMES = {"napiza", "vargas", "tiongson"}

DEFAULT_ASSAYS = [
    {"code": "WBC", "name": "White Blood Cell Count", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "x10^3/uL", "ref_m": (4.5, 11.0), "ref_f": (4.5, 11.0), "decimals": 2},
    {"code": "RBC", "name": "Red Blood Cell Count", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "x10^6/uL", "ref_m": (4.5, 5.9), "ref_f": (4.1, 5.1), "decimals": 2},
    {"code": "HGB", "name": "Hemoglobin", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "g/dL", "ref_m": (13.5, 17.5), "ref_f": (12.0, 16.0), "decimals": 1},
    {"code": "HCT", "name": "Hematocrit", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "%", "ref_m": (40.0, 52.0), "ref_f": (36.0, 46.0), "decimals": 1},
    {"code": "MCV", "name": "Mean Corpuscular Volume", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "fL", "ref_m": (80.0, 100.0), "ref_f": (80.0, 100.0), "decimals": 1},
    {"code": "MCH", "name": "Mean Corpuscular Hemoglobin", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "pg", "ref_m": (27.0, 33.0), "ref_f": (27.0, 33.0), "decimals": 1},
    {"code": "MCHC", "name": "Mean Corpuscular Hgb Conc.", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "g/dL", "ref_m": (31.5, 36.0), "ref_f": (31.5, 36.0), "decimals": 1},
    {"code": "PLT", "name": "Platelet Count", "section": "Hematology", "specimen": "EDTA Whole Blood", "unit": "x10^3/uL", "ref_m": (150.0, 450.0), "ref_f": (150.0, 450.0), "decimals": 0},
    {"code": "FBS", "name": "Fasting Blood Sugar", "section": "Chemistry", "specimen": "Fluoride/Oxalate or Serum", "unit": "mg/dL", "ref_m": (70.0, 99.0), "ref_f": (70.0, 99.0), "decimals": 1},
    {"code": "HBA1C", "name": "Glycated Hemoglobin (HbA1c)", "section": "Chemistry", "specimen": "EDTA Whole Blood", "unit": "%", "ref_m": (4.0, 5.6), "ref_f": (4.0, 5.6), "decimals": 1},
    {"code": "CHOL", "name": "Total Cholesterol", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (125.0, 200.0), "ref_f": (125.0, 200.0), "decimals": 1},
    {"code": "TRIG", "name": "Triglycerides", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (35.0, 150.0), "ref_f": (35.0, 150.0), "decimals": 1},
    {"code": "HDL", "name": "HDL Cholesterol", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (40.0, 80.0), "ref_f": (50.0, 90.0), "decimals": 1},
    {"code": "LDL", "name": "LDL Cholesterol (Calculated)", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (0.0, 100.0), "ref_f": (0.0, 100.0), "decimals": 1},
    {"code": "CREA", "name": "Serum Creatinine", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (0.7, 1.3), "ref_f": (0.6, 1.1), "decimals": 2},
    {"code": "BUA", "name": "Blood Uric Acid", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "mg/dL", "ref_m": (3.5, 7.2), "ref_f": (2.6, 6.0), "decimals": 1},
    {"code": "ALT", "name": "Alanine Aminotransferase (ALT/SGPT)", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "U/L", "ref_m": (7.0, 56.0), "ref_f": (7.0, 45.0), "decimals": 0},
    {"code": "AST", "name": "Aspartate Aminotransferase (AST/SGOT)", "section": "Chemistry", "specimen": "Serum Separator Tube", "unit": "U/L", "ref_m": (8.0, 48.0), "ref_f": (8.0, 40.0), "decimals": 0},
    {"code": "NA", "name": "Sodium (Na+)", "section": "Chemistry", "specimen": "Serum / Lithium Heparin", "unit": "mmol/L", "ref_m": (136.0, 145.0), "ref_f": (136.0, 145.0), "decimals": 1},
    {"code": "K", "name": "Potassium (K+)", "section": "Chemistry", "specimen": "Serum / Lithium Heparin", "unit": "mmol/L", "ref_m": (3.5, 5.1), "ref_f": (3.5, 5.1), "decimals": 2},
    {"code": "UA_PH", "name": "Urine pH", "section": "Clinical Microscopy", "specimen": "Random Midstream Urine", "unit": "pH", "ref_m": (5.0, 8.0), "ref_f": (5.0, 8.0), "decimals": 1},
    {"code": "UA_SG", "name": "Urine Specific Gravity", "section": "Clinical Microscopy", "specimen": "Random Midstream Urine", "unit": "SG", "ref_m": (1.005, 1.030), "ref_f": (1.005, 1.030), "decimals": 3},
    {"code": "UA_WBC", "name": "Urine WBC / hpf", "section": "Clinical Microscopy", "specimen": "Random Midstream Urine", "unit": "/hpf", "ref_m": (0.0, 5.0), "ref_f": (0.0, 5.0), "decimals": 0},
    {"code": "UA_RBC", "name": "Urine RBC / hpf", "section": "Clinical Microscopy", "specimen": "Random Midstream Urine", "unit": "/hpf", "ref_m": (0.0, 3.0), "ref_f": (0.0, 4.0), "decimals": 0},
    {"code": "CRP", "name": "C-Reactive Protein (Quantitative)", "section": "Serology", "specimen": "Serum Separator Tube", "unit": "mg/L", "ref_m": (0.0, 5.0), "ref_f": (0.0, 5.0), "decimals": 1},
    {"code": "TSH", "name": "Thyroid Stimulating Hormone", "section": "Serology", "specimen": "Serum Separator Tube", "unit": "uIU/mL", "ref_m": (0.27, 4.20), "ref_f": (0.27, 4.20), "decimals": 2},
]


# ==============================================================================
# THEME PALETTES (LIGHT MODE DEFAULT, LIVE SWITCHABLE)
# ==============================================================================
THEMES = {
    "light": {
        "name": "Light",
        "bg_main": "#F4F7FA",
        "bg_card": "#FFFFFF",
        "bg_alt": "#EEF2F7",
        "bg_input": "#FFFFFF",
        "bg_header": "#E6ECF5",
        "bg_hover": "#E2EBF6",
        "bg_selected": "#D6E6FA",
        "text_main": "#0F172A",
        "text_muted": "#475569",
        "text_accent": "#0369A1",
        "border": "#CBD5E1",
        "border_focus": "#0284C7",
        "primary": "#0284C7",
        "primary_hover": "#0369A1",
        "primary_text": "#FFFFFF",
        "success": "#15803D",
        "success_bg": "#DCFCE7",
        "warning": "#B45309",
        "warning_bg": "#FEF3C7",
        "danger": "#B91C1C",
        "danger_bg": "#FEE2E2",
        "badge_pending": "#FEF3C7",
        "badge_pending_fg": "#92400E",
        "badge_collected": "#E0F2FE",
        "badge_collected_fg": "#075985",
        "badge_verified": "#DCFCE7",
        "badge_verified_fg": "#166534",
        "plot_bg": "#FFFFFF",
        "plot_grid": "#E2E8F0",
        "plot_line": "#0284C7",
        "plot_mean": "#15803D",
        "plot_sd1": "#0EA5E9",
        "plot_sd2": "#D97706",
        "plot_sd3": "#DC2626",
    },
    "dark": {
        "name": "Dark",
        "bg_main": "#0B1120",
        "bg_card": "#111827",
        "bg_alt": "#1E293B",
        "bg_input": "#0F172A",
        "bg_header": "#172033",
        "bg_hover": "#1F2D45",
        "bg_selected": "#1E3A5F",
        "text_main": "#F1F5F9",
        "text_muted": "#94A3B8",
        "text_accent": "#38BDF8",
        "border": "#334155",
        "border_focus": "#38BDF8",
        "primary": "#0284C7",
        "primary_hover": "#0369A1",
        "primary_text": "#FFFFFF",
        "success": "#22C55E",
        "success_bg": "#14532D",
        "warning": "#F59E0B",
        "warning_bg": "#451A03",
        "danger": "#EF4444",
        "danger_bg": "#450A0A",
        "badge_pending": "#451A03",
        "badge_pending_fg": "#FCD34D",
        "badge_collected": "#0C4A6E",
        "badge_collected_fg": "#7DD3FC",
        "badge_verified": "#14532D",
        "badge_verified_fg": "#86EFAC",
        "plot_bg": "#0F172A",
        "plot_grid": "#1E293B",
        "plot_line": "#38BDF8",
        "plot_mean": "#4ADE80",
        "plot_sd1": "#60A5FA",
        "plot_sd2": "#FBBF24",
        "plot_sd3": "#F87171",
    },
}


def build_stylesheet(mode: str = "light") -> str:
    t = THEMES.get(mode, THEMES["light"])
    return f"""
        QMainWindow, QDialog, QWidget {{
            background-color: {t["bg_main"]};
            color: {t["text_main"]};
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }}
        QFrame[card="true"] {{
            background-color: {t["bg_card"]};
            border: 1px solid {t["border"]};
            border-radius: 8px;
        }}
        QGroupBox {{
            background-color: {t["bg_card"]};
            border: 1px solid {t["border"]};
            border-radius: 8px;
            margin-top: 10px;
            padding: 12px 10px 10px 10px;
            font-weight: 600;
            color: {t["text_main"]};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 12px;
            padding: 0 6px;
            color: {t["text_accent"]};
        }}
        QLabel {{
            color: {t["text_main"]};
            background: transparent;
        }}
        QLabel[muted="true"] {{
            color: {t["text_muted"]};
        }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
            background-color: {t["bg_input"]};
            color: {t["text_main"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 5px 8px;
            selection-background-color: {t["primary"]};
            selection-color: {t["primary_text"]};
        }}
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1.5px solid {t["border_focus"]};
        }}
        QComboBox QAbstractItemView {{
            background-color: {t["bg_card"]};
            color: {t["text_main"]};
            border: 1px solid {t["border"]};
            selection-background-color: {t["bg_selected"]};
            selection-color: {t["text_main"]};
        }}
        QPushButton {{
            background-color: {t["bg_alt"]};
            color: {t["text_main"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {t["bg_hover"]};
            border-color: {t["border_focus"]};
        }}
        QPushButton:pressed {{
            background-color: {t["bg_selected"]};
        }}
        QPushButton[accent="true"] {{
            background-color: {t["primary"]};
            color: {t["primary_text"]};
            border: 1px solid {t["primary"]};
        }}
        QPushButton[accent="true"]:hover {{
            background-color: {t["primary_hover"]};
        }}
        QPushButton[success="true"] {{
            background-color: {t["success"]};
            color: #FFFFFF;
            border: 1px solid {t["success"]};
        }}
        QPushButton[danger="true"] {{
            background-color: {t["danger"]};
            color: #FFFFFF;
            border: 1px solid {t["danger"]};
        }}
        QTabWidget::pane {{
            background-color: {t["bg_card"]};
            border: 1px solid {t["border"]};
            border-radius: 8px;
            top: -1px;
        }}
        QTabBar::tab {{
            background-color: {t["bg_alt"]};
            color: {t["text_muted"]};
            border: 1px solid {t["border"]};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 8px 16px;
            margin-right: 2px;
            font-weight: 600;
        }}
        QTabBar::tab:selected {{
            background-color: {t["bg_card"]};
            color: {t["text_accent"]};
            border-bottom: 2px solid {t["primary"]};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {t["bg_hover"]};
            color: {t["text_main"]};
        }}
        QTableWidget {{
            background-color: {t["bg_card"]};
            alternate-background-color: {t["bg_alt"]};
            color: {t["text_main"]};
            gridline-color: {t["border"]};
            border: 1px solid {t["border"]};
            border-radius: 6px;
            selection-background-color: {t["bg_selected"]};
            selection-color: {t["text_main"]};
        }}
        QHeaderView::section {{
            background-color: {t["bg_header"]};
            color: {t["text_main"]};
            padding: 6px 8px;
            border: none;
            border-right: 1px solid {t["border"]};
            border-bottom: 1px solid {t["border"]};
            font-weight: 700;
        }}
        QScrollArea {{
            background-color: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background-color: {t["bg_alt"]};
            width: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical {{
            background-color: {t["border"]};
            min-height: 28px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {t["text_muted"]};
        }}
        QScrollBar:horizontal {{
            background-color: {t["bg_alt"]};
            height: 12px;
            border-radius: 6px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {t["border"]};
            min-width: 28px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {t["text_muted"]};
        }}
        QStatusBar {{
            background-color: {t["bg_header"]};
            color: {t["text_main"]};
            border-top: 1px solid {t["border"]};
        }}
    """


# ==============================================================================
# CUSTOM VISUALIZER & VERIFICATION WIDGETS
# ==============================================================================
class ReferenceRangeBarWidget(QWidget):
    """Visualizes a numeric result relative to its clinical reference interval [low, high]."""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.value = None
        self.low = 0.0
        self.high = 100.0
        self.unit = ""
        self.label = "Select a test row to inspect reference range."
        self.setMinimumHeight(58)

    def set_theme(self, theme: dict):
        self.theme = theme
        self.update()

    def set_range_data(self, label: str, val_str: str, low: float, high: float, unit: str):
        self.label = label
        self.low = float(low)
        self.high = float(high)
        self.unit = unit
        try:
            self.value = float(str(val_str).strip())
        except (ValueError, TypeError):
            self.value = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.theme

        w = float(self.width())
        h = float(self.height())

        p.setPen(QColor(t["text_main"]))
        f = QFont(self.font())
        f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(4, 2, w - 8, 20), Qt.AlignLeft | Qt.AlignVCenter, self.label)

        bar_x = 12.0
        bar_y = 28.0
        bar_w = max(60.0, w - 24.0)
        bar_h = 16.0

        span = max(1e-6, self.high - self.low)
        scale_min = self.low - span * 0.45
        scale_max = self.high + span * 0.45
        total_span = max(1e-6, scale_max - scale_min)

        def to_x(v):
            frac = (v - scale_min) / total_span
            frac = max(0.0, min(1.0, frac))
            return bar_x + frac * bar_w

        x_low = to_x(self.low)
        x_high = to_x(self.high)

        # Out-of-range track
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(t["warning_bg"]))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 6, 6)

        # Normal reference band
        p.setBrush(QColor(t["success_bg"]))
        p.drawRect(QRectF(x_low, bar_y, max(4.0, x_high - x_low), bar_h))

        # Border
        p.setPen(QPen(QColor(t["border"]), 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 6, 6)

        # Marker for value
        if self.value is not None:
            vx = to_x(self.value)
            is_out = (self.value < self.low) or (self.value > self.high)
            marker_col = QColor(t["danger"] if is_out else t["primary"])
            p.setPen(QPen(marker_col, 2.0))
            p.drawLine(QPointF(vx, bar_y - 4), QPointF(vx, bar_y + bar_h + 4))
            p.setBrush(marker_col)
            p.drawEllipse(QPointF(vx, bar_y + bar_h / 2.0), 5.0, 5.0)

        p.end()


class VerificationStatusPulseWidget(QWidget):
    """Clean visual status indicator with timed verification highlight."""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.status_text = "Ready"
        self.active_highlight = False
        self.setFixedHeight(28)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._clear_highlight)

    def set_theme(self, theme: dict):
        self.theme = theme
        self.update()

    def trigger_status(self, text: str, duration_ms: int = 1800):
        self.status_text = text
        self.active_highlight = True
        self.update()
        self._timer.start(duration_ms)

    def _clear_highlight(self):
        self.active_highlight = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        t = self.theme
        rect = QRectF(2, 2, float(self.width() - 4), float(self.height() - 4))
        bg = QColor(t["badge_verified"] if self.active_highlight else t["bg_alt"])
        fg = QColor(t["badge_verified_fg"] if self.active_highlight else t["text_muted"])
        p.setPen(QPen(QColor(t["border"]), 1.0))
        p.setBrush(bg)
        p.drawRoundedRect(rect, 6, 6)
        p.setPen(fg)
        f = QFont(self.font())
        f.setBold(self.active_highlight)
        p.setFont(f)
        p.drawText(rect, Qt.AlignCenter, self.status_text)
        p.end()


# ==============================================================================
# DATABASE & REALISTIC MONOCYTES CLINICAL SEEDER
# ==============================================================================
class LISDatabase:
    def __init__(self, db_path: str = DB_FILENAME):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()
        self.seed_if_empty()

    def init_schema(self):
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mrn TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                sex TEXT NOT NULL,
                dob TEXT NOT NULL,
                contact TEXT DEFAULT '',
                address TEXT DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS assays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                section TEXT NOT NULL,
                specimen TEXT NOT NULL,
                unit TEXT NOT NULL,
                ref_min_m REAL NOT NULL,
                ref_max_m REAL NOT NULL,
                ref_min_f REAL NOT NULL,
                ref_max_f REAL NOT NULL,
                decimals INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS lab_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_no TEXT UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL,
                physician TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Routine',
                specimen_status TEXT NOT NULL DEFAULT 'Pending',
                clinical_notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                collected_at TEXT DEFAULT '',
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            );

            CREATE TABLE IF NOT EXISTS order_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                assay_code TEXT NOT NULL,
                specimen_status TEXT NOT NULL DEFAULT 'Pending',
                result_value TEXT DEFAULT '',
                flag TEXT DEFAULT '',
                test_status TEXT NOT NULL DEFAULT 'Pending',
                verified_by TEXT DEFAULT '',
                verified_at TEXT DEFAULT '',
                updated_at TEXT NOT NULL,
                FOREIGN KEY(order_id) REFERENCES lab_orders(id),
                FOREIGN KEY(assay_code) REFERENCES assays(code)
            );

            CREATE TABLE IF NOT EXISTS qc_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assay_code TEXT NOT NULL,
                lot_no TEXT NOT NULL,
                level_name TEXT NOT NULL,
                measured_value REAL NOT NULL,
                target_mean REAL NOT NULL,
                sd_value REAL NOT NULL,
                run_date TEXT NOT NULL,
                operator_name TEXT NOT NULL,
                westgard_flag TEXT NOT NULL,
                FOREIGN KEY(assay_code) REFERENCES assays(code)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL
            );
        """)
        self.conn.commit()

    def log_audit(self, actor: str, role: str, action: str, details: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT INTO audit_logs (timestamp, actor, role, action, details) VALUES (?, ?, ?, ?, ?)",
            (ts, actor, role, action, details),
        )
        self.conn.commit()

    @staticmethod
    def infer_sex_from_name(full_name: str) -> str:
        parts = [p.strip().lower().rstrip(",") for p in full_name.replace(",", " ").split() if p.strip()]
        for token in parts:
            if token in MALE_PATIENT_LASTNAMES:
                return "Male"
        return "Female"

    def seed_if_empty(self):
        cur = self.conn.cursor()
        for a in DEFAULT_ASSAYS:
            cur.execute("SELECT id FROM assays WHERE code = ?", (a["code"],))
            if not cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO assays (code, name, section, specimen, unit, ref_min_m, ref_max_m, ref_min_f, ref_max_f, decimals)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        a["code"],
                        a["name"],
                        a["section"],
                        a["specimen"],
                        a["unit"],
                        a["ref_m"][0],
                        a["ref_m"][1],
                        a["ref_f"][0],
                        a["ref_f"][1],
                        a["decimals"],
                    ),
                )
        self.conn.commit()

        cur.execute("SELECT COUNT(*) AS cnt FROM patients")
        if cur.fetchone()["cnt"] == 0:
            self._seed_monocytes_cases()

        cur.execute("SELECT COUNT(*) AS cnt FROM qc_runs")
        if cur.fetchone()["cnt"] == 0:
            self._seed_qc_runs()

    def _seed_monocytes_cases(self):
        rng = random.Random(20261125)
        cohort_names = [
            "Christian Napiza",
            "Justin Vargas",
            "Mark Tiongson",
            "Ariech Legaspi",
            "Melody Bajande",
            "Christine Patani-e",
            "Chauncy Melvida",
            "Elaijeen Cordova",
            "Dianne Pastor",
            "Michaela Malabago",
            "Nielmarie Pontioso",
            "Princess Aguilo",
            "Keturah Totisano",
            "Artura Mana-ay",
            "Gaia Aubrey Manalo",
            "Angela Abong",
            "Camille Alave",
            "Beatrice Boboli",
            "Danica Bogtae",
            "Erica Cambronero",
            "Hannah Canto",
            "Isabel Cardinal",
            "Janine Chan",
            "Katrina Dominguez",
            "Lorraine Gallego",
            "Marianne Gayoso",
            "Nicole Go Hee",
            "Patricia Hermitano",
            "Rachel Jordan",
            "Sophia Lanaria",
        ]

        start_dob = date(2004, 1, 1)
        end_dob = date(2006, 12, 31)
        span_days = (end_dob - start_dob).days
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.cursor()

        assay_rows = cur.execute("SELECT * FROM assays").fetchall()
        assay_map = {r["code"]: dict(r) for r in assay_rows}

        panel_sets = [
            ["WBC", "RBC", "HGB", "HCT", "MCV", "MCH", "MCHC", "PLT"],
            ["FBS", "CHOL", "TRIG", "HDL", "LDL", "CREA", "BUA"],
            ["ALT", "AST", "NA", "K", "CRP"],
            ["UA_PH", "UA_SG", "UA_WBC", "UA_RBC"],
            ["HBA1C", "TSH", "FBS", "CHOL"],
        ]

        for idx, name in enumerate(cohort_names, start=1):
            mrn = f"MONO-{202600 + idx:06d}"
            sex = self.infer_sex_from_name(name)
            dob_date = start_dob + timedelta(days=rng.randint(0, span_days))
            dob_str = dob_date.strftime("%Y-%m-%d")
            contact = f"09{rng.randint(15, 98)}{rng.randint(1000000, 9999999)}"
            address = f"Brgy. {rng.randint(1, 41)}, Bacolod City, Negros Occidental"

            cur.execute(
                """
                INSERT INTO patients (mrn, full_name, sex, dob, contact, address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (mrn, name, sex, dob_str, contact, address, now_str),
            )
            patient_id = cur.lastrowid

            order_no = f"ORD-{20261100 + idx}"
            physician = REQUESTING_PHYSICIANS[idx % len(REQUESTING_PHYSICIANS)]
            priority = "STAT" if idx % 6 == 0 else "Routine"
            created_dt = (datetime.now() - timedelta(hours=rng.randint(2, 72))).strftime("%Y-%m-%d %H:%M:%S")

            if idx % 3 == 0:
                order_spec_status = "Pending"
                collected_at = ""
            else:
                order_spec_status = "Collected"
                collected_at = created_dt

            cur.execute(
                """
                INSERT INTO lab_orders (order_no, patient_id, physician, priority, specimen_status, clinical_notes, created_at, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_no,
                    patient_id,
                    physician,
                    priority,
                    order_spec_status,
                    "Monocytes BSMT clinical simulation case",
                    created_dt,
                    collected_at,
                ),
            )
            order_id = cur.lastrowid

            chosen_codes = panel_sets[idx % len(panel_sets)]
            for t_i, code in enumerate(chosen_codes):
                a_info = assay_map[code]
                low_v = a_info["ref_min_m"] if sex == "Male" else a_info["ref_min_f"]
                high_v = a_info["ref_max_m"] if sex == "Male" else a_info["ref_max_f"]
                dec = a_info["decimals"]

                if t_i == 0:
                    t_status = "Verified" if idx % 2 == 0 else "Pending"
                elif t_i == len(chosen_codes) - 1:
                    t_status = "Pending"
                else:
                    t_status = rng.choice(["Verified", "Pending"])

                span = high_v - low_v
                if rng.random() < 0.18:
                    val = high_v + span * rng.uniform(0.05, 0.25)
                elif rng.random() < 0.12:
                    val = max(0.0, low_v - span * rng.uniform(0.05, 0.20))
                else:
                    val = rng.uniform(low_v + span * 0.1, high_v - span * 0.1)

                if code == "UA_SG":
                    val = round(rng.uniform(1.010, 1.025), 3)
                elif code == "UA_PH":
                    val = round(rng.uniform(5.5, 7.5), 1)
                elif dec == 0:
                    val = float(int(round(val)))
                else:
                    val = round(val, dec)

                val_str = f"{val:.{dec}f}"
                flag = self.compute_flag(val, low_v, high_v)
                verified_by = "Gaia Aubrey Manalo, MD, FPSP" if t_status == "Verified" else ""
                verified_at = now_str if t_status == "Verified" else ""

                cur.execute(
                    """
                    INSERT INTO order_tests (
                        order_id, assay_code, specimen_status, result_value, flag,
                        test_status, verified_by, verified_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        order_id,
                        code,
                        order_spec_status,
                        val_str,
                        flag,
                        t_status,
                        verified_by,
                        verified_at,
                        created_dt,
                    ),
                )

            if idx <= 12:
                order_no2 = f"ORD-{20262100 + idx}"
                phys2 = REQUESTING_PHYSICIANS[(idx + 1) % len(REQUESTING_PHYSICIANS)]
                extra_codes = ["FBS", "HBA1C", "CHOL", "TRIG", "HDL", "LDL", "CREA", "BUA", "ALT", "AST", "CRP", "TSH"]
                panel2 = extra_codes[:8] if idx % 2 == 1 else ["WBC", "HGB", "PLT", "FBS", "CREA", "CRP"]
                cur.execute(
                    """
                    INSERT INTO lab_orders (order_no, patient_id, physician, priority, specimen_status, clinical_notes, created_at, collected_at)
                    VALUES (?, ?, ?, ?, 'Pending', ?, ?, '')
                    """,
                    (
                        order_no2,
                        patient_id,
                        phys2,
                        "Routine",
                        "Pending follow-up panel (Admin / Worklist queue)",
                        now_str,
                    ),
                )
                order_id2 = cur.lastrowid
                for code in panel2:
                    a_info = assay_map[code]
                    low_v = a_info["ref_min_m"] if sex == "Male" else a_info["ref_min_f"]
                    high_v = a_info["ref_max_m"] if sex == "Male" else a_info["ref_max_f"]
                    dec = a_info["decimals"]
                    sample_val = round(rng.uniform(low_v, high_v), dec)
                    s_str = f"{sample_val:.{dec}f}"
                    flg = self.compute_flag(sample_val, low_v, high_v)
                    cur.execute(
                        """
                        INSERT INTO order_tests (
                            order_id, assay_code, specimen_status, result_value, flag,
                            test_status, verified_by, verified_at, updated_at
                        )
                        VALUES (?, ?, 'Pending', ?, ?, 'Pending', '', '', ?)
                        """,
                        (order_id2, code, s_str, flg, now_str),
                    )

        self.conn.commit()
        self.log_audit("System Seeder", "System", "SEED_DB", "Seeded Monocytes cohort patients (DOB 2004-2006), orders, and pending tests.")

    def _seed_qc_runs(self):
        rng = random.Random(42)
        now = datetime.now()
        qc_configs = [
            ("WBC", "LOT-WBC-2026A", "Level 1 Normal", 6.80, 0.25),
            ("HGB", "LOT-HGB-2026B", "Level 2 Abnormal High", 16.50, 0.40),
            ("FBS", "LOT-CHM-2026C", "Level 1 Normal", 92.00, 3.20),
            ("CREA", "LOT-CHM-2026C", "Level 1 Normal", 1.00, 0.06),
        ]
        for code, lot, lvl, mean, sd in qc_configs:
            for i in range(18):
                run_dt = (now - timedelta(days=18 - i)).strftime("%Y-%m-%d %H:%M")
                if code == "FBS" and i == 15:
                    measured = round(mean + 3.2 * sd, 2)
                elif code == "WBC" and i == 12:
                    measured = round(mean - 2.3 * sd, 2)
                else:
                    measured = round(rng.gauss(mean, sd * 0.85), 2)
                flag = self.evaluate_westgard(measured, mean, sd)
                self.conn.execute(
                    """
                    INSERT INTO qc_runs (assay_code, lot_no, level_name, measured_value, target_mean, sd_value, run_date, operator_name, westgard_flag)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (code, lot, lvl, measured, mean, sd, run_dt, "Carlyle Theodore Dioleste, RMT", flag),
                )
        self.conn.commit()

    @staticmethod
    def compute_flag(val: float, low: float, high: float) -> str:
        if val < low:
            return "L"
        if val > high:
            return "H"
        return "N"

    @staticmethod
    def evaluate_westgard(measured: float, mean: float, sd: float) -> str:
        if sd <= 0:
            return "PASS"
        z = abs(measured - mean) / sd
        if z > 3.0:
            return "FAIL (1:3s)"
        if z > 2.0:
            return "WARN (1:2s)"
        return "PASS"


# ==============================================================================
# ZOOMABLE & SCROLLABLE QC CHART WIDGET
# ==============================================================================
class ZoomableQCChartWidget(QWidget):
    """Scrollable and zoomable Levey-Jennings QC chart canvas."""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.zoom_factor = 1.0
        self.runs_data = []
        self.assay_code = "WBC"
        self.unit = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        ctrl_bar = QHBoxLayout()
        ctrl_bar.addWidget(QLabel("Chart Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(75)
        self.zoom_slider.setMaximum(250)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(160)
        self.zoom_slider.valueChanged.connect(self._on_slider_zoom)
        ctrl_bar.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(48)
        ctrl_bar.addWidget(self.zoom_label)

        btn_out = QPushButton("Zoom -")
        btn_out.setFixedWidth(68)
        btn_out.clicked.connect(lambda: self.set_zoom(self.zoom_factor - 0.15))
        ctrl_bar.addWidget(btn_out)

        btn_in = QPushButton("Zoom +")
        btn_in.setFixedWidth(68)
        btn_in.clicked.connect(lambda: self.set_zoom(self.zoom_factor + 0.15))
        ctrl_bar.addWidget(btn_in)

        btn_reset = QPushButton("Reset Zoom")
        btn_reset.clicked.connect(lambda: self.set_zoom(1.0))
        ctrl_bar.addWidget(btn_reset)

        ctrl_bar.addStretch()
        hint = QLabel("Tip: Ctrl + Scroll or use Zoom slider; scroll bars adjust view")
        hint.setProperty("muted", True)
        ctrl_bar.addWidget(hint)
        layout.addLayout(ctrl_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.viewport().installEventFilter(self)

        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(4, 4, 4, 4)

        if HAS_MATPLOTLIB:
            self.figure = Figure(figsize=(8.0, 4.2), dpi=100)
            self.canvas = FigureCanvas(self.figure)
            self.canvas_layout.addWidget(self.canvas)
        else:
            self.figure = None
            self.canvas = None
            self.fallback_label = QLabel("Matplotlib not installed; QC tabular data available below.")
            self.canvas_layout.addWidget(self.fallback_label)

        self.scroll_area.setWidget(self.canvas_container)
        layout.addWidget(self.scroll_area)
        self._apply_zoom_size()

    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport() and event.type() == QWheelEvent.Type.Wheel:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                step = 0.12 if delta > 0 else -0.12
                self.set_zoom(self.zoom_factor + step)
                return True
        return super().eventFilter(obj, event)

    def set_zoom(self, factor: float):
        clamped = max(0.75, min(2.50, round(factor, 2)))
        self.zoom_factor = clamped
        pct = int(round(clamped * 100))
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(pct)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{pct}%")
        self._apply_zoom_size()
        self.redraw()

    def _on_slider_zoom(self, val: int):
        self.set_zoom(val / 100.0)

    def _apply_zoom_size(self):
        base_w = 780
        base_h = 390
        w = int(base_w * self.zoom_factor)
        h = int(base_h * self.zoom_factor)
        self.canvas_container.setMinimumSize(w, h)
        self.canvas_container.resize(w, h)
        if self.canvas is not None:
            self.canvas.setMinimumSize(w - 8, h - 8)
            self.canvas.resize(w - 8, h - 8)

    def set_theme(self, theme: dict):
        self.theme = theme
        self.redraw()

    def plot_runs(self, assay_code: str, unit: str, runs: list):
        self.assay_code = assay_code
        self.unit = unit
        self.runs_data = runs or []
        self.redraw()

    def redraw(self):
        if not HAS_MATPLOTLIB or self.figure is None or self.canvas is None:
            return
        t = self.theme
        self.figure.clear()
        self.figure.patch.set_facecolor(t["plot_bg"])
        ax = self.figure.add_subplot(111)
        ax.set_facecolor(t["plot_bg"])

        if not self.runs_data:
            ax.text(
                0.5, 0.5, f"No QC runs logged for {self.assay_code}",
                ha="center", va="center", color=t["text_muted"], fontsize=11 * self.zoom_factor
            )
            ax.set_xticks([])
            ax.set_yticks([])
            self.canvas.draw()
            return

        xs = list(range(1, len(self.runs_data) + 1))
        ys = [float(r["measured_value"]) for r in self.runs_data]
        mean = float(self.runs_data[-1]["target_mean"])
        sd = float(self.runs_data[-1]["sd_value"])

        ax.axhline(mean, color=t["plot_mean"], linestyle="-", linewidth=1.6, label=f"Mean ({mean:.2f})")
        if sd > 0:
            for k, col, ls in [
                (1, t["plot_sd1"], "--"),
                (2, t["plot_sd2"], "-."),
                (3, t["plot_sd3"], ":"),
            ]:
                ax.axhline(mean + k * sd, color=col, linestyle=ls, linewidth=1.1, label=f"+{k}SD ({mean + k*sd:.2f})" if k == 3 else None)
                ax.axhline(mean - k * sd, color=col, linestyle=ls, linewidth=1.1)

        ax.plot(xs, ys, marker="o", color=t["plot_line"], linewidth=1.8, markersize=5.5)

        for x_val, y_val, r in zip(xs, ys, self.runs_data):
            if "FAIL" in r["westgard_flag"]:
                ax.scatter([x_val], [y_val], color=t["plot_sd3"], s=65, zorder=5)
            elif "WARN" in r["westgard_flag"]:
                ax.scatter([x_val], [y_val], color=t["plot_sd2"], s=55, zorder=5)

        ax.set_title(
            f"Levey-Jennings Chart — {self.assay_code} ({self.unit}) | Zoom {int(self.zoom_factor*100)}%",
            color=t["text_main"], fontsize=11 * self.zoom_factor, fontweight="bold"
        )
        ax.set_xlabel("Run Sequence #", color=t["text_main"], fontsize=9.5 * self.zoom_factor)
        ax.set_ylabel(f"Measured ({self.unit})", color=t["text_main"], fontsize=9.5 * self.zoom_factor)
        ax.tick_params(colors=t["text_main"], labelsize=8.5 * self.zoom_factor)
        ax.grid(True, color=t["plot_grid"], linestyle="--", linewidth=0.6)
        for spine in ax.spines.values():
            spine.set_color(t["border"])

        leg = ax.legend(loc="upper right", fontsize=8 * self.zoom_factor)
        leg.get_frame().set_facecolor(t["bg_card"])
        leg.get_frame().set_edgecolor(t["border"])
        for txt in leg.get_texts():
            txt.set_color(t["text_main"])

        self.figure.tight_layout()
        self.canvas.draw()


# ==============================================================================
# BATCH VERIFY DIALOG (SCROLLABLE)
# ==============================================================================
class BatchVerifyDialog(QDialog):
    """Scrollable batch verification modal so large multi-test orders never squish."""

    def __init__(self, db: LISDatabase, order_row, test_rows: list, patient_row, assay_map: dict, actor_name: str, theme: dict, parent=None):
        super().__init__(parent)
        self.db = db
        self.order_row = order_row
        self.test_rows = test_rows
        self.patient_row = patient_row
        self.assay_map = assay_map
        self.actor_name = actor_name
        self.theme = theme
        self.row_controls = []

        self.setWindowTitle(f"Batch Verify Results — {order_row['order_no']} ({patient_row['full_name']})")
        self.resize(880, 640)
        self.setMinimumSize(680, 420)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        hdr_frame = QFrame()
        hdr_frame.setProperty("card", True)
        hdr_lay = QVBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(12, 10, 12, 10)
        title_lbl = QLabel(f"Order: {order_row['order_no']}   |   Patient: {patient_row['full_name']} ({patient_row['mrn']})   |   Sex/DOB: {patient_row['sex']} / {patient_row['dob']}")
        title_lbl.setStyleSheet("font-weight: 700; font-size: 11pt;")
        sub_lbl = QLabel(f"Requesting Physician: {order_row['physician']}   |   Priority: {order_row['priority']}   |   Tests in Panel: {len(test_rows)}")
        sub_lbl.setProperty("muted", True)
        hdr_lay.addWidget(title_lbl)
        hdr_lay.addWidget(sub_lbl)
        root.addWidget(hdr_frame)

        q_bar = QHBoxLayout()
        btn_all_ver = QPushButton("Mark All Verified")
        btn_all_ver.clicked.connect(lambda: self._set_all_statuses("Verified"))
        q_bar.addWidget(btn_all_ver)

        btn_all_pend = QPushButton("Mark All Pending")
        btn_all_pend.clicked.connect(lambda: self._set_all_statuses("Pending"))
        q_bar.addWidget(btn_all_pend)

        q_bar.addStretch()
        scroll_note = QLabel("Scroll vertically or horizontally as needed for large test panels")
        scroll_note.setProperty("muted", True)
        q_bar.addWidget(scroll_note)
        root.addLayout(q_bar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        inner_widget = QWidget()
        grid = QGridLayout(inner_widget)
        grid.setContentsMargins(6, 6, 12, 6)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        headers = ["Assay", "Specimen", "Result Value", "Unit", "Ref Range", "Flag", "Status"]
        for col_idx, h_text in enumerate(headers):
            lbl = QLabel(h_text)
            lbl.setStyleSheet("font-weight: 700;")
            lbl.setMinimumHeight(24)
            grid.addWidget(lbl, 0, col_idx)

        sex = patient_row["sex"]
        for r_idx, t_row in enumerate(test_rows, start=1):
            code = t_row["assay_code"]
            a_info = assay_map.get(code, {})
            low_v = a_info.get("ref_min_m", 0.0) if sex == "Male" else a_info.get("ref_min_f", 0.0)
            high_v = a_info.get("ref_max_m", 100.0) if sex == "Male" else a_info.get("ref_max_f", 100.0)
            dec = int(a_info.get("decimals", 1))
            unit = a_info.get("unit", "")

            assay_lbl = QLabel(f"{code} — {a_info.get('name', code)}")
            assay_lbl.setMinimumWidth(210)
            assay_lbl.setMinimumHeight(30)

            spec_lbl = QLabel(t_row["specimen_status"] or order_row["specimen_status"])
            spec_lbl.setMinimumWidth(90)

            val_edit = QLineEdit(str(t_row["result_value"] or ""))
            val_edit.setMinimumWidth(105)
            val_edit.setMinimumHeight(30)

            unit_lbl = QLabel(unit)
            unit_lbl.setMinimumWidth(75)

            ref_lbl = QLabel(f"{low_v:.{dec}f} - {high_v:.{dec}f}")
            ref_lbl.setMinimumWidth(110)

            flag_lbl = QLabel(str(t_row["flag"] or "N"))
            flag_lbl.setMinimumWidth(42)
            flag_lbl.setAlignment(Qt.AlignCenter)

            status_combo = QComboBox()
            status_combo.addItems(["Pending", "Verified"])
            cur_st = t_row["test_status"] if t_row["test_status"] in ("Pending", "Verified") else "Pending"
            status_combo.setCurrentText(cur_st)
            status_combo.setMinimumWidth(110)
            status_combo.setMinimumHeight(30)

            def make_updater(edit_w, f_lbl, lo, hi, d):
                def _upd():
                    txt = edit_w.text().strip()
                    try:
                        num = float(txt)
                        f_lbl.setText(LISDatabase.compute_flag(num, lo, hi))
                    except ValueError:
                        f_lbl.setText("")
                return _upd

            val_edit.textChanged.connect(make_updater(val_edit, flag_lbl, low_v, high_v, dec))

            grid.addWidget(assay_lbl, r_idx, 0)
            grid.addWidget(spec_lbl, r_idx, 1)
            grid.addWidget(val_edit, r_idx, 2)
            grid.addWidget(unit_lbl, r_idx, 3)
            grid.addWidget(ref_lbl, r_idx, 4)
            grid.addWidget(flag_lbl, r_idx, 5)
            grid.addWidget(status_combo, r_idx, 6)

            self.row_controls.append({
                "test_id": t_row["id"],
                "assay_code": code,
                "low": low_v,
                "high": high_v,
                "val_edit": val_edit,
                "flag_lbl": flag_lbl,
                "status_combo": status_combo,
            })

        scroll.setWidget(inner_widget)
        root.addWidget(scroll, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Save Batch Results")
        btn_save.setProperty("accent", True)
        btn_save.clicked.connect(self._save_batch)
        btn_row.addWidget(btn_save)

        root.addLayout(btn_row)

    def _set_all_statuses(self, status_text: str):
        for item in self.row_controls:
            item["status_combo"].setCurrentText(status_text)

    def _save_batch(self):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.conn.cursor()
        verified_count = 0

        for item in self.row_controls:
            val_txt = item["val_edit"].text().strip()
            flag_txt = item["flag_lbl"].text().strip()
            st_txt = item["status_combo"].currentText()

            try:
                num_val = float(val_txt)
                if not flag_txt:
                    flag_txt = LISDatabase.compute_flag(num_val, item["low"], item["high"])
            except ValueError:
                pass

            v_by = self.actor_name if st_txt == "Verified" else ""
            v_at = now_str if st_txt == "Verified" else ""
            if st_txt == "Verified":
                verified_count += 1

            cur.execute(
                """
                UPDATE order_tests
                SET result_value = ?, flag = ?, test_status = ?, verified_by = ?, verified_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (val_txt, flag_txt, st_txt, v_by, v_at, now_str, item["test_id"]),
            )

        self.db.conn.commit()
        self.db.log_audit(
            self.actor_name,
            "Staff",
            "BATCH_VERIFY",
            f"Order {self.order_row['order_no']} ({self.patient_row['full_name']}): saved {len(self.row_controls)} tests ({verified_count} Verified).",
        )
        self.accept()


# ==============================================================================
# PIN LOGIN DIALOG (LIGHT MODE DEFAULT)
# ==============================================================================
class PinLoginDialog(QDialog):
    def __init__(self, theme_mode: str = "light", parent=None):
        super().__init__(parent)
        self.theme_mode = theme_mode
        self.authenticated_user = None
        self.setWindowTitle(f"{APP_TITLE} — Staff PIN Login")
        self.setFixedSize(440, 310)
        self.setStyleSheet(build_stylesheet(theme_mode))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        hdr = QLabel(APP_TITLE)
        hdr.setStyleSheet("font-size: 16pt; font-weight: 800;")
        sub = QLabel("Enter 4-digit RMT (0001–0012) or Pathologist (1111) PIN")
        sub.setProperty("muted", True)
        lay.addWidget(hdr)
        lay.addWidget(sub)

        form = QFormLayout()
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.Password)
        self.pin_input.setMaxLength(4)
        self.pin_input.setPlaceholderText("e.g. 0012 or 1111")
        self.pin_input.returnPressed.connect(self._attempt_login)
        form.addRow("Staff PIN:", self.pin_input)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        self.theme_combo.setCurrentText("Light" if theme_mode == "light" else "Dark")
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        form.addRow("Default Theme:", self.theme_combo)
        lay.addLayout(form)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setStyleSheet("color: #B91C1C; font-weight: 600;")
        lay.addWidget(self.feedback_lbl)

        lay.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        btn_login = QPushButton("Sign In")
        btn_login.setProperty("accent", True)
        btn_login.clicked.connect(self._attempt_login)
        btns.addWidget(btn_login)
        lay.addLayout(btns)

    def _on_theme_change(self, label: str):
        self.theme_mode = "dark" if label.lower() == "dark" else "light"
        self.setStyleSheet(build_stylesheet(self.theme_mode))

    def _attempt_login(self):
        pin = self.pin_input.text().strip()
        if pin in STAFF_ROLES:
            name, role = STAFF_ROLES[pin]
            self.authenticated_user = {"pin": pin, "name": name, "role": role}
            self.accept()
        else:
            self.feedback_lbl.setText("Invalid PIN. Use an authorized Monocytes RMT or Pathologist PIN.")
            self.pin_input.selectAll()
            self.pin_input.setFocus()


# ==============================================================================
# MAIN LIS APPLICATION WINDOW
# ==============================================================================
class MonocytesLISWindow(QMainWindow):
    def __init__(self, db: LISDatabase, user_info: dict, initial_theme: str = "light"):
        super().__init__()
        self.db = db
        self.user_info = user_info
        self.theme_mode = initial_theme if initial_theme in ("light", "dark") else "light"
        self.admin_mode = False

        self.setWindowTitle(f"{APP_TITLE} ({APP_VERSION}) — {user_info['name']} [{user_info['role']}]")
        self.resize(1320, 840)
        self.setMinimumSize(1024, 680)

        self._build_ui()
        self.apply_theme(self.theme_mode)
        self.refresh_all_views()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(10, 10, 10, 10)
        main_lay.setSpacing(8)

        top_frame = QFrame()
        top_frame.setProperty("card", True)
        top_lay = QHBoxLayout(top_frame)
        top_lay.setContentsMargins(12, 8, 12, 8)

        brand_lbl = QLabel(f"{APP_TITLE}")
        brand_lbl.setStyleSheet("font-size: 13pt; font-weight: 800;")
        top_lay.addWidget(brand_lbl)

        user_lbl = QLabel(f"Logged in: {self.user_info['name']} ({self.user_info['role']})")
        user_lbl.setProperty("muted", True)
        top_lay.addWidget(user_lbl)

        self.status_pulse = VerificationStatusPulseWidget(THEMES[self.theme_mode])
        self.status_pulse.setMinimumWidth(190)
        top_lay.addWidget(self.status_pulse)

        top_lay.addStretch()

        self.theme_btn = QPushButton("Theme: Light")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top_lay.addWidget(self.theme_btn)

        self.admin_toggle_btn = QPushButton("Admin Mode: OFF")
        self.admin_toggle_btn.setCheckable(True)
        self.admin_toggle_btn.clicked.connect(self.toggle_admin_mode)
        top_lay.addWidget(self.admin_toggle_btn)

        main_lay.addWidget(top_frame)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_lay.addWidget(self.tabs, stretch=1)

        self._build_worklist_tab()
        self._build_patients_tab()
        self._build_qc_tab()
        self._build_admin_tab()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — Light Mode default active.")

    def apply_theme(self, mode: str):
        self.theme_mode = "dark" if mode == "dark" else "light"
        self.setStyleSheet(build_stylesheet(self.theme_mode))
        self.theme_btn.setText(f"Theme: {'Dark' if self.theme_mode == 'dark' else 'Light'}")
        if hasattr(self, "qc_chart"):
            self.qc_chart.set_theme(THEMES[self.theme_mode])
        if hasattr(self, "ref_bar"):
            self.ref_bar.set_theme(THEMES[self.theme_mode])
        if hasattr(self, "status_pulse"):
            self.status_pulse.set_theme(THEMES[self.theme_mode])

    def toggle_theme(self):
        next_mode = "dark" if self.theme_mode == "light" else "light"
        self.apply_theme(next_mode)
        self.status_pulse.trigger_status(f"Theme: {next_mode.capitalize()}")
        self.status_bar.showMessage(f"Switched theme to {next_mode.capitalize()} Mode.")

    def toggle_admin_mode(self):
        self.admin_mode = self.admin_toggle_btn.isChecked()
        if self.admin_mode:
            self.admin_toggle_btn.setText("Admin Mode: ON")
            self.admin_toggle_btn.setProperty("accent", True)
        else:
            self.admin_toggle_btn.setText("Admin Mode: OFF")
            self.admin_toggle_btn.setProperty("accent", False)
        self.admin_toggle_btn.style().unpolish(self.admin_toggle_btn)
        self.admin_toggle_btn.style().polish(self.admin_toggle_btn)
        self.refresh_all_views()
        self.status_pulse.trigger_status("Admin Mode ON" if self.admin_mode else "Admin Mode OFF")
        self.status_bar.showMessage(f"Admin Mode {'enabled — showing pending & admin sample queues' if self.admin_mode else 'disabled'}.")

    def _on_tab_changed(self, index: int):
        tab_text = self.tabs.tabText(index)
        if "QC" in tab_text and hasattr(self, "qc_chart"):
            self.refresh_qc_view()
        elif "Patients" in tab_text:
            self.refresh_patients_view()
        elif "Worklist" in tab_text:
            self.refresh_worklist_view()
        elif "Admin" in tab_text:
            self.refresh_admin_view()

    # --------------------------------------------------------------------------
    # TAB 1: WORKLIST & SPECIMEN COLLECTION (WHOLE ORDER COLLECTED)
    # --------------------------------------------------------------------------
    def _build_worklist_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        ctrl_lay = QHBoxLayout()
        ctrl_lay.addWidget(QLabel("Filter Worklist:"))
        self.wl_search = QLineEdit()
        self.wl_search.setPlaceholderText("Search order #, patient name, MRN, physician, or assay...")
        self.wl_search.textChanged.connect(self.refresh_worklist_view)
        ctrl_lay.addWidget(self.wl_search)

        self.wl_status_filter = QComboBox()
        self.wl_status_filter.addItems(["All", "Pending", "Collected", "Verified"])
        self.wl_status_filter.currentTextChanged.connect(self.refresh_worklist_view)
        ctrl_lay.addWidget(self.wl_status_filter)

        self.btn_verify_results = QPushButton("Verify Results")
        self.btn_verify_results.setProperty("accent", True)
        self.btn_verify_results.clicked.connect(self.open_verify_results_for_selected)
        ctrl_lay.addWidget(self.btn_verify_results)

        btn_collect_order = QPushButton("Mark Selected Order Collected")
        btn_collect_order.clicked.connect(self.mark_selected_order_collected)
        ctrl_lay.addWidget(btn_collect_order)

        btn_pdf = QPushButton("Export Order PDF")
        btn_pdf.clicked.connect(self.export_selected_order_pdf)
        ctrl_lay.addWidget(btn_pdf)

        lay.addLayout(ctrl_lay)

        self.wl_table = QTableWidget(0, 8)
        self.wl_table.setHorizontalHeaderLabels([
            "Order #", "Patient Name", "MRN", "Physician",
            "Specimen Status", "Tests Summary", "Test Status", "Actions"
        ])
        self.wl_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wl_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.wl_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.wl_table.setAlternatingRowColors(True)
        self.wl_table.itemSelectionChanged.connect(self._on_worklist_row_selected)
        lay.addWidget(self.wl_table, stretch=2)

        # Expandable / Detailed Tests Breakdown & Reference Range Visualizer
        detail_box = QGroupBox("Order Test Panel Details & Reference Range Visualizer")
        d_lay = QVBoxLayout(detail_box)
        self.ref_bar = ReferenceRangeBarWidget(THEMES[self.theme_mode])
        d_lay.addWidget(self.ref_bar)

        self.order_tests_table = QTableWidget(0, 7)
        self.order_tests_table.setHorizontalHeaderLabels([
            "Assay", "Test Name", "Result", "Unit", "Ref Range", "Flag", "Status"
        ])
        self.order_tests_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_tests_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.order_tests_table.setAlternatingRowColors(True)
        self.order_tests_table.itemSelectionChanged.connect(self._on_order_test_selected)
        d_lay.addWidget(self.order_tests_table)

        lay.addWidget(detail_box, stretch=1)
        self.tabs.addTab(tab, "Worklist")

    def mark_order_entirely_collected(self, order_id: int, order_no: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.db.conn.cursor()
        cur.execute(
            """
            UPDATE lab_orders
            SET specimen_status = 'Collected',
                collected_at = CASE WHEN collected_at = '' THEN ? ELSE collected_at END
            WHERE id = ?
            """,
            (now_str, order_id),
        )
        cur.execute(
            """
            UPDATE order_tests
            SET specimen_status = 'Collected', updated_at = ?
            WHERE order_id = ?
            """,
            (now_str, order_id),
        )
        self.db.conn.commit()
        self.db.log_audit(
            self.user_info["name"],
            self.user_info["role"],
            "ORDER_COLLECTED",
            f"Entire order {order_no} and all associated tests set to Collected.",
        )
        self.refresh_worklist_view()
        self.status_pulse.trigger_status(f"Collected: {order_no}")
        self.status_bar.showMessage(f"Order {order_no}: entire order and all tests marked as Collected.")

    def mark_selected_order_collected(self):
        row = self.wl_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select Order", "Please select a worklist row first.")
            return
        item0 = self.wl_table.item(row, 0)
        order_id = item0.data(Qt.UserRole)
        order_no = item0.text()
        self.mark_order_entirely_collected(order_id, order_no)

    def _current_worklist_order_id(self):
        row = self.wl_table.currentRow()
        if row < 0:
            return None
        it = self.wl_table.item(row, 0)
        return it.data(Qt.UserRole) if it else None

    def _on_worklist_row_selected(self):
        order_id = self._current_worklist_order_id()
        self.order_tests_table.setRowCount(0)
        if not order_id:
            return

        cur = self.db.conn.cursor()
        order = cur.execute("SELECT * FROM lab_orders WHERE id = ?", (order_id,)).fetchone()
        patient = cur.execute("SELECT * FROM patients WHERE id = ?", (order["patient_id"],)).fetchone()
        tests = cur.execute("SELECT * FROM order_tests WHERE order_id = ? ORDER BY id ASC", (order_id,)).fetchall()
        assays = {r["code"]: dict(r) for r in cur.execute("SELECT * FROM assays").fetchall()}

        sex = patient["sex"] if patient else "Female"
        for t in tests:
            a = assays.get(t["assay_code"], {})
            lo = a.get("ref_min_m", 0.0) if sex == "Male" else a.get("ref_min_f", 0.0)
            hi = a.get("ref_max_m", 100.0) if sex == "Male" else a.get("ref_max_f", 100.0)
            dec = int(a.get("decimals", 1))
            unit = a.get("unit", "")

            r = self.order_tests_table.rowCount()
            self.order_tests_table.insertRow(r)
            it_c = QTableWidgetItem(t["assay_code"])
            it_c.setData(Qt.UserRole, {"lo": lo, "hi": hi, "unit": unit, "name": a.get("name", t["assay_code"]), "val": t["result_value"]})
            self.order_tests_table.setItem(r, 0, it_c)
            self.order_tests_table.setItem(r, 1, QTableWidgetItem(a.get("name", t["assay_code"])))
            self.order_tests_table.setItem(r, 2, QTableWidgetItem(t["result_value"] or ""))
            self.order_tests_table.setItem(r, 3, QTableWidgetItem(unit))
            self.order_tests_table.setItem(r, 4, QTableWidgetItem(f"{lo:.{dec}f} - {hi:.{dec}f}"))
            self.order_tests_table.setItem(r, 5, QTableWidgetItem(t["flag"] or "N"))
            self.order_tests_table.setItem(r, 6, QTableWidgetItem(t["test_status"]))

        if self.order_tests_table.rowCount() > 0:
            self.order_tests_table.selectRow(0)

    def _on_order_test_selected(self):
        r = self.order_tests_table.currentRow()
        if r < 0:
            return
        it0 = self.order_tests_table.item(r, 0)
        it2 = self.order_tests_table.item(r, 2)
        if not it0:
            return
        meta = it0.data(Qt.UserRole) or {}
        val_str = it2.text() if it2 else ""
        lbl = f"{it0.text()} ({meta.get('name', '')}) — Result: {val_str or 'N/A'} {meta.get('unit', '')} | Ref: {meta.get('lo', 0)}–{meta.get('hi', 100)}"
        self.ref_bar.set_range_data(lbl, val_str, meta.get("lo", 0.0), meta.get("hi", 100.0), meta.get("unit", ""))

    def open_verify_results_for_selected(self, order_id=None):
        if not isinstance(order_id, int):
            order_id = self._current_worklist_order_id()
        if not order_id:
            QMessageBox.information(self, "Verify Results", "Select an order row first to verify results.")
            return

        cur = self.db.conn.cursor()
        order_row = cur.execute("SELECT * FROM lab_orders WHERE id = ?", (order_id,)).fetchone()
        if not order_row:
            return
        patient_row = cur.execute("SELECT * FROM patients WHERE id = ?", (order_row["patient_id"],)).fetchone()
        test_rows = cur.execute("SELECT * FROM order_tests WHERE order_id = ? ORDER BY id ASC", (order_id,)).fetchall()
        assay_rows = cur.execute("SELECT * FROM assays").fetchall()
        assay_map = {r["code"]: dict(r) for r in assay_rows}

        dlg = BatchVerifyDialog(
            self.db,
            dict(order_row),
            [dict(t) for t in test_rows],
            dict(patient_row),
            assay_map,
            self.user_info["name"],
            THEMES[self.theme_mode],
            self,
        )
        dlg.setStyleSheet(build_stylesheet(self.theme_mode))
        if dlg.exec() == QDialog.Accepted:
            self.refresh_worklist_view()
            self.refresh_admin_view()
            self.status_pulse.trigger_status(f"Verified: {order_row['order_no']}")
            self.status_bar.showMessage(f"Batch verification saved for order {order_row['order_no']}.")

    def export_selected_order_pdf(self):
        order_id = self._current_worklist_order_id()
        if not order_id:
            QMessageBox.information(self, "Export PDF", "Select an order row first.")
            return

        cur = self.db.conn.cursor()
        order = cur.execute("SELECT * FROM lab_orders WHERE id = ?", (order_id,)).fetchone()
        patient = cur.execute("SELECT * FROM patients WHERE id = ?", (order["patient_id"],)).fetchone()
        tests = cur.execute("SELECT * FROM order_tests WHERE order_id = ? ORDER BY id ASC", (order_id,)).fetchall()
        assays = {r["code"]: dict(r) for r in cur.execute("SELECT * FROM assays").fetchall()}

        default_path = f"{order['order_no']}_{patient['full_name'].replace(' ', '_')}_Lab_Report.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Laboratory PDF Report", default_path, "PDF Files (*.pdf)")
        if not file_path:
            return

        rows_html = []
        sex = patient["sex"]
        for t in tests:
            a = assays.get(t["assay_code"], {})
            lo = a.get("ref_min_m", 0.0) if sex == "Male" else a.get("ref_min_f", 0.0)
            hi = a.get("ref_max_m", 100.0) if sex == "Male" else a.get("ref_max_f", 100.0)
            dec = int(a.get("decimals", 1))
            rows_html.append(
                f"<tr><td>{t['assay_code']}</td><td>{a.get('name', t['assay_code'])}</td>"
                f"<td><b>{t['result_value']}</b></td><td>{a.get('unit', '')}</td>"
                f"<td>{lo:.{dec}f} - {hi:.{dec}f}</td><td>{t['flag']}</td><td>{t['test_status']}</td></tr>"
            )

        html = f"""
        <html><body style="font-family: Arial, sans-serif; color: #111;">
        <h2>Monocytes Delegates LIS — Laboratory Report</h2>
        <p><b>Order #:</b> {order['order_no']} &nbsp;|&nbsp; <b>Date:</b> {order['created_at']}<br/>
        <b>Patient:</b> {patient['full_name']} ({patient['mrn']}) &nbsp;|&nbsp; <b>Sex/DOB:</b> {patient['sex']} / {patient['dob']}<br/>
        <b>Requesting Physician:</b> {order['physician']} &nbsp;|&nbsp; <b>Specimen:</b> {order['specimen_status']}</p>
        <table border="1" cellspacing="0" cellpadding="6" width="100%">
        <tr style="background:#eef2f7;"><th>Code</th><th>Assay</th><th>Result</th><th>Unit</th><th>Ref Range</th><th>Flag</th><th>Status</th></tr>
        {''.join(rows_html)}
        </table>
        <p style="margin-top:24px;"><b>Verified / Encoded By:</b> {self.user_info['name']} ({self.user_info['role']})</p>
        </body></html>
        """
        from PySide6.QtGui import QTextDocument
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        doc.print_(printer)
        self.db.log_audit(self.user_info["name"], self.user_info["role"], "EXPORT_PDF", f"Exported {file_path}")
        self.status_bar.showMessage(f"Exported PDF report to {file_path}")

    def refresh_worklist_view(self):
        q = self.wl_search.text().strip().lower()
        st_filter = self.wl_status_filter.currentText()
        prev_oid = self._current_worklist_order_id()

        cur = self.db.conn.cursor()
        orders = cur.execute("""
            SELECT o.*, p.full_name, p.mrn, p.sex, p.dob
            FROM lab_orders o
            JOIN patients p ON o.patient_id = p.id
            ORDER BY o.id DESC
        """).fetchall()

        self.wl_table.setRowCount(0)
        for o in orders:
            tests = cur.execute("SELECT * FROM order_tests WHERE order_id = ?", (o["id"],)).fetchall()
            codes = [t["assay_code"] for t in tests]
            statuses = [t["test_status"] for t in tests]

            if all(s == "Verified" for s in statuses) and statuses:
                overall_test_status = "Verified"
            elif any(s == "Verified" for s in statuses):
                overall_test_status = "Partially Verified"
            else:
                overall_test_status = "Pending"

            spec_st = o["specimen_status"]
            summary_str = ", ".join(codes[:5]) + (f" (+{len(codes)-5})" if len(codes) > 5 else "")

            haystack = f"{o['order_no']} {o['full_name']} {o['mrn']} {o['physician']} {' '.join(codes)}".lower()
            if q and q not in haystack:
                continue

            if st_filter == "Pending" and overall_test_status == "Verified":
                continue
            if st_filter == "Collected" and spec_st != "Collected":
                continue
            if st_filter == "Verified" and overall_test_status != "Verified":
                continue

            r_idx = self.wl_table.rowCount()
            self.wl_table.insertRow(r_idx)

            it_ord = QTableWidgetItem(o["order_no"])
            it_ord.setData(Qt.UserRole, o["id"])
            self.wl_table.setItem(r_idx, 0, it_ord)
            self.wl_table.setItem(r_idx, 1, QTableWidgetItem(o["full_name"]))
            self.wl_table.setItem(r_idx, 2, QTableWidgetItem(o["mrn"]))
            self.wl_table.setItem(r_idx, 3, QTableWidgetItem(o["physician"]))

            spec_combo = QComboBox()
            spec_combo.addItems(["Pending", "Collected"])
            spec_combo.setCurrentText(spec_st if spec_st in ("Pending", "Collected") else "Pending")
            oid = o["id"]
            ono = o["order_no"]

            def make_spec_cb(order_id_val, order_no_val, prev_status):
                def _on_change(new_val):
                    if new_val == "Collected" and prev_status != "Collected":
                        self.mark_order_entirely_collected(order_id_val, order_no_val)
                return _on_change

            spec_combo.currentTextChanged.connect(make_spec_cb(oid, ono, spec_st))
            self.wl_table.setCellWidget(r_idx, 4, spec_combo)

            self.wl_table.setItem(r_idx, 5, QTableWidgetItem(summary_str))
            self.wl_table.setItem(r_idx, 6, QTableWidgetItem(overall_test_status))

            btn_ver = QPushButton("Verify Results")
            btn_ver.clicked.connect(lambda _checked=False, target_oid=oid: self.open_verify_results_for_selected(target_oid))
            self.wl_table.setCellWidget(r_idx, 7, btn_ver)

        if self.wl_table.rowCount() > 0:
            selected_r = 0
            if prev_oid:
                for r in range(self.wl_table.rowCount()):
                    if self.wl_table.item(r, 0).data(Qt.UserRole) == prev_oid:
                        selected_r = r
                        break
            self.wl_table.selectRow(selected_r)
            self._on_worklist_row_selected()

    # --------------------------------------------------------------------------
    # TAB 2: SEARCHABLE PATIENTS & ORDER NEW TESTS
    # --------------------------------------------------------------------------
    def _build_patients_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        search_bar = QHBoxLayout()
        search_bar.addWidget(QLabel("Search Patient:"))
        self.patient_search_input = QLineEdit()
        self.patient_search_input.setPlaceholderText("Type patient name, MRN, or birthday to search & select...")
        self.patient_search_input.textChanged.connect(self._on_patient_search_changed)
        search_bar.addWidget(self.patient_search_input, stretch=2)

        self.patient_quick_combo = QComboBox()
        self.patient_quick_combo.setMinimumWidth(280)
        self.patient_quick_combo.currentIndexChanged.connect(self._on_patient_combo_selected)
        search_bar.addWidget(self.patient_quick_combo, stretch=1)

        lay.addLayout(search_bar)

        self.patients_table = QTableWidget(0, 6)
        self.patients_table.setHorizontalHeaderLabels(["MRN", "Patient Name", "Sex", "Birthday", "Contact", "Orders"])
        self.patients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.patients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.patients_table.setAlternatingRowColors(True)
        self.patients_table.itemSelectionChanged.connect(self._on_patient_table_selected)
        lay.addWidget(self.patients_table, stretch=1)

        order_box = QGroupBox("Order New Tests for Selected Patient")
        o_lay = QGridLayout(order_box)

        self.selected_patient_lbl = QLabel("Selected Patient: None")
        self.selected_patient_lbl.setStyleSheet("font-weight: 700;")
        o_lay.addWidget(self.selected_patient_lbl, 0, 0, 1, 2)

        o_lay.addWidget(QLabel("Requesting Physician:"), 1, 0)
        self.order_phys_combo = QComboBox()
        self.order_phys_combo.addItems(REQUESTING_PHYSICIANS)
        o_lay.addWidget(self.order_phys_combo, 1, 1)

        o_lay.addWidget(QLabel("Priority:"), 1, 2)
        self.order_prio_combo = QComboBox()
        self.order_prio_combo.addItems(["Routine", "STAT"])
        o_lay.addWidget(self.order_prio_combo, 1, 3)

        o_lay.addWidget(QLabel("Select Assays:"), 2, 0)
        self.assay_select_combo = QComboBox()
        o_lay.addWidget(self.assay_select_combo, 2, 1)

        self.extra_assays_edit = QLineEdit()
        self.extra_assays_edit.setPlaceholderText("Or comma-separated codes (e.g. WBC, HGB, FBS, CREA)")
        o_lay.addWidget(self.extra_assays_edit, 2, 2)

        btn_create_order = QPushButton("Create Test Order")
        btn_create_order.setProperty("accent", True)
        btn_create_order.clicked.connect(self.create_new_test_order)
        o_lay.addWidget(btn_create_order, 2, 3)

        lay.addWidget(order_box)
        self.tabs.addTab(tab, "Patients")

    def _on_patient_search_changed(self):
        query = self.patient_search_input.text().strip().lower()
        self.refresh_patients_view(filter_query=query)
        if self.patients_table.rowCount() > 0 and query:
            self.patients_table.selectRow(0)
            mrn_item = self.patients_table.item(0, 0)
            name_item = self.patients_table.item(0, 1)
            if mrn_item and name_item:
                self.selected_patient_lbl.setText(f"Selected Patient: {name_item.text()} ({mrn_item.text()})")

    def _on_patient_combo_selected(self, idx: int):
        if idx < 0:
            return
        pid = self.patient_quick_combo.itemData(idx)
        if not pid:
            return
        for r in range(self.patients_table.rowCount()):
            it = self.patients_table.item(r, 0)
            if it and it.data(Qt.UserRole) == pid:
                self.patients_table.selectRow(r)
                name_it = self.patients_table.item(r, 1)
                self.selected_patient_lbl.setText(f"Selected Patient: {name_it.text()} ({it.text()})")
                break

    def _on_patient_table_selected(self):
        row = self.patients_table.currentRow()
        if row < 0:
            return
        it0 = self.patients_table.item(row, 0)
        it1 = self.patients_table.item(row, 1)
        if it0 and it1:
            self.selected_patient_lbl.setText(f"Selected Patient: {it1.text()} ({it0.text()})")

    def _get_selected_patient_id(self):
        row = self.patients_table.currentRow()
        if row >= 0:
            it0 = self.patients_table.item(row, 0)
            if it0:
                return it0.data(Qt.UserRole)
        idx = self.patient_quick_combo.currentIndex()
        if idx >= 0:
            return self.patient_quick_combo.itemData(idx)
        return None

    def create_new_test_order(self):
        pid = self._get_selected_patient_id()
        if not pid:
            QMessageBox.warning(self, "No Patient Selected", "Search and select a patient first.")
            return

        cur = self.db.conn.cursor()
        patient = cur.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
        if not patient:
            return

        assay_rows = cur.execute("SELECT * FROM assays").fetchall()
        assay_map = {r["code"].upper(): dict(r) for r in assay_rows}

        selected_codes = []
        extra_raw = self.extra_assays_edit.text().strip()
        if extra_raw:
            for token in extra_raw.split(","):
                code = token.strip().upper()
                if code in assay_map and code not in selected_codes:
                    selected_codes.append(code)
        if not selected_codes:
            c_code = self.assay_select_combo.currentData()
            if c_code and c_code.upper() in assay_map:
                selected_codes.append(c_code.upper())

        if not selected_codes:
            QMessageBox.warning(self, "No Valid Assay", "Please choose a valid assay to order.")
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_no = f"ORD-{int(datetime.now().strftime('%H%M%S'))}{rng_suffix()}"
        phys = self.order_phys_combo.currentText()
        prio = self.order_prio_combo.currentText()

        cur.execute(
            """
            INSERT INTO lab_orders (order_no, patient_id, physician, priority, specimen_status, clinical_notes, created_at, collected_at)
            VALUES (?, ?, ?, ?, 'Pending', 'Ordered via searchable Patient Registry', ?, '')
            """,
            (order_no, pid, phys, prio, now_str),
        )
        order_id = cur.lastrowid

        sex = patient["sex"]
        for code in selected_codes:
            a_info = assay_map[code]
            low_v = a_info["ref_min_m"] if sex == "Male" else a_info["ref_min_f"]
            high_v = a_info["ref_max_m"] if sex == "Male" else a_info["ref_max_f"]
            dec = int(a_info["decimals"])
            mid_val = round((low_v + high_v) / 2.0, dec)
            val_str = f"{mid_val:.{dec}f}"
            flg = LISDatabase.compute_flag(mid_val, low_v, high_v)
            cur.execute(
                """
                INSERT INTO order_tests (order_id, assay_code, specimen_status, result_value, flag, test_status, verified_by, verified_at, updated_at)
                VALUES (?, ?, 'Pending', ?, ?, 'Pending', '', '', ?)
                """,
                (order_id, code, val_str, flg, now_str),
            )

        self.db.conn.commit()
        self.db.log_audit(
            self.user_info["name"],
            self.user_info["role"],
            "CREATE_ORDER",
            f"Created order {order_no} for {patient['full_name']} with assays: {', '.join(selected_codes)}.",
        )
        self.extra_assays_edit.clear()
        self.refresh_patients_view(filter_query=self.patient_search_input.text().strip().lower())
        self.refresh_worklist_view()
        self.status_pulse.trigger_status(f"Ordered: {order_no}")
        self.status_bar.showMessage(f"Created order {order_no} for {patient['full_name']} ({', '.join(selected_codes)}).")

    def refresh_patients_view(self, filter_query: str = ""):
        cur = self.db.conn.cursor()
        patients = cur.execute("SELECT * FROM patients ORDER BY id ASC").fetchall()

        if self.assay_select_combo.count() == 0:
            assays = cur.execute("SELECT code, name FROM assays ORDER BY code ASC").fetchall()
            for a in assays:
                self.assay_select_combo.addItem(f"{a['code']} — {a['name']}", a["code"])

        prev_pid = self.patient_quick_combo.currentData()
        self.patient_quick_combo.blockSignals(True)
        self.patient_quick_combo.clear()

        self.patients_table.setRowCount(0)
        for p in patients:
            ord_cnt = cur.execute("SELECT COUNT(*) AS c FROM lab_orders WHERE patient_id = ?", (p["id"],)).fetchone()["c"]
            hay = f"{p['mrn']} {p['full_name']} {p['dob']} {p['sex']}".lower()
            if filter_query and filter_query not in hay:
                continue

            self.patient_quick_combo.addItem(f"{p['full_name']} ({p['mrn']})", p["id"])

            r = self.patients_table.rowCount()
            self.patients_table.insertRow(r)
            it_mrn = QTableWidgetItem(p["mrn"])
            it_mrn.setData(Qt.UserRole, p["id"])
            self.patients_table.setItem(r, 0, it_mrn)
            self.patients_table.setItem(r, 1, QTableWidgetItem(p["full_name"]))
            self.patients_table.setItem(r, 2, QTableWidgetItem(p["sex"]))
            self.patients_table.setItem(r, 3, QTableWidgetItem(p["dob"]))
            self.patients_table.setItem(r, 4, QTableWidgetItem(p["contact"]))
            self.patients_table.setItem(r, 5, QTableWidgetItem(str(ord_cnt)))

        if prev_pid:
            for i in range(self.patient_quick_combo.count()):
                if self.patient_quick_combo.itemData(i) == prev_pid:
                    self.patient_quick_combo.setCurrentIndex(i)
                    break
        self.patient_quick_combo.blockSignals(False)

    # --------------------------------------------------------------------------
    # TAB 3: SCROLLABLE & ZOOMABLE QC TAB
    # --------------------------------------------------------------------------
    def _build_qc_tab(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(6, 6, 6, 6)

        self.qc_page_scroll = QScrollArea()
        self.qc_page_scroll.setWidgetResizable(True)
        self.qc_page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.qc_page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        qc_inner = QWidget()
        lay = QVBoxLayout(qc_inner)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("QC Assay:"))
        self.qc_assay_combo = QComboBox()
        self.qc_assay_combo.addItems(["WBC", "HGB", "FBS", "CREA", "PLT", "CHOL"])
        self.qc_assay_combo.currentTextChanged.connect(self.refresh_qc_view)
        top_row.addWidget(self.qc_assay_combo)

        top_row.addWidget(QLabel("Measured Value:"))
        self.qc_val_spin = QDoubleSpinBox()
        self.qc_val_spin.setRange(0.0, 2000.0)
        self.qc_val_spin.setDecimals(2)
        self.qc_val_spin.setValue(6.80)
        top_row.addWidget(self.qc_val_spin)

        top_row.addWidget(QLabel("Target Mean:"))
        self.qc_mean_spin = QDoubleSpinBox()
        self.qc_mean_spin.setRange(0.0, 2000.0)
        self.qc_mean_spin.setDecimals(2)
        self.qc_mean_spin.setValue(6.80)
        top_row.addWidget(self.qc_mean_spin)

        top_row.addWidget(QLabel("SD:"))
        self.qc_sd_spin = QDoubleSpinBox()
        self.qc_sd_spin.setRange(0.01, 500.0)
        self.qc_sd_spin.setDecimals(2)
        self.qc_sd_spin.setValue(0.25)
        top_row.addWidget(self.qc_sd_spin)

        btn_log_qc = QPushButton("Log QC Run")
        btn_log_qc.setProperty("accent", True)
        btn_log_qc.clicked.connect(self.log_qc_run)
        top_row.addWidget(btn_log_qc)
        top_row.addStretch()
        lay.addLayout(top_row)

        self.qc_chart = ZoomableQCChartWidget(THEMES[self.theme_mode])
        self.qc_chart.setMinimumHeight(440)
        lay.addWidget(self.qc_chart)

        self.qc_table = QTableWidget(0, 6)
        self.qc_table.setHorizontalHeaderLabels(["Run Date", "Assay", "Lot #", "Measured", "Mean / SD", "Westgard"])
        self.qc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.qc_table.setAlternatingRowColors(True)
        self.qc_table.setMinimumHeight(210)
        lay.addWidget(self.qc_table)

        self.qc_page_scroll.setWidget(qc_inner)
        outer.addWidget(self.qc_page_scroll)
        self.tabs.addTab(tab, "Quality Control (QC)")

    def log_qc_run(self):
        code = self.qc_assay_combo.currentText()
        meas = float(self.qc_val_spin.value())
        mean = float(self.qc_mean_spin.value())
        sd = float(self.qc_sd_spin.value())
        flag = LISDatabase.evaluate_westgard(meas, mean, sd)
        run_dt = datetime.now().strftime("%Y-%m-%d %H:%M")

        self.db.conn.execute(
            """
            INSERT INTO qc_runs (assay_code, lot_no, level_name, measured_value, target_mean, sd_value, run_date, operator_name, westgard_flag)
            VALUES (?, ?, 'Level 1 Control', ?, ?, ?, ?, ?, ?)
            """,
            (code, f"LOT-{code}-2026", meas, mean, sd, run_dt, self.user_info["name"], flag),
        )
        self.db.conn.commit()
        self.db.log_audit(self.user_info["name"], self.user_info["role"], "LOG_QC", f"{code} value={meas} ({flag})")
        self.refresh_qc_view()
        self.status_bar.showMessage(f"Logged {code} QC run ({meas}) — {flag}.")

    def refresh_qc_view(self):
        code = self.qc_assay_combo.currentText()
        cur = self.db.conn.cursor()
        assay_row = cur.execute("SELECT unit FROM assays WHERE code = ?", (code,)).fetchone()
        unit = assay_row["unit"] if assay_row else ""
        runs = cur.execute(
            "SELECT * FROM qc_runs WHERE assay_code = ? ORDER BY id ASC",
            (code,),
        ).fetchall()
        runs_list = [dict(r) for r in runs]
        self.qc_chart.plot_runs(code, unit, runs_list)

        self.qc_table.setRowCount(0)
        for r in reversed(runs_list):
            row_i = self.qc_table.rowCount()
            self.qc_table.insertRow(row_i)
            self.qc_table.setItem(row_i, 0, QTableWidgetItem(r["run_date"]))
            self.qc_table.setItem(row_i, 1, QTableWidgetItem(r["assay_code"]))
            self.qc_table.setItem(row_i, 2, QTableWidgetItem(r["lot_no"]))
            self.qc_table.setItem(row_i, 3, QTableWidgetItem(f"{r['measured_value']:.2f} {unit}"))
            self.qc_table.setItem(row_i, 4, QTableWidgetItem(f"{r['target_mean']:.2f} / {r['sd_value']:.2f}"))
            self.qc_table.setItem(row_i, 5, QTableWidgetItem(r["westgard_flag"]))

    # --------------------------------------------------------------------------
    # TAB 4: ADMIN MODE SAMPLE QUEUE & AUDIT LOGS
    # --------------------------------------------------------------------------
    def _build_admin_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        adm_top = QHBoxLayout()
        self.admin_status_lbl = QLabel("Admin Mode is OFF — toggle 'Admin Mode' in top bar to manage pending sample test queues.")
        self.admin_status_lbl.setStyleSheet("font-weight: 700;")
        adm_top.addWidget(self.admin_status_lbl)

        btn_add_pending_samples = QPushButton("Add More Pending Sample Tests")
        btn_add_pending_samples.setProperty("accent", True)
        btn_add_pending_samples.clicked.connect(self.add_more_pending_samples_admin)
        adm_top.addWidget(btn_add_pending_samples)

        lay.addLayout(adm_top)

        self.admin_pending_table = QTableWidget(0, 6)
        self.admin_pending_table.setHorizontalHeaderLabels([
            "Order #", "Patient Name", "Physician", "Specimen", "Pending Tests", "Action"
        ])
        self.admin_pending_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_pending_table.setAlternatingRowColors(True)
        lay.addWidget(self.admin_pending_table, stretch=1)

        self.audit_table = QTableWidget(0, 4)
        self.audit_table.setHorizontalHeaderLabels(["Timestamp", "Actor", "Action", "Details"])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.setAlternatingRowColors(True)
        lay.addWidget(self.audit_table, stretch=1)

        self.tabs.addTab(tab, "Admin")

    def add_more_pending_samples_admin(self):
        cur = self.db.conn.cursor()
        patients = cur.execute("SELECT * FROM patients ORDER BY id ASC").fetchall()
        if not patients:
            return

        assays = cur.execute("SELECT * FROM assays").fetchall()
        assay_map = {a["code"]: dict(a) for a in assays}
        pending_pool = ["WBC", "HGB", "HCT", "PLT", "FBS", "HBA1C", "CHOL", "TRIG", "HDL", "LDL", "CREA", "BUA", "ALT", "AST", "NA", "K", "CRP", "TSH"]

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        added_orders = 0
        added_tests = 0

        existing_cnt = cur.execute("SELECT COUNT(*) AS c FROM lab_orders").fetchone()["c"]
        for i in range(5):
            p = patients[(existing_cnt + i) % len(patients)]
            order_no = f"ORD-ADM-{existing_cnt + i + 1:04d}"
            phys = REQUESTING_PHYSICIANS[(existing_cnt + i) % len(REQUESTING_PHYSICIANS)]
            cur.execute(
                """
                INSERT INTO lab_orders (order_no, patient_id, physician, priority, specimen_status, clinical_notes, created_at, collected_at)
                VALUES (?, ?, ?, 'Routine', 'Pending', 'Admin sample pending batch', ?, '')
                """,
                (order_no, p["id"], phys, now_str),
            )
            oid = cur.lastrowid
            added_orders += 1

            chosen = pending_pool[(i * 3) % len(pending_pool) : (i * 3) % len(pending_pool) + 6]
            if len(chosen) < 4:
                chosen = pending_pool[:5]

            sex = p["sex"]
            for code in chosen:
                a_info = assay_map[code]
                low_v = a_info["ref_min_m"] if sex == "Male" else a_info["ref_min_f"]
                high_v = a_info["ref_max_m"] if sex == "Male" else a_info["ref_max_f"]
                dec = int(a_info["decimals"])
                mid_val = round((low_v + high_v) / 2.0, dec)
                val_str = f"{mid_val:.{dec}f}"
                flg = LISDatabase.compute_flag(mid_val, low_v, high_v)
                cur.execute(
                    """
                    INSERT INTO order_tests (order_id, assay_code, specimen_status, result_value, flag, test_status, verified_by, verified_at, updated_at)
                    VALUES (?, ?, 'Pending', ?, ?, 'Pending', '', '', ?)
                    """,
                    (oid, code, val_str, flg, now_str),
                )
                added_tests += 1

        self.db.conn.commit()
        self.db.log_audit(
            self.user_info["name"],
            self.user_info["role"],
            "ADMIN_ADD_PENDING",
            f"Added {added_orders} pending sample orders ({added_tests} pending tests).",
        )
        self.refresh_admin_view()
        self.refresh_worklist_view()
        self.status_pulse.trigger_status(f"+{added_orders} Pending Orders")
        self.status_bar.showMessage(f"Added {added_orders} pending sample orders ({added_tests} pending tests).")

    def refresh_admin_view(self):
        cur = self.db.conn.cursor()
        self.admin_pending_table.setRowCount(0)

        if self.admin_mode:
            self.admin_status_lbl.setText("Admin Mode is ON — Active Pending Sample Orders Queue:")
            orders = cur.execute("""
                SELECT o.*, p.full_name
                FROM lab_orders o
                JOIN patients p ON o.patient_id = p.id
                ORDER BY o.id DESC
            """).fetchall()
            for o in orders:
                p_tests = cur.execute(
                    "SELECT assay_code FROM order_tests WHERE order_id = ? AND test_status = 'Pending'",
                    (o["id"],),
                ).fetchall()
                if not p_tests:
                    continue
                codes = [t["assay_code"] for t in p_tests]
                r = self.admin_pending_table.rowCount()
                self.admin_pending_table.insertRow(r)
                self.admin_pending_table.setItem(r, 0, QTableWidgetItem(o["order_no"]))
                self.admin_pending_table.setItem(r, 1, QTableWidgetItem(o["full_name"]))
                self.admin_pending_table.setItem(r, 2, QTableWidgetItem(o["physician"]))
                self.admin_pending_table.setItem(r, 3, QTableWidgetItem(o["specimen_status"]))
                self.admin_pending_table.setItem(r, 4, QTableWidgetItem(", ".join(codes)))

                btn_open = QPushButton("Verify Results")
                oid_val = o["id"]
                btn_open.clicked.connect(lambda _chk=False, tid=oid_val: self.open_verify_results_for_selected(tid))
                self.admin_pending_table.setCellWidget(r, 5, btn_open)
        else:
            self.admin_status_lbl.setText("Admin Mode is OFF — enable Admin Mode in the top bar to view/add pending sample queues.")

        logs = cur.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 60").fetchall()
        self.audit_table.setRowCount(0)
        for lg in logs:
            r = self.audit_table.rowCount()
            self.audit_table.insertRow(r)
            self.audit_table.setItem(r, 0, QTableWidgetItem(lg["timestamp"]))
            self.audit_table.setItem(r, 1, QTableWidgetItem(lg["actor"]))
            self.audit_table.setItem(r, 2, QTableWidgetItem(lg["action"]))
            self.audit_table.setItem(r, 3, QTableWidgetItem(lg["details"]))

    def refresh_all_views(self):
        self.refresh_worklist_view()
        self.refresh_patients_view(filter_query=self.patient_search_input.text().strip().lower())
        self.refresh_qc_view()
        self.refresh_admin_view()


_COUNTER = 0


def rng_suffix() -> str:
    global _COUNTER
    _COUNTER = (_COUNTER + 1) % 1000
    return f"{_COUNTER:03d}"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    default_theme = "light"
    db = LISDatabase(DB_FILENAME)

    login_dlg = PinLoginDialog(theme_mode=default_theme)
    if login_dlg.exec() != QDialog.Accepted or not login_dlg.authenticated_user:
        sys.exit(0)

    win = MonocytesLISWindow(
        db=db,
        user_info=login_dlg.authenticated_user,
        initial_theme=login_dlg.theme_mode,
    )
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# ==============================================================================
# ASSAY REFERENCE CATALOG & DIAGNOSTIC HELPERS
# ==============================================================================
def format_reference_interval(assay_row: dict, sex: str) -> str:
    low = assay_row.get("ref_min_m", 0.0) if sex == "Male" else assay_row.get("ref_min_f", 0.0)
    high = assay_row.get("ref_max_m", 100.0) if sex == "Male" else assay_row.get("ref_max_f", 100.0)
    dec = int(assay_row.get("decimals", 1))
    unit = assay_row.get("unit", "")
    return f"{low:.{dec}f} – {high:.{dec}f} {unit}".strip()


def classify_result_severity(value_str: str, low: float, high: float) -> str:
    try:
        v = float(str(value_str).strip())
    except (ValueError, TypeError):
        return "Pending Entry"
    span = max(1e-6, high - low)
    if v < low - 0.35 * span:
        return "Critical Low"
    if v < low:
        return "Low"
    if v > high + 0.35 * span:
        return "Critical High"
    if v > high:
        return "High"
    return "Normal"


def summarize_order_counts(test_rows: list) -> dict:
    total = len(test_rows)
    verified = sum(1 for r in test_rows if r.get("test_status") == "Verified")
    pending = sum(1 for r in test_rows if r.get("test_status") != "Verified")
    flagged = sum(1 for r in test_rows if r.get("flag") in ("L", "H"))
    return {
        "total": total,
        "verified": verified,
        "pending": pending,
        "flagged": flagged,
    }
