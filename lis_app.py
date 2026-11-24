import sys
import os
import re
import csv
import json
import random
import shutil
import sqlite3
import hashlib
from datetime import datetime, date, timedelta

if sys.platform == "win32":
    import ctypes

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import (
    Qt, QTimer, QRectF, QPointF, QEasingCurve,
    QVariantAnimation, Signal, QEvent
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QLinearGradient,
    QFont, QKeySequence, QShortcut, QBrush
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QTabWidget, QSplitter, QFrame, QScrollArea, QStackedWidget,
    QDialog, QMessageBox, QFileDialog, QCheckBox, QAbstractItemView,
    QGraphicsDropShadowEffect, QSizePolicy
)
from fpdf import FPDF

APP_TITLE = "Monocytes Delegates LIS"
DEFAULT_DB_NAME = "monocytes_delegates_lis_v4.db"
CONFIG_FILE = "lis_config.json"
ADMIN_MODE_PIN = "0000"

CURRENT_THEME = "light"

SAMPLE_PATIENT_NAMES = [
    "Andrea Rei G. Naria",
    "Angela Lyka Z. Go Hee",
    "Antherese C. Palacios",
    "Arianne Jhanne V. Cardinal",
    "Avegail L. Gayoso",
    "Christian Vien V. Napiza",
    "Christine Joy Chan",
    "Christine Mae S. Tramado",
    "Eloisa T. Lanaria",
    "Jasmine Cyrile B. Alave",
    "Jasmine S. Mahilum",
    "Jen Kaye Marie B. Bogtae",
    "Jhelaicka Masheil D. Hermitaño",
    "Josef Raphael S. Tiongson",
    "Justin Jake P. Vargas",
    "Rizza May S. Cambronero",
    "Samantha Angel Sotto",
    "Shaira Lois C. Guardiana",
    "Shane Louisse B. Padrones",
    "Shane Rose L. Jordan",
    "Sherdounie A. Boboli",
    "Sofiah R. Canto",
    "Tashana C. Gallego",
    "Vincess Rem C. Abong",
    "Zacci Nicole S. Sarmiento",
]

SAMPLE_PHYSICIANS = [
    "Dr. Shaun Bautista",
    "Dr. Ramelin David",
    "Dr. Raan Feril",
    "Dr. Marinelle Garcia",
]

MALE_SAMPLE_PATIENTS = {
    "Christian Vien V. Napiza",
    "Josef Raphael S. Tiongson",
    "Justin Jake P. Vargas",
}


def load_config() -> dict:
    cfg = {"db_path": DEFAULT_DB_NAME, "theme": "light"}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    if cfg.get("theme") not in ("light", "dark"):
        cfg["theme"] = "light"
    return cfg


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


APP_CONFIG = load_config()
CURRENT_THEME = APP_CONFIG.get("theme", "light")

INITIAL_STAFF = [
    ("0001", "Carlyle Dioleste, RMT", "Medical Technologist (RMT)", "PRC-0098412", ""),
    ("0002", "Ariech Legaspi, RMT", "Medical Technologist (RMT)", "PRC-0098413", ""),
    ("0003", "Melody Bajande, RMT", "Medical Technologist (RMT)", "PRC-0098414", ""),
    ("0004", "Christine Patani-e, RMT", "Medical Technologist (RMT)", "PRC-0098415", ""),
    ("0005", "Chauncy Melvida, RMT", "Medical Technologist (RMT)", "PRC-0098416", ""),
    ("0006", "Elaijeen Cordova, RMT", "Medical Technologist (RMT)", "PRC-0098417", ""),
    ("0007", "Dianne Pastor, RMT", "Medical Technologist (RMT)", "PRC-0098418", ""),
    ("0008", "Michael Malabago, RMT", "Medical Technologist (RMT)", "PRC-0098419", ""),
    ("0009", "Nielmarc Pontioso, RMT", "Medical Technologist (RMT)", "PRC-0098420", ""),
    ("0010", "Princess Aguilo, RMT", "Medical Technologist (RMT)", "PRC-0098421", ""),
    ("0011", "Keturah Totisano, RMT", "Medical Technologist (RMT)", "PRC-0098422", ""),
    ("0012", "Arthur Mana-ay, RMT", "Medical Technologist (RMT)", "PRC-0098423", ""),
    ("1111", "Gaia Aubrey Manalo, MD", "Pathologist", "PRC-0142890", ""),
]

DEFAULT_TESTS = [
    ("White Blood Cell Count (WBC)", "Hematology", "x10^9/L", 4.5, 11.0, 2.0, 30.0, 35.0, "Lavender (EDTA)", "4.5 - 11.0"),
    ("Red Blood Cell Count (RBC)", "Hematology", "x10^12/L", 4.2, 5.9, 2.5, 7.5, 20.0, "Lavender (EDTA)", "4.2 - 5.9"),
    ("Hemoglobin (Hgb)", "Hematology", "g/dL", 12.0, 17.5, 7.0, 20.0, 20.0, "Lavender (EDTA)", "12.0 - 17.5"),
    ("Hematocrit (Hct)", "Hematology", "%", 36.0, 50.0, 21.0, 60.0, 20.0, "Lavender (EDTA)", "36.0 - 50.0"),
    ("MCV", "Hematology", "fL", 80.0, 100.0, 60.0, 120.0, 15.0, "Lavender (EDTA)", "80.0 - 100.0"),
    ("MCH", "Hematology", "pg", 27.0, 33.0, 18.0, 42.0, 15.0, "Lavender (EDTA)", "27.0 - 33.0"),
    ("MCHC", "Hematology", "g/dL", 32.0, 36.0, 26.0, 40.0, 15.0, "Lavender (EDTA)", "32.0 - 36.0"),
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
    ("LDL Cholesterol (Calc)", "Clinical Chemistry", "mg/dL", 0.0, 100.0, None, 250.0, 30.0, "Gold (SST)", "< 100"),
    ("Troponin I (hs-cTnI)", "Immunology", "ng/mL", 0.0, 0.04, None, 0.40, 50.0, "Gold (SST)", "< 0.04"),
    ("Dengue NS1 Antigen", "Serology", "Qualitative", None, None, None, None, 0.0, "Gold (SST)", "Non-Reactive"),
    ("Urinalysis (Complete)", "Clinical Microscopy", "Profile", None, None, None, None, 0.0, "Sterile Urine Cup", "Yellow / Clear / Neg"),
    ("Fecalysis (Routine)", "Clinical Microscopy", "Profile", None, None, None, None, 0.0, "Sterile Container", "Brown / Formed / NOPS"),
    ("Culture & Sensitivity (C&S)", "Microbiology", "Antibiogram", None, None, None, None, 0.0, "Sterile Container", "No Growth"),
]

DEFAULT_DEMOGRAPHIC_RANGES = [
    ("Hemoglobin (Hgb)", "Male", 15.0, 150.0, 13.5, 17.5, 7.0, 20.0, "13.5 - 17.5 (Adult M)"),
    ("Hemoglobin (Hgb)", "Female", 15.0, 150.0, 12.0, 15.5, 7.0, 20.0, "12.0 - 15.5 (Adult F)"),
    ("Hemoglobin (Hgb)", "All", 0.0, 14.99, 11.0, 14.5, 7.0, 19.0, "11.0 - 14.5 (Peds)"),
    ("Hematocrit (Hct)", "Male", 15.0, 150.0, 41.0, 50.0, 21.0, 60.0, "41.0 - 50.0 (Adult M)"),
    ("Hematocrit (Hct)", "Female", 15.0, 150.0, 36.0, 44.0, 21.0, 60.0, "36.0 - 44.0 (Adult F)"),
    ("Red Blood Cell Count (RBC)", "Male", 15.0, 150.0, 4.5, 5.9, 2.5, 7.5, "4.5 - 5.9 (Adult M)"),
    ("Red Blood Cell Count (RBC)", "Female", 15.0, 150.0, 4.1, 5.1, 2.5, 7.5, "4.1 - 5.1 (Adult F)"),
    ("Creatinine", "Male", 15.0, 150.0, 0.7, 1.3, None, 5.0, "0.7 - 1.3 (Adult M)"),
    ("Creatinine", "Female", 15.0, 150.0, 0.6, 1.1, None, 5.0, "0.6 - 1.1 (Adult F)"),
    ("Creatinine", "All", 0.0, 14.99, 0.3, 0.7, None, 3.5, "0.3 - 0.7 (Peds)"),
    ("White Blood Cell Count (WBC)", "All", 0.0, 14.99, 5.0, 14.5, 2.0, 35.0, "5.0 - 14.5 (Peds)"),
]

PRESET_PANELS = {
    "Full CBC + Indices": [
        "White Blood Cell Count (WBC)", "Red Blood Cell Count (RBC)",
        "Hemoglobin (Hgb)", "Hematocrit (Hct)", "MCV", "MCH", "MCHC",
        "Platelet Count (PLT)"
    ],
    "Basic Metabolic (BMP)": [
        "Fasting Blood Glucose (FBS)", "Blood Urea Nitrogen (BUN)",
        "Creatinine", "Sodium (Na+)", "Potassium (K+)", "Total Calcium"
    ],
    "Hepatic Function": [
        "ALT (SGPT)", "AST (SGOT)", "Albumin"
    ],
    "Lipid Profile": [
        "Total Cholesterol", "Triglycerides", "HDL Cholesterol", "LDL Cholesterol (Calc)"
    ],
    "Coagulation Panel": [
        "Prothrombin Time (PT)", "INR", "Activated Partial Thromboplastin Time (aPTT)"
    ],
    "Clinical Microscopy": [
        "Urinalysis (Complete)", "Fecalysis (Routine)"
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
    "Amoxicillin-Clavulanate", "Ceftriaxone", "Cefuroxime", "Ciprofloxacin",
    "Levofloxacin", "Gentamicin", "Amikacin", "Meropenem",
    "Piperacillin-Tazobactam", "Trimethoprim-Sulfamethoxazole", "Nitrofurantoin", "Vancomycin",
]

ORGANISMS_LIST = [
    "Escherichia coli", "Klebsiella pneumoniae", "Staphylococcus aureus (MSSA)",
    "Staphylococcus aureus (MRSA)", "Pseudomonas aeruginosa", "Enterococcus faecalis",
    "Proteus mirabilis", "Salmonella enterica", "No Pathogen Isolated / Normal Flora",
]

TUBE_COLORS = {
    "Lavender (EDTA)": ("#A855F7", "#F3E8FF"),
    "Gold (SST)": ("#EAB308", "#FEF9C3"),
    "Light Blue (Citrate)": ("#38BDF8", "#E0F2FE"),
    "Green (Heparin)": ("#10B981", "#D1FAE5"),
    "Sterile Urine Cup": ("#F97316", "#FFEDD5"),
    "Sterile Container": ("#F43F5E", "#FFE4E6"),
}

THEMES = {
    "dark": {
        "bg": "#080C15",
        "surface": "#0E1424",
        "subpanel": "#121A2E",
        "topbar": "#0B101D",
        "input_bg": "#090E1A",
        "input_focus": "#0C1424",
        "border": "#1E293B",
        "border_strong": "#334155",
        "text": "#E2E8F0",
        "text_bright": "#F8FAFC",
        "muted": "#94A3B8",
        "btn_bg": "#162033",
        "btn_hover": "#1E2B44",
        "tab_bg": "#0B101D",
        "tab_sel": "#121B2E",
        "table_alt": "#0C1322",
        "group_row": "#10192D",
        "accent": "#38BDF8",
        "primary": "#0284C7",
        "success": "#059669",
        "danger": "#BE123C",
        "chart_fig": "#090E1A",
        "chart_ax": "#0E1424",
        "chart_grid": "#1E293B",
    },
    "light": {
        "bg": "#F1F5F9",
        "surface": "#FFFFFF",
        "subpanel": "#F8FAFC",
        "topbar": "#FFFFFF",
        "input_bg": "#FFFFFF",
        "input_focus": "#F0F9FF",
        "border": "#CBD5E1",
        "border_strong": "#94A3B8",
        "text": "#1E293B",
        "text_bright": "#0F172A",
        "muted": "#475569",
        "btn_bg": "#E2E8F0",
        "btn_hover": "#CBD5E1",
        "tab_bg": "#E2E8F0",
        "tab_sel": "#FFFFFF",
        "table_alt": "#F8FAFC",
        "group_row": "#E0F2FE",
        "accent": "#0284C7",
        "primary": "#0284C7",
        "success": "#059669",
        "danger": "#E11D48",
        "chart_fig": "#FFFFFF",
        "chart_ax": "#F8FAFC",
        "chart_grid": "#CBD5E1",
    }
}


def build_qss(theme_name: str = "light") -> str:
    t = THEMES.get(theme_name, THEMES["light"])
    return f"""
QMainWindow, QWidget#RootCanvas, QDialog, QMessageBox {{
    background-color: {t['bg']};
    color: {t['text']};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 10pt;
}}
QWidget {{
    color: {t['text']};
    font-family: "Segoe UI", "Inter", sans-serif;
}}
QMessageBox {{
    background-color: {t['surface']};
    border: 1px solid {t['border_strong']};
}}
QMessageBox QLabel {{
    color: {t['text_bright']};
    background-color: transparent;
    font-size: 10pt;
    padding: 4px;
}}
QMessageBox QPushButton {{
    min-width: 86px;
    padding: 7px 14px;
}}
QFrame#SurfaceCard {{
    background-color: {t['surface']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}
QFrame#SubPanel {{
    background-color: {t['subpanel']};
    border: 1px solid {t['border']};
    border-radius: 8px;
}}
QFrame#TopHeaderBar {{
    background-color: {t['topbar']};
    border-bottom: 1px solid {t['border']};
}}
QScrollArea {{
    background-color: transparent;
    border: none;
}}
QScrollArea#DarkScroll {{
    background-color: {t['input_bg']};
    border: 1px solid {t['border']};
    border-radius: 8px;
}}
QWidget#ScrollContent {{
    background-color: {t['input_bg']};
}}
QWidget#CardScrollContent {{
    background-color: {t['surface']};
}}
QLabel#SectionHeader {{
    font-size: 11pt;
    font-weight: 700;
    color: {t['text_bright']};
}}
QLabel#GroupTitle {{
    font-size: 8.5pt;
    font-weight: 700;
    color: {t['muted']};
    letter-spacing: 0.6px;
    padding-top: 4px;
}}
QLabel#FieldLabel {{
    color: {t['text']};
    font-size: 9pt;
    font-weight: 600;
}}
QLabel#MutedLabel {{
    color: {t['muted']};
    font-size: 9pt;
}}
QLabel#MonoBadge {{
    font-family: "Consolas", "JetBrains Mono", monospace;
    background-color: {t['subpanel']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    padding: 4px 10px;
    color: {t['text']};
    font-weight: 600;
}}
QLineEdit, QComboBox, QTextEdit, QPlainTextEdit {{
    background-color: {t['input_bg']};
    border: 1px solid {t['border_strong']};
    border-radius: 7px;
    padding: 7px 10px;
    color: {t['text_bright']};
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {t['accent']};
    background-color: {t['input_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {t['surface']};
    border: 1px solid {t['border_strong']};
    color: {t['text_bright']};
    selection-background-color: #1D4ED8;
    selection-color: #FFFFFF;
}}
QPushButton {{
    background-color: {t['btn_bg']};
    border: 1px solid {t['border_strong']};
    border-radius: 7px;
    padding: 7px 13px;
    color: {t['text_bright']};
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {t['btn_hover']};
    border-color: {t['accent']};
}}
QPushButton:pressed {{
    background-color: {t['subpanel']};
}}
QPushButton#PrimaryBtn {{
    background-color: {t['primary']};
    border: 1px solid #38BDF8;
    color: #FFFFFF;
}}
QPushButton#PrimaryBtn:hover {{
    background-color: #0369A1;
}}
QPushButton#SuccessBtn {{
    background-color: {t['success']};
    border: 1px solid #34D399;
    color: #FFFFFF;
}}
QPushButton#SuccessBtn:hover {{
    background-color: #047857;
}}
QPushButton#DangerBtn {{
    background-color: {t['danger']};
    border: 1px solid #FB7185;
    color: #FFFFFF;
}}
QPushButton#DangerBtn:hover {{
    background-color: #9F1239;
}}
QPushButton#AdminActiveBtn {{
    background-color: #1E3A8A;
    border: 1px solid #60A5FA;
    color: #DBEAFE;
}}
QPushButton#AdminActiveBtn:hover {{
    background-color: #1D4ED8;
}}
QPushButton#KeypadBtn {{
    background-color: {t['subpanel']};
    border: 1px solid {t['border_strong']};
    border-radius: 8px;
    font-family: "Consolas", monospace;
    font-size: 13pt;
    font-weight: 700;
    color: {t['text_bright']};
    min-height: 44px;
}}
QPushButton#KeypadBtn:hover {{
    background-color: {t['btn_hover']};
    border-color: {t['accent']};
    color: {t['accent']};
}}
QTabWidget::pane {{
    border: 1px solid {t['border']};
    border-radius: 9px;
    background-color: {t['bg']};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {t['tab_bg']};
    border: 1px solid {t['border']};
    border-bottom: none;
    border-top-left-radius: 7px;
    border-top-right-radius: 7px;
    padding: 9px 16px;
    margin-right: 4px;
    color: {t['muted']};
    font-weight: 600;
    font-size: 9.5pt;
}}
QTabBar::tab:selected {{
    background-color: {t['tab_sel']};
    border-color: {t['border_strong']};
    border-top: 2px solid {t['accent']};
    color: {t['text_bright']};
}}
QTabBar::tab:hover:!selected {{
    background-color: {t['surface']};
    color: {t['text_bright']};
}}
QTableWidget, QTreeWidget {{
    background-color: {t['input_bg']};
    alternate-background-color: {t['table_alt']};
    gridline-color: {t['border']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    selection-background-color: #1D4ED8;
    selection-color: #FFFFFF;
    outline: 0;
}}
QTableWidget::item, QTreeWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {t['border']};
}}
QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: #1D4ED8;
    color: #FFFFFF;
}}
QHeaderView::section {{
    background-color: {t['subpanel']};
    color: {t['muted']};
    font-weight: 700;
    font-size: 9pt;
    border: none;
    border-bottom: 1px solid {t['border_strong']};
    border-right: 1px solid {t['border']};
    padding: 7px 8px;
}}
QScrollBar:vertical {{
    background: {t['bg']};
    width: 11px;
}}
QScrollBar::handle:vertical {{
    background: {t['border_strong']};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['accent']};
}}
QScrollBar:horizontal {{
    background: {t['bg']};
    height: 11px;
}}
QScrollBar::handle:horizontal {{
    background: {t['border_strong']};
    border-radius: 5px;
    min-width: 24px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}
QCheckBox {{
    spacing: 10px;
    color: {t['text_bright']};
    background-color: transparent;
    font-size: 9.5pt;
}}
QCheckBox::indicator {{
    width: 17px;
    height: 17px;
    border-radius: 4px;
    border: 1px solid {t['border_strong']};
    background: {t['input_bg']};
}}
QCheckBox::indicator:checked {{
    background: {t['primary']};
    border-color: {t['accent']};
}}
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


def apply_window_titlebar_theme(widget: QWidget):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        val = ctypes.c_int(1 if CURRENT_THEME == "dark" else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val)
        )
    except Exception:
        pass


def _styled_msgbox(parent: QWidget, icon: QMessageBox.Icon, title: str, text: str, buttons=QMessageBox.Ok) -> QMessageBox:
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    box.setStyleSheet(build_qss(CURRENT_THEME))
    apply_window_titlebar_theme(box)
    return box


def show_info(parent: QWidget, title: str, text: str):
    _styled_msgbox(parent, QMessageBox.Information, title, text).exec()


def show_warn(parent: QWidget, title: str, text: str):
    _styled_msgbox(parent, QMessageBox.Warning, title, text).exec()


def show_error(parent: QWidget, title: str, text: str):
    _styled_msgbox(parent, QMessageBox.Critical, title, text).exec()


def ask_confirm(parent: QWidget, title: str, text: str) -> bool:
    res = _styled_msgbox(parent, QMessageBox.Question, title, text, QMessageBox.Yes | QMessageBox.No).exec()
    return res == QMessageBox.Yes


def get_db_path() -> str:
    return APP_CONFIG.get("db_path") or DEFAULT_DB_NAME


def get_conn():
    db_file = get_db_path()
    conn = sqlite3.connect(db_file, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=10000;")
    except Exception:
        pass
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
            role TEXT NOT NULL,
            prc_license TEXT,
            sig_path TEXT
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
        CREATE TABLE IF NOT EXISTS reference_ranges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            sex TEXT NOT NULL,
            min_age_years REAL NOT NULL,
            max_age_years REAL NOT NULL,
            low_val REAL,
            high_val REAL,
            crit_low REAL,
            crit_high REAL,
            ref_label TEXT,
            UNIQUE(test_name, sex, min_age_years, max_age_years)
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
            diff_json TEXT,
            microscopy_json TEXT
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

    _ensure_column(cur, "staff", "prc_license", "TEXT")
    _ensure_column(cur, "staff", "sig_path", "TEXT")
    _ensure_column(cur, "patients", "contact", "TEXT")

    order_upgrades = [
        ("collected_at", "TEXT"), ("verified_by", "TEXT"), ("verified_at", "TEXT"),
        ("amended_reason", "TEXT"), ("panic_notified_to", "TEXT"), ("delta_flag", "TEXT"),
        ("critical_flag", "INTEGER DEFAULT 0"), ("storage_slot", "TEXT"),
        ("pathologist_note", "TEXT"), ("pathologist_signed_by", "TEXT"),
        ("pathologist_signed_at", "TEXT"), ("antibiogram_json", "TEXT"),
        ("diff_json", "TEXT"), ("microscopy_json", "TEXT"), ("tube_type", "TEXT"),
        ("ref_range", "TEXT"), ("unit", "TEXT"),
    ]
    for col, col_def in order_upgrades:
        _ensure_column(cur, "orders", col, col_def)

    test_upgrades = [
        ("crit_low", "REAL"), ("crit_high", "REAL"), ("delta_pct", "REAL DEFAULT 30.0"),
        ("tube_type", "TEXT DEFAULT 'Gold (SST)'"), ("ref_range", "TEXT"),
    ]
    for col, col_def in test_upgrades:
        _ensure_column(cur, "tests", col, col_def)

    cur.execute("DELETE FROM staff WHERE pin IN ('1234', '9999') OR name LIKE '%Demo%'")

    for pin, name, role, prc, sig in INITIAL_STAFF:
        cur.execute(
            "INSERT OR IGNORE INTO staff (pin, name, role, prc_license, sig_path) VALUES (?, ?, ?, ?, ?)",
            (pin, name, role, prc, sig)
        )
        cur.execute(
            "UPDATE staff SET prc_license = COALESCE(NULLIF(prc_license, ''), ?) WHERE pin = ?",
            (prc, pin)
        )

    for t in DEFAULT_TESTS:
        cur.execute("""
            INSERT OR IGNORE INTO tests
            (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, t)

    for dr in DEFAULT_DEMOGRAPHIC_RANGES:
        cur.execute("""
            INSERT OR IGNORE INTO reference_ranges
            (test_name, sex, min_age_years, max_age_years, low_val, high_val, crit_low, crit_high, ref_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dr)

    for q in DEFAULT_QC_TARGETS:
        cur.execute("""
            INSERT OR IGNORE INTO qc_targets (label, test_name, level, target_mean, sd, unit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, q)

    conn.commit()
    conn.close()


def parse_age_years(dob_str: str) -> float:
    if not dob_str:
        return 30.0
    s = dob_str.strip().lower()
    m_ymd = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m_ymd:
        try:
            b = date(int(m_ymd.group(1)), int(m_ymd.group(2)), int(m_ymd.group(3)))
            days = (date.today() - b).days
            return max(0.0, days / 365.25)
        except Exception:
            return 30.0
    m_num = re.match(r"^(\d+(?:\.\d+)?)\s*([ymd]?)", s)
    if m_num:
        val = float(m_num.group(1))
        unit = m_num.group(2)
        if unit == "m":
            return val / 12.0
        if unit == "d":
            return val / 365.25
        return val
    return 30.0


def resolve_patient_interval(conn, test_name: str, sex: str, dob_str: str):
    base = conn.execute("SELECT * FROM tests WHERE test_name = ?", (test_name,)).fetchone()
    if not base:
        return (None, None, None, None, "-", 30.0)

    age_y = parse_age_years(dob_str)
    pt_sex = (sex or "All").strip()

    rule = conn.execute("""
        SELECT * FROM reference_ranges
        WHERE test_name = ?
          AND (sex = ? OR sex = 'All')
          AND ? >= min_age_years AND ? <= max_age_years
        ORDER BY CASE WHEN sex = ? THEN 0 ELSE 1 END, (max_age_years - min_age_years) ASC
        LIMIT 1
    """, (test_name, pt_sex, age_y, age_y, pt_sex)).fetchone()

    if rule:
        return (
            rule["low_val"], rule["high_val"],
            rule["crit_low"] if rule["crit_low"] is not None else base["crit_low"],
            rule["crit_high"] if rule["crit_high"] is not None else base["crit_high"],
            rule["ref_label"] or base["ref_range"],
            base["delta_pct"] or 30.0
        )

    return (
        base["low_val"], base["high_val"], base["crit_low"], base["crit_high"],
        base["ref_range"] or "-", base["delta_pct"] or 30.0
    )


def perform_daily_backup():
    db_file = get_db_path()
    if not os.path.exists(db_file):
        return
    try:
        os.makedirs("backups", exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d")
        dest = os.path.join("backups", f"mdl_auto_backup_{stamp}.db")
        shutil.copy2(db_file, dest)
        files = sorted(
            [os.path.join("backups", f) for f in os.listdir("backups") if f.endswith(".db")],
            key=os.path.getmtime, reverse=True
        )
        for old in files[14:]:
            os.remove(old)
    except Exception:
        pass


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


def _make_item(text: str, color_hex: str = None, align=None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setToolTip(text)
    if color_hex:
        item.setForeground(QColor(color_hex))
    if align is not None:
        item.setTextAlignment(align)
    return item


def _sample_dob_for_index(idx: int) -> str:
    """Deterministic birthday strictly between 2004-01-01 and 2006-12-31."""
    year = 2004 + (idx % 3)
    month = ((idx * 3) % 12) + 1
    day = ((idx * 5) % 27) + 1
    return f"{year:04d}-{month:02d}-{day:02d}"


def _sample_physician_for_index(idx: int) -> str:
    return SAMPLE_PHYSICIANS[idx % len(SAMPLE_PHYSICIANS)]


def _sample_sex_for_name(full_name: str) -> str:
    return "Male" if full_name in MALE_SAMPLE_PATIENTS else "Female"


def seed_sample_clinical_cases(operator_name: str) -> dict:
    """Seeds clinical cases with DOBs in 2004-2006, approved physicians, sex rules,
    at least one pending/verified test per sample patient, and extra pending/STAT admin orders."""
    conn = get_conn()
    cur = conn.cursor()
    now_dt = datetime.now()
    fmt = "%Y-%m-%d %H:%M:%S"

    seeded_specimens = set()

    def _get_or_create_patient(idx: int) -> int:
        full_name = SAMPLE_PATIENT_NAMES[idx]
        mrn = f"MONO-{1001 + idx:04d}"
        dob = _sample_dob_for_index(idx)
        sex = _sample_sex_for_name(full_name)
        physician = _sample_physician_for_index(idx)
        contact = f"0917-555-{1000 + idx:04d}"

        row = cur.execute("SELECT id FROM patients WHERE mrn = ?", (mrn,)).fetchone()
        if row:
            cur.execute(
                "UPDATE patients SET full_name=?, dob=?, sex=?, contact=?, physician=? WHERE id=?",
                (full_name, dob, sex, contact, physician, row["id"])
            )
            return row["id"]
        cur.execute(
            "INSERT INTO patients (mrn, full_name, dob, sex, contact, physician, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (mrn, full_name, dob, sex, contact, physician, (now_dt - timedelta(days=5)).strftime(fmt))
        )
        return cur.lastrowid

    def _insert_order(
        spec_id: str, pid: int, test_name: str, priority: str = "Routine",
        status: str = "Ordered", result_val: str = None, flag: str = None,
        notes: str = "", ordered_ago_min: int = 90, collected_ago_min=None,
        verified_ago_min=None, panic_notified: str = "", delta_flag: str = "",
        crit_flag: int = 0, slot: str = "Rack A1", path_note: str = "",
        path_signed_by: str = "", path_signed_ago_min=None,
        abg_json: str = None, diff_json: str = None, mic_json: str = None
    ):
        t_row = cur.execute("SELECT * FROM tests WHERE test_name = ?", (test_name,)).fetchone()
        p_row = cur.execute("SELECT sex, dob FROM patients WHERE id = ?", (pid,)).fetchone()
        _, _, _, _, ref_lbl, _ = resolve_patient_interval(conn, test_name, p_row["sex"], p_row["dob"])

        ord_at = (now_dt - timedelta(minutes=ordered_ago_min)).strftime(fmt)
        coll_at = (now_dt - timedelta(minutes=collected_ago_min)).strftime(fmt) if collected_ago_min is not None else None
        ver_at = (now_dt - timedelta(minutes=verified_ago_min)).strftime(fmt) if verified_ago_min is not None else None
        ps_at = (now_dt - timedelta(minutes=path_signed_ago_min)).strftime(fmt) if path_signed_ago_min is not None else None

        cur.execute("""
            INSERT INTO orders (
                specimen_id, patient_id, test_name, department, priority, status,
                result_value, flag, unit, ref_range, tube_type, notes,
                ordered_by, ordered_at, collected_at, verified_by, verified_at,
                panic_notified_to, delta_flag, critical_flag, storage_slot,
                pathologist_note, pathologist_signed_by, pathologist_signed_at,
                antibiogram_json, diff_json, microscopy_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            spec_id, pid, test_name, t_row["department"], priority, status,
            result_val, flag, t_row["unit"], ref_lbl, t_row["tube_type"], notes,
            operator_name, ord_at, coll_at,
            operator_name if ver_at else None, ver_at,
            panic_notified, delta_flag, crit_flag, slot,
            path_note, path_signed_by, ps_at,
            abg_json, diff_json, mic_json
        ))
        seeded_specimens.add(spec_id)

    # Register all 25 sample patients cleanly first
    pids = [_get_or_create_patient(i) for i in range(len(SAMPLE_PATIENT_NAMES))]

    # 1. Critical Value Read-Back Case (idx 0: Andrea Rei G. Naria — Female)
    _insert_order(
        "MDL-261125-9001", pids[0], "Potassium (K+)", priority="STAT", status="Verified",
        result_val="6.5", flag="CRITICAL HIGH",
        notes="Repeat run confirmed hyperkalemia; non-hemolyzed specimen.",
        ordered_ago_min=110, collected_ago_min=95, verified_ago_min=42,
        panic_notified="Dr. Shaun Bautista (ER) — Read-back verified",
        crit_flag=1, slot="Fridge A (2-8°C) (Rack 1 - Slot A2)"
    )

    # 2. Full CBC + PBS Smear Review (idx 1: Angela Lyka Z. Go Hee — Female)
    cbc_spec = "MDL-261125-9002"
    cbc_vals = [
        ("White Blood Cell Count (WBC)", "15.8", "HIGH", "Marked leukocytosis"),
        ("Red Blood Cell Count (RBC)", "3.65", "LOW", ""),
        ("Hemoglobin (Hgb)", "9.8", "LOW", "Moderate anemia"),
        ("Hematocrit (Hct)", "30.2", "LOW", ""),
        ("MCV", "82.7", "NORMAL", ""),
        ("MCH", "26.8", "LOW", ""),
        ("MCHC", "32.4", "NORMAL", ""),
        ("Platelet Count (PLT)", "118", "LOW", "Mild thrombocytopenia"),
    ]
    for t_nm, r_val, flg, n_txt in cbc_vals:
        _insert_order(
            cbc_spec, pids[1], t_nm, priority="Urgent", status="Verified",
            result_val=r_val, flag=flg, notes=n_txt,
            ordered_ago_min=180, collected_ago_min=165, verified_ago_min=75,
            slot="Hematology Rack 1 (Rack 1 - Slot B1)"
        )
    diff_payload = json.dumps({
        "counts": {"Neutrophils": 78, "Lymphocytes": 14, "Monocytes": 6, "Eosinophils": 1, "Basophils": 1, "nRBC": 2},
        "morphology": "Neutrophilic leukocytosis with toxic granulation (+2) and Dohle bodies; mild anisocytosis."
    })
    _insert_order(
        cbc_spec, pids[1], "Peripheral Blood Smear (PBS)", priority="Urgent", status="Verified",
        result_val="Neut:78% Lymph:14% Mono:6% Eos:1% Baso:1% nRBC:2/100", flag="ABNORMAL",
        notes="Neutrophilic leukocytosis with toxic granulation (+2) and Dohle bodies; mild anisocytosis.",
        ordered_ago_min=180, collected_ago_min=165, verified_ago_min=70,
        diff_json=diff_payload, slot="Hematology Rack 1 (Rack 1 - Slot B1)"
    )

    # 3. Dengue Workup with Serial Trend History (idx 2: Antherese C. Palacios — Female)
    _insert_order(
        "MDL-261122-3011", pids[2], "Platelet Count (PLT)", priority="Routine", status="Verified",
        result_val="142", flag="LOW", notes="Day 2 fever serial platelet check",
        ordered_ago_min=4320, collected_ago_min=4300, verified_ago_min=4240
    )
    _insert_order(
        "MDL-261123-4012", pids[2], "Platelet Count (PLT)", priority="Urgent", status="Verified",
        result_val="84", flag="LOW", notes="Day 3 fever serial platelet check",
        ordered_ago_min=2880, collected_ago_min=2860, verified_ago_min=2800
    )
    dengue_today_spec = "MDL-261125-9003"
    _insert_order(
        dengue_today_spec, pids[2], "Dengue NS1 Antigen", priority="STAT", status="Verified",
        result_val="REACTIVE", flag="ABNORMAL", notes="NS1 positive on Day 4 illness",
        ordered_ago_min=140, collected_ago_min=125, verified_ago_min=55,
        slot="Serology Rack 1 (Rack 1 - Slot C1)"
    )
    _insert_order(
        dengue_today_spec, pids[2], "Platelet Count (PLT)", priority="STAT", status="Verified",
        result_val="48", flag="LOW", notes="Downward serial trend; close monitoring",
        ordered_ago_min=140, collected_ago_min=125, verified_ago_min=50,
        delta_flag="43% shift vs prior (84)", slot="Hematology Rack 1 (Rack 1 - Slot B2)"
    )
    _insert_order(
        dengue_today_spec, pids[2], "Hematocrit (Hct)", priority="STAT", status="Verified",
        result_val="43.8", flag="NORMAL", notes="Serial Hct baseline",
        ordered_ago_min=140, collected_ago_min=125, verified_ago_min=50,
        slot="Hematology Rack 1 (Rack 1 - Slot B2)"
    )

    # 4. Culture & Antibiogram (idx 3: Arianne Jhanne V. Cardinal — Female)
    abg_payload = json.dumps({
        "organism": "Escherichia coli",
        "colony": "> 100,000 CFU/mL Pure Growth (Midstream Urine)",
        "panel": {
            "Amoxicillin-Clavulanate": "S (Susceptible)",
            "Ceftriaxone": "S (Susceptible)",
            "Ciprofloxacin": "R (Resistant)",
            "Nitrofurantoin": "S (Susceptible)",
            "Trimethoprim-Sulfamethoxazole": "R (Resistant)",
        }
    })
    _insert_order(
        "MDL-261125-9004", pids[3], "Culture & Sensitivity (C&S)", priority="Routine", status="Verified",
        result_val="Escherichia coli (5 Abx)", flag="ABNORMAL",
        notes="Extended beta-lactamase negative; susceptible to Nitrofurantoin & Ceftriaxone.",
        ordered_ago_min=1440, collected_ago_min=1420, verified_ago_min=95,
        abg_json=abg_payload, slot="Microbiology Incubator 1 (Slot M4)"
    )

    # 5. Urinalysis & Fecalysis Microscopy (idx 4: Avegail L. Gayoso — Female)
    ua_payload = json.dumps({
        "Color": "Dark Yellow", "Transparency": "Slightly Turbid", "Specific Gravity": "1.020",
        "Reaction (pH)": "6.0", "Protein (Albumin)": "Trace", "Glucose (Sugar)": "Negative",
        "Ketones": "Negative", "Blood / Hemoglobin": "Negative",
        "Bilirubin / Urobilinogen": "Negative / Normal", "Nitrite / Leukocyte Est.": "Nitrite Neg / LE Pos",
        "Pus Cells (WBC / hpf)": "10 - 20 /hpf", "Red Blood Cells (RBC / hpf)": "1 - 3 /hpf",
        "Epithelial Cells": "Few", "Bacteria": "Moderate", "Casts & Crystals": "None Seen"
    })
    fa_payload = json.dumps({
        "Color": "Brown", "Consistency": "Formed", "Mucus": "Absent", "Occult Blood": "Negative",
        "Pus Cells (WBC / hpf)": "0 - 1 /hpf", "Red Blood Cells (RBC / hpf)": "None Seen",
        "Fat Globules / Starch": "Few", "Ova & Parasites (NOPS)": "No Ova or Parasites Seen (NOPS)"
    })
    _insert_order(
        "MDL-261125-9005", pids[4], "Urinalysis (Complete)", priority="Routine", status="Verified",
        result_val="Dark Yellow / Slightly Turbid / WBC:10 - 20 /hpf", flag="ABNORMAL",
        notes="Moderate bacteria with pyuria; correlate clinically for UTI.",
        ordered_ago_min=210, collected_ago_min=195, verified_ago_min=85,
        mic_json=ua_payload, slot="Microscopy Bench 1 (Slot U1)"
    )
    _insert_order(
        "MDL-261125-9006", pids[4], "Fecalysis (Routine)", priority="Routine", status="Verified",
        result_val="Brown / Formed / No Ova or Parasites Seen (NOPS)", flag="NORMAL",
        notes="No ova, cysts, or trophozoites seen.",
        ordered_ago_min=210, collected_ago_min=195, verified_ago_min=80,
        mic_json=fa_payload, slot="Microscopy Bench 1 (Slot F1)"
    )

    # 6. Pending STAT & In-Process Orders (idx 5: Christian Vien V. Napiza — Male)
    _insert_order(
        "MDL-261125-9007", pids[5], "Troponin I (hs-cTnI)", priority="STAT", status="In-Process",
        notes="Pending analyzer result — STAT draw.",
        ordered_ago_min=48, collected_ago_min=36, slot="Chemistry Rack 2 (Rack 2 - Slot A1)"
    )
    _insert_order(
        "MDL-261125-9007", pids[5], "Fasting Blood Glucose (FBS)", priority="STAT", status="Ordered",
        notes="Pending phlebotomy/result entry.",
        ordered_ago_min=48, collected_ago_min=None, slot="Phlebotomy Tray 1"
    )

    # 7. Guarantee every single remaining patient (idx 6..24) has at least 1 Verified or Pending test,
    # plus extra pending/in-process/STAT samples for Admin testing
    pending_pool = [
        ("Fasting Blood Glucose (FBS)", "STAT", "Ordered", "Pending specimen collection & run"),
        ("White Blood Cell Count (WBC)", "Urgent", "In-Process", "Pending differential & verification"),
        ("Creatinine", "Routine", "Ordered", "Pending chemistry run"),
        ("Total Cholesterol", "Routine", "In-Process", "Pending lipid verification"),
        ("Prothrombin Time (PT)", "STAT", "Ordered", "Pending coagulation assay"),
        ("ALT (SGPT)", "Routine", "In-Process", "Pending hepatic panel verification"),
        ("Sodium (Na+)", "Urgent", "Ordered", "Pending electrolyte run"),
    ]
    verified_pool = [
        ("Hemoglobin (Hgb)", "14.1", "NORMAL", "Routine baseline"),
        ("Fasting Blood Glucose (FBS)", "86", "NORMAL", "Fasting verified"),
        ("Platelet Count (PLT)", "254", "NORMAL", "Adequate count"),
        ("Creatinine", "0.8", "NORMAL", "Within reference"),
        ("White Blood Cell Count (WBC)", "7.2", "NORMAL", "Normal WBC"),
        ("Total Cholesterol", "178", "NORMAL", "Desirable lipid level"),
    ]

    for idx in range(6, len(SAMPLE_PATIENT_NAMES)):
        pid = pids[idx]
        p_info = pending_pool[idx % len(pending_pool)]
        v_info = verified_pool[idx % len(verified_pool)]
        spec_pend = f"MDL-261125-91{idx:02d}"
        spec_ver = f"MDL-261125-92{idx:02d}"

        _insert_order(
            spec_pend, pid, p_info[0], priority=p_info[1], status=p_info[2],
            notes=p_info[3], ordered_ago_min=30 + idx * 5,
            collected_ago_min=15 + idx * 3 if p_info[2] == "In-Process" else None,
            slot=f"Bench Rack A{(idx % 4) + 1}"
        )
        # Alternate verified test so every patient has clear verified + pending coverage
        if idx % 2 == 0:
            _insert_order(
                spec_ver, pid, v_info[0], priority="Routine", status="Verified",
                result_val=v_info[1], flag=v_info[2], notes=v_info[3],
                ordered_ago_min=180 + idx * 4, collected_ago_min=160 + idx * 4, verified_ago_min=60 + idx * 2,
                slot=f"Archive Rack B{(idx % 3) + 1}"
            )

    # Extra pending/STAT orders on Justin Jake P. Vargas (idx 14) & Josef Raphael S. Tiongson (idx 13)
    _insert_order(
        "MDL-261125-9301", pids[13], "Platelet Count (PLT)", priority="STAT", status="In-Process",
        notes="Pending STAT platelet verification", ordered_ago_min=35, collected_ago_min=20,
        slot="Hematology Rack 1"
    )
    _insert_order(
        "MDL-261125-9302", pids[14], "Potassium (K+)", priority="STAT", status="Ordered",
        notes="Pending STAT electrolyte draw", ordered_ago_min=22, collected_ago_min=None,
        slot="Phlebotomy Tray 2"
    )

    # 8. 12 Days of Levey-Jennings QC Points (Hemoglobin Level 1: Mean=13.8, SD=0.35)
    qc_label = "Hemoglobin (Hgb) | Level 1 (Normal)"
    qc_mean = 13.8
    qc_sd = 0.35
    qc_offsets = [-0.15, 0.12, -0.22, 0.25, -0.08, 0.18, -0.30, 0.05, 0.28, -0.18, 0.10, -0.12]
    for day_idx, z_off in enumerate(qc_offsets):
        run_dt = (now_dt - timedelta(days=11 - day_idx, hours=2)).strftime(fmt)
        measured = round(qc_mean + z_off * qc_sd, 2)
        z_val = round((measured - qc_mean) / qc_sd, 2)
        w_stat = "FAIL (1-3s Violation)" if abs(z_val) > 3.0 else ("WARN (1-2s Warning)" if abs(z_val) > 2.0 else "PASS (In Control)")
        cur.execute("""
            INSERT INTO qc_logs (label, measured, z_score, westgard_status, operator, logged_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (qc_label, measured, z_val, w_stat, operator_name, run_dt))

    conn.commit()
    conn.close()
    log_audit(operator_name, "SAMPLE_CASES_SEEDED", "-", "Seeded 2004-2006 sample patients, approved MDs, sex rules, pending/verified tests & QC")
    return {
        "patients_total": len(SAMPLE_PATIENT_NAMES),
        "qc_points": len(qc_offsets),
        "specimens_seeded": len(seeded_specimens),
    }


# ==============================================================================
# CLINICAL VISUAL INDICATORS (REFERENCE RANGE GAUGE, COLLECTION TUBE, CHARTS)
# ==============================================================================

class VectorRangeGauge(QWidget):
    """Clinical reference interval gauge showing where a numeric result sits."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(72)
        self.norm_pos = 0.5
        self.flag_text = "AWAITING RESULT"
        self.flag_color = QColor("#64748B")
        self.low_lbl = "-"
        self.high_lbl = "-"

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(420)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.valueChanged.connect(self._on_step)

    def _on_step(self, v):
        self.norm_pos = float(v)
        self.update()

    def set_reading(self, val_str: str, low_val, high_val, crit_low, crit_high, flag: str, animate_from_center: bool = False):
        self.flag_text = flag or "PENDING"
        self.low_lbl = f"{low_val:g}" if low_val is not None else "-"
        self.high_lbl = f"{high_val:g}" if high_val is not None else "-"

        color_map = {
            "NORMAL": "#10B981",
            "LOW": "#F59E0B",
            "HIGH": "#F97316",
            "CRITICAL LOW": "#F43F5E",
            "CRITICAL HIGH": "#F43F5E",
            "ABNORMAL": "#F43F5E",
            "REJECTED": "#64748B",
            "CANCELLED": "#64748B",
        }
        self.flag_color = QColor(color_map.get(self.flag_text, "#0284C7"))

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

        start_pos = 0.5 if animate_from_center else self.norm_pos
        if abs(start_pos - target) < 0.01 and animate_from_center:
            start_pos = 0.12

        self.anim.stop()
        self.anim.setStartValue(start_pos)
        self.anim.setEndValue(target)
        self.anim.start()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w = self.width()
        is_dark = (CURRENT_THEME == "dark")

        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(self.flag_color)
        status_str = p.fontMetrics().elidedText(f"Status: {self.flag_text}", Qt.ElideRight, max(40, w - 6))
        p.drawText(QRectF(2, 2, w - 4, 20), Qt.AlignLeft | Qt.AlignVCenter, status_str)

        bar_x, bar_y = 10.0, 28.0
        bar_w, bar_h = max(40.0, w - 20.0), 12.0

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#1E293B" if is_dark else "#CBD5E1"))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 6, 6)

        p.setBrush(QColor(245, 158, 11, 150))
        p.drawRoundedRect(QRectF(bar_x, bar_y, bar_w * 0.26, bar_h), 6, 6)

        p.setBrush(QColor(244, 63, 94, 155))
        p.drawRoundedRect(QRectF(bar_x + bar_w * 0.74, bar_y, bar_w * 0.26, bar_h), 6, 6)

        p.setBrush(QColor(16, 185, 129, 210))
        p.drawRect(QRectF(bar_x + bar_w * 0.25, bar_y, bar_w * 0.50, bar_h))

        p.setFont(QFont("Consolas", 8))
        p.setPen(QColor("#94A3B8" if is_dark else "#475569"))
        x_lo = bar_x + bar_w * 0.25
        x_hi = bar_x + bar_w * 0.75
        p.drawLine(QPointF(x_lo, bar_y - 3), QPointF(x_lo, bar_y + bar_h + 3))
        p.drawLine(QPointF(x_hi, bar_y - 3), QPointF(x_hi, bar_y + bar_h + 3))

        lo_rect_x = max(0.0, x_lo - 42.0)
        hi_rect_x = min(max(0.0, w - 84.0), x_hi - 42.0)
        p.drawText(QRectF(lo_rect_x, bar_y + bar_h + 4, 84, 16), Qt.AlignCenter, self.low_lbl)
        p.drawText(QRectF(hi_rect_x, bar_y + bar_h + 4, 84, 16), Qt.AlignCenter, self.high_lbl)

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
        self.setToolTip(f"Collection Container: {self.tube_name}")
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        is_dark = (CURRENT_THEME == "dark")
        cap_hex, _ = TUBE_COLORS.get(self.tube_name, ("#38BDF8", "#E0F2FE"))
        cap_col = QColor(cap_hex)

        p.setPen(QPen(QColor("#64748B"), 1.2))
        p.setBrush(QColor("#1E293B" if is_dark else "#E2E8F0"))
        p.drawRoundedRect(QRectF(10, 8, 26, 12), 5, 5)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(225, 29, 72, 185))
        p.drawRoundedRect(QRectF(12, 10, 14, 8), 3, 3)

        p.setBrush(cap_col)
        p.drawRoundedRect(QRectF(2, 7, 9, 14), 2, 2)

        p.setPen(QColor("#CBD5E1" if is_dark else "#1E293B"))
        p.setFont(QFont("Segoe UI", 9, QFont.DemiBold))
        avail_w = max(40, self.width() - 48)
        txt = p.fontMetrics().elidedText(f"Container: {self.tube_name}", Qt.ElideRight, avail_w)
        p.drawText(QRectF(44, 3, avail_w, 24), Qt.AlignLeft | Qt.AlignVCenter, txt)


class MplCanvas(FigureCanvas):
    """Theme-aware Matplotlib canvas for QC Levey-Jennings and Patient Trends."""

    def __init__(self, width=5.5, height=3.4, dpi=100):
        t = THEMES[CURRENT_THEME]
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=t["chart_fig"])
        self.ax = self.fig.add_subplot(111)
        self._style_ax(self.ax)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _style_ax(self, ax):
        t = THEMES[CURRENT_THEME]
        self.fig.set_facecolor(t["chart_fig"])
        ax.set_facecolor(t["chart_ax"])
        ax.tick_params(colors=t["muted"], labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(t["border_strong"])
        ax.title.set_color(t["text_bright"])
        ax.xaxis.label.set_color(t["muted"])
        ax.yaxis.label.set_color(t["muted"])


# ==============================================================================
# ADMIN MODE PIN DIALOG
# ==============================================================================

class AdminPinDialog(QDialog):
    """Theme-aware PIN prompt for unlocking Admin Mode."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Mode Access")
        self.setFixedWidth(360)
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 20)
        lay.setSpacing(12)

        title = QLabel("Admin Mode Authentication")
        title.setObjectName("SectionHeader")
        lay.addWidget(title)

        desc = QLabel("Enter the 4-digit Admin PIN to access Reports, Staff Roster, Network Sync, and Audit Logs.")
        desc.setObjectName("MutedLabel")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        self.in_pin = QLineEdit()
        self.in_pin.setPlaceholderText("••••")
        self.in_pin.setEchoMode(QLineEdit.Password)
        self.in_pin.setMaxLength(4)
        self.in_pin.setAlignment(Qt.AlignCenter)
        self.in_pin.setStyleSheet("""
            QLineEdit {
                font-family: 'Consolas', monospace;
                font-size: 16pt;
                font-weight: 700;
                letter-spacing: 8px;
                padding: 10px;
            }
        """)
        self.in_pin.returnPressed.connect(self._check_pin)
        lay.addWidget(self.in_pin)

        self.lbl_err = QLabel("")
        self.lbl_err.setStyleSheet("color: #FB7185; font-size: 9pt; font-weight: 600;")
        self.lbl_err.setVisible(False)
        lay.addWidget(self.lbl_err)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Unlock Admin Mode")
        btn_ok.setObjectName("PrimaryBtn")
        btn_ok.clicked.connect(self._check_pin)
        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(btn_ok, 2)
        lay.addLayout(btn_row)

        self.in_pin.setFocus()

    def _check_pin(self):
        if self.in_pin.text().strip() == ADMIN_MODE_PIN:
            self.accept()
        else:
            self.lbl_err.setText("Incorrect Admin PIN.")
            self.lbl_err.setVisible(True)
            self.in_pin.clear()
            self.in_pin.setFocus()


# ==============================================================================
# AGE / SEX REFERENCE RANGE EDITOR DIALOG
# ==============================================================================

class ReferenceRangeEditorDialog(QDialog):
    """Editor for age- and sex-specific clinical reference intervals per assay."""

    def __init__(self, test_name: str, operator_name: str, parent=None):
        super().__init__(parent)
        self.test_name = test_name
        self.operator_name = operator_name
        self.editing_rule_id = None
        self.setWindowTitle(f"Age & Sex Reference Ranges — {test_name}")
        self.resize(840, 500)
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        hdr = QLabel(f"Demographic Reference Rules: {test_name}")
        hdr.setObjectName("SectionHeader")
        lay.addWidget(hdr)

        sub = QLabel("Configure age brackets (in years, e.g. 0 to 14.99 for pediatrics) and sex-specific limits.")
        sub.setObjectName("MutedLabel")
        lay.addWidget(sub)

        form_card = QFrame()
        form_card.setObjectName("SurfaceCard")
        fg = QGridLayout(form_card)
        fg.setContentsMargins(12, 10, 12, 10)
        fg.setSpacing(8)

        self.cmb_sex = QComboBox()
        self.cmb_sex.addItems(["Female", "Male", "All"])

        self.in_min_age = QLineEdit("0")
        self.in_min_age.setPlaceholderText("Min Age (yrs)")

        self.in_max_age = QLineEdit("150")
        self.in_max_age.setPlaceholderText("Max Age (yrs)")

        self.in_low = QLineEdit()
        self.in_low.setPlaceholderText("Low (e.g. 12.0)")

        self.in_high = QLineEdit()
        self.in_high.setPlaceholderText("High (e.g. 15.5)")

        self.in_crit_low = QLineEdit()
        self.in_crit_low.setPlaceholderText("Crit Low (opt)")

        self.in_crit_high = QLineEdit()
        self.in_crit_high.setPlaceholderText("Crit High (opt)")

        self.in_label = QLineEdit()
        self.in_label.setPlaceholderText("Display Label (e.g. 12.0 - 15.5 Adult F)")

        btn_save_rule = QPushButton("Save Rule")
        btn_save_rule.setObjectName("SuccessBtn")
        btn_save_rule.clicked.connect(self._save_rule)

        btn_new_rule = QPushButton("Clear Form")
        btn_new_rule.clicked.connect(self._clear_form)

        btn_del_rule = QPushButton("Delete Selected")
        btn_del_rule.setObjectName("DangerBtn")
        btn_del_rule.clicked.connect(self._delete_rule)

        fg.addWidget(QLabel("Sex:"), 0, 0)
        fg.addWidget(self.cmb_sex, 0, 1)
        fg.addWidget(QLabel("Min Age (yrs):"), 0, 2)
        fg.addWidget(self.in_min_age, 0, 3)
        fg.addWidget(QLabel("Max Age (yrs):"), 0, 4)
        fg.addWidget(self.in_max_age, 0, 5)

        fg.addWidget(QLabel("Low:"), 1, 0)
        fg.addWidget(self.in_low, 1, 1)
        fg.addWidget(QLabel("High:"), 1, 2)
        fg.addWidget(self.in_high, 1, 3)
        fg.addWidget(QLabel("Ref Label:"), 1, 4)
        fg.addWidget(self.in_label, 1, 5)

        fg.addWidget(QLabel("Crit Low:"), 2, 0)
        fg.addWidget(self.in_crit_low, 2, 1)
        fg.addWidget(QLabel("Crit High:"), 2, 2)
        fg.addWidget(self.in_crit_high, 2, 3)

        act_sub = QHBoxLayout()
        act_sub.addWidget(btn_save_rule)
        act_sub.addWidget(btn_new_rule)
        act_sub.addWidget(btn_del_rule)
        fg.addLayout(act_sub, 2, 4, 1, 2)

        lay.addWidget(form_card)

        self.tbl_rules = QTableWidget(0, 8)
        self.tbl_rules.setHorizontalHeaderLabels([
            "ID", "Sex", "Min Age", "Max Age", "Low", "High", "Crit Low / High", "Ref Label"
        ])
        self.tbl_rules.setColumnHidden(0, True)
        self.tbl_rules.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_rules.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_rules.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_rules.setAlternatingRowColors(True)
        self.tbl_rules.itemSelectionChanged.connect(self._on_row_select)
        lay.addWidget(self.tbl_rules, 1)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        lay.addWidget(btn_close, 0, Qt.AlignRight)

        self._load_rules()

    def _load_rules(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT * FROM reference_ranges
            WHERE test_name = ?
            ORDER BY sex ASC, min_age_years ASC
        """, (self.test_name,)).fetchall()
        conn.close()

        self.tbl_rules.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tbl_rules.setItem(i, 0, _make_item(str(r["id"])))
            self.tbl_rules.setItem(i, 1, _make_item(r["sex"]))
            self.tbl_rules.setItem(i, 2, _make_item(f"{r['min_age_years']:g}"))
            self.tbl_rules.setItem(i, 3, _make_item(f"{r['max_age_years']:g}"))
            self.tbl_rules.setItem(i, 4, _make_item(f"{r['low_val']:g}" if r["low_val"] is not None else "-"))
            self.tbl_rules.setItem(i, 5, _make_item(f"{r['high_val']:g}" if r["high_val"] is not None else "-"))
            clo = f"{r['crit_low']:g}" if r["crit_low"] is not None else "-"
            chi = f"{r['crit_high']:g}" if r["crit_high"] is not None else "-"
            self.tbl_rules.setItem(i, 6, _make_item(f"{clo} / {chi}"))
            self.tbl_rules.setItem(i, 7, _make_item(r["ref_label"] or "-"))
        self.tbl_rules.resizeRowsToContents()

    def _clear_form(self):
        self.editing_rule_id = None
        self.cmb_sex.setCurrentIndex(0)
        self.in_min_age.setText("0")
        self.in_max_age.setText("150")
        self.in_low.clear()
        self.in_high.clear()
        self.in_crit_low.clear()
        self.in_crit_high.clear()
        self.in_label.clear()
        self.tbl_rules.clearSelection()

    def _on_row_select(self):
        rows = self.tbl_rules.selectionModel().selectedRows()
        if not rows:
            return
        rid = int(self.tbl_rules.item(rows[0].row(), 0).text())
        conn = get_conn()
        r = conn.execute("SELECT * FROM reference_ranges WHERE id = ?", (rid,)).fetchone()
        conn.close()
        if not r:
            return
        self.editing_rule_id = rid
        self.cmb_sex.setCurrentText(r["sex"])
        self.in_min_age.setText(f"{r['min_age_years']:g}")
        self.in_max_age.setText(f"{r['max_age_years']:g}")
        self.in_low.setText(f"{r['low_val']:g}" if r["low_val"] is not None else "")
        self.in_high.setText(f"{r['high_val']:g}" if r["high_val"] is not None else "")
        self.in_crit_low.setText(f"{r['crit_low']:g}" if r["crit_low"] is not None else "")
        self.in_crit_high.setText(f"{r['crit_high']:g}" if r["crit_high"] is not None else "")
        self.in_label.setText(r["ref_label"] or "")

    @staticmethod
    def _opt_float(widget: QLineEdit):
        txt = widget.text().strip()
        if not txt:
            return None
        return float(txt)

    def _save_rule(self):
        try:
            min_age = float(self.in_min_age.text().strip() or "0")
            max_age = float(self.in_max_age.text().strip() or "150")
            lo = self._opt_float(self.in_low)
            hi = self._opt_float(self.in_high)
            clo = self._opt_float(self.in_crit_low)
            chi = self._opt_float(self.in_crit_high)
        except Exception:
            show_warn(self, "Invalid Input", "Ages and limits must be valid numbers.")
            return

        if max_age < min_age:
            show_warn(self, "Invalid Age Range", "Max Age must be greater than or equal to Min Age.")
            return

        sex = self.cmb_sex.currentText()
        label = self.in_label.text().strip()
        if not label:
            if lo is not None and hi is not None:
                label = f"{lo:g} - {hi:g} ({sex})"
            else:
                label = f"Ref ({sex}, {min_age:g}-{max_age:g}y)"

        conn = get_conn()
        try:
            if self.editing_rule_id:
                conn.execute("""
                    UPDATE reference_ranges
                    SET sex=?, min_age_years=?, max_age_years=?, low_val=?, high_val=?, crit_low=?, crit_high=?, ref_label=?
                    WHERE id=?
                """, (sex, min_age, max_age, lo, hi, clo, chi, label, self.editing_rule_id))
            else:
                conn.execute("""
                    INSERT INTO reference_ranges
                    (test_name, sex, min_age_years, max_age_years, low_val, high_val, crit_low, crit_high, ref_label)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(test_name, sex, min_age_years, max_age_years) DO UPDATE SET
                        low_val=excluded.low_val, high_val=excluded.high_val,
                        crit_low=excluded.crit_low, crit_high=excluded.crit_high,
                        ref_label=excluded.ref_label
                """, (self.test_name, sex, min_age, max_age, lo, hi, clo, chi, label))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            show_warn(self, "Duplicate Bracket", "A rule with that Sex and Age bracket already exists for this assay.")
            return
        conn.close()

        log_audit(self.operator_name, "DEMO_REF_RANGE_SAVED", "-", f"{self.test_name}: {label}")
        self._clear_form()
        self._load_rules()

    def _delete_rule(self):
        rows = self.tbl_rules.selectionModel().selectedRows()
        if not rows:
            show_info(self, "Select Rule", "Select a reference range row to delete.")
            return
        rid = int(self.tbl_rules.item(rows[0].row(), 0).text())
        if not ask_confirm(self, "Delete Reference Rule", "Remove the selected demographic reference range?"):
            return
        conn = get_conn()
        conn.execute("DELETE FROM reference_ranges WHERE id = ?", (rid,))
        conn.commit()
        conn.close()
        log_audit(self.operator_name, "DEMO_REF_RANGE_DELETED", "-", f"{self.test_name} rule #{rid}")
        self._clear_form()
        self._load_rules()


# ==============================================================================
# CLEAN STAFF PIN LOGIN SCREEN (LIGHT & DARK AWARE)
# ==============================================================================

class CleanLoginBackdrop(QWidget):
    def paintEvent(self, event):
        p = QPainter(self)
        w, h = self.width(), self.height()
        grad = QLinearGradient(0, 0, w, h)
        if CURRENT_THEME == "dark":
            grad.setColorAt(0.0, QColor("#070B14"))
            grad.setColorAt(0.5, QColor("#0B1120"))
            grad.setColorAt(1.0, QColor("#060911"))
        else:
            grad.setColorAt(0.0, QColor("#E2E8F0"))
            grad.setColorAt(0.5, QColor("#F1F5F9"))
            grad.setColorAt(1.0, QColor("#E0F2FE"))
        p.fillRect(0, 0, w, h, grad)


class StaffLoginScreen(QWidget):
    authenticated = Signal(dict)
    theme_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pin_buffer = ""
        self.locked_transition = False

        root = QGridLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.bg_canvas = CleanLoginBackdrop(self)
        root.addWidget(self.bg_canvas, 0, 0)

        top_overlay = QWidget(self)
        top_overlay.setAttribute(Qt.WA_TranslucentBackground)
        to_lay = QHBoxLayout(top_overlay)
        to_lay.setContentsMargins(20, 16, 20, 0)
        to_lay.addStretch()
        self.btn_login_theme = QPushButton("Light Mode" if CURRENT_THEME == "dark" else "Dark Mode")
        self.btn_login_theme.setFocusPolicy(Qt.NoFocus)
        self.btn_login_theme.clicked.connect(self.theme_toggled.emit)
        to_lay.addWidget(self.btn_login_theme)
        root.addWidget(top_overlay, 0, 0, Qt.AlignTop)

        center_wrap = QWidget(self)
        center_wrap.setAttribute(Qt.WA_TranslucentBackground)
        c_lay = QVBoxLayout(center_wrap)
        c_lay.setAlignment(Qt.AlignCenter)

        self.card = QFrame()
        self.card.setFixedWidth(390)
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 140))
        self.card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(28, 28, 28, 24)
        card_lay.setSpacing(14)

        self.badge = QLabel("MDL")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFixedSize(46, 46)
        badge_row = QHBoxLayout()
        badge_row.setAlignment(Qt.AlignCenter)
        badge_row.addWidget(self.badge)
        card_lay.addLayout(badge_row)

        self.lbl_brand = QLabel("Monocytes Delegates LIS")
        self.lbl_brand.setAlignment(Qt.AlignCenter)
        card_lay.addWidget(self.lbl_brand)

        self.lbl_sub = QLabel("Clinical Laboratory Information System")
        self.lbl_sub.setAlignment(Qt.AlignCenter)
        card_lay.addWidget(self.lbl_sub)

        slot_row = QHBoxLayout()
        slot_row.setSpacing(12)
        slot_row.setAlignment(Qt.AlignCenter)
        self.pin_slots = []
        for _ in range(4):
            box = QLabel("•")
            box.setAlignment(Qt.AlignCenter)
            box.setFixedSize(52, 52)
            self.pin_slots.append(box)
            slot_row.addWidget(box)
        card_lay.addLayout(slot_row)

        self.lbl_status = QLabel("Enter 4-digit staff PIN")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        card_lay.addWidget(self.lbl_status)

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

        self.lbl_hint = QLabel("Keyboard number pad supported")
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        card_lay.addWidget(self.lbl_hint)

        c_lay.addWidget(self.card)
        root.addWidget(center_wrap, 0, 0)
        self.setFocusPolicy(Qt.StrongFocus)
        self.apply_theme()

    def apply_theme(self):
        t = THEMES[CURRENT_THEME]
        self.btn_login_theme.setText("Light Mode" if CURRENT_THEME == "dark" else "Dark Mode")
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {t['surface']};
                border: 1px solid {t['border_strong']};
                border-radius: 14px;
            }}
        """)
        self.badge.setStyleSheet(f"""
            background-color: {t['subpanel']};
            border: 1px solid {t['accent']};
            border-radius: 11px;
            color: {t['accent']};
            font-size: 12.5pt;
            font-weight: 800;
            letter-spacing: 1px;
        """)
        self.lbl_brand.setStyleSheet(f"color: {t['text_bright']}; font-size: 14.5pt; font-weight: 700; border: none; background: transparent;")
        self.lbl_sub.setStyleSheet(f"color: {t['muted']}; font-size: 9pt; border: none; background: transparent;")
        self.lbl_status.setStyleSheet(f"color: {t['muted']}; font-size: 9pt; border: none; background: transparent;")
        self.lbl_hint.setStyleSheet(f"color: {t['muted']}; font-size: 8pt; border: none; background: transparent;")
        self._refresh_slots(t["border_strong"])
        self.bg_canvas.update()

    def reset_gate(self):
        self.pin_buffer = ""
        self.locked_transition = False
        self.lbl_status.setText("Enter 4-digit staff PIN")
        self.apply_theme()
        self.setFocus()

    def _refresh_slots(self, border_hex="#38BDF8"):
        t = THEMES[CURRENT_THEME]
        for i, slot in enumerate(self.pin_slots):
            if i < len(self.pin_buffer):
                slot.setText("●")
                slot.setStyleSheet(f"""
                    background-color: {t['subpanel']};
                    border: 2px solid {border_hex};
                    border-radius: 10px;
                    color: {border_hex};
                    font-family: 'Consolas', monospace;
                    font-size: 18pt;
                    font-weight: 700;
                """)
            else:
                slot.setText("•")
                slot.setStyleSheet(f"""
                    background-color: {t['input_bg']};
                    border: 1px solid {t['border_strong']};
                    border-radius: 10px;
                    color: {t['muted']};
                    font-family: 'Consolas', monospace;
                    font-size: 18pt;
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
        t = THEMES[CURRENT_THEME]
        if k == "CLR":
            self.pin_buffer = ""
            self._refresh_slots(t["border_strong"])
            self.lbl_status.setText("Enter 4-digit staff PIN")
            self.lbl_status.setStyleSheet(f"color: {t['muted']}; font-size: 9pt; border: none; background: transparent;")
        elif k == "⌫":
            self.pin_buffer = self.pin_buffer[:-1]
            self._refresh_slots(t["accent"])
        else:
            if len(self.pin_buffer) < 4:
                self.pin_buffer += k
                self._refresh_slots(t["accent"])
                if len(self.pin_buffer) == 4:
                    QTimer.singleShot(80, self._verify_pin)

    def _verify_pin(self):
        if self.locked_transition:
            return
        conn = get_conn()
        row = conn.execute("SELECT pin, name, role, prc_license, sig_path FROM staff WHERE pin = ?", (self.pin_buffer,)).fetchone()
        conn.close()

        if not row:
            self._refresh_slots("#F43F5E")
            self.lbl_status.setText("Invalid PIN — please try again")
            self.lbl_status.setStyleSheet("color: #F43F5E; font-size: 9pt; font-weight: 600; border: none; background: transparent;")
            self.pin_buffer = ""
            return

        self.locked_transition = True
        self._refresh_slots("#10B981")
        user = {
            "pin": row["pin"],
            "name": row["name"],
            "role": row["role"],
            "prc_license": row["prc_license"] or "",
            "sig_path": row["sig_path"] or "",
        }
        self.lbl_status.setText(f"Welcome, {user['name']}")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 9.5pt; font-weight: 700; border: none; background: transparent;")
        log_audit(f"{user['name']} ({user['pin']})", "SESSION_UNLOCK", "-", f"Role: {user['role']}")
        QTimer.singleShot(260, lambda: self.authenticated.emit(user))


# ==============================================================================
# CLINICAL INTERACTIVE DIALOGS (BATCH PANEL, MICROSCOPY, CALCULATORS, DIFF, ABX)
# ==============================================================================

class BatchPanelDialog(QDialog):
    """Scrollable Batch Panel Result Entry & Auto-Calculated Indices."""

    def __init__(self, specimen_id: str, operator_name: str, parent=None):
        super().__init__(parent)
        self.specimen_id = specimen_id
        self.operator_name = operator_name
        self.setWindowTitle(f"Batch Verify Panel — {specimen_id}")
        self.resize(900, 560)
        self.setMinimumSize(680, 420)
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

        conn = get_conn()
        self.orders = [dict(r) for r in conn.execute("""
            SELECT o.*, p.full_name, p.mrn, p.sex, p.dob
            FROM orders o JOIN patients p ON o.patient_id = p.id
            WHERE o.specimen_id = ? ORDER BY o.id ASC
        """, (specimen_id,)).fetchall()]
        self.patient = dict(conn.execute("SELECT * FROM patients WHERE id = ?", (self.orders[0]["patient_id"],)).fetchone()) if self.orders else {}
        self.intervals = {}
        for o in self.orders:
            self.intervals[o["id"]] = resolve_patient_interval(
                conn, o["test_name"], self.patient.get("sex"), self.patient.get("dob")
            )
        conn.close()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        scroll_area = QScrollArea()
        scroll_area.setObjectName("DarkScroll")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        body = QWidget()
        body.setObjectName("CardScrollContent")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)

        hdr = QLabel(
            f"Patient: {self.patient.get('full_name', '-')} ({self.patient.get('mrn', '-')})  |  "
            f"Sex/DOB: {self.patient.get('sex', '-')} / {self.patient.get('dob', '-')}"
        )
        hdr.setObjectName("SectionHeader")
        hdr.setWordWrap(True)
        lay.addWidget(hdr)

        sub = QLabel(f"Specimen: {specimen_id} ({len(self.orders)} assays) — Scroll freely for large panels. MCV, MCH, MCHC, and LDL auto-compute.")
        sub.setObjectName("MutedLabel")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        self.tbl = QTableWidget(len(self.orders), 6)
        self.tbl.setHorizontalHeaderLabels(["Assay", "Result", "Unit", "Demographic Ref. Range", "Auto-Flag", "Note"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self.tbl.setColumnWidth(0, 210)
        self.tbl.setColumnWidth(1, 130)
        self.tbl.setColumnWidth(2, 85)
        self.tbl.setColumnWidth(3, 155)
        self.tbl.setColumnWidth(4, 110)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tbl.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        self.result_inputs = {}
        self.note_inputs = {}
        self.flag_items = {}

        for idx, o in enumerate(self.orders):
            self.tbl.setRowHeight(idx, 38)
            it_name = _make_item(o["test_name"])
            it_name.setFlags(Qt.ItemIsEnabled)
            self.tbl.setItem(idx, 0, it_name)

            inp = QLineEdit(o["result_value"] or "")
            inp.setPlaceholderText("Enter value...")
            inp.setMinimumHeight(30)
            inp.textChanged.connect(lambda _txt, row_idx=idx: self._on_row_changed(row_idx))
            self.tbl.setCellWidget(idx, 1, inp)
            self.result_inputs[o["test_name"]] = (o, inp)

            it_unit = _make_item(o["unit"] or "-")
            it_unit.setFlags(Qt.ItemIsEnabled)
            self.tbl.setItem(idx, 2, it_unit)

            lo, hi, clo, chi, ref_lbl, _ = self.intervals[o["id"]]
            it_ref = _make_item(ref_lbl)
            it_ref.setFlags(Qt.ItemIsEnabled)
            self.tbl.setItem(idx, 3, it_ref)

            it_flag = _make_item(o["flag"] or o["status"])
            it_flag.setFlags(Qt.ItemIsEnabled)
            self.tbl.setItem(idx, 4, it_flag)
            self.flag_items[idx] = it_flag

            inp_note = QLineEdit(o["notes"] or "")
            inp_note.setPlaceholderText("Optional note...")
            inp_note.setMinimumHeight(30)
            self.tbl.setCellWidget(idx, 5, inp_note)
            self.note_inputs[o["id"]] = inp_note

            self._evaluate_row_flag(idx)

        # Ensure table has comfortable minimum height inside scroll area so rows never squish
        desired_tbl_h = min(680, max(240, 40 + len(self.orders) * 40))
        self.tbl.setMinimumHeight(desired_tbl_h)
        lay.addWidget(self.tbl, 1)

        scroll_area.setWidget(body)
        outer.addWidget(scroll_area, 1)

        btn_row = QHBoxLayout()
        btn_calc = QPushButton("Auto-Compute Indices (MCV/MCH/MCHC/LDL)")
        btn_calc.clicked.connect(self._auto_compute_derived)
        btn_row.addWidget(btn_calc)

        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ver_all = QPushButton("Verify Panel")
        btn_ver_all.setObjectName("SuccessBtn")
        btn_ver_all.setMinimumHeight(38)
        btn_ver_all.clicked.connect(self._verify_all)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ver_all)
        outer.addLayout(btn_row)

    def _on_row_changed(self, row_idx: int):
        self._evaluate_row_flag(row_idx)
        self._auto_compute_derived(silent=True)

    def _evaluate_row_flag(self, row_idx: int):
        o = self.orders[row_idx]
        _, inp = self.result_inputs[o["test_name"]]
        val_str = inp.text().strip()
        it_flag = self.flag_items[row_idx]
        if not val_str:
            it_flag.setText("PENDING")
            it_flag.setForeground(QColor("#94A3B8"))
            return
        lo, hi, clo, chi, _, _ = self.intervals[o["id"]]
        flag = "NORMAL"
        try:
            v = float(val_str)
            if clo is not None and v <= clo:
                flag = "CRITICAL LOW"
            elif chi is not None and v >= chi:
                flag = "CRITICAL HIGH"
            elif lo is not None and v < lo:
                flag = "LOW"
            elif hi is not None and v > hi:
                flag = "HIGH"
        except Exception:
            if any(k in val_str.upper() for k in ("REACTIVE", "POSITIVE", "MRSA", "ABNORMAL")):
                flag = "ABNORMAL"
        it_flag.setText(flag)
        if "CRITICAL" in flag or flag in ("HIGH", "ABNORMAL"):
            it_flag.setForeground(QColor("#E11D48"))
        elif flag == "LOW":
            it_flag.setForeground(QColor("#D97706"))
        else:
            it_flag.setForeground(QColor("#059669"))

    def _get_num(self, test_name: str):
        pair = self.result_inputs.get(test_name)
        if not pair:
            return None
        try:
            return float(pair[1].text().strip())
        except Exception:
            return None

    def _set_num_if_present(self, test_name: str, value: float, decimals: int = 1):
        pair = self.result_inputs.get(test_name)
        if not pair:
            return
        inp = pair[1]
        inp.blockSignals(True)
        inp.setText(f"{value:.{decimals}f}")
        inp.blockSignals(False)
        for idx, o in enumerate(self.orders):
            if o["test_name"] == test_name:
                self._evaluate_row_flag(idx)

    def _auto_compute_derived(self, silent: bool = False):
        rbc = self._get_num("Red Blood Cell Count (RBC)")
        hgb = self._get_num("Hemoglobin (Hgb)")
        hct = self._get_num("Hematocrit (Hct)")
        if rbc and hct and rbc > 0:
            self._set_num_if_present("MCV", (hct * 10.0) / rbc, 1)
        if rbc and hgb and rbc > 0:
            self._set_num_if_present("MCH", (hgb * 10.0) / rbc, 1)
        if hct and hgb and hct > 0:
            self._set_num_if_present("MCHC", (hgb * 100.0) / hct, 1)

        tc = self._get_num("Total Cholesterol")
        tg = self._get_num("Triglycerides")
        hdl = self._get_num("HDL Cholesterol")
        if tc is not None and tg is not None and hdl is not None and tg < 400:
            self._set_num_if_present("LDL Cholesterol (Calc)", tc - hdl - (tg / 5.0), 1)

    def _verify_all(self):
        conn = get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        verified_count = 0

        for idx, o in enumerate(self.orders):
            _, inp = self.result_inputs[o["test_name"]]
            val_str = inp.text().strip()
            if not val_str:
                continue
            lo, hi, clo, chi, ref_lbl, _ = self.intervals[o["id"]]
            flag = "NORMAL"
            is_crit = 0
            try:
                v = float(val_str)
                if clo is not None and v <= clo:
                    flag = "CRITICAL LOW"; is_crit = 1
                elif chi is not None and v >= chi:
                    flag = "CRITICAL HIGH"; is_crit = 1
                elif lo is not None and v < lo:
                    flag = "LOW"
                elif hi is not None and v > hi:
                    flag = "HIGH"
            except Exception:
                if any(k in val_str.upper() for k in ("REACTIVE", "POSITIVE", "MRSA", "ABNORMAL")):
                    flag = "ABNORMAL"

            note_txt = self.note_inputs[o["id"]].text().strip()
            coll_ts = o["collected_at"] or now
            conn.execute("""
                UPDATE orders SET
                    result_value = ?, flag = ?, status = 'Verified', ref_range = ?,
                    notes = ?, collected_at = ?, verified_by = ?, verified_at = ?, critical_flag = ?
                WHERE id = ?
            """, (val_str, flag, ref_lbl, note_txt, coll_ts, self.operator_name, now, is_crit, o["id"]))
            verified_count += 1

        conn.commit()
        conn.close()
        if verified_count == 0:
            show_warn(self, "No Results Entered", "Enter at least one test value before verifying.")
            return
        log_audit(self.operator_name, "BATCH_PANEL_VERIFIED", self.specimen_id, f"Verified {verified_count} assays")
        self.accept()


class MicroscopyDialog(QDialog):
    """Structured Clinical Microscopy (Urinalysis & Fecalysis) Form."""

    def __init__(self, test_name: str, existing_json: str = "", parent=None):
        super().__init__(parent)
        self.is_fecal = "fecal" in test_name.lower()
        self.setWindowTitle(f"Clinical Microscopy — {test_name}")
        self.resize(560, 560)
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

        saved = {}
        if existing_json:
            try:
                saved = json.loads(existing_json)
            except Exception:
                saved = {}

        lay = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setObjectName("DarkScroll")
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner.setObjectName("ScrollContent")
        grid = QGridLayout(inner)
        grid.setContentsMargins(14, 14, 14, 14)
        grid.setSpacing(8)

        self.fields = {}
        if not self.is_fecal:
            specs = [
                ("Color", ["Yellow", "Straw", "Amber", "Dark Yellow", "Reddish / Hematuria", "Cloudy White"]),
                ("Transparency", ["Clear", "Slightly Turbid", "Turbid", "Flocculent"]),
                ("Specific Gravity", ["1.005", "1.010", "1.015", "1.020", "1.025", "1.030"]),
                ("Reaction (pH)", ["5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0"]),
                ("Protein (Albumin)", ["Negative", "Trace", "+1 (30 mg/dL)", "+2 (100 mg/dL)", "+3 (300 mg/dL)", "+4 (>1000 mg/dL)"]),
                ("Glucose (Sugar)", ["Negative", "Trace", "+1 (100 mg/dL)", "+2 (250 mg/dL)", "+3 (500 mg/dL)", "+4 (>1000 mg/dL)"]),
                ("Ketones", ["Negative", "Trace", "Small (+1)", "Moderate (+2)", "Large (+3)"]),
                ("Blood / Hemoglobin", ["Negative", "Trace", "+1", "+2", "+3"]),
                ("Bilirubin / Urobilinogen", ["Negative / Normal", "Bilirubin +1", "Urobilinogen Increased"]),
                ("Nitrite / Leukocyte Est.", ["Negative / Negative", "Nitrite Pos / LE Neg", "Nitrite Neg / LE Pos", "Both Positive"]),
                ("Pus Cells (WBC / hpf)", ["0 - 2 /hpf", "2 - 5 /hpf", "5 - 10 /hpf", "10 - 20 /hpf", "20 - 50 /hpf", "TNTC (>100 /hpf)"]),
                ("Red Blood Cells (RBC / hpf)", ["0 - 1 /hpf", "1 - 3 /hpf", "3 - 10 /hpf", "10 - 30 /hpf", "TNTC (>100 /hpf)"]),
                ("Epithelial Cells", ["Few", "Moderate", "Many"]),
                ("Bacteria", ["None Seen", "Few", "Moderate", "Many"]),
                ("Casts & Crystals", ["None Seen", "Hyaline Casts (0-2/lpf)", "Granular Casts", "Calcium Oxalate Crystals", "Uric Acid Crystals", "Amorphous Urates"]),
            ]
        else:
            specs = [
                ("Color", ["Brown", "Dark Brown", "Yellowish", "Greenish", "Black / Melena", "Reddish"]),
                ("Consistency", ["Formed", "Semi-Formed", "Soft", "Mushy", "Watery / Liquid"]),
                ("Mucus", ["Absent", "Present (+1)", "Abundant (+3)"]),
                ("Occult Blood", ["Negative", "Positive"]),
                ("Pus Cells (WBC / hpf)", ["0 - 1 /hpf", "2 - 5 /hpf", "5 - 15 /hpf", "TNTC"]),
                ("Red Blood Cells (RBC / hpf)", ["None Seen", "1 - 3 /hpf", "5 - 15 /hpf", "Many"]),
                ("Fat Globules / Starch", ["None Seen", "Few", "Moderate", "Many"]),
                ("Ova & Parasites (NOPS)", ["No Ova or Parasites Seen (NOPS)", "Ascaris lumbricoides ova", "Trichuris trichiura ova", "Hookworm ova", "Entamoeba histolytica cysts/trophs", "Giardia lamblia cysts"]),
            ]

        for idx, (label, opts) in enumerate(specs):
            grid.addWidget(QLabel(label + ":"), idx, 0)
            cmb = QComboBox()
            cmb.setEditable(True)
            cmb.addItems(opts)
            if label in saved:
                cmb.setCurrentText(saved[label])
            grid.addWidget(cmb, idx, 1)
            self.fields[label] = cmb

        scroll.setWidget(inner)
        lay.addWidget(scroll)

        btn_save = QPushButton("Save Microscopy Findings")
        btn_save.setObjectName("SuccessBtn")
        btn_save.clicked.connect(self.accept)
        lay.addWidget(btn_save)

    def export_payload(self):
        data = {k: cmb.currentText().strip() for k, cmb in self.fields.items()}
        if self.is_fecal:
            summary = f"{data.get('Color', '')} / {data.get('Consistency', '')} / {data.get('Ova & Parasites (NOPS)', 'NOPS')}"
        else:
            summary = f"{data.get('Color', '')} / {data.get('Transparency', '')} / WBC:{data.get('Pus Cells (WBC / hpf)', '')}"
        return json.dumps(data), summary


class RmtCalculatorDialog(QDialog):
    """Hematology & Clinical Chemistry derived indices calculator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clinical Indices Calculator")
        self.resize(520, 440)
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)
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
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

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
            ("Neutrophils", "N", "#0284C7"),
            ("Lymphocytes", "L", "#6366F1"),
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
            f"font-size: 15pt; font-weight: 700; color: {'#10B981' if tot == 100 else '#0284C7'}; padding: 6px;"
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
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

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
        scroll.setObjectName("DarkScroll")
        scroll.setWidgetResizable(True)
        inner = QWidget()
        inner.setObjectName("ScrollContent")
        grid = QGridLayout(inner)
        grid.setContentsMargins(12, 12, 12, 12)
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
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)

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
        lbl.setWordWrap(True)
        top.addWidget(lbl, 1)

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
        self.tbl.setWordWrap(True)
        for i, r in enumerate(self.rows):
            ts = r["verified_at"] or r["ordered_at"] or "-"
            self.tbl.setItem(i, 0, _make_item(ts))
            self.tbl.setItem(i, 1, _make_item(r["specimen_id"]))
            self.tbl.setItem(i, 2, _make_item(r["test_name"]))
            self.tbl.setItem(i, 3, _make_item(r["result_value"] or "Pending"))
            self.tbl.setItem(i, 4, _make_item(r["unit"] or ""))
            fl_col = None
            if r["flag"] in ("HIGH", "CRITICAL HIGH", "CRITICAL LOW", "ABNORMAL"):
                fl_col = "#E11D48"
            elif r["flag"] == "LOW":
                fl_col = "#D97706"
            elif r["flag"] == "NORMAL":
                fl_col = "#059669"
            self.tbl.setItem(i, 5, _make_item(r["flag"] or r["status"], fl_col))
            self.tbl.setItem(i, 6, _make_item(r["verified_by"] or "-"))
        self.tbl.resizeRowsToContents()
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
        t = THEMES[CURRENT_THEME]
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

        ax.plot(xs, ys, color="#0284C7", marker="o", linewidth=2.0, markersize=6, label=test_name)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:g}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", color=t["text_bright"], fontsize=8)

        ax.set_title(f"Serial Trend: {test_name} ({unit})", fontsize=10, fontweight="bold")
        ax.grid(True, color=t["chart_grid"], linestyle=":", linewidth=0.8)
        ax.legend(loc="upper left", facecolor=t["surface"], edgecolor=t["border_strong"], labelcolor=t["text"], fontsize=8)
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
    pdf.cell(53, 5, _pdf_safe(f"REPORT ID: {doc_hash}"), align="R")

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
    microscopies = []

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
        if o.get("microscopy_json"):
            try:
                microscopies.append((o["test_name"], json.loads(o["microscopy_json"])))
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
            note_bits.append(f"CRITICAL READ-BACK: Notified {o['panic_notified_to']}")
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

    rmt_prc = ""
    rmt_sig_path = ""
    if verifiers:
        first_rmt = sorted(verifiers)[0]
        s_row = conn.execute("SELECT prc_license, sig_path FROM staff WHERE name = ?", (first_rmt,)).fetchone()
        if s_row:
            rmt_prc = s_row["prc_license"] or ""
            rmt_sig_path = s_row["sig_path"] or ""

    md_row = conn.execute("SELECT prc_license, sig_path FROM staff WHERE pin = '1111'").fetchone()
    md_prc = md_row["prc_license"] if md_row and md_row["prc_license"] else "PRC-0142890"
    md_sig_path = md_row["sig_path"] if md_row and md_row["sig_path"] else ""
    conn.close()

    for t_name, m_obj in microscopies:
        if y > 235:
            pdf.add_page(); y = 18
        y += 3
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(15, 23, 42)
        pdf.set_xy(12, y)
        pdf.cell(186, 5, _pdf_safe(f"Structured Clinical Microscopy Report ({t_name}):"))
        y += 5.5
        pdf.set_font("Helvetica", "", 8)
        items = list(m_obj.items())
        for i in range(0, len(items), 2):
            k1, v1 = items[i]
            pdf.set_xy(14, y)
            pdf.cell(92, 4.8, _pdf_safe(f"{k1}: {v1}"), border=1)
            if i + 1 < len(items):
                k2, v2 = items[i + 1]
                pdf.cell(92, 4.8, _pdf_safe(f"{k2}: {v2}"), border=1)
            y += 4.8

    for t_name, d_obj in diffs:
        if y > 240:
            pdf.add_page(); y = 18
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
        if y > 235:
            pdf.add_page(); y = 18
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

    y = max(y + 14, 246)
    if y > 266:
        pdf.add_page()
        y = 238

    if rmt_sig_path and os.path.exists(rmt_sig_path):
        try:
            pdf.image(rmt_sig_path, x=35, y=y - 12, w=40)
        except Exception:
            pass
    if md_sig_path and os.path.exists(md_sig_path):
        try:
            pdf.image(md_sig_path, x=135, y=y - 12, w=40)
        except Exception:
            pass

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
    rmt_sub = f"Medical Technologist (RMT)  {rmt_prc}".strip()
    pdf.cell(80, 4, _pdf_safe(rmt_sub), align="C")
    pdf.set_xy(115, y + 6)
    md_sub = f"Anatomic & Clinical Pathologist  {md_prc}  {pathologist_sig}".strip()
    pdf.cell(80, 4, _pdf_safe(md_sub), align="C")

    pdf.output(out_path)


def generate_barcode_label_pdf(patient: dict, specimen_id: str, order: dict, out_path: str):
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
    for ch in digest[:42]:
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
        WHERE o.status NOT IN ('Verified', 'Amended', 'Rejected', 'Cancelled')
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
    pdf.cell(186, 7, _pdf_safe(f"MONOCYTES DELEGATES LIS — SHIFT HANDOVER ({shift_label})"))
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
    pdf.cell(186, 6, _pdf_safe(f"2. Critical Value Read-Backs ({len(criticals)})"))
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
    theme_toggled = Signal()

    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.user = current_user
        self.selected_order_id = None
        self.selected_specimen_id = None
        self.qc_lockout_enabled = False
        self.failed_qc_tests = set()
        self.editing_patient_id = None
        self.admin_mode = False
        self.collapsed_specimens = set()
        self.qc_zoom_factor = 1.0

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top Header Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopHeaderBar")
        top_bar.setFixedHeight(52)
        tb_lay = QHBoxLayout(top_bar)
        tb_lay.setContentsMargins(16, 6, 16, 6)
        tb_lay.setSpacing(10)

        self.lbl_logo = QLabel("Monocytes Delegates LIS")
        self.lbl_logo.setStyleSheet("font-size: 12pt; font-weight: 700;")
        tb_lay.addWidget(self.lbl_logo)

        self.lbl_qc_pill = QLabel("QC: In Control")
        tb_lay.addWidget(self.lbl_qc_pill)

        tb_lay.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setObjectName("MonoBadge")
        tb_lay.addWidget(self.lbl_clock)

        role_short = "Pathologist" if "Pathologist" in self.user["role"] else "RMT"
        op_full = f"{self.user['name']}  •  {role_short}"
        self.lbl_op = QLabel(op_full)
        self.lbl_op.setToolTip(op_full)
        self.lbl_op.setMaximumWidth(295)
        self.lbl_op.setObjectName("MonoBadge")
        tb_lay.addWidget(self.lbl_op)

        self.btn_theme = QPushButton("Light Mode" if CURRENT_THEME == "dark" else "Dark Mode")
        self.btn_theme.setToolTip("Switch between Light and Dark interface themes")
        self.btn_theme.clicked.connect(self.theme_toggled.emit)
        tb_lay.addWidget(self.btn_theme)

        self.btn_admin_mode = QPushButton("Admin Mode")
        self.btn_admin_mode.clicked.connect(self._toggle_admin_mode)
        tb_lay.addWidget(self.btn_admin_mode)

        btn_lock = QPushButton("Lock / Switch User")
        btn_lock.setObjectName("DangerBtn")
        btn_lock.clicked.connect(self.lock_requested.emit)
        tb_lay.addWidget(btn_lock)

        root.addWidget(top_bar)

        # Main Tabbed Workspace
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(12, 10, 12, 12)
        body_lay.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_worklist_tab(), "Worklist")
        self.tabs.addTab(self._build_requisition_tab(), "New Order")
        self.tabs.addTab(self._build_patients_tab(), "Patients")
        self.tabs.addTab(self._build_pathologist_tab(), "Pathologist Review")
        self.tabs.addTab(self._build_qc_tab(), "Quality Control")
        self.tabs.addTab(self._build_catalog_tab(), "Test Catalog")
        self.admin_tab_widget = self._build_admin_tab()
        body_lay.addWidget(self.tabs, 1)

        root.addWidget(body, 1)

        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._focus_search)
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self._focus_barcode)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._passive_sync)
        self.sync_timer.start(8000)

        self._update_qc_pill()
        self.refresh_all()

    def on_theme_changed(self):
        self.btn_theme.setText("Light Mode" if CURRENT_THEME == "dark" else "Dark Mode")
        self._update_qc_pill()
        self.range_gauge.update()
        self.tube_badge.update()
        self.refresh_worklist()
        self.refresh_qc()

    def _passive_sync(self):
        if self.tabs.currentIndex() == 0 and not self.in_result.hasFocus():
            self.refresh_kpis()
            self.refresh_worklist()

    def _toggle_admin_mode(self):
        if self.admin_mode:
            self.admin_mode = False
            idx = self.tabs.indexOf(self.admin_tab_widget)
            if idx >= 0:
                self.tabs.removeTab(idx)
            self.btn_admin_mode.setText("Admin Mode")
            self.btn_admin_mode.setObjectName("")
            self.btn_admin_mode.style().unpolish(self.btn_admin_mode)
            self.btn_admin_mode.style().polish(self.btn_admin_mode)
            log_audit(self.user["name"], "ADMIN_MODE_DISABLED", "-", "Exited Admin Mode")
            return

        dlg = AdminPinDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.admin_mode = True
            if self.tabs.indexOf(self.admin_tab_widget) < 0:
                self.tabs.addTab(self.admin_tab_widget, "Reports & Admin")
            self.tabs.setCurrentWidget(self.admin_tab_widget)
            self.btn_admin_mode.setText("Admin Mode: ON")
            self.btn_admin_mode.setObjectName("AdminActiveBtn")
            self.btn_admin_mode.style().unpolish(self.btn_admin_mode)
            self.btn_admin_mode.style().polish(self.btn_admin_mode)
            log_audit(self.user["name"], "ADMIN_MODE_ENABLED", "-", "Unlocked Admin Mode (PIN 0000)")

    def _update_clock(self):
        self.lbl_clock.setText(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))

    def _focus_search(self):
        self.tabs.setCurrentIndex(0)
        self.in_search.setFocus()
        self.in_search.selectAll()

    def _focus_barcode(self):
        self.tabs.setCurrentIndex(0)
        self.in_barcode.setFocus()
        self.in_barcode.selectAll()

    # --------------------------------------------------------------------------
    # TAB 1: WORKLIST (GROUPED BY PATIENT/SPECIMEN) & CLINICAL INSPECTOR
    # --------------------------------------------------------------------------
    def _build_worklist_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)

        flt = QHBoxLayout()
        flt.setSpacing(8)

        self.in_barcode = QLineEdit()
        self.in_barcode.setPlaceholderText("Scan Tube Barcode (Ctrl+B)...")
        self.in_barcode.setMaximumWidth(205)
        self.in_barcode.returnPressed.connect(self._on_barcode_scan)
        flt.addWidget(self.in_barcode)

        self.in_search = QLineEdit()
        self.in_search.setPlaceholderText("Filter specimen, patient, MRN, or test (Ctrl+F)...")
        self.in_search.textChanged.connect(self.refresh_worklist)
        flt.addWidget(self.in_search, 2)

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
            "Critical / Abnormal", "Verified / Amended", "Rejected / Cancelled"
        ])
        self.cmb_status_filter.currentTextChanged.connect(self.refresh_worklist)
        flt.addWidget(self.cmb_status_filter, 1)

        btn_exp_all = QPushButton("Expand All")
        btn_exp_all.clicked.connect(self._expand_all_groups)
        flt.addWidget(btn_exp_all)

        btn_col_all = QPushButton("Minimize All")
        btn_col_all.clicked.connect(self._collapse_all_groups)
        flt.addWidget(btn_col_all)

        self.lbl_queue_counts = QLabel("Total: 0  |  Pending: 0  |  STAT: 0  |  Verified: 0")
        self.lbl_queue_counts.setObjectName("MonoBadge")
        flt.addWidget(self.lbl_queue_counts)

        btn_new = QPushButton("+ New Order")
        btn_new.setObjectName("PrimaryBtn")
        btn_new.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        flt.addWidget(btn_new)

        lay.addLayout(flt)

        splitter = QSplitter(Qt.Horizontal)

        self.tbl_worklist = QTreeWidget()
        self.tbl_worklist.setColumnCount(8)
        self.tbl_worklist.setHeaderLabels([
            "Specimen ID", "Patient Name", "Test / Assay", "Department", "Priority", "TAT (Coll / Bench)", "Result", "Status"
        ])
        hdr = self.tbl_worklist.header()
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(True)
        self.tbl_worklist.setColumnWidth(0, 155)
        self.tbl_worklist.setColumnWidth(1, 175)
        self.tbl_worklist.setColumnWidth(2, 195)
        self.tbl_worklist.setColumnWidth(3, 120)
        self.tbl_worklist.setColumnWidth(4, 68)
        self.tbl_worklist.setColumnWidth(5, 118)
        self.tbl_worklist.setColumnWidth(6, 105)
        self.tbl_worklist.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_worklist.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_worklist.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_worklist.setAlternatingRowColors(True)
        self.tbl_worklist.setUniformRowHeights(False)
        self.tbl_worklist.setIndentation(18)
        self.tbl_worklist.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tbl_worklist.itemSelectionChanged.connect(self._on_worklist_select)
        self.tbl_worklist.itemExpanded.connect(self._on_group_expanded)
        self.tbl_worklist.itemCollapsed.connect(self._on_group_collapsed)
        self.tbl_worklist.itemDoubleClicked.connect(self._on_worklist_double_click)
        splitter.addWidget(self.tbl_worklist)

        scroll = QScrollArea()
        scroll.setObjectName("DarkScroll")
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(400)

        insp = QWidget()
        insp.setObjectName("CardScrollContent")
        il = QVBoxLayout(insp)
        il.setContentsMargins(16, 14, 16, 14)
        il.setSpacing(10)

        self.lbl_insp_spec = QLabel("Select a specimen row")
        self.lbl_insp_spec.setObjectName("SectionHeader")
        self.lbl_insp_spec.setWordWrap(True)
        il.addWidget(self.lbl_insp_spec)

        self.lbl_insp_meta = QLabel("Click any row on the left to enter results, inspect demographic reference ranges, or print reports.")
        self.lbl_insp_meta.setObjectName("MutedLabel")
        self.lbl_insp_meta.setWordWrap(True)
        il.addWidget(self.lbl_insp_meta)

        self.tube_badge = TubeBadgeWidget()
        il.addWidget(self.tube_badge)

        self.range_gauge = VectorRangeGauge()
        il.addWidget(self.range_gauge)

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

        self.btn_batch = QPushButton("Batch Verify")
        self.btn_batch.setObjectName("PrimaryBtn")
        self.btn_batch.setMinimumHeight(38)
        self.btn_batch.setToolTip("Open scrollable multi-test grid entry for all assays in this specimen")
        self.btn_batch.clicked.connect(self._open_batch_panel)
        act_row.addWidget(self.btn_batch, 1)

        btn_reject = QPushButton("Reject")
        btn_reject.setObjectName("DangerBtn")
        btn_reject.setMinimumHeight(38)
        btn_reject.setToolTip("Log clinical specimen rejection (hemolysis, QNS, clotted, etc.)")
        btn_reject.clicked.connect(self._reject_selected_order)
        act_row.addWidget(btn_reject, 1)
        il.addLayout(act_row)

        self.btn_cancel_order = QPushButton("Cancel Order (Uncollected)")
        self.btn_cancel_order.setToolTip("Cancel an uncollected order prior to specimen draw")
        self.btn_cancel_order.clicked.connect(self._cancel_selected_order)
        il.addWidget(self.btn_cancel_order)

        grp_tools = QLabel("SPECIMEN HANDLING & BENCH TOOLS")
        grp_tools.setObjectName("GroupTitle")
        il.addWidget(grp_tools)

        stage_row = QHBoxLayout()
        btn_collect = QPushButton("Collected")
        btn_collect.setToolTip("Mark entire order / specimen as Collected")
        btn_collect.clicked.connect(lambda: self._advance_stage("Collected"))
        btn_proc = QPushButton("In-Process")
        btn_proc.clicked.connect(lambda: self._advance_stage("In-Process"))
        btn_store = QPushButton("Storage Slot")
        btn_store.clicked.connect(self._assign_storage_slot)
        stage_row.addWidget(btn_collect)
        stage_row.addWidget(btn_proc)
        stage_row.addWidget(btn_store)
        il.addLayout(stage_row)

        tools_grid = QGridLayout()
        tools_grid.setSpacing(6)
        btn_calc = QPushButton("Calculators")
        btn_calc.clicked.connect(self._open_calculators)
        btn_diff = QPushButton("100-Cell Diff")
        btn_diff.clicked.connect(self._open_wbc_diff)
        btn_micro = QPushButton("Microscopy Form")
        btn_micro.clicked.connect(self._open_microscopy_form)
        btn_abx = QPushButton("Antibiogram")
        btn_abx.clicked.connect(self._open_antibiogram)
        tools_grid.addWidget(btn_calc, 0, 0)
        tools_grid.addWidget(btn_diff, 0, 1)
        tools_grid.addWidget(btn_micro, 1, 0)
        tools_grid.addWidget(btn_abx, 1, 1)
        il.addLayout(tools_grid)

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

    def _on_barcode_scan(self):
        code = self.in_barcode.text().strip()
        if not code:
            return
        conn = get_conn()
        row = conn.execute("SELECT id, specimen_id FROM orders WHERE specimen_id LIKE ? ORDER BY id ASC LIMIT 1", (f"%{code}%",)).fetchone()
        conn.close()
        self.in_barcode.clear()
        if not row:
            show_warn(self, "Specimen Not Found", f"No specimen matching '{code}' in active worklist.")
            return
        self.collapsed_specimens.discard(row["specimen_id"])
        self.selected_order_id = row["id"]
        self.refresh_worklist()
        self._load_inspector_order(row["id"], animate_from_center=False)
        self.in_result.setFocus()

    def _expand_all_groups(self):
        self.collapsed_specimens.clear()
        self.tbl_worklist.expandAll()

    def _collapse_all_groups(self):
        for i in range(self.tbl_worklist.topLevelItemCount()):
            top = self.tbl_worklist.topLevelItem(i)
            if top.childCount() > 0:
                spec_id = top.data(0, Qt.UserRole + 1)
                if spec_id:
                    self.collapsed_specimens.add(spec_id)
                top.setExpanded(False)

    def _on_group_expanded(self, item: QTreeWidgetItem):
        spec_id = item.data(0, Qt.UserRole + 1)
        if spec_id:
            self.collapsed_specimens.discard(spec_id)

    def _on_group_collapsed(self, item: QTreeWidgetItem):
        spec_id = item.data(0, Qt.UserRole + 1)
        if spec_id:
            self.collapsed_specimens.add(spec_id)

    def _on_worklist_double_click(self, item: QTreeWidgetItem, col: int):
        if item.childCount() > 0:
            spec_id = item.data(0, Qt.UserRole + 1)
            if spec_id:
                self.selected_specimen_id = spec_id
                self._open_batch_panel()
        else:
            self.in_result.setFocus()
            self.in_result.selectAll()

    def _on_worklist_select(self):
        items = self.tbl_worklist.selectedItems()
        if not items:
            return
        item = items[0]
        spec_grp = item.data(0, Qt.UserRole + 1)
        if spec_grp:
            self.selected_specimen_id = spec_grp
        order_id = item.data(0, Qt.UserRole)
        if order_id is None and item.childCount() > 0:
            order_id = item.child(0).data(0, Qt.UserRole)
        if order_id is None:
            return
        self._load_inspector_order(int(order_id), animate_from_center=False)

    def _load_inspector_order(self, order_id: int, animate_from_center: bool = False):
        self.selected_order_id = order_id
        conn = get_conn()
        o = conn.execute("""
            SELECT o.*, p.full_name, p.mrn, p.sex, p.dob
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            WHERE o.id = ?
        """, (order_id,)).fetchone()
        if not o:
            conn.close()
            return
        self.selected_specimen_id = o["specimen_id"]
        lo, hi, clo, chi, ref_lbl, _ = resolve_patient_interval(conn, o["test_name"], o["sex"], o["dob"])
        conn.close()

        self.lbl_insp_spec.setText(f"{o['specimen_id']}  •  {o['test_name']}")
        slot_txt = o["storage_slot"] or "Unassigned"
        self.lbl_insp_meta.setText(
            f"Patient: {o['full_name']} ({o['mrn']})\n"
            f"Demographics: {o['sex'] or '-'}  |  DOB/Age: {o['dob'] or '-'}\n"
            f"Priority: {o['priority']}  |  Stage: {o['status']}  |  Storage: {slot_txt}\n"
            f"Ref. Range ({o['sex'] or 'All'}): {ref_lbl} {o['unit'] or ''}"
        )
        self.tube_badge.set_tube(o["tube_type"])
        self.in_result.setText(o["result_value"] or "")
        self.in_notes.setText(o["notes"] or "")
        self.btn_cancel_order.setEnabled(not o["collected_at"] and o["status"] == "Ordered")
        self.range_gauge.set_reading(
            o["result_value"] or "", lo, hi, clo, chi,
            o["flag"] or o["status"], animate_from_center=animate_from_center
        )

    def _cancel_selected_order(self):
        if not self.selected_order_id:
            show_info(self, "No Selection", "Select an uncollected order to cancel.")
            return
        target_id = self.selected_order_id
        conn = get_conn()
        o = conn.execute("SELECT * FROM orders WHERE id = ?", (target_id,)).fetchone()
        if not o:
            conn.close()
            return
        if o["collected_at"] or o["status"] != "Ordered":
            conn.close()
            show_warn(
                self, "Cannot Cancel Collected Order",
                "Only uncollected orders in 'Ordered' status can be cancelled.\n"
                "Use 'Reject' if the specimen has already been collected."
            )
            return
        conn.close()

        dlg = QDialog(self)
        dlg.setWindowTitle("Cancel Uncollected Order")
        dlg.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(dlg)
        l = QVBoxLayout(dlg)
        l.addWidget(QLabel(f"Cancel order for {o['test_name']} ({o['specimen_id']})?\nEnter cancellation reason:"))
        cmb_reason = QComboBox()
        cmb_reason.setEditable(True)
        cmb_reason.addItems([
            "Duplicate Order Entered",
            "Physician Discontinued Test",
            "Patient Discharged / Left Before Draw",
            "Order Placed on Wrong Patient",
        ])
        l.addWidget(cmb_reason)
        b_ok = QPushButton("Confirm Order Cancellation")
        b_ok.setObjectName("DangerBtn")
        b_ok.clicked.connect(dlg.accept)
        l.addWidget(b_ok)

        if dlg.exec() == QDialog.Accepted:
            reason = cmb_reason.currentText().strip() or "Cancelled prior to collection"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            note_prev = (o["notes"] or "").strip()
            merged_note = f"{note_prev} | CANCELLED: {reason}".strip(" |")
            conn = get_conn()
            conn.execute("""
                UPDATE orders
                SET status = 'Cancelled', flag = 'CANCELLED', notes = ?, verified_by = ?, verified_at = ?
                WHERE id = ?
            """, (merged_note, self.user["name"], now, target_id))
            conn.commit()
            conn.close()
            log_audit(self.user["name"], "ORDER_CANCELLED", o["specimen_id"], f"{o['test_name']}: {reason}")
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)

    def _open_batch_panel(self):
        spec_id = self.selected_specimen_id
        if not spec_id and self.selected_order_id:
            conn = get_conn()
            r = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (self.selected_order_id,)).fetchone()
            conn.close()
            if r:
                spec_id = r["specimen_id"]
        if not spec_id:
            show_info(self, "Select Specimen", "Select a specimen or grouped order from the worklist first.")
            return
        dlg = BatchPanelDialog(spec_id, self.user["name"], self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_all()
            if self.selected_order_id:
                self._load_inspector_order(self.selected_order_id, animate_from_center=True)

    def _open_microscopy_form(self):
        if not self.selected_order_id:
            show_info(self, "Select Specimen", "Select a Urinalysis or Fecalysis order first.")
            return
        target_id = self.selected_order_id
        conn = get_conn()
        o = conn.execute("SELECT test_name, microscopy_json, specimen_id FROM orders WHERE id = ?", (target_id,)).fetchone()
        conn.close()
        dlg = MicroscopyDialog(o["test_name"], o["microscopy_json"] or "", self)
        if dlg.exec() == QDialog.Accepted:
            raw_json, summary = dlg.export_payload()
            conn = get_conn()
            conn.execute("UPDATE orders SET microscopy_json = ? WHERE id = ?", (raw_json, target_id))
            conn.commit()
            conn.close()
            self.in_result.setText(summary)
            log_audit(self.user["name"], "MICROSCOPY_SAVED", o["specimen_id"], summary)
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)

    def _advance_stage(self, stage: str):
        if not self.selected_order_id and not self.selected_specimen_id:
            return
        target_id = self.selected_order_id
        conn = get_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        spec_id = self.selected_specimen_id
        if target_id:
            row = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (target_id,)).fetchone()
            if row:
                spec_id = row["specimen_id"]

        if stage == "Collected" and spec_id:
            # Update the entire order (all assays under this specimen_id) to Collected
            cur = conn.execute("""
                UPDATE orders
                SET status = 'Collected', collected_at = COALESCE(collected_at, ?)
                WHERE specimen_id = ? AND status NOT IN ('Verified', 'Amended', 'Rejected', 'Cancelled')
            """, (now, spec_id))
            updated_cnt = cur.rowcount
            conn.commit()
            conn.close()
            log_audit(self.user["name"], "ORDER_COLLECTED", spec_id, f"Marked {updated_cnt} test(s) in order as Collected")
            self.refresh_all()
            if target_id:
                self._load_inspector_order(target_id, animate_from_center=False)
            show_info(self, "Order Collected", f"Entire order ({spec_id}) marked as Collected ({updated_cnt} test(s) updated).")
            return

        if target_id:
            conn.execute(
                "UPDATE orders SET status = ?, collected_at = COALESCE(collected_at, ?) WHERE id = ?",
                (stage, now, target_id)
            )
            conn.commit()
            conn.close()
            log_audit(self.user["name"], f"STAGE_{stage.upper()}", spec_id or "-", f"Order #{target_id}")
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)
        else:
            conn.close()

    def _assign_storage_slot(self):
        if not self.selected_order_id:
            return
        target_id = self.selected_order_id
        dlg = QDialog(self)
        dlg.setWindowTitle("Assign Specimen Storage Slot")
        dlg.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(dlg)
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
            conn.execute("UPDATE orders SET storage_slot = ? WHERE id = ?", (slot, target_id))
            conn.commit()
            conn.close()
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)

    def _open_calculators(self):
        dlg = RmtCalculatorDialog(self)
        if dlg.exec() == QDialog.Accepted and dlg.generated_summary:
            cur = self.in_notes.text().strip()
            self.in_notes.setText(f"{cur} | {dlg.generated_summary}".strip(" |"))

    def _open_wbc_diff(self):
        if not self.selected_order_id:
            show_info(self, "Select Specimen", "Select a Hematology / CBC / PBS order first.")
            return
        target_id = self.selected_order_id
        conn = get_conn()
        o = conn.execute("SELECT diff_json, specimen_id FROM orders WHERE id = ?", (target_id,)).fetchone()
        conn.close()
        dlg = WbcDiffCounterDialog(o["diff_json"] or "", self)
        if dlg.exec() == QDialog.Accepted:
            raw_json, summary, morph = dlg.export_payload()
            conn = get_conn()
            conn.execute("UPDATE orders SET diff_json = ? WHERE id = ?", (raw_json, target_id))
            conn.commit()
            conn.close()
            if not self.in_result.text().strip():
                self.in_result.setText(summary)
            self.in_notes.setText(morph)
            log_audit(self.user["name"], "WBC_DIFF_SAVED", o["specimen_id"], summary)
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)

    def _open_antibiogram(self):
        if not self.selected_order_id:
            show_info(self, "Select Specimen", "Select a Microbiology / Culture order first.")
            return
        target_id = self.selected_order_id
        conn = get_conn()
        o = conn.execute("SELECT antibiogram_json, specimen_id FROM orders WHERE id = ?", (target_id,)).fetchone()
        conn.close()
        dlg = AntibiogramDialog(o["antibiogram_json"] or "", self)
        if dlg.exec() == QDialog.Accepted:
            raw_json, short_res = dlg.export_payload()
            conn = get_conn()
            conn.execute("UPDATE orders SET antibiogram_json = ? WHERE id = ?", (raw_json, target_id))
            conn.commit()
            conn.close()
            self.in_result.setText(short_res)
            log_audit(self.user["name"], "ANTIBIOGRAM_SAVED", o["specimen_id"], short_res)
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=False)

    def _verify_selected_order(self):
        if not self.selected_order_id:
            show_info(self, "No Selection", "Please select a specimen order from the worklist first.")
            return
        val_str = self.in_result.text().strip()
        if not val_str:
            show_warn(self, "Missing Result", "Enter a result value before verifying.")
            return

        verified_id = self.selected_order_id
        conn = get_conn()
        o = conn.execute("""
            SELECT o.*, p.sex, p.dob
            FROM orders o
            JOIN patients p ON o.patient_id = p.id
            WHERE o.id = ?
        """, (verified_id,)).fetchone()
        if not o:
            conn.close()
            return

        if self.qc_lockout_enabled and o["test_name"] in self.failed_qc_tests:
            conn.close()
            show_error(
                self, "QC Lockout Active",
                f"Verification blocked for {o['test_name']}.\nResolve the active Westgard 1-3s QC failure first."
            )
            return

        lo, hi, clo, chi, ref_lbl, delta_pct = resolve_patient_interval(conn, o["test_name"], o["sex"], o["dob"])

        flag = "NORMAL"
        is_crit = 0
        try:
            v = float(val_str)
            if clo is not None and v <= clo:
                flag = "CRITICAL LOW"
                is_crit = 1
            elif chi is not None and v >= chi:
                flag = "CRITICAL HIGH"
                is_crit = 1
            elif lo is not None and v < lo:
                flag = "LOW"
            elif hi is not None and v > hi:
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
        if prior and delta_pct:
            try:
                v_now = float(val_str)
                v_old = float(prior["result_value"])
                if v_old != 0:
                    pct_diff = abs((v_now - v_old) / v_old) * 100.0
                    if pct_diff >= float(delta_pct):
                        delta_msg = f"{pct_diff:.0f}% shift vs prior ({v_old:g})"
                        if not ask_confirm(
                            self, "Delta Check Alert",
                            f"Result shifted {pct_diff:.1f}% from prior value ({v_old:g} -> {v_now:g}).\n"
                            f"Confirm specimen identity and proceed with release?"
                        ):
                            conn.close()
                            return
            except Exception:
                pass

        panic_notified = o["panic_notified_to"] or ""
        if is_crit:
            dlg = QDialog(self)
            dlg.setWindowTitle("Critical Value — Read-Back Log")
            dlg.setStyleSheet(build_qss(CURRENT_THEME))
            apply_window_titlebar_theme(dlg)
            dl = QVBoxLayout(dlg)
            warn = QLabel(f"CRITICAL VALUE: {o['test_name']} = {val_str} ({flag})\nRecord physician/nurse notified and read-back confirmation:")
            warn.setStyleSheet("color: #FB7185; font-weight: 700;")
            dl.addWidget(warn)
            in_md = QLineEdit()
            in_md.setPlaceholderText("e.g., Dr. Shaun Bautista / Nurse Cruz — Read-back confirmed")
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
            dlg_am.setStyleSheet(build_qss(CURRENT_THEME))
            apply_window_titlebar_theme(dlg_am)
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
        coll_ts = o["collected_at"] or now
        conn.execute("""
            UPDATE orders SET
                result_value = ?, flag = ?, status = ?, ref_range = ?, notes = ?,
                collected_at = ?, verified_by = ?, verified_at = ?, amended_reason = ?,
                panic_notified_to = ?, delta_flag = ?, critical_flag = ?
            WHERE id = ?
        """, (
            val_str, flag, new_status, ref_lbl, self.in_notes.text().strip(),
            coll_ts, self.user["name"], now, amend_reason,
            panic_notified, delta_msg, is_crit, verified_id
        ))
        conn.commit()
        conn.close()

        log_audit(self.user["name"], f"RESULT_{new_status.upper()}", o["specimen_id"], f"{o['test_name']} = {val_str} [{flag}]")
        self.selected_order_id = verified_id
        self.refresh_all()
        self._load_inspector_order(verified_id, animate_from_center=True)

    def _reject_selected_order(self):
        if not self.selected_order_id:
            return
        target_id = self.selected_order_id
        dlg = QDialog(self)
        dlg.setWindowTitle("Reject Specimen")
        dlg.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(dlg)
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
            row = conn.execute("SELECT specimen_id FROM orders WHERE id = ?", (target_id,)).fetchone()
            conn.execute("""
                UPDATE orders SET status = 'Rejected', flag = 'REJECTED', notes = ?, verified_by = ?, verified_at = ?
                WHERE id = ?
            """, (f"REJECTED: {reason}", self.user["name"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target_id))
            conn.commit()
            conn.close()
            log_audit(self.user["name"], "SPECIMEN_REJECTED", row["specimen_id"] if row else "-", reason)
            self.refresh_all()
            self._load_inspector_order(target_id, animate_from_center=True)

    def _print_consolidated_pdf(self):
        if not self.selected_order_id:
            show_info(self, "Select Specimen", "Select an order from the worklist to print its report.")
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
                    show_info(self, "PDF Saved", f"Saved to:\n{path}")
            except Exception as e:
                show_error(self, "PDF Error", str(e))

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
    # TAB 2: NEW ORDER & ACCESSIONING (WITH SEARCHABLE PATIENT SELECTOR)
    # --------------------------------------------------------------------------
    def _build_requisition_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(14)

        left_scroll = QScrollArea()
        left_scroll.setObjectName("DarkScroll")
        left_scroll.setWidgetResizable(True)

        left = QWidget()
        left.setObjectName("CardScrollContent")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(18, 16, 18, 16)
        ll.setSpacing(10)

        lbl = QLabel("1. Patient & Order Details")
        lbl.setObjectName("SectionHeader")
        ll.addWidget(lbl)

        l_exist = QLabel("Search & Select Registered Patient:")
        l_exist.setObjectName("FieldLabel")
        ll.addWidget(l_exist)

        self.in_req_pt_search = QLineEdit()
        self.in_req_pt_search.setPlaceholderText("Type patient name or MRN to filter...")
        self.in_req_pt_search.textChanged.connect(self._filter_req_patients)
        ll.addWidget(self.in_req_pt_search)

        self.cmb_req_patient = QComboBox()
        self.cmb_req_patient.setEditable(True)
        self.cmb_req_patient.setInsertPolicy(QComboBox.NoInsert)
        self.cmb_req_patient.lineEdit().setPlaceholderText("Search or pick registered patient...")
        self.cmb_req_patient.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cmb_req_patient.setMinimumContentsLength(22)
        self.cmb_req_patient.currentIndexChanged.connect(self._on_req_patient_pick)
        ll.addWidget(self.cmb_req_patient)

        self.in_pt_name = QLineEdit(); self.in_pt_name.setPlaceholderText("Full Name (Last, First MI)")
        self.in_pt_mrn = QLineEdit(); self.in_pt_mrn.setPlaceholderText("MRN (auto-generated if blank)")
        self.in_pt_dob = QLineEdit(); self.in_pt_dob.setPlaceholderText("DOB (YYYY-MM-DD) or Age (e.g. 34y, 6m)")
        self.cmb_pt_sex = QComboBox(); self.cmb_pt_sex.addItems(["Female", "Male", "Other"])
        self.in_pt_contact = QLineEdit(); self.in_pt_contact.setPlaceholderText("Contact Number (Optional)")
        self.in_pt_md = QLineEdit(); self.in_pt_md.setPlaceholderText("Requesting Physician (e.g., Dr. Shaun Bautista)")

        for title_txt, widget in [
            ("Patient Full Name:", self.in_pt_name),
            ("Medical Record Number (MRN):", self.in_pt_mrn),
        ]:
            fl = QLabel(title_txt); fl.setObjectName("FieldLabel")
            ll.addWidget(fl); ll.addWidget(widget)

        fl_ds = QLabel("Date of Birth / Age & Sex:"); fl_ds.setObjectName("FieldLabel")
        ll.addWidget(fl_ds)
        r_ds = QHBoxLayout()
        r_ds.addWidget(self.in_pt_dob, 2)
        r_ds.addWidget(self.cmb_pt_sex, 1)
        ll.addLayout(r_ds)

        for title_txt, widget in [
            ("Contact Number:", self.in_pt_contact),
            ("Requesting Physician:", self.in_pt_md),
        ]:
            fl = QLabel(title_txt); fl.setObjectName("FieldLabel")
            ll.addWidget(fl); ll.addWidget(widget)

        fl_pr = QLabel("Order Priority & Bench Rack Slot:"); fl_pr.setObjectName("FieldLabel")
        ll.addWidget(fl_pr)
        r_pr = QHBoxLayout()
        self.cmb_req_priority = QComboBox(); self.cmb_req_priority.addItems(["Routine", "STAT", "Urgent"])
        self.in_req_slot = QLineEdit("Bench Rack A1")
        r_pr.addWidget(self.cmb_req_priority, 1)
        r_pr.addWidget(self.in_req_slot, 1)
        ll.addLayout(r_pr)

        ll.addSpacing(6)
        self.btn_submit_req = QPushButton("Create Order (0 Assays)")
        self.btn_submit_req.setObjectName("SuccessBtn")
        self.btn_submit_req.setMinimumHeight(42)
        self.btn_submit_req.clicked.connect(self._submit_requisition)
        ll.addWidget(self.btn_submit_req)
        ll.addStretch()

        left_scroll.setWidget(left)

        right = QFrame()
        right.setObjectName("SurfaceCard")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(18, 16, 18, 16)
        rl.setSpacing(10)

        lbl2 = QLabel("2. Select Panels & Assays")
        lbl2.setObjectName("SectionHeader")
        rl.addWidget(lbl2)

        panel_grid = QGridLayout()
        panel_grid.setSpacing(6)
        for idx, (p_name, tests_list) in enumerate(PRESET_PANELS.items()):
            b = QPushButton(f"+ {p_name}")
            b.clicked.connect(lambda checked=False, tl=tests_list: self._apply_preset_panel(tl))
            panel_grid.addWidget(b, idx // 3, idx % 3)
        rl.addLayout(panel_grid)

        filter_row = QHBoxLayout()
        self.in_assay_filter = QLineEdit()
        self.in_assay_filter.setPlaceholderText("Filter assays by name, department, or tube...")
        self.in_assay_filter.textChanged.connect(self._filter_assay_checkboxes)
        filter_row.addWidget(self.in_assay_filter, 3)

        btn_clr = QPushButton("Clear All")
        btn_clr.clicked.connect(self._clear_test_checks)
        filter_row.addWidget(btn_clr)
        rl.addLayout(filter_row)

        scroll = QScrollArea()
        scroll.setObjectName("DarkScroll")
        scroll.setWidgetResizable(True)

        chk_container = QWidget()
        chk_container.setObjectName("ScrollContent")
        self.chk_list_layout = QVBoxLayout(chk_container)
        self.chk_list_layout.setContentsMargins(10, 8, 10, 8)
        self.chk_list_layout.setSpacing(2)

        self.test_checkboxes = {}
        self.assay_row_widgets = []
        scroll.setWidget(chk_container)
        rl.addWidget(scroll, 1)

        lay.addWidget(left_scroll, 2)
        lay.addWidget(right, 3)
        return w

    def _filter_req_patients(self, text: str):
        q = text.strip().lower()
        cur_pid = self.cmb_req_patient.currentData()
        conn = get_conn()
        pts = conn.execute("SELECT id, full_name, mrn FROM patients ORDER BY full_name ASC").fetchall()
        conn.close()

        self.cmb_req_patient.blockSignals(True)
        self.cmb_req_patient.clear()
        self.cmb_req_patient.addItem("-- New Patient --", None)
        for p in pts:
            label = f"{p['full_name']} ({p['mrn']})"
            if not q or q in label.lower():
                self.cmb_req_patient.addItem(label, p["id"])
        if cur_pid:
            idx = self.cmb_req_patient.findData(cur_pid)
            if idx >= 0:
                self.cmb_req_patient.setCurrentIndex(idx)
        self.cmb_req_patient.blockSignals(False)

    def _on_req_patient_pick(self):
        pid = self.cmb_req_patient.currentData()
        if not pid:
            self.in_pt_name.clear()
            self.in_pt_mrn.clear()
            self.in_pt_dob.clear()
            self.in_pt_contact.clear()
            self.in_pt_md.clear()
            return
        conn = get_conn()
        pt = conn.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
        conn.close()
        if pt:
            self.in_pt_name.setText(pt["full_name"])
            self.in_pt_mrn.setText(pt["mrn"])
            self.in_pt_dob.setText(pt["dob"] or "")
            self.cmb_pt_sex.setCurrentText(pt["sex"] or "Female")
            self.in_pt_contact.setText(pt["contact"] or "")
            self.in_pt_md.setText(pt["physician"] or "")

    def _update_selected_assay_count(self):
        cnt = sum(1 for cb in self.test_checkboxes.values() if cb.isChecked())
        self.btn_submit_req.setText(f"Create Order ({cnt} Assay{'s' if cnt != 1 else ''})")

    def _filter_assay_checkboxes(self, text: str):
        q = text.strip().lower()
        for row_widget, search_blob in self.assay_row_widgets:
            row_widget.setVisible(not q or q in search_blob)

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
            show_warn(self, "Missing Patient Name", "Enter or select a patient name.")
            return
        selected_tests = [t for t, cb in self.test_checkboxes.items() if cb.isChecked()]
        if not selected_tests:
            show_warn(self, "No Assays Selected", "Select at least one test or preset panel.")
            return

        mrn = self.in_pt_mrn.text().strip() or f"MRN-{random.randint(100000, 999999)}"
        dob_val = self.in_pt_dob.text().strip()
        sex_val = self.cmb_pt_sex.currentText()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        spec_id = f"MDL-{datetime.now().strftime('%y%m%d')}-{random.randint(1000, 9999)}"

        conn = get_conn()
        cur = conn.cursor()
        existing = cur.execute("SELECT id FROM patients WHERE mrn = ?", (mrn,)).fetchone()
        if existing:
            pid = existing["id"]
            cur.execute(
                "UPDATE patients SET full_name=?, dob=?, sex=?, contact=?, physician=? WHERE id=?",
                (name, dob_val, sex_val, self.in_pt_contact.text().strip(), self.in_pt_md.text().strip(), pid)
            )
        else:
            cur.execute(
                "INSERT INTO patients (mrn, full_name, dob, sex, contact, physician, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mrn, name, dob_val, sex_val, self.in_pt_contact.text().strip(), self.in_pt_md.text().strip(), now)
            )
            pid = cur.lastrowid

        first_order_id = None
        for t_name in selected_tests:
            t_info = cur.execute("SELECT * FROM tests WHERE test_name = ?", (t_name,)).fetchone()
            _, _, _, _, ref_lbl, _ = resolve_patient_interval(conn, t_name, sex_val, dob_val)
            cur.execute("""
                INSERT INTO orders (
                    specimen_id, patient_id, test_name, department, priority, status,
                    unit, ref_range, tube_type, ordered_by, ordered_at, storage_slot
                ) VALUES (?, ?, ?, ?, ?, 'Ordered', ?, ?, ?, ?, ?, ?)
            """, (
                spec_id, pid, t_name, t_info["department"], self.cmb_req_priority.currentText(),
                t_info["unit"], ref_lbl, t_info["tube_type"],
                self.user["name"], now, self.in_req_slot.text().strip()
            ))
            if first_order_id is None:
                first_order_id = cur.lastrowid

        conn.commit()
        conn.close()
        log_audit(self.user["name"], "REQUISITION_CREATED", spec_id, f"{name} ({len(selected_tests)} assays)")
        self._clear_test_checks()
        self.selected_order_id = first_order_id
        self.refresh_all()
        if first_order_id:
            self._load_inspector_order(first_order_id, animate_from_center=False)
        self.tabs.setCurrentIndex(0)
        show_info(self, "Order Created", f"Specimen ID: {spec_id}\nPatient: {name}\nAssays Queued: {len(selected_tests)}")

    # --------------------------------------------------------------------------
    # TAB 3: PATIENTS REGISTRATION & DIRECTORY
    # --------------------------------------------------------------------------
    def _build_patients_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(14)

        reg_scroll = QScrollArea()
        reg_scroll.setObjectName("DarkScroll")
        reg_scroll.setWidgetResizable(True)

        reg_card = QWidget()
        reg_card.setObjectName("CardScrollContent")
        rl = QVBoxLayout(reg_card)
        rl.setContentsMargins(18, 16, 18, 16)
        rl.setSpacing(10)

        self.lbl_pt_form_title = QLabel("Register New Patient")
        self.lbl_pt_form_title.setObjectName("SectionHeader")
        rl.addWidget(self.lbl_pt_form_title)

        sub = QLabel("Create a new patient record or click a row on the right to update details.")
        sub.setObjectName("MutedLabel")
        sub.setWordWrap(True)
        rl.addWidget(sub)

        self.reg_name = QLineEdit(); self.reg_name.setPlaceholderText("Full Name (Last, First MI)")
        self.reg_mrn = QLineEdit(); self.reg_mrn.setPlaceholderText("MRN (auto-generated if blank)")
        self.reg_dob = QLineEdit(); self.reg_dob.setPlaceholderText("YYYY-MM-DD or Age (e.g. 34y, 6m)")
        self.reg_sex = QComboBox(); self.reg_sex.addItems(["Female", "Male", "Other"])
        self.reg_contact = QLineEdit(); self.reg_contact.setPlaceholderText("Phone / Mobile Number")
        self.reg_md = QLineEdit(); self.reg_md.setPlaceholderText("Attending / Requesting Physician")

        for label_txt, widget in [
            ("Full Name:", self.reg_name),
            ("Medical Record Number (MRN):", self.reg_mrn),
            ("Date of Birth / Age:", self.reg_dob),
            ("Sex:", self.reg_sex),
            ("Contact Number:", self.reg_contact),
            ("Requesting Physician:", self.reg_md),
        ]:
            fl = QLabel(label_txt); fl.setObjectName("FieldLabel")
            rl.addWidget(fl); rl.addWidget(widget)

        rl.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_save_pt = QPushButton("Save Patient")
        btn_save_pt.setObjectName("SuccessBtn")
        btn_save_pt.setMinimumHeight(38)
        btn_save_pt.clicked.connect(self._save_patient_profile)
        btn_row.addWidget(btn_save_pt, 2)

        btn_clear_pt = QPushButton("Clear")
        btn_clear_pt.setMinimumHeight(38)
        btn_clear_pt.clicked.connect(self._clear_patient_form)
        btn_row.addWidget(btn_clear_pt, 1)
        rl.addLayout(btn_row)

        btn_open_hist = QPushButton("View Selected Patient Lab History")
        btn_open_hist.setObjectName("PrimaryBtn")
        btn_open_hist.setMinimumHeight(36)
        btn_open_hist.clicked.connect(self._open_registry_selected_history)
        rl.addWidget(btn_open_hist)

        rl.addStretch()
        reg_scroll.setWidget(reg_card)

        dir_card = QFrame()
        dir_card.setObjectName("SurfaceCard")
        dl = QVBoxLayout(dir_card)
        dl.setContentsMargins(16, 16, 16, 16)
        dl.setSpacing(10)

        top = QHBoxLayout()
        lbl_dir = QLabel("Registered Patients")
        lbl_dir.setObjectName("SectionHeader")
        top.addWidget(lbl_dir)
        top.addStretch()

        self.in_pt_search = QLineEdit()
        self.in_pt_search.setPlaceholderText("Search name, MRN, or physician...")
        self.in_pt_search.setMinimumWidth(260)
        self.in_pt_search.textChanged.connect(self.refresh_patients)
        top.addWidget(self.in_pt_search)
        dl.addLayout(top)

        self.tbl_patients = QTableWidget(0, 7)
        self.tbl_patients.setHorizontalHeaderLabels(["ID", "MRN", "Full Name", "DOB / Age", "Sex", "Contact", "Physician"])
        self.tbl_patients.setColumnHidden(0, True)
        p_hdr = self.tbl_patients.horizontalHeader()
        p_hdr.setSectionResizeMode(QHeaderView.Interactive)
        p_hdr.setStretchLastSection(True)
        self.tbl_patients.setColumnWidth(1, 115)
        self.tbl_patients.setColumnWidth(2, 200)
        self.tbl_patients.setColumnWidth(3, 100)
        self.tbl_patients.setColumnWidth(4, 70)
        self.tbl_patients.setColumnWidth(5, 115)
        self.tbl_patients.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_patients.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_patients.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_patients.setAlternatingRowColors(True)
        self.tbl_patients.setWordWrap(True)
        self.tbl_patients.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tbl_patients.itemSelectionChanged.connect(self._on_patient_row_selected)
        self.tbl_patients.doubleClicked.connect(self._on_patient_double_click)
        dl.addWidget(self.tbl_patients, 1)

        lay.addWidget(reg_scroll, 2)
        lay.addWidget(dir_card, 3)
        return w

    def _clear_patient_form(self):
        self.editing_patient_id = None
        self.lbl_pt_form_title.setText("Register New Patient")
        self.reg_name.clear()
        self.reg_mrn.clear()
        self.reg_dob.clear()
        self.reg_sex.setCurrentIndex(0)
        self.reg_contact.clear()
        self.reg_md.clear()
        self.tbl_patients.clearSelection()

    def _on_patient_row_selected(self):
        rows = self.tbl_patients.selectionModel().selectedRows()
        if not rows:
            return
        pid = int(self.tbl_patients.item(rows[0].row(), 0).text())
        conn = get_conn()
        pt = conn.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
        conn.close()
        if not pt:
            return
        self.editing_patient_id = pid
        self.lbl_pt_form_title.setText("Edit Patient Profile")
        self.reg_name.setText(pt["full_name"] or "")
        self.reg_mrn.setText(pt["mrn"] or "")
        self.reg_dob.setText(pt["dob"] or "")
        self.reg_sex.setCurrentText(pt["sex"] or "Female")
        self.reg_contact.setText(pt["contact"] or "")
        self.reg_md.setText(pt["physician"] or "")

    def _save_patient_profile(self):
        name = self.reg_name.text().strip()
        if not name:
            show_warn(self, "Missing Name", "Patient full name is required.")
            return
        mrn = self.reg_mrn.text().strip() or f"MRN-{random.randint(100000, 999999)}"
        dob = self.reg_dob.text().strip()
        sex = self.reg_sex.currentText()
        contact = self.reg_contact.text().strip()
        md = self.reg_md.text().strip()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_conn()
        try:
            if self.editing_patient_id:
                conn.execute(
                    "UPDATE patients SET mrn=?, full_name=?, dob=?, sex=?, contact=?, physician=? WHERE id=?",
                    (mrn, name, dob, sex, contact, md, self.editing_patient_id)
                )
                action = "PATIENT_UPDATED"
            else:
                conn.execute(
                    "INSERT INTO patients (mrn, full_name, dob, sex, contact, physician, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (mrn, name, dob, sex, contact, md, now)
                )
                action = "PATIENT_REGISTERED"
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            show_warn(self, "Duplicate MRN", f"MRN '{mrn}' already belongs to another patient.")
            return
        conn.close()

        log_audit(self.user["name"], action, "-", f"{name} ({mrn})")
        self._clear_patient_form()
        self.refresh_all()
        show_info(self, "Patient Saved", f"Patient record saved:\n{name} ({mrn})")

    def _open_registry_selected_history(self):
        rows = self.tbl_patients.selectionModel().selectedRows()
        if not rows:
            show_info(self, "Select Patient", "Select a patient row from the directory first.")
            return
        pid = int(self.tbl_patients.item(rows[0].row(), 0).text())
        PatientHistoryDialog(pid, self).exec()

    def _on_patient_double_click(self, idx):
        pid = int(self.tbl_patients.item(idx.row(), 0).text())
        PatientHistoryDialog(pid, self).exec()

    # --------------------------------------------------------------------------
    # TAB 4: PATHOLOGIST REVIEW & CO-SIGN
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
        info.setStyleSheet("font-weight: 600;")
        info.setWordWrap(True)
        bl.addWidget(info)
        lay.addWidget(banner)

        self.tbl_path = QTableWidget(0, 7)
        self.tbl_path.setHorizontalHeaderLabels(["ID", "Specimen ID", "Patient", "Assay", "Result", "Flag / Trigger", "Co-Sign Status"])
        self.tbl_path.setColumnHidden(0, True)
        self.tbl_path.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_path.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_path.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_path.setWordWrap(True)
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
            show_info(self, "Select Case", "Select a specimen row to co-sign.")
            return
        if self.user["pin"] != "1111" and "Pathologist" not in self.user["role"]:
            if not ask_confirm(
                self, "Pathologist Signature",
                "You are logged in as RMT. Record co-signature for Gaia Aubrey Manalo, MD?"
            ):
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
    # TAB 5: QUALITY CONTROL (SCROLLABLE & ZOOMABLE LEVEY-JENNINGS)
    # --------------------------------------------------------------------------
    def _build_qc_tab(self) -> QWidget:
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)

        self.qc_scroll = QScrollArea()
        self.qc_scroll.setObjectName("DarkScroll")
        self.qc_scroll.setWidgetResizable(True)
        self.qc_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.qc_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.qc_scroll.viewport().installEventFilter(self)

        self.qc_inner = QWidget()
        self.qc_inner.setObjectName("CardScrollContent")
        lay = QVBoxLayout(self.qc_inner)
        lay.setContentsMargins(14, 14, 14, 14)
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

        btn_z_out = QPushButton("-")
        btn_z_out.setFixedWidth(34)
        btn_z_out.setToolTip("Zoom Out QC View (or Ctrl + Scroll)")
        btn_z_out.clicked.connect(lambda: self._set_qc_zoom(self.qc_zoom_factor - 0.15))

        self.lbl_qc_zoom = QLabel("100%")
        self.lbl_qc_zoom.setObjectName("MonoBadge")

        btn_z_in = QPushButton("+")
        btn_z_in.setFixedWidth(34)
        btn_z_in.setToolTip("Zoom In QC View (or Ctrl + Scroll)")
        btn_z_in.clicked.connect(lambda: self._set_qc_zoom(self.qc_zoom_factor + 0.15))

        btn_z_reset = QPushButton("100%")
        btn_z_reset.setToolTip("Reset QC Zoom to 100%")
        btn_z_reset.clicked.connect(lambda: self._set_qc_zoom(1.0))

        cl.addWidget(btn_z_out)
        cl.addWidget(self.lbl_qc_zoom)
        cl.addWidget(btn_z_in)
        cl.addWidget(btn_z_reset)

        lay.addWidget(ctrl_bar)

        self.qc_canvas = MplCanvas(width=8.5, height=3.4, dpi=100)
        self.qc_canvas.setMinimumHeight(340)
        lay.addWidget(self.qc_canvas)

        self.tbl_qc = QTableWidget(0, 6)
        self.tbl_qc.setHorizontalHeaderLabels(["Timestamp", "Control Lot", "Measured", "Z-Score", "Westgard Status", "Operator"])
        self.tbl_qc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_qc.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_qc.setMinimumHeight(240)
        lay.addWidget(self.tbl_qc)

        self.qc_scroll.setWidget(self.qc_inner)
        outer_lay.addWidget(self.qc_scroll, 1)
        return outer

    def eventFilter(self, obj, event):
        if hasattr(self, "qc_scroll") and obj is self.qc_scroll.viewport() and event.type() == QEvent.Wheel:
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                step = 0.15 if delta > 0 else -0.15
                self._set_qc_zoom(self.qc_zoom_factor + step)
                return True
        return super().eventFilter(obj, event)

    def _set_qc_zoom(self, zoom: float):
        clamped = max(0.70, min(2.00, round(zoom, 2)))
        self.qc_zoom_factor = clamped
        if hasattr(self, "lbl_qc_zoom"):
            self.lbl_qc_zoom.setText(f"{int(round(clamped * 100))}%")
        if hasattr(self, "qc_canvas"):
            self.qc_canvas.setMinimumHeight(int(340 * clamped))
        if hasattr(self, "tbl_qc"):
            self.tbl_qc.setMinimumHeight(int(240 * clamped))
        self.refresh_qc()

    def _toggle_qc_lockout(self, state: bool):
        self.qc_lockout_enabled = state
        self._update_qc_pill()

    def _update_qc_pill(self):
        if self.qc_lockout_enabled and self.failed_qc_tests:
            self.lbl_qc_pill.setText(f"QC Lockout: {len(self.failed_qc_tests)} Assay(s)")
            self.lbl_qc_pill.setStyleSheet(
                "background-color: rgba(244,63,94,0.18); border: 1px solid #F43F5E; "
                "color: #F43F5E; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 8.5pt;"
            )
        else:
            self.lbl_qc_pill.setText("QC: In Control")
            self.lbl_qc_pill.setStyleSheet(
                "background-color: rgba(16,185,129,0.16); border: 1px solid #10B981; "
                "color: #10B981; border-radius: 6px; padding: 3px 10px; font-weight: 600; font-size: 8.5pt;"
            )

    def _log_qc_run(self):
        label = self.cmb_qc_target.currentText()
        try:
            measured = float(self.in_qc_val.text().strip())
        except Exception:
            show_warn(self, "Invalid Number", "Enter a valid numeric QC measurement.")
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
            show_error(
                self, "Westgard 1-3s Violation",
                f"Control: {label}\nMeasured: {measured} {t['unit']} (Z = {z:+.2f} SD)\n\n"
                f"Exceeds +/- 3 SD limits. Recalibrate before releasing patient results."
            )

    def refresh_qc(self):
        t_style = THEMES[CURRENT_THEME]
        label = self.cmb_qc_target.currentText()
        conn = get_conn()
        target = conn.execute("SELECT * FROM qc_targets WHERE label = ?", (label,)).fetchone()
        logs = conn.execute("SELECT * FROM qc_logs WHERE label = ? ORDER BY id DESC LIMIT 20", (label,)).fetchall()
        conn.close()

        self.tbl_qc.setRowCount(len(logs))
        for i, r in enumerate(logs):
            self.tbl_qc.setItem(i, 0, _make_item(r["logged_at"]))
            self.tbl_qc.setItem(i, 1, _make_item(r["label"]))
            self.tbl_qc.setItem(i, 2, _make_item(f"{r['measured']:g}"))
            self.tbl_qc.setItem(i, 3, _make_item(f"{r['z_score']:+.2f} SD"))
            st_col = "#E11D48" if "FAIL" in r["westgard_status"] else ("#D97706" if "WARN" in r["westgard_status"] else "#059669")
            self.tbl_qc.setItem(i, 4, _make_item(r["westgard_status"], st_col))
            self.tbl_qc.setItem(i, 5, _make_item(r["operator"]))

        ax = self.qc_canvas.ax
        ax.clear()
        self.qc_canvas._style_ax(ax)

        title_sz = max(8, int(round(10 * self.qc_zoom_factor)))
        tick_sz = max(7, int(round(8 * self.qc_zoom_factor)))
        ax.tick_params(colors=t_style["muted"], labelsize=tick_sz)

        if target:
            mean, sd = target["target_mean"], target["sd"]
            ax.axhspan(mean - sd, mean + sd, color="#10B981", alpha=0.14)
            ax.axhline(mean, color="#10B981", linewidth=1.3, label=f"Mean ({mean})")
            ax.axhline(mean + 2 * sd, color="#F59E0B", linestyle="--", linewidth=1.0, label="+/- 2 SD (Warn)")
            ax.axhline(mean - 2 * sd, color="#F59E0B", linestyle="--", linewidth=1.0)
            ax.axhline(mean + 3 * sd, color="#F43F5E", linestyle=":", linewidth=1.2, label="+/- 3 SD (1-3s)")
            ax.axhline(mean - 3 * sd, color="#F43F5E", linestyle=":", linewidth=1.2)

            pts = list(reversed(logs))
            if pts:
                xs = [f"#{idx+1}" for idx in range(len(pts))]
                ys = [p["measured"] for p in pts]
                ax.plot(xs, ys, color="#0284C7", marker="o", linewidth=2.0 * self.qc_zoom_factor, markersize=6 * self.qc_zoom_factor)
                for p_row, x_lbl, y_val in zip(pts, xs, ys):
                    pt_col = "#E11D48" if "FAIL" in p_row["westgard_status"] else ("#D97706" if "WARN" in p_row["westgard_status"] else "#0284C7")
                    ax.plot(x_lbl, y_val, marker="o", color=pt_col, markersize=7 * self.qc_zoom_factor)

            ax.set_title(f"Levey-Jennings Chart — {label} ({target['unit']})", fontsize=title_sz, fontweight="bold")
            ax.grid(True, color=t_style["chart_grid"], linestyle=":", linewidth=0.8)
            ax.legend(loc="upper left", facecolor=t_style["surface"], edgecolor=t_style["border_strong"], labelcolor=t_style["text"], fontsize=tick_sz)

        self.qc_canvas.fig.tight_layout()
        self.qc_canvas.draw()

    # --------------------------------------------------------------------------
    # TAB 6: TEST CATALOG & DEMOGRAPHIC REFERENCE INTERVALS
    # --------------------------------------------------------------------------
    def _build_catalog_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        card = QFrame()
        card.setObjectName("SurfaceCard")
        grid = QGridLayout(card)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setSpacing(8)

        self.cat_name = QLineEdit(); self.cat_name.setPlaceholderText("Test Name (e.g., HbA1c)")
        self.cat_dept = QComboBox()
        self.cat_dept.addItems([
            "Hematology", "Clinical Chemistry", "Coagulation",
            "Immunology", "Serology", "Clinical Microscopy", "Microbiology"
        ])
        self.cat_unit = QLineEdit(); self.cat_unit.setPlaceholderText("Unit (e.g., %)")
        self.cat_low = QLineEdit(); self.cat_low.setPlaceholderText("Low (e.g., 4.0)")
        self.cat_high = QLineEdit(); self.cat_high.setPlaceholderText("High (e.g., 5.6)")
        self.cat_crit_hi = QLineEdit(); self.cat_crit_hi.setPlaceholderText("Crit High (opt)")
        self.cat_tube = QComboBox()
        self.cat_tube.addItems(list(TUBE_COLORS.keys()))
        btn_add = QPushButton("Add / Update Test")
        btn_add.setObjectName("PrimaryBtn")
        btn_add.clicked.connect(self._save_catalog_test)

        btn_demo_ranges = QPushButton("Age / Sex Ranges...")
        btn_demo_ranges.setToolTip("Configure age- and sex-specific clinical reference intervals for the selected assay")
        btn_demo_ranges.clicked.connect(self._open_demographic_range_editor)

        grid.addWidget(QLabel("Test Name:"), 0, 0); grid.addWidget(self.cat_name, 0, 1)
        grid.addWidget(QLabel("Department:"), 0, 2); grid.addWidget(self.cat_dept, 0, 3)
        grid.addWidget(QLabel("Unit:"), 0, 4); grid.addWidget(self.cat_unit, 0, 5)
        grid.addWidget(QLabel("Low:"), 1, 0); grid.addWidget(self.cat_low, 1, 1)
        grid.addWidget(QLabel("High:"), 1, 2); grid.addWidget(self.cat_high, 1, 3)
        grid.addWidget(QLabel("Tube:"), 1, 4); grid.addWidget(self.cat_tube, 1, 5)
        grid.addWidget(QLabel("Crit High:"), 2, 0); grid.addWidget(self.cat_crit_hi, 2, 1)
        grid.addWidget(btn_demo_ranges, 2, 2, 1, 2)
        grid.addWidget(btn_add, 2, 4, 1, 2)
        lay.addWidget(card)

        self.tbl_catalog = QTableWidget(0, 7)
        self.tbl_catalog.setHorizontalHeaderLabels(["Assay", "Department", "Unit", "Default Ref.", "Crit High", "Delta %", "Collection Tube"])
        c_hdr = self.tbl_catalog.horizontalHeader()
        c_hdr.setSectionResizeMode(QHeaderView.Interactive)
        c_hdr.setStretchLastSection(True)
        self.tbl_catalog.setColumnWidth(0, 230)
        self.tbl_catalog.setColumnWidth(1, 145)
        self.tbl_catalog.setColumnWidth(2, 85)
        self.tbl_catalog.setColumnWidth(3, 130)
        self.tbl_catalog.setColumnWidth(4, 85)
        self.tbl_catalog.setColumnWidth(5, 80)
        self.tbl_catalog.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_catalog.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tbl_catalog.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_catalog.setAlternatingRowColors(True)
        self.tbl_catalog.setWordWrap(True)
        self.tbl_catalog.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tbl_catalog.doubleClicked.connect(self._on_catalog_double_click)
        lay.addWidget(self.tbl_catalog, 1)
        return w

    def _on_catalog_double_click(self, idx):
        t_name = self.tbl_catalog.item(idx.row(), 0).text()
        self.cat_name.setText(t_name)
        self._open_demographic_range_editor()

    def _open_demographic_range_editor(self):
        t_name = self.cat_name.text().strip()
        if not t_name:
            rows = self.tbl_catalog.selectionModel().selectedRows()
            if rows:
                t_name = self.tbl_catalog.item(rows[0].row(), 0).text()
        if not t_name:
            show_info(self, "Select Assay", "Select an assay in the catalog table first.")
            return
        ReferenceRangeEditorDialog(t_name, self.user["name"], self).exec()
        self.refresh_worklist()
        if self.selected_order_id:
            self._load_inspector_order(self.selected_order_id, animate_from_center=False)

    def _save_catalog_test(self):
        t_name = self.cat_name.text().strip()
        if not t_name:
            return
        dept = self.cat_dept.currentText()
        unit = self.cat_unit.text().strip() or "-"
        tube = self.cat_tube.currentText()

        def _f(w):
            try:
                return float(w.text().strip())
            except Exception:
                return None

        lo, hi, chi = _f(self.cat_low), _f(self.cat_high), _f(self.cat_crit_hi)
        ref_str = f"{lo:g} - {hi:g}" if (lo is not None and hi is not None) else "Qualitative / Profile"

        conn = get_conn()
        conn.execute("""
            INSERT INTO tests (test_name, department, unit, low_val, high_val, crit_high, tube_type, ref_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(test_name) DO UPDATE SET
                department=excluded.department, unit=excluded.unit,
                low_val=excluded.low_val, high_val=excluded.high_val,
                crit_high=excluded.crit_high, tube_type=excluded.tube_type,
                ref_range=excluded.ref_range
        """, (t_name, dept, unit, lo, hi, chi, tube, ref_str))
        conn.commit()
        conn.close()
        log_audit(self.user["name"], "CATALOG_TEST_SAVED", "-", f"{t_name} ({ref_str})")
        self.cat_name.clear(); self.cat_unit.clear(); self.cat_low.clear(); self.cat_high.clear(); self.cat_crit_hi.clear()
        self.refresh_all()

    # --------------------------------------------------------------------------
    # TAB 7: ADMIN MODE — HANDOVER, CSV EXPORT, STAFF, NETWORK SYNC & AUDIT
    # --------------------------------------------------------------------------
    def _build_admin_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        top = QFrame()
        top.setObjectName("SurfaceCard")
        tl = QHBoxLayout(top)

        btn_seed = QPushButton("Load Sample Clinical Cases")
        btn_seed.setObjectName("PrimaryBtn")
        btn_seed.setToolTip("Populate sample clinical cases, serial trends, microscopy, antibiogram, STATs & QC")
        btn_seed.clicked.connect(self._seed_sample_cases)
        tl.addWidget(btn_seed)

        btn_handover = QPushButton("Generate Shift Handover PDF")
        btn_handover.setObjectName("PrimaryBtn")
        btn_handover.clicked.connect(self._generate_handover)
        tl.addWidget(btn_handover)

        btn_csv = QPushButton("Export Worklist CSV")
        btn_csv.clicked.connect(self._export_csv)
        tl.addWidget(btn_csv)

        btn_db = QPushButton("Switch / Connect Shared DB...")
        btn_db.clicked.connect(self._switch_shared_db)
        tl.addWidget(btn_db)

        self.lbl_db_path = QLabel(f"DB: {get_db_path()}")
        self.lbl_db_path.setObjectName("MonoBadge")
        tl.addWidget(self.lbl_db_path)
        lay.addWidget(top)

        sub_tabs = QTabWidget()

        staff_w = QWidget()
        sl = QVBoxLayout(staff_w)
        s_form = QGridLayout()
        self.st_pin = QLineEdit(); self.st_pin.setPlaceholderText("4-digit PIN (e.g., 0013)")
        self.st_name = QLineEdit(); self.st_name.setPlaceholderText("Full Name + Credentials")
        self.st_role = QComboBox(); self.st_role.addItems(["Medical Technologist (RMT)", "Pathologist"])
        self.st_prc = QLineEdit(); self.st_prc.setPlaceholderText("PRC License No.")
        self.st_sig = QLineEdit(); self.st_sig.setPlaceholderText("Signature PNG path (optional)")
        btn_sig_pick = QPushButton("Browse PNG...")
        btn_sig_pick.clicked.connect(self._pick_signature_file)
        btn_st_save = QPushButton("Save Staff Member")
        btn_st_save.setObjectName("SuccessBtn")
        btn_st_save.clicked.connect(self._save_staff_member)

        s_form.addWidget(QLabel("PIN:"), 0, 0); s_form.addWidget(self.st_pin, 0, 1)
        s_form.addWidget(QLabel("Name:"), 0, 2); s_form.addWidget(self.st_name, 0, 3)
        s_form.addWidget(QLabel("Role:"), 0, 4); s_form.addWidget(self.st_role, 0, 5)
        s_form.addWidget(QLabel("PRC License:"), 1, 0); s_form.addWidget(self.st_prc, 1, 1)
        s_form.addWidget(QLabel("Signature:"), 1, 2); s_form.addWidget(self.st_sig, 1, 3)
        s_form.addWidget(btn_sig_pick, 1, 4); s_form.addWidget(btn_st_save, 1, 5)
        sl.addLayout(s_form)

        self.tbl_staff = QTableWidget(0, 5)
        self.tbl_staff.setHorizontalHeaderLabels(["PIN", "Name", "Role", "PRC License", "Signature File"])
        self.tbl_staff.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_staff.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sl.addWidget(self.tbl_staff, 1)
        sub_tabs.addTab(staff_w, "Staff & PRC Signatures")

        aud_w = QWidget()
        al = QVBoxLayout(aud_w)
        self.tbl_audit = QTableWidget(0, 5)
        self.tbl_audit.setHorizontalHeaderLabels(["Timestamp", "Operator", "Action", "Specimen ID", "Details"])
        self.tbl_audit.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_audit.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl_audit.setWordWrap(True)
        al.addWidget(self.tbl_audit, 1)
        sub_tabs.addTab(aud_w, "Audit Trail")

        lay.addWidget(sub_tabs, 1)
        return w

    def _seed_sample_cases(self):
        if not ask_confirm(
            self, "Load Sample Clinical Cases",
            "Seed realistic clinical cases (2004-2006 patient DOBs, approved physicians, sex rules, pending & verified tests, serial trends, microscopy, antibiogram, STATs & 12-day QC)?"
        ):
            return
        summary = seed_sample_clinical_cases(self.user["name"])
        self.refresh_all()
        show_info(
            self, "Sample Clinical Cases Loaded",
            f"Seeded {summary['specimens_seeded']} specimens across {summary['patients_total']} patients "
            f"(every sample patient has pending/verified coverage) and {summary['qc_points']} QC data points."
        )

    def _pick_signature_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Signature Image", "", "PNG Images (*.png)")
        if path:
            self.st_sig.setText(path)

    def _save_staff_member(self):
        pin = self.st_pin.text().strip()
        name = self.st_name.text().strip()
        if len(pin) != 4 or not pin.isdigit() or not name:
            show_warn(self, "Invalid Staff Data", "Enter a 4-digit numeric PIN and full name.")
            return
        conn = get_conn()
        conn.execute("""
            INSERT INTO staff (pin, name, role, prc_license, sig_path)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(pin) DO UPDATE SET
                name=excluded.name, role=excluded.role,
                prc_license=excluded.prc_license, sig_path=excluded.sig_path
        """, (pin, name, self.st_role.currentText(), self.st_prc.text().strip(), self.st_sig.text().strip()))
        conn.commit()
        conn.close()
        log_audit(self.user["name"], "STAFF_UPDATED", "-", f"{name} (PIN {pin})")
        self.st_pin.clear(); self.st_name.clear(); self.st_prc.clear(); self.st_sig.clear()
        self.refresh_admin()

    def _switch_shared_db(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Shared SQLite LIS Database", "", "SQLite DB (*.db *.sqlite)")
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Create Shared SQLite LIS Database", "monocytes_shared_lis.db", "SQLite DB (*.db)")
        if path:
            APP_CONFIG["db_path"] = path
            save_config(APP_CONFIG)
            init_db()
            self.lbl_db_path.setText(f"DB: {path}")
            log_audit(self.user["name"], "SHARED_DB_SWITCHED", "-", path)
            self.refresh_all()

    def _generate_handover(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Shift Handover Report")
        dlg.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(dlg)
        l = QVBoxLayout(dlg)
        l.addWidget(QLabel("Select Shift:"))
        cmb = QComboBox()
        cmb.addItems(["AM Shift (06:00 - 14:00)", "PM Shift (14:00 - 22:00)", "Night Shift (22:00 - 06:00)"])
        l.addWidget(cmb)
        b = QPushButton("Export Handover PDF")
        b.setObjectName("PrimaryBtn")
        b.clicked.connect(dlg.accept)
        l.addWidget(b)
        if dlg.exec() == QDialog.Accepted:
            path, _ = QFileDialog.getSaveFileName(self, "Save Shift Handover PDF", "Shift_Handover.pdf", "PDF Files (*.pdf)")
            if path:
                generate_shift_handover_pdf(self.user["name"], cmb.currentText(), path)
                if sys.platform == "win32":
                    os.startfile(path)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Worklist CSV", "monocytes_lis_worklist.csv", "CSV Files (*.csv)")
        if not path:
            return
        conn = get_conn()
        rows = conn.execute("""
            SELECT o.specimen_id, p.mrn, p.full_name, p.sex, p.dob, o.test_name, o.department,
                   o.priority, o.status, o.result_value, o.flag, o.unit, o.ref_range, o.verified_by, o.verified_at
            FROM orders o JOIN patients p ON o.patient_id = p.id ORDER BY o.id DESC
        """).fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Specimen ID", "MRN", "Patient", "Sex", "DOB", "Test", "Department", "Priority", "Status", "Result", "Flag", "Unit", "Ref Range", "Verified By", "Verified At"])
            for r in rows:
                w.writerow(list(r))
        show_info(self, "CSV Exported", f"Exported {len(rows)} rows to:\n{path}")

    # --------------------------------------------------------------------------
    # REFRESH ALL VIEWS
    # --------------------------------------------------------------------------
    def refresh_all(self):
        self.refresh_kpis()
        self.refresh_worklist()
        self.refresh_patient_dropdown()
        self.refresh_patients()
        self.refresh_test_checkboxes()
        self.refresh_pathologist()
        self.refresh_qc_targets()
        self.refresh_qc()
        self.refresh_catalog()
        self.refresh_admin()

    def refresh_kpis(self):
        conn = get_conn()
        total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Verified', 'Amended', 'Rejected', 'Cancelled')").fetchone()[0]
        stat_p = conn.execute("SELECT COUNT(*) FROM orders WHERE priority = 'STAT' AND status NOT IN ('Verified', 'Amended', 'Rejected', 'Cancelled')").fetchone()[0]
        verified = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Verified', 'Amended')").fetchone()[0]
        conn.close()
        self.lbl_queue_counts.setText(f"Total: {total}  |  Pending: {pending}  |  STAT: {stat_p}  |  Verified: {verified}")

    @staticmethod
    def _format_tat(row) -> str:
        fmt = "%Y-%m-%d %H:%M:%S"
        now = datetime.now()
        try:
            ord_dt = datetime.strptime(row["ordered_at"], fmt)
        except Exception:
            return "-"
        if row["verified_at"]:
            try:
                ver_dt = datetime.strptime(row["verified_at"], fmt)
                mins = max(1, int((ver_dt - ord_dt).total_seconds() // 60))
                return f"Done {mins}m"
            except Exception:
                return "Done"
        if row["collected_at"]:
            try:
                col_dt = datetime.strptime(row["collected_at"], fmt)
                bench_m = max(0, int((now - col_dt).total_seconds() // 60))
                return f"Bench {bench_m}m"
            except Exception:
                return "Bench"
        wait_m = max(0, int((now - ord_dt).total_seconds() // 60))
        return f"Coll {wait_m}m"

    def refresh_worklist(self):
        search = self.in_search.text().strip().lower()
        dept = self.cmb_dept_filter.currentText()
        st_flt = self.cmb_status_filter.currentText()

        conn = get_conn()
        rows = conn.execute("""
            SELECT o.*, p.full_name, p.mrn
            FROM orders o JOIN patients p ON o.patient_id = p.id
            ORDER BY
                CASE o.priority WHEN 'STAT' THEN 0 WHEN 'Urgent' THEN 1 ELSE 2 END,
                o.id DESC
        """).fetchall()
        conn.close()

        filtered = []
        for r in rows:
            if dept != "All Departments" and r["department"] != dept:
                continue
            if st_flt == "Pending / Active" and r["status"] in ("Verified", "Amended", "Rejected", "Cancelled"):
                continue
            if st_flt == "STAT Only" and r["priority"] != "STAT":
                continue
            if st_flt == "Critical / Abnormal" and not (
                r["critical_flag"] == 1 or (r["flag"] and any(k in r["flag"] for k in ("HIGH", "LOW", "ABNORMAL")))
            ):
                continue
            if st_flt == "Verified / Amended" and r["status"] not in ("Verified", "Amended"):
                continue
            if st_flt == "Rejected / Cancelled" and r["status"] not in ("Rejected", "Cancelled"):
                continue

            blob = f"{r['specimen_id']} {r['full_name']} {r['mrn']} {r['test_name']} {r['department']} {r['status']}".lower()
            if search and search not in blob:
                continue
            filtered.append(r)

        groups = {}
        group_order = []
        for r in filtered:
            sid = r["specimen_id"]
            if sid not in groups:
                groups[sid] = []
                group_order.append(sid)
            groups[sid].append(r)

        t_style = THEMES[CURRENT_THEME]
        is_dark = (CURRENT_THEME == "dark")
        group_bg = QBrush(QColor(t_style["group_row"]))

        self.tbl_worklist.blockSignals(True)
        self.tbl_worklist.clear()

        target_child_item = None
        first_selectable_child = None

        for sid in group_order:
            items = groups[sid]
            first = items[0]
            has_stat = any(x["priority"] == "STAT" for x in items)
            has_crit = any(
                x["critical_flag"] == 1 or (x["flag"] and any(k in x["flag"] for k in ("HIGH", "LOW", "ABNORMAL")))
                for x in items
            )
            ver_cnt = sum(1 for x in items if x["status"] in ("Verified", "Amended"))
            rej_can_cnt = sum(1 for x in items if x["status"] in ("Rejected", "Cancelled"))

            if len(items) == 1:
                r = first
                top = QTreeWidgetItem([
                    r["specimen_id"],
                    r["full_name"],
                    r["test_name"],
                    r["department"],
                    r["priority"],
                    self._format_tat(r),
                    r["result_value"] or "-",
                    r["flag"] or r["status"]
                ])
                top.setData(0, Qt.UserRole, r["id"])
                top.setData(0, Qt.UserRole + 1, r["specimen_id"])
                self._apply_row_colors(top, r, is_dark)
                for c in range(8):
                    top.setToolTip(c, f"{r['specimen_id']} | {r['full_name']} ({r['mrn']}) | {r['test_name']} | {r['status']}")
                self.tbl_worklist.addTopLevelItem(top)
                if first_selectable_child is None:
                    first_selectable_child = top
                if self.selected_order_id == r["id"]:
                    target_child_item = top
            else:
                if ver_cnt + rej_can_cnt == len(items):
                    grp_status = f"Done ({ver_cnt}/{len(items)})"
                else:
                    grp_status = f"{ver_cnt}/{len(items)} Verified"

                top = QTreeWidgetItem([
                    sid,
                    first["full_name"],
                    f"{len(items)} Tests (Double-click for Batch)",
                    first["department"],
                    "STAT" if has_stat else first["priority"],
                    self._format_tat(first),
                    f"{len(items)} assays",
                    grp_status
                ])
                top.setData(0, Qt.UserRole, first["id"])
                top.setData(0, Qt.UserRole + 1, sid)
                for c in range(8):
                    top.setBackground(c, group_bg)
                    top.setFont(c, QFont("Segoe UI", 9, QFont.Bold))
                if has_crit:
                    top.setForeground(7, QColor("#F43F5E" if is_dark else "#E11D48"))
                elif ver_cnt == len(items):
                    top.setForeground(7, QColor("#34D399" if is_dark else "#059669"))
                else:
                    top.setForeground(7, QColor("#38BDF8" if is_dark else "#0284C7"))

                self.tbl_worklist.addTopLevelItem(top)

                for r in items:
                    child = QTreeWidgetItem([
                        "└─ " + r["specimen_id"],
                        r["full_name"],
                        r["test_name"],
                        r["department"],
                        r["priority"],
                        self._format_tat(r),
                        r["result_value"] or "-",
                        r["flag"] or r["status"]
                    ])
                    child.setData(0, Qt.UserRole, r["id"])
                    child.setData(0, Qt.UserRole + 1, r["specimen_id"])
                    self._apply_row_colors(child, r, is_dark)
                    for c in range(8):
                        child.setToolTip(c, f"{r['specimen_id']} | {r['full_name']} ({r['mrn']}) | {r['test_name']} | {r['status']}")
                    top.addChild(child)
                    if first_selectable_child is None:
                        first_selectable_child = child
                    if self.selected_order_id == r["id"]:
                        target_child_item = child

                top.setExpanded(sid not in self.collapsed_specimens)

        self.tbl_worklist.blockSignals(False)

        chosen = target_child_item or first_selectable_child
        if chosen is not None:
            self.tbl_worklist.setCurrentItem(chosen)
            chosen.setSelected(True)
            oid = chosen.data(0, Qt.UserRole)
            if oid and self.selected_order_id is None:
                self._load_inspector_order(int(oid), animate_from_center=False)

    @staticmethod
    def _apply_row_colors(item: QTreeWidgetItem, r, is_dark: bool):
        if r["priority"] == "STAT" and r["status"] not in ("Verified", "Amended", "Rejected", "Cancelled"):
            item.setForeground(4, QColor("#F43F5E" if is_dark else "#E11D48"))

        st_col = None
        if r["critical_flag"] == 1 or (r["flag"] and "CRITICAL" in r["flag"]):
            st_col = "#F43F5E" if is_dark else "#E11D48"
        elif r["flag"] in ("HIGH", "ABNORMAL"):
            st_col = "#FB923C" if is_dark else "#EA580C"
        elif r["flag"] == "LOW":
            st_col = "#FBBF24" if is_dark else "#D97706"
        elif r["status"] in ("Verified", "Amended"):
            st_col = "#34D399" if is_dark else "#059669"
        elif r["status"] in ("Rejected", "Cancelled"):
            st_col = "#94A3B8" if is_dark else "#64748B"

        if st_col:
            item.setForeground(7, QColor(st_col))

    def refresh_patient_dropdown(self):
        cur = self.cmb_req_patient.currentData()
        conn = get_conn()
        pts = conn.execute("SELECT id, full_name, mrn FROM patients ORDER BY full_name ASC").fetchall()
        conn.close()
        self.cmb_req_patient.blockSignals(True)
        self.cmb_req_patient.clear()
        self.cmb_req_patient.addItem("-- New Patient --", None)
        for p in pts:
            self.cmb_req_patient.addItem(f"{p['full_name']} ({p['mrn']})", p["id"])
        if cur:
            idx = self.cmb_req_patient.findData(cur)
            if idx >= 0:
                self.cmb_req_patient.setCurrentIndex(idx)
        self.cmb_req_patient.blockSignals(False)

    def refresh_patients(self):
        q = self.in_pt_search.text().strip().lower() if hasattr(self, "in_pt_search") else ""
        conn = get_conn()
        pts = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
        conn.close()
        if q:
            pts = [
                p for p in pts
                if q in (p["full_name"] or "").lower()
                or q in (p["mrn"] or "").lower()
                or q in (p["physician"] or "").lower()
            ]
        self.tbl_patients.setRowCount(len(pts))
        for i, p in enumerate(pts):
            self.tbl_patients.setRowHeight(i, 36)
            self.tbl_patients.setItem(i, 0, _make_item(str(p["id"])))
            self.tbl_patients.setItem(i, 1, _make_item(p["mrn"]))
            self.tbl_patients.setItem(i, 2, _make_item(p["full_name"]))
            self.tbl_patients.setItem(i, 3, _make_item(p["dob"] or "-"))
            self.tbl_patients.setItem(i, 4, _make_item(p["sex"] or "-"))
            self.tbl_patients.setItem(i, 5, _make_item(p["contact"] or "-"))
            self.tbl_patients.setItem(i, 6, _make_item(p["physician"] or "-"))

    def refresh_test_checkboxes(self):
        checked_prev = {t for t, cb in self.test_checkboxes.items() if cb.isChecked()}
        while self.chk_list_layout.count():
            item = self.chk_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.test_checkboxes.clear()
        self.assay_row_widgets.clear()

        conn = get_conn()
        tests = conn.execute("SELECT test_name, department, tube_type, ref_range FROM tests ORDER BY department, test_name").fetchall()
        conn.close()

        cur_dept = None
        for t in tests:
            if t["department"] != cur_dept:
                cur_dept = t["department"]
                sec = QLabel(cur_dept.upper())
                sec.setObjectName("GroupTitle")
                self.chk_list_layout.addWidget(sec)

            row_w = QWidget()
            row_w.setStyleSheet("background: transparent;")
            row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(4, 3, 6, 3)
            row_l.setSpacing(8)

            cb = QCheckBox(t["test_name"])
            if t["test_name"] in checked_prev:
                cb.setChecked(True)
            cb.toggled.connect(self._update_selected_assay_count)

            tube_str = t["tube_type"] or "Gold (SST)"
            cap_hex, _ = TUBE_COLORS.get(tube_str, ("#38BDF8", "#E0F2FE"))
            tube_lbl = QLabel(tube_str)
            tube_lbl.setStyleSheet(f"color: {cap_hex}; font-size: 8.5pt; font-weight: 600; background: transparent;")

            row_l.addWidget(cb, 1)
            row_l.addWidget(tube_lbl, 0, Qt.AlignRight)

            self.chk_list_layout.addWidget(row_w)
            self.test_checkboxes[t["test_name"]] = cb
            blob = f"{t['test_name']} {t['department']} {tube_str}".lower()
            self.assay_row_widgets.append((row_w, blob))

        self._update_selected_assay_count()

    def refresh_pathologist(self):
        conn = get_conn()
        rows = conn.execute("""
            SELECT o.*, p.full_name
            FROM orders o JOIN patients p ON o.patient_id = p.id
            WHERE o.critical_flag = 1
               OR o.status = 'Amended'
               OR o.diff_json IS NOT NULL
               OR o.antibiogram_json IS NOT NULL
               OR o.test_name LIKE '%Smear%'
               OR o.test_name LIKE '%Culture%'
            ORDER BY o.id DESC
        """).fetchall()
        conn.close()

        self.tbl_path.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tbl_path.setRowHeight(i, 38)
            trigger = "CRITICAL" if r["critical_flag"] else (r["status"] if r["status"] == "Amended" else r["department"])
            cosign = f"Signed: {r['pathologist_signed_by']}" if r["pathologist_signed_by"] else "Awaiting Co-Sign"
            self.tbl_path.setItem(i, 0, _make_item(str(r["id"])))
            self.tbl_path.setItem(i, 1, _make_item(r["specimen_id"]))
            self.tbl_path.setItem(i, 2, _make_item(r["full_name"]))
            self.tbl_path.setItem(i, 3, _make_item(r["test_name"]))
            self.tbl_path.setItem(i, 4, _make_item(r["result_value"] or "-"))
            self.tbl_path.setItem(i, 5, _make_item(trigger, "#E11D48" if r["critical_flag"] else "#0284C7"))
            self.tbl_path.setItem(i, 6, _make_item(cosign, "#059669" if r["pathologist_signed_by"] else "#D97706"))

    def refresh_qc_targets(self):
        cur = self.cmb_qc_target.currentText()
        conn = get_conn()
        rows = conn.execute("SELECT label FROM qc_targets ORDER BY label").fetchall()
        conn.close()
        self.cmb_qc_target.blockSignals(True)
        self.cmb_qc_target.clear()
        for r in rows:
            self.cmb_qc_target.addItem(r["label"])
        if cur:
            self.cmb_qc_target.setCurrentText(cur)
        self.cmb_qc_target.blockSignals(False)

    def refresh_catalog(self):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM tests ORDER BY department, test_name").fetchall()
        conn.close()
        self.tbl_catalog.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.tbl_catalog.setRowHeight(i, 36)
            self.tbl_catalog.setItem(i, 0, _make_item(r["test_name"]))
            self.tbl_catalog.setItem(i, 1, _make_item(r["department"]))
            self.tbl_catalog.setItem(i, 2, _make_item(r["unit"] or "-"))
            self.tbl_catalog.setItem(i, 3, _make_item(r["ref_range"] or "-"))
            self.tbl_catalog.setItem(i, 4, _make_item(f"{r['crit_high']:g}" if r["crit_high"] is not None else "-"))
            self.tbl_catalog.setItem(i, 5, _make_item(f"{r['delta_pct']:g}%" if r["delta_pct"] else "-"))
            self.tbl_catalog.setItem(i, 6, _make_item(r["tube_type"] or "-"))

    def refresh_admin(self):
        conn = get_conn()
        staff_rows = conn.execute("SELECT * FROM staff ORDER BY pin").fetchall()
        aud_rows = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 120").fetchall()
        conn.close()

        self.tbl_staff.setRowCount(len(staff_rows))
        for i, s in enumerate(staff_rows):
            self.tbl_staff.setRowHeight(i, 34)
            self.tbl_staff.setItem(i, 0, _make_item(s["pin"]))
            self.tbl_staff.setItem(i, 1, _make_item(s["name"]))
            self.tbl_staff.setItem(i, 2, _make_item(s["role"]))
            self.tbl_staff.setItem(i, 3, _make_item(s["prc_license"] or "-"))
            self.tbl_staff.setItem(i, 4, _make_item(s["sig_path"] or "None"))

        self.tbl_audit.setRowCount(len(aud_rows))
        for i, a in enumerate(aud_rows):
            self.tbl_audit.setRowHeight(i, 34)
            self.tbl_audit.setItem(i, 0, _make_item(a["timestamp"]))
            self.tbl_audit.setItem(i, 1, _make_item(a["operator"]))
            self.tbl_audit.setItem(i, 2, _make_item(a["action"]))
            self.tbl_audit.setItem(i, 3, _make_item(a["specimen_id"] or "-"))
            self.tbl_audit.setItem(i, 4, _make_item(a["details"] or ""))


# ==============================================================================
# APPLICATION SHELL (PIN GATE -> WORKSPACE)
# ==============================================================================

class MonocytesLisWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1380, 840)
        self.setMinimumSize(1024, 680)
        self.workspace = None

        self.stack = QStackedWidget()
        self.stack.setObjectName("RootCanvas")
        self.setCentralWidget(self.stack)

        self.login_screen = StaffLoginScreen(self)
        self.login_screen.authenticated.connect(self._on_authenticated)
        self.login_screen.theme_toggled.connect(self._toggle_theme)
        self.stack.addWidget(self.login_screen)
        self.stack.setCurrentWidget(self.login_screen)

        self._apply_global_theme()

    def _toggle_theme(self):
        global CURRENT_THEME
        CURRENT_THEME = "light" if CURRENT_THEME == "dark" else "dark"
        APP_CONFIG["theme"] = CURRENT_THEME
        save_config(APP_CONFIG)
        self._apply_global_theme()

    def _apply_global_theme(self):
        QApplication.instance().setStyleSheet(build_qss(CURRENT_THEME))
        self.setStyleSheet(build_qss(CURRENT_THEME))
        apply_window_titlebar_theme(self)
        if self.login_screen:
            self.login_screen.apply_theme()
        if self.workspace:
            self.workspace.on_theme_changed()

    def _on_authenticated(self, user: dict):
        if self.workspace is not None:
            self.stack.removeWidget(self.workspace)
            self.workspace.deleteLater()
            self.workspace = None

        self.workspace = MainWorkspace(user, self)
        self.workspace.lock_requested.connect(self._lock_to_login)
        self.workspace.theme_toggled.connect(self._toggle_theme)
        self.stack.addWidget(self.workspace)
        self.stack.setCurrentWidget(self.workspace)
        self._apply_global_theme()

    def _lock_to_login(self):
        if self.workspace is not None:
            log_audit(f"{self.workspace.user['name']} ({self.workspace.user['pin']})", "SESSION_LOCK", "-", "Locked to PIN gate")
            self.stack.removeWidget(self.workspace)
            self.workspace.deleteLater()
            self.workspace = None
        self.login_screen.reset_gate()
        self.stack.setCurrentWidget(self.login_screen)
        self._apply_global_theme()


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyle("Fusion")

    init_db()
    perform_daily_backup()

    win = MonocytesLisWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
