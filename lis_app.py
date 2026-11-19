import sqlite3
import os
import csv
import shutil
import hashlib
import webbrowser
from datetime import datetime, timedelta
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from fpdf import FPDF

# --- Global Appearance ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

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
    ("1111", "Gaia Aubrey Manalo, MD", "Pathologist"),
]

# (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
DEFAULT_TESTS = [
    ("White Blood Cell Count (WBC)", "Hematology", "x10^9/L", 4.5, 11.0, 2.0, 30.0, 35.0, "Lavender (EDTA)", "4.5 - 11.0 x10^9/L"),
    ("Hemoglobin (Hgb)", "Hematology", "g/dL", 12.0, 17.5, 7.0, 20.0, 25.0, "Lavender (EDTA)", "12.0 - 17.5 g/dL"),
    ("Platelet Count (PLT)", "Hematology", "x10^9/L", 150.0, 450.0, 50.0, 1000.0, 40.0, "Lavender (EDTA)", "150 - 450 x10^9/L"),
    ("Monocytes (Absolute)", "Hematology", "x10^9/L", 0.2, 0.8, 0.05, 3.0, 50.0, "Lavender (EDTA)", "0.2 - 0.8 x10^9/L"),
    ("Fasting Blood Glucose", "Chemistry", "mg/dL", 70.0, 99.0, 45.0, 400.0, 35.0, "Gold (SST)", "70 - 99 mg/dL"),
    ("HbA1c", "Chemistry", "%", 4.0, 5.6, None, 14.0, 20.0, "Lavender (EDTA)", "4.0 - 5.6 %"),
    ("Creatinine (Serum)", "Chemistry", "mg/dL", 0.6, 1.3, None, 6.0, 30.0, "Gold (SST)", "0.6 - 1.3 mg/dL"),
    ("Total Cholesterol", "Chemistry", "mg/dL", 0.0, 200.0, None, None, 25.0, "Gold (SST)", "< 200 mg/dL"),
    ("ALT (SGPT)", "Chemistry", "U/L", 7.0, 56.0, None, 500.0, 40.0, "Gold (SST)", "7 - 56 U/L"),
    ("Urinalysis (Complete)", "Microscopy", "", None, None, None, None, None, "Sterile Urine Cup", "Negative / Normal"),
    ("Urine Culture & Sensitivity", "Microbiology", "", None, None, None, None, None, "Sterile Urine Cup", "No Growth"),
    ("Blood Typing (ABO/Rh)", "Immunohematology", "", None, None, None, None, None, "Pink (EDTA)", "Qualitative"),
]

QC_TARGETS = {
    "Hemoglobin (Hgb) | Level 1 (Normal)": ("Hemoglobin (Hgb)", "Level 1 (Normal)", 13.8, 0.35, "g/dL"),
    "Hemoglobin (Hgb) | Level 2 (Abnormal)": ("Hemoglobin (Hgb)", "Level 2 (Abnormal)", 7.8, 0.25, "g/dL"),
    "White Blood Cell Count (WBC) | Level 1 (Normal)": ("White Blood Cell Count (WBC)", "Level 1 (Normal)", 7.5, 0.40, "x10^9/L"),
    "Fasting Blood Glucose | Level 1 (Normal)": ("Fasting Blood Glucose", "Level 1 (Normal)", 88.0, 3.0, "mg/dL"),
    "Fasting Blood Glucose | Level 2 (High)": ("Fasting Blood Glucose", "Level 2 (High)", 245.0, 7.5, "mg/dL"),
}

def safe_pdf_text(text):
    if text is None:
        return ""
    cleaned = str(text).replace("—", "-").replace("–", "-").replace("•", "-").replace("±", "+/-")
    return cleaned.encode("latin-1", "replace").decode("latin-1")

# --- Database Layer ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            pin TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            mrn TEXT UNIQUE,
            full_name TEXT NOT NULL,
            dob TEXT,
            sex TEXT,
            phone TEXT,
            physician TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_catalog (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT UNIQUE NOT NULL,
            department TEXT,
            unit TEXT,
            low_val REAL,
            high_val REAL,
            crit_low REAL,
            crit_high REAL,
            delta_pct REAL,
            tube_type TEXT,
            ref_range TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            specimen_id TEXT NOT NULL,
            patient_id INTEGER,
            test_name TEXT NOT NULL,
            department TEXT,
            tube_type TEXT,
            priority TEXT DEFAULT 'Routine',
            status TEXT DEFAULT 'Pending',
            result_value TEXT DEFAULT '',
            prior_result TEXT DEFAULT '-',
            flag TEXT DEFAULT '',
            delta_flag TEXT DEFAULT '',
            reference_range TEXT,
            notes TEXT DEFAULT '',
            verified_by TEXT DEFAULT '',
            order_date TEXT,
            verified_date TEXT DEFAULT '',
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS qc_logs (
            qc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            assay_key TEXT,
            assay_name TEXT,
            level TEXT,
            measured_val REAL,
            target_mean REAL,
            target_sd REAL,
            z_score REAL,
            westgard_status TEXT,
            operator TEXT,
            run_date TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            operator TEXT,
            role TEXT,
            action TEXT,
            reference_id TEXT,
            details TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM staff")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO staff (pin, full_name, role) VALUES (?, ?, ?)", INITIAL_STAFF)

    cur.execute("SELECT COUNT(*) FROM test_catalog")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO test_catalog (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, DEFAULT_TESTS)

    conn.commit()
    conn.close()

def log_audit(operator, role, action, ref_id, details):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log (timestamp, operator, role, action, reference_id, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operator, role, action, ref_id, details))
    conn.commit()
    conn.close()

def get_pathologist_name():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT full_name FROM staff WHERE role LIKE '%Pathologist%' LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "Gaia Aubrey Manalo, MD"

# --- PDF Generators (Cumulative Report & Barcode Tube Label) ---
class MonocytesReportPDF(FPDF):
    def header(self):
        self.set_fill_color(10, 15, 28)
        self.rect(0, 0, 210, 34, 'F')
        self.set_fill_color(99, 102, 241)
        self.rect(0, 34, 210, 1.5, 'F')
        self.set_xy(10, 8)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 17)
        self.cell(140, 9, "MONOCYTES DELEGATES LIS", new_x="RIGHT", new_y="TOP", align="L")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(129, 140, 248)
        self.cell(50, 9, "ACCREDITED CLINICAL LAB", new_x="LMARGIN", new_y="NEXT", align="R")

        self.set_x(10)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, "Diagnostic Pathology, Hematology & Clinical Chemistry | Cumulative Laboratory Report", new_x="LMARGIN", new_y="NEXT", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(203, 213, 225)
        self.line(10, 275, 200, 275)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Monocytes Delegates LIS v4.0 - Printed {datetime.now().strftime('%Y-%m-%d %H:%M')} - Confidential Medical Record", align="C")

def generate_specimen_pdf(patient_info, specimen_id, order_rows, save_path):
    pdf = MonocytesReportPDF()
    pdf.add_page()
    pdf.set_text_color(15, 23, 42)

    doc_hash = hashlib.sha256(f"{specimen_id}-{patient_info['mrn']}".encode()).hexdigest()[:12].upper()
    pathologist_name = get_pathologist_name()

    # Demographics Card
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, 40, 190, 30, 'F')
    pdf.set_xy(14, 43)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(105, 6, safe_pdf_text(f"PATIENT: {patient_info['full_name']}  (MRN: {patient_info['mrn']})"), border=0)
    pdf.cell(80, 6, safe_pdf_text(f"SPECIMEN ID: {specimen_id}"), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(105, 6, safe_pdf_text(f"DOB / Sex: {patient_info['dob']}  |  {patient_info['sex']}"), border=0)
    pdf.cell(80, 6, safe_pdf_text(f"Collected: {order_rows[0]['order_date']}"), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.cell(105, 6, safe_pdf_text(f"Requesting Clinician: {patient_info['physician']}"), border=0)
    pdf.cell(80, 6, safe_pdf_text(f"Priority: {order_rows[0]['priority']}  |  Auth ID: {doc_hash}"), border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Results Table Header
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(56, 9, "Investigation / Assay", border=1, fill=True)
    pdf.cell(28, 9, "Result", border=1, fill=True, align="C")
    pdf.cell(26, 9, "Prior Result", border=1, fill=True, align="C")
    pdf.cell(24, 9, "Flag", border=1, fill=True, align="C")
    pdf.cell(56, 9, "Reference Interval", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    for row in order_rows:
        pdf.set_text_color(15, 23, 42)
        pdf.cell(56, 9, safe_pdf_text(row['test_name'][:34]), border=1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(28, 9, safe_pdf_text(row['result_value']), border=1, align="C")
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(26, 9, safe_pdf_text(row['prior_result'] or "-"), border=1, align="C")

        flag_str = str(row['flag'])
        if row['status'] == "Amended":
            flag_str = f"{flag_str} [AMENDED]"
        if row['delta_flag']:
            flag_str = f"{flag_str} ({row['delta_flag']})"

        if "CRITICAL" in flag_str or "HIGH" in flag_str or "REJECTED" in flag_str:
            pdf.set_text_color(220, 38, 38)
            pdf.set_font("Helvetica", "B", 8)
        elif "LOW" in flag_str or "AMENDED" in flag_str:
            pdf.set_text_color(217, 119, 6)
            pdf.set_font("Helvetica", "B", 8)
        elif "NORMAL" in flag_str:
            pdf.set_text_color(22, 163, 74)
            pdf.set_font("Helvetica", "B", 8.5)
        pdf.cell(24, 9, safe_pdf_text(flag_str), border=1, align="C")

        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(56, 9, safe_pdf_text(row['reference_range']), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        if row['notes']:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(71, 85, 105)
            pdf.cell(190, 6, safe_pdf_text(f"   Clinical / Read-Back Note: {row['notes']}"), border="LRB", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)

    pdf.ln(14)
    verifiers = ", ".join(sorted(set(r['verified_by'] for r in order_rows if r['verified_by'])))
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(95, 7, safe_pdf_text(f"Verified By: {verifiers or 'Authorized RMT'}"), border="T")
    pdf.cell(95, 7, safe_pdf_text(f"Pathologist: {pathologist_name}"), border="T", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, safe_pdf_text(f"Document Digital Verification Code: MDL-{doc_hash} | End of Clinical Laboratory Report"), new_x="LMARGIN", new_y="NEXT")
    pdf.output(save_path)

def generate_barcode_label_pdf(patient_info, specimen_id, tubes, priority, order_date, save_path):
    pdf = FPDF(orientation="L", unit="mm", format=(46, 82))
    pdf.set_auto_page_break(False)
    pdf.add_page()

    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 82, 7, 'F')
    pdf.set_xy(3, 1.5)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 7)
    pdf.cell(52, 4, "MONOCYTES DELEGATES LIS", border=0)
    if priority == "STAT":
        pdf.set_fill_color(220, 38, 38)
        pdf.cell(24, 4, "STAT PRIORITY", border=0, fill=True, align="C")
    else:
        pdf.cell(24, 4, safe_pdf_text(priority.upper()), border=0, align="R")

    pdf.set_xy(3, 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.cell(76, 4.5, safe_pdf_text(f"{patient_info['full_name']} ({patient_info['mrn']})"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(3)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(76, 3.8, safe_pdf_text(f"DOB: {patient_info['dob']} | Sex: {patient_info['sex']} | {order_date}"), new_x="LMARGIN", new_y="NEXT")

    bits = "".join(f"{ord(c):08b}" for c in specimen_id)
    x_pos = 5.0
    y_top = 18.0
    bar_h = 13.0
    pdf.set_fill_color(0, 0, 0)
    for idx, b in enumerate(bits[:96]):
        w = 0.72 if b == "1" else 0.36
        if idx % 2 == 0 or b == "1":
            pdf.rect(x_pos, y_top, w, bar_h, 'F')
        x_pos += 0.74
        if x_pos > 76:
            break

    pdf.set_xy(3, 32)
    pdf.set_font("Courier", "B", 9)
    pdf.cell(76, 4.5, safe_pdf_text(f"*{specimen_id}*"), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(3, 37.5)
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 7)
    tube_str = ", ".join(sorted(set(tubes)))
    pdf.cell(76, 5, safe_pdf_text(f"TUBES: {tube_str}"), border=1, fill=True, align="C")

    pdf.output(save_path)

# --- Custom Vector Range Gauge Canvas (Two-Line Long-Name Safe) ---
class AnimatedRangeGauge(tk.Canvas):
    def __init__(self, master, height=64, **kwargs):
        super().__init__(master, height=height, highlightthickness=0, **kwargs)
        self.progress = 0.0
        self.bar_color = "#6366f1"
        self.low_marker = 0.28
        self.high_marker = 0.72
        self.top_text = "Select an order row to inspect"
        self.sub_text = "Awaiting specimen telemetry"
        self.anim_id = None
        self.bind("<Configure>", lambda _: self.redraw())

    def set_state(self, target_ratio, color, top_text, sub_text, animate=True):
        self.bar_color = color
        self.top_text = top_text
        self.sub_text = sub_text
        if self.anim_id:
            self.after_cancel(self.anim_id)
            self.anim_id = None

        if not animate:
            self.progress = target_ratio
            self.redraw()
            return

        steps = 22
        step_idx = [0]

        def tick():
            step_idx[0] += 1
            t = step_idx[0] / steps
            eased = 1.0 - pow(1.0 - t, 3)
            self.progress = target_ratio * eased
            self.redraw()
            if step_idx[0] < steps:
                self.anim_id = self.after(14, tick)
            else:
                self.anim_id = None

        self.anim_id = self.after(10, tick)

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), 220)
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = "#090d16" if is_dark else "#f1f5f9"
        track_col = "#1e293b" if is_dark else "#e2e8f0"
        txt_col = "#f8fafc" if is_dark else "#0f172a"
        sub_col = "#94a3b8" if is_dark else "#475569"

        self.configure(bg=bg_col)
        self.create_text(10, 12, text=self.top_text, anchor="w", fill=txt_col, font=("Segoe UI", 9, "bold"), width=w - 20)
        self.create_text(10, 27, text=self.sub_text, anchor="w", fill=self.bar_color, font=("Segoe UI", 8, "bold"), width=w - 20)

        pad_x = 10
        track_y1, track_y2 = 38, 48
        track_w = w - 2 * pad_x
        self.create_rectangle(pad_x, track_y1, pad_x + track_w, track_y2, fill=track_col, outline="")

        z_x1 = pad_x + track_w * self.low_marker
        z_x2 = pad_x + track_w * self.high_marker
        zone_col = "#14332a" if is_dark else "#dcfce7"
        self.create_rectangle(z_x1, track_y1, z_x2, track_y2, fill=zone_col, outline="")

        fill_w = max(0, track_w * self.progress)
        if fill_w > 0:
            self.create_rectangle(pad_x, track_y1, pad_x + fill_w, track_y2, fill=self.bar_color, outline="")
            cap_x = pad_x + fill_w
            self.create_oval(cap_x - 5, track_y1 - 2, cap_x + 5, track_y2 + 2, fill="#ffffff", outline=self.bar_color, width=2)

        self.create_line(z_x1, track_y1 - 3, z_x1, track_y2 + 3, fill="#64748b", width=1.5)
        self.create_line(z_x2, track_y1 - 3, z_x2, track_y2 + 3, fill="#64748b", width=1.5)
        self.create_text(z_x1, 56, text="LOW", fill=sub_col, font=("Segoe UI", 7, "bold"))
        self.create_text(z_x2, 56, text="HIGH", fill=sub_col, font=("Segoe UI", 7, "bold"))

# --- Animated Levey-Jennings QC Vector Chart ---
class LeveyJenningsCanvas(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, highlightthickness=0, **kwargs)
        self.points = []
        self.mean = 0.0
        self.sd = 1.0
        self.title = "Select a QC Assay above to plot Levey-Jennings Control Chart"
        self.bind("<Configure>", lambda _: self.redraw())

    def plot(self, title, mean, sd, points):
        self.title = title
        self.mean = mean
        self.sd = max(sd, 0.0001)
        self.points = points
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), 400)
        h = max(self.winfo_height(), 240)
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_col = "#0f172a" if is_dark else "#ffffff"
        txt_col = "#f8fafc" if is_dark else "#0f172a"
        self.configure(bg=bg_col)

        self.create_text(18, 16, text=self.title, anchor="w", fill=txt_col, font=("Segoe UI", 11, "bold"))

        left, right, top, bottom = 58, w - 28, 38, h - 32
        plot_w = max(right - left, 100)
        plot_h = max(bottom - top, 100)

        def y_for_z(z):
            clamped = max(-3.6, min(3.6, z))
            return top + plot_h * (0.5 - clamped / 7.6)

        sd_levels = [
            (3.0, "+3SD", "#ef4444"),
            (2.0, "+2SD", "#f59e0b"),
            (1.0, "+1SD", "#475569"),
            (0.0, "MEAN", "#10b981"),
            (-1.0, "-1SD", "#475569"),
            (-2.0, "-2SD", "#f59e0b"),
            (-3.0, "-3SD", "#ef4444"),
        ]
        for z, lbl, col in sd_levels:
            y = y_for_z(z)
            dash = () if z == 0.0 else (4, 4)
            self.create_line(left, y, right, y, fill=col, width=1.5 if z == 0.0 else 1, dash=dash)
            self.create_text(left - 8, y, text=lbl, anchor="e", fill=col, font=("Consolas", 8, "bold"))

        if not self.points:
            self.create_text(left + plot_w / 2, top + plot_h / 2, text="No QC runs recorded yet for this control level.", fill="#64748b", font=("Segoe UI", 10))
            return

        coords = []
        n = len(self.points)
        for idx, (r_date, val, z, status) in enumerate(self.points):
            x = left + (plot_w * (idx + 0.5) / max(n, 1))
            y = y_for_z(z)
            coords.append((x, y, val, z, status, r_date))

        if len(coords) > 1:
            line_pts = []
            for c in coords:
                line_pts.extend([c[0], c[1]])
            self.create_line(*line_pts, fill="#6366f1", width=2.2)

        for idx, (x, y, val, z, status, r_date) in enumerate(coords, start=1):
            node_col = "#ef4444" if "1-3s" in status else "#f59e0b" if "1-2s" in status else "#10b981"
            self.create_oval(x - 5, y - 5, x + 5, y + 5, fill=node_col, outline="#ffffff", width=1.5)
            self.create_text(x, y - 12, text=f"{val}", fill=txt_col, font=("Consolas", 8, "bold"))
            self.create_text(x, bottom + 12, text=f"#{idx}", fill="#94a3b8", font=("Consolas", 8))

# --- Main Application ---
class MonocytesDelegatesLIS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monocytes Delegates LIS v4.0 — Enterprise Clinical Diagnostic Suite")
        self.geometry("1400x850")
        self.minsize(1100, 680)

        self.current_user = "Locked Session"
        self.current_role = "Unauthenticated"
        self.is_authenticated = False
        self.pulse_state = False
        self.selected_patient_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar Navigation Rail ---
        self.sidebar = ctk.CTkFrame(self, width=245, corner_radius=0, fg_color=("#f1f5f9", "#060911"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)

        brand_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_box.grid(row=0, column=0, padx=20, pady=(24, 18), sticky="ew")
        ctk.CTkLabel(brand_box, text="MONOCYTES", font=ctk.CTkFont(size=21, weight="bold"), text_color=("#0f172a", "#f8fafc")).pack(anchor="w")
        ctk.CTkLabel(brand_box, text="DELEGATES LIS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6366f1").pack(anchor="w")
        ctk.CTkLabel(brand_box, text="v4.0 Enterprise Clinical Suite", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", pady=(2, 0))

        self.nav_buttons = {}
        nav_items = [
            ("orders", "Worklist & Verification", "transparent"),
            ("new_order", "+ New Requisition", "#4f46e5"),
            ("patients", "Patient Registry", "transparent"),
            ("qc", "Quality Control (QC)", "transparent"),
            ("catalog", "Test Catalog & Cutoffs", "transparent"),
            ("audit", "Audit Trail & Staff PINs", "transparent"),
        ]

        for idx, (key, label, color) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=label, height=40, anchor="w", corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold" if key == "new_order" else "normal"),
                fg_color=color,
                hover_color="#4338ca" if key == "new_order" else ("#e2e8f0", "#1e293b"),
                text_color="white" if key == "new_order" else ("#0f172a", "#e2e8f0"),
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=idx, column=0, padx=16, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        # Active Operator Card & Theme Footer
        footer_box = ctk.CTkFrame(self.sidebar, fg_color=("#e2e8f0", "#0f172a"), corner_radius=10)
        footer_box.grid(row=8, column=0, padx=16, pady=18, sticky="ew")

        self.lbl_operator = ctk.CTkLabel(footer_box, text=self.current_user, font=ctk.CTkFont(size=12, weight="bold"), wraplength=190, justify="left")
        self.lbl_operator.pack(anchor="w", padx=12, pady=(10, 0))
        self.lbl_role = ctk.CTkLabel(footer_box, text=self.current_role, font=ctk.CTkFont(size=10), text_color="#818cf8", wraplength=190, justify="left")
        self.lbl_role.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkButton(footer_box, text="Switch Operator / Lock", height=28, font=ctk.CTkFont(size=11), fg_color="#334155", hover_color="#475569", command=self.open_login_modal).pack(fill="x", padx=12, pady=(0, 8))

        self.theme_menu = ctk.CTkOptionMenu(
            footer_box, values=["Dark", "Light"], height=28, fg_color=("#cbd5e1", "#1e293b"),
            button_color="#4f46e5", text_color=("#0f172a", "#f8fafc"),
            command=self.change_theme
        )
        self.theme_menu.pack(fill="x", padx=12, pady=(0, 12))

        # --- Build Views ---
        self.frames = {}
        self.build_orders_frame()
        self.build_new_order_frame()
        self.build_patients_frame()
        self.build_qc_frame()
        self.build_catalog_frame()
        self.build_audit_frame()

        self.show_frame("orders")
        self.start_stat_pulse()
        self.after(150, self.open_login_modal)

    # ==========================================
    # DUAL-AXIS SCROLLABLE TREEVIEW HELPER
    # ==========================================
    def _create_scrolled_treeview(self, parent, columns, widths, left_align_cols=()):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for c, w in zip(columns, widths):
            tree.heading(c, text=c)
            tree.column(c, width=w, minwidth=max(50, w - 20), stretch=False, anchor="w" if c in left_align_cols else "center")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(2, 0))
        vsb.grid(row=0, column=1, sticky="ns", pady=(2, 0))
        hsb.grid(row=1, column=0, sticky="ew", padx=(2, 0))
        return tree

    def start_stat_pulse(self):
        self.pulse_state = not self.pulse_state
        try:
            stat_count = int(self.kpi_stat.cget("text"))
        except ValueError:
            stat_count = 0
        if stat_count > 0:
            self.stat_dot.configure(text_color="#ef4444" if self.pulse_state else "#7f1d1d")
        else:
            self.stat_dot.configure(text_color="#10b981")
        self.after(650, self.start_stat_pulse)

    # ==========================================
    # CLEAN PIN AUTHENTICATION MODAL (NO DEMO PROFILES)
    # ==========================================
    def open_login_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Monocytes Delegates LIS — Staff Authentication")
        modal.geometry("420x270")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        def on_close():
            if not self.is_authenticated:
                self.destroy()
            else:
                modal.destroy()

        modal.protocol("WM_DELETE_WINDOW", on_close)

        ctk.CTkLabel(modal, text="MONOCYTES DELEGATES LIS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#6366f1").pack(pady=(24, 2))
        ctk.CTkLabel(modal, text="OPERATOR PIN LOGIN", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 6))
        ctk.CTkLabel(modal, text="Enter your assigned 4-digit RMT or Pathologist PIN", text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(0, 16))

        pin_entry = ctk.CTkEntry(modal, placeholder_text="••••", show="•", width=240, height=42, font=ctk.CTkFont(size=18, weight="bold"), justify="center")
        pin_entry.pack(pady=(0, 14))
        pin_entry.focus_set()

        def attempt_login(_event=None):
            code = pin_entry.get().strip()
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT full_name, role FROM staff WHERE pin = ?", (code,))
            row = cur.fetchone()
            conn.close()

            if row:
                self.current_user, self.current_role = row
                self.is_authenticated = True
                self.lbl_operator.configure(text=self.current_user)
                self.lbl_role.configure(text=self.current_role)
                log_audit(self.current_user, self.current_role, "OPERATOR_LOGIN", f"PIN-{code[:2]}**", "Authenticated session")
                modal.destroy()
            else:
                pin_entry.delete(0, "end")
                messagebox.showerror("Access Denied", "Invalid Staff PIN. Please check your credentials and try again.", parent=modal)

        pin_entry.bind("<Return>", attempt_login)
        ctk.CTkButton(modal, text="Authenticate & Unlock", width=240, height=40, font=ctk.CTkFont(size=13, weight="bold"), fg_color="#4f46e5", hover_color="#4338ca", command=attempt_login).pack()

    def change_theme(self, mode):
        ctk.set_appearance_mode(mode)
        self.apply_treeview_theme()
        self.range_gauge.redraw()
        self.lj_canvas.redraw()

    def apply_treeview_theme(self):
        style = ttk.Style()
        style.theme_use("default")
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#0f172a" if is_dark else "#ffffff"
        fg = "#f1f5f9" if is_dark else "#0f172a"
        head_bg = "#1e293b" if is_dark else "#e2e8f0"
        head_fg = "#f8fafc" if is_dark else "#0f172a"

        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=32, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=head_bg, foreground=head_fg, relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#4f46e5")], foreground=[("selected", "#ffffff")])

    def show_frame(self, name):
        for k, frame in self.frames.items():
            frame.grid_forget()
            if k != "new_order":
                self.nav_buttons[k].configure(fg_color=("#e2e8f0", "#1e293b") if k == name else "transparent")
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=22, pady=18)

        if name == "orders":
            self.refresh_orders()
        elif name == "new_order":
            self.refresh_requisition_view()
        elif name == "patients":
            self.refresh_patients()
        elif name == "qc":
            self.refresh_qc_view()
        elif name == "catalog":
            self.refresh_catalog()
        elif name == "audit":
            self.refresh_audit()
            self.refresh_staff_list()

    # ==========================================
    # VIEW 1: SPLIT-PANE WORKLIST & SCROLLABLE INSPECTOR
    # ==========================================
    def build_orders_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["orders"] = frame
        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # KPI Telemetry Row
        kpi_row = ctk.CTkFrame(frame, fg_color="transparent")
        kpi_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.kpi_total = self._make_kpi_card(kpi_row, 0, "TOTAL ASSAYS", "0", "#6366f1")
        self.kpi_pending = self._make_kpi_card(kpi_row, 1, "PENDING WORKLIST", "0", "#f59e0b")
        self.kpi_stat, self.stat_dot = self._make_kpi_card(kpi_row, 2, "ACTIVE STAT / SLA", "0", "#ef4444", with_dot=True)
        self.kpi_done = self._make_kpi_card(kpi_row, 3, "VERIFIED & RELEASED", "0", "#10b981")

        # Filter & Export Toolbar
        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_orders())
        ctk.CTkEntry(toolbar, placeholder_text="Search Patient, MRN, Specimen ID, or Test...", textvariable=self.search_var, width=320, height=35).pack(side="left", padx=(0, 10))

        self.status_filter = ctk.CTkSegmentedButton(toolbar, values=["All", "Pending", "Completed", "Amended", "Rejected"], selected_color="#4f46e5", command=lambda _: self.refresh_orders())
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=5)

        ctk.CTkButton(toolbar, text="Export CSV Log", width=120, height=35, fg_color=("#e2e8f0", "#1e293b"), text_color=("#0f172a", "#f8fafc"), hover_color="#4f46e5", command=self.export_csv).pack(side="right")

        # Left/Center: Dual-Axis Scrollable Clinical Worklist
        table_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        table_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        self.apply_treeview_theme()

        cols = ("ID", "Specimen ID", "Patient", "Assay / Investigation", "Priority", "TAT", "Status", "Result", "Flag", "Verified By")
        widths = [45, 135, 175, 200, 75, 78, 88, 105, 115, 165]
        self.order_tree = self._create_scrolled_treeview(table_card, cols, widths, left_align_cols=("Patient", "Assay / Investigation", "Verified By"))

        self.order_tree.tag_configure("stat", foreground="#f87171")
        self.order_tree.tag_configure("critical", foreground="#ff4d6d")
        self.order_tree.tag_configure("high", foreground="#ef4444")
        self.order_tree.tag_configure("low", foreground="#f59e0b")
        self.order_tree.tag_configure("amended", foreground="#38bdf8")
        self.order_tree.tag_configure("normal", foreground="#10b981")
        self.order_tree.tag_configure("rejected", foreground="#94a3b8")

        self.order_tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # Right: Scrollable Clinical Inspector & Verification Drawer
        inspector = ctk.CTkScrollableFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"), width=355)
        inspector.grid(row=2, column=1, sticky="nsew")

        ctk.CTkLabel(inspector, text="CLINICAL INSPECTOR", font=ctk.CTkFont(size=12, weight="bold"), text_color="#818cf8").pack(anchor="w", padx=12, pady=(8, 2))
        self.insp_spec = ctk.CTkLabel(inspector, text="No Specimen Selected", font=ctk.CTkFont(size=14, weight="bold"), wraplength=310, justify="left")
        self.insp_spec.pack(anchor="w", padx=12)
        self.insp_patient = ctk.CTkLabel(inspector, text="Click any row to inspect & verify", font=ctk.CTkFont(size=11), text_color="gray", wraplength=310, justify="left")
        self.insp_patient.pack(anchor="w", padx=12, pady=(2, 8))

        # Delta Check & Tube Box
        delta_box = ctk.CTkFrame(inspector, fg_color=("#e2e8f0", "#090d16"), corner_radius=8)
        delta_box.pack(fill="x", padx=10, pady=(0, 8))
        self.insp_tube = ctk.CTkLabel(delta_box, text="Tube: -", font=ctk.CTkFont(size=11), wraplength=295, justify="left")
        self.insp_tube.pack(anchor="w", padx=10, pady=(6, 0))
        self.insp_prior = ctk.CTkLabel(delta_box, text="Prior Result: -", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8", wraplength=295, justify="left")
        self.insp_prior.pack(anchor="w", padx=10, pady=(2, 6))

        ctk.CTkButton(inspector, text="View Patient Cumulative History", height=28, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1, border_color="#4f46e5", text_color=("#4f46e5", "#818cf8"), hover_color=("#e0e7ff", "#1e1b4b"), command=self.open_patient_history_modal).pack(fill="x", padx=10, pady=(0, 10))

        # Animated Vector Range Gauge
        self.range_gauge = AnimatedRangeGauge(inspector, height=64)
        self.range_gauge.pack(fill="x", padx=10, pady=(0, 10))

        # Result Entry Inputs
        ctk.CTkLabel(inspector, text="Measured Result Value:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=12)
        self.res_input = ctk.CTkEntry(inspector, placeholder_text="e.g. 6.8 or Negative", height=34)
        self.res_input.pack(fill="x", padx=12, pady=(2, 8))

        ctk.CTkLabel(inspector, text="Clinical / Amendment / Rejection Note:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=12)
        self.note_input = ctk.CTkEntry(inspector, placeholder_text="Optional note or QNS/Hemolyzed", height=34)
        self.note_input.pack(fill="x", padx=12, pady=(2, 12))

        ctk.CTkButton(inspector, text="Verify & Release Result", height=38, font=ctk.CTkFont(weight="bold"), fg_color="#10b981", hover_color="#059669", command=self.verify_result).pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkButton(inspector, text="Reject Specimen", height=32, fg_color="#dc2626", hover_color="#b91c1c", command=self.reject_sample).pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkButton(inspector, text="Print Consolidated PDF Report", height=36, font=ctk.CTkFont(weight="bold"), fg_color="#4f46e5", hover_color="#4338ca", command=self.export_specimen_report).pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkButton(inspector, text="Print Tube Barcode Label", height=32, fg_color=("#cbd5e1", "#1e293b"), text_color=("#0f172a", "#f8fafc"), hover_color="#334155", command=self.export_barcode_label).pack(fill="x", padx=12, pady=(0, 14))

    def _animate_kpi_value(self, lbl, target_num):
        try:
            current = int(lbl.cget("text"))
        except ValueError:
            current = 0
        if current == target_num:
            return
        steps = 10
        idx = [0]

        def step():
            idx[0] += 1
            val = int(current + (target_num - current) * (idx[0] / steps))
            lbl.configure(text=str(val))
            if idx[0] < steps:
                self.after(18, step)
            else:
                lbl.configure(text=str(target_num))

        step()

    def _make_kpi_card(self, parent, col, title, val, accent, with_dot=False):
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        card.grid(row=0, column=col, padx=6 if col in (1, 2) else (0, 6) if col == 0 else (6, 0), sticky="ew")
        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(10, 0))
        ctk.CTkLabel(top, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack(side="left")
        dot = None
        if with_dot:
            dot = ctk.CTkLabel(top, text="●", font=ctk.CTkFont(size=12), text_color=accent)
            dot.pack(side="right")
        lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=accent)
        lbl.pack(anchor="w", padx=16, pady=(2, 10))
        return (lbl, dot) if with_dot else lbl

    def on_row_select(self, _event=None):
        sel = self.order_tree.selection()
        if not sel:
            return
        order_id = self.order_tree.item(sel[0])["values"][0]

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT o.specimen_id, p.patient_id, p.full_name, p.mrn, o.test_name, o.tube_type, o.status, o.result_value, o.prior_result, o.flag, o.reference_range,
                   c.low_val, c.high_val
            FROM orders o
            JOIN patients p ON o.patient_id = p.patient_id
            LEFT JOIN test_catalog c ON o.test_name = c.test_name
            WHERE o.order_id = ?
        """, (order_id,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return

        spec_id, pat_id, p_name, mrn, test_name, tube, status, res_val, prior_val, flag, ref_range, low, high = r
        self.selected_patient_id = pat_id
        self.insp_spec.configure(text=f"{spec_id}  •  {test_name}")
        self.insp_patient.configure(text=f"Patient: {p_name} ({mrn})")
        self.insp_tube.configure(text=f"Specimen Tube: {tube or 'Standard'}")
        self.insp_prior.configure(text=f"Prior Result: {prior_val or 'None on file'}")

        if status == "Pending":
            self.range_gauge.set_state(0.0, "#4f46e5", f"{test_name}", f"PENDING  |  Ref: {ref_range}", animate=True)
            return

        if "CRITICAL" in flag:
            color, target = "#ff1e42", 0.98
        elif flag == "HIGH":
            color, target = "#ef4444", 0.90
        elif flag == "LOW":
            color, target = "#f59e0b", 0.16
        elif flag == "REJECTED":
            color, target = "#64748b", 0.0
        else:
            color, target = "#10b981", 0.52

        if low is not None and high is not None:
            try:
                num_val = float(str(res_val).split()[0])
                span = max(float(high) - float(low), 0.001)
                ratio = 0.28 + ((num_val - float(low)) / span) * 0.44
                target = max(0.06, min(0.98, ratio))
            except (ValueError, IndexError):
                pass

        self.range_gauge.set_state(target, color, f"{test_name}: {res_val}", f"[{flag}]  |  Ref: {ref_range}", animate=True)

    def refresh_orders(self, reselect_id=None):
        for r in self.order_tree.get_children():
            self.order_tree.delete(r)

        q = f"%{self.search_var.get().strip()}%"
        st = self.status_filter.get()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM orders")
        self._animate_kpi_value(self.kpi_total, cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        self._animate_kpi_value(self.kpi_pending, cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM orders WHERE priority='STAT' AND status='Pending'")
        self._animate_kpi_value(self.kpi_stat, cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Completed', 'Amended')")
        self._animate_kpi_value(self.kpi_done, cur.fetchone()[0])

        sql = """
            SELECT o.order_id, o.specimen_id, p.full_name, o.test_name, o.priority, o.order_date, o.status, o.result_value, o.flag, o.delta_flag, o.verified_by
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE (p.full_name LIKE ? OR p.mrn LIKE ? OR o.specimen_id LIKE ? OR o.test_name LIKE ?)
        """
        params = [q, q, q, q]
        if st != "All":
            sql += " AND o.status = ?"
            params.append(st)
        sql += " ORDER BY o.order_id DESC"

        cur.execute(sql, params)
        now = datetime.now()
        target_item = None

        for row in cur.fetchall():
            oid, spec, pname, tname, prio, odate, status, res, flag, dflag, vby = row
            try:
                dt = datetime.strptime(odate, "%Y-%m-%d %H:%M")
                mins = max(0, int((now - dt).total_seconds() // 60))
            except Exception:
                mins = 0
            sla = 60 if prio == "STAT" else 240
            tat_str = f"{mins}m/{sla}m" if status == "Pending" else "Done"

            disp_flag = f"{flag} {dflag}".strip()
            tags = ()
            if status == "Rejected":
                tags = ("rejected",)
            elif "CRITICAL" in flag:
                tags = ("critical",)
            elif flag == "HIGH":
                tags = ("high",)
            elif flag == "LOW":
                tags = ("low",)
            elif status == "Amended":
                tags = ("amended",)
            elif flag == "NORMAL":
                tags = ("normal",)
            elif prio == "STAT" and status == "Pending":
                tags = ("stat",)

            item_id = self.order_tree.insert("", "end", values=(oid, spec, pname, tname, prio, tat_str, status, res, disp_flag, vby), tags=tags)
            if reselect_id and oid == reselect_id:
                target_item = item_id
        conn.close()

        if target_item:
            self.order_tree.selection_set(target_item)
            self.order_tree.focus(target_item)
            self.on_row_select()

    def verify_result(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select an order row in the worklist first.")
            return

        raw_val = self.res_input.get().strip()
        if not raw_val:
            messagebox.showwarning("Input Required", "Enter a measured result value.")
            return

        note = self.note_input.get().strip()
        item = self.order_tree.item(sel[0])["values"]
        order_id, specimen_id, test_name, old_status, old_res = item[0], item[1], item[3], item[6], item[7]

        new_status = "Completed"
        if old_status in ("Completed", "Amended"):
            if not messagebox.askyesno("Amend Verified Result", f"This assay was already verified as '{old_res}'.\n\nAmend result and log audit trail?"):
                return
            if not note:
                messagebox.showwarning("Amendment Reason Required", "Enter the reason for amending this result in the Note box.")
                return
            new_status = "Amended"
            note = f"[AMENDED from '{old_res}'] {note}"

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT patient_id FROM orders WHERE order_id = ?", (order_id,))
        patient_id = cur.fetchone()[0]

        cur.execute("""
            SELECT result_value FROM orders
            WHERE patient_id = ? AND test_name = ? AND status IN ('Completed', 'Amended') AND order_id < ?
            ORDER BY order_id DESC LIMIT 1
        """, (patient_id, test_name, order_id))
        prior_row = cur.fetchone()
        prior_str = prior_row[0] if prior_row else "-"

        cur.execute("SELECT unit, low_val, high_val, crit_low, crit_high, delta_pct FROM test_catalog WHERE test_name = ?", (test_name,))
        cat = cur.fetchone()

        flag = "NORMAL"
        delta_flag = ""
        display_val = raw_val
        is_critical = False

        if cat:
            unit, low, high, crit_low, crit_high, delta_pct = cat
            try:
                num = float(raw_val)
                display_val = f"{raw_val} {unit}".strip()
                if crit_low is not None and num < crit_low:
                    flag, is_critical = "CRITICAL LOW", True
                elif crit_high is not None and num > crit_high:
                    flag, is_critical = "CRITICAL HIGH", True
                elif low is not None and num < low:
                    flag = "LOW"
                elif high is not None and num > high:
                    flag = "HIGH"

                if prior_str != "-" and delta_pct is not None:
                    try:
                        prior_num = float(prior_str.split()[0])
                        if prior_num > 0:
                            pct_change = abs(num - prior_num) / prior_num * 100.0
                            if pct_change >= float(delta_pct):
                                delta_flag = f"DELTA {int(pct_change)}%"
                    except (ValueError, IndexError):
                        pass
            except ValueError:
                if raw_val.lower() in ("positive", "abnormal", "reactive", "detected"):
                    flag = "ABNORMAL"

        if is_critical:
            clinician = ctk.CTkInputDialog(
                text=f"CRITICAL PANIC RESULT ({display_val})!\n\nAccreditation requires immediate physician notification.\nEnter Name of Notified Clinician/Nurse for Read-Back Log:",
                title="CRITICAL VALUE ALERT"
            ).get_input()
            if not clinician or not clinician.strip():
                conn.close()
                messagebox.showwarning("Verification Halted", "Critical results cannot be released without documenting clinician read-back.")
                return
            readback_note = f"[CRITICAL READ-BACK CONFIRMED with {clinician.strip()} at {datetime.now().strftime('%H:%M')}]"
            note = f"{readback_note} {note}".strip()

        if delta_flag:
            if not messagebox.askyesno("Automated Delta Check Alert", f"{delta_flag} detected compared to prior result ({prior_str}).\n\nConfirm specimen identity and release result?"):
                conn.close()
                return

        cur.execute("""
            UPDATE orders
            SET result_value = ?, prior_result = ?, flag = ?, delta_flag = ?, status = ?,
                notes = ?, verified_by = ?, verified_date = ?
            WHERE order_id = ?
        """, (display_val, prior_str, flag, delta_flag, new_status, note, self.current_user, datetime.now().strftime("%Y-%m-%d %H:%M"), order_id))
        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "AMEND_RESULT" if new_status == "Amended" else "VERIFY_RESULT", specimen_id, f"{test_name}: {display_val} ({flag})")
        self.res_input.delete(0, "end")
        self.note_input.delete(0, "end")
        self.refresh_orders(reselect_id=order_id)

        if test_name == "Urinalysis (Complete)" and flag != "NORMAL":
            if messagebox.askyesno("Reflex Protocol Triggered", "Abnormal Urinalysis detected.\n\nAutomatically add 'Urine Culture & Sensitivity' to this Specimen ID?"):
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO orders (specimen_id, patient_id, test_name, department, tube_type, priority, reference_range, order_date)
                    VALUES (?, ?, 'Urine Culture & Sensitivity', 'Microbiology', 'Sterile Urine Cup', 'Routine', 'No Growth', ?)
                """, (specimen_id, patient_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                conn.close()
                log_audit(self.current_user, self.current_role, "REFLEX_ORDER", specimen_id, "Added Urine Culture & Sensitivity")
                self.refresh_orders(reselect_id=order_id)

    def reject_sample(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select a specimen row to reject.")
            return
        reason = self.note_input.get().strip()
        if not reason:
            messagebox.showwarning("Reason Required", "Enter rejection reason in the Note box (e.g., Hemolyzed, QNS, Clotted).")
            return
        item = self.order_tree.item(sel[0])["values"]
        order_id, specimen_id = item[0], item[1]

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            UPDATE orders SET result_value = 'Rejected', flag = 'REJECTED', status = 'Rejected', notes = ?, verified_by = ?
            WHERE order_id = ?
        """, (reason, self.current_user, order_id))
        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "REJECT_SPECIMEN", specimen_id, reason)
        self.note_input.delete(0, "end")
        self.refresh_orders(reselect_id=order_id)

    def open_patient_history_modal(self, patient_id=None):
        pid = patient_id or self.selected_patient_id
        if not pid:
            messagebox.showwarning("No Patient Selected", "Select an order row or patient first.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT mrn, full_name, dob, sex, physician FROM patients WHERE patient_id = ?", (pid,))
        pat = cur.fetchone()
        cur.execute("""
            SELECT order_date, specimen_id, test_name, status, result_value, flag, reference_range, verified_by
            FROM orders WHERE patient_id = ? ORDER BY order_id DESC
        """, (pid,))
        rows = cur.fetchall()
        conn.close()

        if not pat:
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Cumulative Lab History — {pat[1]} ({pat[0]})")
        win.geometry("920x480")
        win.transient(self)

        hdr = ctk.CTkFrame(win, fg_color=("#e2e8f0", "#0f172a"), corner_radius=8)
        hdr.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(hdr, text=f"{pat[1]}  ({pat[0]})", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))
        ctk.CTkLabel(hdr, text=f"DOB: {pat[2]}  |  Sex: {pat[3]}  |  Primary Clinician: {pat[4]}", font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w", padx=14, pady=(0, 10))

        t_box = ctk.CTkFrame(win)
        t_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        cols = ("Date", "Specimen ID", "Assay / Test", "Status", "Result", "Flag", "Ref Range", "Verified By")
        widths = [125, 130, 185, 85, 100, 95, 130, 155]
        h_tree = self._create_scrolled_treeview(t_box, cols, widths, left_align_cols=("Assay / Test", "Verified By"))
        for r in rows:
            h_tree.insert("", "end", values=r)

    def export_specimen_report(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Click an order row in the worklist first.")
            return

        specimen_id = self.order_tree.item(sel[0])["values"][1]
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.mrn, p.full_name, p.dob, p.sex, p.physician,
                   o.test_name, o.department, o.priority, o.status, o.result_value, o.prior_result, o.flag, o.delta_flag, o.reference_range, o.notes, o.verified_by, o.order_date
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE o.specimen_id = ?
        """, (specimen_id,))
        rows = cur.fetchall()
        conn.close()

        if any(r[8] == "Pending" for r in rows):
            if not messagebox.askyesno("Pending Assays", "Some assays on this specimen are still Pending. Generate preliminary report anyway?"):
                return

        patient_info = {"mrn": rows[0][0], "full_name": rows[0][1], "dob": rows[0][2], "sex": rows[0][3], "physician": rows[0][4]}
        order_dicts = [{
            "test_name": r[5], "department": r[6], "priority": r[7], "status": r[8],
            "result_value": r[9] or "Pending", "prior_result": r[10] or "-", "flag": r[11] or "-",
            "delta_flag": r[12] or "", "reference_range": r[13], "notes": r[14],
            "verified_by": r[15], "order_date": r[16]
        } for r in rows]

        clean_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in patient_info['full_name'])
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"MonocytesLIS_Report_{specimen_id}_{clean_name}.pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            try:
                generate_specimen_pdf(patient_info, specimen_id, order_dicts, path)
                log_audit(self.current_user, self.current_role, "PRINT_REPORT", specimen_id, f"Exported PDF to {os.path.basename(path)}")
                if os.name == "nt":
                    os.startfile(path)
                else:
                    webbrowser.open(path)
            except Exception as e:
                messagebox.showerror("PDF Error", f"Failed to generate PDF:\n{e}")

    def export_barcode_label(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select an order row to print its tube barcode label.")
            return

        specimen_id = self.order_tree.item(sel[0])["values"][1]
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.mrn, p.full_name, p.dob, p.sex, o.tube_type, o.priority, o.order_date
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE o.specimen_id = ?
        """, (specimen_id,))
        rows = cur.fetchall()
        conn.close()

        patient_info = {"mrn": rows[0][0], "full_name": rows[0][1], "dob": rows[0][2], "sex": rows[0][3]}
        tubes = [r[4] or "Standard" for r in rows]
        priority, odate = rows[0][5], rows[0][6]

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"Barcode_{specimen_id}.pdf",
            filetypes=[("PDF Label", "*.pdf")]
        )
        if path:
            try:
                generate_barcode_label_pdf(patient_info, specimen_id, tubes, priority, odate, path)
                log_audit(self.current_user, self.current_role, "PRINT_BARCODE", specimen_id, "Generated tube label")
                if os.name == "nt":
                    os.startfile(path)
                else:
                    webbrowser.open(path)
            except Exception as e:
                messagebox.showerror("Label Error", f"Failed to generate barcode label:\n{e}")

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=f"MonocytesLIS_Worklist_{datetime.now().strftime('%Y%m%d')}.csv",
            filetypes=[("CSV Spreadsheet", "*.csv")]
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Order ID", "Specimen ID", "Patient", "Assay", "Priority", "TAT", "Status", "Result", "Flag", "Verified By"])
            for row_id in self.order_tree.get_children():
                writer.writerow(self.order_tree.item(row_id)["values"])
        messagebox.showinfo("Export Complete", "Worklist log exported to CSV.")

    # ==========================================
    # VIEW 2: REQUISITION & PRESET PANELS
    # ==========================================
    def build_new_order_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        self.frames["new_order"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(frame, text="New Laboratory Requisition & Panel Order", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=28, pady=(22, 2))
        ctk.CTkLabel(frame, text="Select a patient, use 1-click preset panels or individual assays, and accession under a unified Specimen ID.", text_color="gray").grid(row=1, column=0, sticky="w", padx=28, pady=(0, 14))

        top_controls = ctk.CTkFrame(frame, fg_color="transparent")
        top_controls.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 12))

        ctk.CTkLabel(top_controls, text="Patient:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 8))
        self.req_patient_menu = ctk.CTkOptionMenu(top_controls, values=["No Patients Registered"], width=360)
        self.req_patient_menu.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(top_controls, text="Priority:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 8))
        self.req_priority = ctk.CTkSegmentedButton(top_controls, values=["Routine", "Urgent", "STAT"], selected_color="#4f46e5")
        self.req_priority.set("Routine")
        self.req_priority.pack(side="left")

        preset_bar = ctk.CTkFrame(frame, fg_color="transparent")
        preset_bar.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 10))
        ctk.CTkLabel(preset_bar, text="Quick Panels:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#818cf8").pack(side="left", padx=(0, 10))

        presets = [
            ("Full CBC Panel", ["White Blood Cell Count (WBC)", "Hemoglobin (Hgb)", "Platelet Count (PLT)", "Monocytes (Absolute)"]),
            ("Metabolic Panel", ["Fasting Blood Glucose", "Creatinine (Serum)"]),
            ("Hepatic & Lipid", ["Total Cholesterol", "ALT (SGPT)"]),
        ]
        for label, tests in presets:
            ctk.CTkButton(preset_bar, text=f"+ {label}", height=28, font=ctk.CTkFont(size=11), fg_color="#1e293b", hover_color="#4f46e5", command=lambda t=tests: self.apply_preset_panel(t)).pack(side="left", padx=4)

        ctk.CTkButton(preset_bar, text="Clear All", height=28, width=80, font=ctk.CTkFont(size=11), fg_color="transparent", border_width=1, border_color="#475569", command=lambda: self.apply_preset_panel([], clear=True)).pack(side="right")

        self.test_scroll = ctk.CTkScrollableFrame(frame, label_text="Select Assays / Lab Panel (with Tube Guide)")
        self.test_scroll.grid(row=4, column=0, sticky="nsew", padx=28, pady=(0, 16))
        self.test_vars = {}

        ctk.CTkButton(frame, text="Accession Specimen & Submit Panel Order", height=44, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#4f46e5", hover_color="#4338ca", command=self.submit_panel_order).grid(row=5, column=0, sticky="ew", padx=28, pady=(0, 22))

    def apply_preset_panel(self, test_names, clear=False):
        if clear:
            for var, _, _, _ in self.test_vars.values():
                var.set(False)
            return
        for t in test_names:
            if t in self.test_vars:
                self.test_vars[t][0].set(True)

    def refresh_requisition_view(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT patient_id, mrn, full_name FROM patients ORDER BY full_name ASC")
        p_rows = cur.fetchall()

        self.patient_map = {f"{r[1]} - {r[2]}": r[0] for r in p_rows}
        if self.patient_map:
            vals = list(self.patient_map.keys())
            self.req_patient_menu.configure(values=vals)
            self.req_patient_menu.set(vals[0])
        else:
            self.req_patient_menu.configure(values=["No Patients Registered"])
            self.req_patient_menu.set("No Patients Registered")

        for widget in self.test_scroll.winfo_children():
            widget.destroy()
        self.test_vars.clear()

        cur.execute("SELECT test_name, department, tube_type, ref_range FROM test_catalog ORDER BY department, test_name")
        for idx, (t_name, dept, tube, ref) in enumerate(cur.fetchall()):
            var = ctk.BooleanVar(value=False)
            self.test_vars[t_name] = (var, dept, tube, ref)
            cb = ctk.CTkCheckBox(self.test_scroll, text=f"[{dept}]  {t_name}   •   Tube: {tube}   (Ref: {ref})", variable=var, checkbox_width=20, checkbox_height=20)
            cb.grid(row=idx, column=0, sticky="w", padx=12, pady=6)
        conn.close()

    def submit_panel_order(self):
        sel_p = self.req_patient_menu.get()
        if sel_p not in self.patient_map:
            messagebox.showwarning("No Patient", "Register a patient in the Patient Registry first.")
            return

        chosen = [(name, meta[1], meta[2], meta[3]) for name, meta in self.test_vars.items() if meta[0].get()]
        if not chosen:
            messagebox.showwarning("No Assays Selected", "Check at least one lab test to order.")
            return

        patient_id = self.patient_map[sel_p]
        priority = self.req_priority.get()
        now = datetime.now()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT specimen_id) FROM orders")
        spec_num = cur.fetchone()[0] + 1
        specimen_id = f"MDL-{now.strftime('%Y%m%d')}-{spec_num:03d}"
        date_str = now.strftime("%Y-%m-%d %H:%M")

        for test_name, dept, tube, ref in chosen:
            cur.execute("""
                INSERT INTO orders (specimen_id, patient_id, test_name, department, tube_type, priority, reference_range, order_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (specimen_id, patient_id, test_name, dept, tube, priority, ref, date_str))

        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "ACCESSION_ORDER", specimen_id, f"Ordered {len(chosen)} assays ({priority})")
        messagebox.showinfo("Specimen Accessioned", f"Specimen ID: {specimen_id}\nAssays Ordered: {len(chosen)}\nPriority: {priority}")
        self.show_frame("orders")

    # ==========================================
    # VIEW 3: PATIENT REGISTRY
    # ==========================================
    def build_patients_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["patients"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        card.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(card, text="Register New Patient (Double-click any patient below to view cumulative lab history)", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=16, pady=(12, 6))

        self.p_name = ctk.CTkEntry(card, placeholder_text="Full Name *", width=220)
        self.p_name.grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        self.p_dob = ctk.CTkEntry(card, placeholder_text="DOB (YYYY-MM-DD)", width=140)
        self.p_dob.grid(row=1, column=1, padx=8, pady=(0, 14))

        self.p_sex = ctk.CTkOptionMenu(card, values=["Male", "Female", "Other"], width=105)
        self.p_sex.grid(row=1, column=2, padx=8, pady=(0, 14))

        self.p_phone = ctk.CTkEntry(card, placeholder_text="Phone Number", width=140)
        self.p_phone.grid(row=1, column=3, padx=8, pady=(0, 14))

        self.p_doc = ctk.CTkEntry(card, placeholder_text="Requesting Physician", width=185)
        self.p_doc.grid(row=1, column=4, padx=8, pady=(0, 14))

        ctk.CTkButton(card, text="+ Register", width=110, fg_color="#10b981", hover_color="#059669", command=self.add_patient).grid(row=1, column=5, padx=(8, 16), pady=(0, 14))

        t_frame = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        t_frame.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "MRN", "Full Name", "DOB", "Sex", "Phone", "Requesting Physician")
        widths = [55, 110, 230, 115, 85, 140, 220]
        self.patient_tree = self._create_scrolled_treeview(t_frame, cols, widths, left_align_cols=("Full Name", "Requesting Physician"))
        self.patient_tree.bind("<Double-1>", self._on_patient_double_click)

    def _on_patient_double_click(self, _event=None):
        sel = self.patient_tree.selection()
        if sel:
            pid = self.patient_tree.item(sel[0])["values"][0]
            self.open_patient_history_modal(patient_id=pid)

    def add_patient(self):
        name = self.p_name.get().strip()
        if not name:
            messagebox.showwarning("Required", "Patient Full Name is required.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM patients")
        mrn = f"MRN-{1000 + cur.fetchone()[0] + 1}"
        cur.execute("""
            INSERT INTO patients (mrn, full_name, dob, sex, phone, physician)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (mrn, name, self.p_dob.get().strip() or "N/A", self.p_sex.get(), self.p_phone.get().strip() or "N/A", self.p_doc.get().strip() or "Walk-in / Self"))
        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "REGISTER_PATIENT", mrn, name)
        for entry in (self.p_name, self.p_dob, self.p_phone, self.p_doc):
            entry.delete(0, "end")
        self.refresh_patients()

    def refresh_patients(self):
        for r in self.patient_tree.get_children():
            self.patient_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients ORDER BY patient_id DESC")
        for row in cur.fetchall():
            self.patient_tree.insert("", "end", values=row)
        conn.close()

    # ==========================================
    # VIEW 4: QUALITY CONTROL & LEVEY-JENNINGS CHART
    # ==========================================
    def build_qc_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["qc"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=2)
        frame.grid_rowconfigure(2, weight=1)

        top_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        top_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(top_card, text="Daily Analyzer Quality Control & Westgard Evaluation", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(12, 6))

        self.qc_combo = ctk.CTkOptionMenu(top_card, values=list(QC_TARGETS.keys()), width=360, command=lambda _: self.refresh_qc_view())
        self.qc_combo.grid(row=1, column=0, padx=(16, 10), pady=(0, 14))

        self.qc_val_entry = ctk.CTkEntry(top_card, placeholder_text="Measured QC Value", width=160)
        self.qc_val_entry.grid(row=1, column=1, padx=8, pady=(0, 14))

        ctk.CTkButton(top_card, text="Log QC Run & Evaluate Westgard", fg_color="#4f46e5", hover_color="#4338ca", command=self.log_qc_run).grid(row=1, column=2, padx=10, pady=(0, 14))

        chart_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        chart_card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.lj_canvas = LeveyJenningsCanvas(chart_card)
        self.lj_canvas.pack(fill="both", expand=True, padx=4, pady=4)

        hist_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        hist_card.grid(row=2, column=0, sticky="nsew")
        cols = ("QC ID", "Assay", "Control Level", "Measured", "Target Mean", "Z-Score", "Westgard Rule", "Operator", "Timestamp")
        widths = [65, 190, 145, 90, 95, 80, 175, 175, 135]
        self.qc_tree = self._create_scrolled_treeview(hist_card, cols, widths, left_align_cols=("Assay", "Operator"))

    def log_qc_run(self):
        key = self.qc_combo.get()
        try:
            val = float(self.qc_val_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Value", "Enter a numeric QC measurement.")
            return

        assay, level, mean, sd, unit = QC_TARGETS[key]
        z = round((val - mean) / sd, 2)
        if abs(z) > 3.0:
            status = "FAIL (1-3s Out of Control)"
        elif abs(z) > 2.0:
            status = "WARN (1-2s Warning)"
        else:
            status = "PASS (In Control)"

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO qc_logs (assay_key, assay_name, level, measured_val, target_mean, target_sd, z_score, westgard_status, operator, run_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (key, assay, level, val, mean, sd, z, status, self.current_user, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "LOG_QC", assay, f"{level}: {val} {unit} (Z={z}, {status})")
        self.qc_val_entry.delete(0, "end")
        self.refresh_qc_view()

        if "FAIL" in status:
            messagebox.showerror("Westgard 1-3s Violation", f"QC Out of Control ({val} {unit}, Z = {z})!\n\nRecalibrate analyzer before releasing patient results.")

    def refresh_qc_view(self):
        key = self.qc_combo.get()
        assay, level, mean, sd, unit = QC_TARGETS[key]

        for r in self.qc_tree.get_children():
            self.qc_tree.delete(r)

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT qc_id, assay_name, level, measured_val, target_mean, z_score, westgard_status, operator, run_date
            FROM qc_logs WHERE assay_key = ? ORDER BY qc_id DESC LIMIT 20
        """, (key,))
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            self.qc_tree.insert("", "end", values=row)

        chart_pts = [(r[8], r[3], r[5], r[6]) for r in reversed(rows)]
        self.lj_canvas.plot(f"Levey-Jennings Chart: {key}  (Mean: {mean} {unit}, 1SD: {sd})", mean, sd, chart_pts)

    # ==========================================
    # VIEW 5: TEST CATALOG & CRITICAL CUTOFFS
    # ==========================================
    def build_catalog_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["catalog"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        add_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        add_card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(add_card, text="Add Custom Assay, Tube Type & Critical Panic Thresholds", font=ctk.CTkFont(size=15, weight="bold")).grid(row=0, column=0, columnspan=9, sticky="w", padx=16, pady=(12, 6))

        self.c_name = ctk.CTkEntry(add_card, placeholder_text="Assay Name *", width=165)
        self.c_name.grid(row=1, column=0, padx=(16, 4), pady=(0, 14))

        self.c_dept = ctk.CTkOptionMenu(add_card, values=["Hematology", "Chemistry", "Microscopy", "Immunohematology", "Microbiology"], width=125)
        self.c_dept.grid(row=1, column=1, padx=4, pady=(0, 14))

        self.c_unit = ctk.CTkEntry(add_card, placeholder_text="Unit", width=75)
        self.c_unit.grid(row=1, column=2, padx=4, pady=(0, 14))

        self.c_low = ctk.CTkEntry(add_card, placeholder_text="Low", width=65)
        self.c_low.grid(row=1, column=3, padx=4, pady=(0, 14))

        self.c_high = ctk.CTkEntry(add_card, placeholder_text="High", width=65)
        self.c_high.grid(row=1, column=4, padx=4, pady=(0, 14))

        self.c_crit_high = ctk.CTkEntry(add_card, placeholder_text="Panic High", width=80)
        self.c_crit_high.grid(row=1, column=5, padx=4, pady=(0, 14))

        self.c_tube = ctk.CTkEntry(add_card, placeholder_text="Tube (e.g. Gold SST)", width=125)
        self.c_tube.grid(row=1, column=6, padx=4, pady=(0, 14))

        self.c_ref = ctk.CTkEntry(add_card, placeholder_text="Display Range *", width=135)
        self.c_ref.grid(row=1, column=7, padx=4, pady=(0, 14))

        ctk.CTkButton(add_card, text="+ Add", width=80, fg_color="#4f46e5", hover_color="#4338ca", command=self.add_assay).grid(row=1, column=8, padx=(4, 16), pady=(0, 14))

        t_frame = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        t_frame.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "Assay Name", "Dept", "Unit", "Low", "High", "Crit Low", "Crit High", "Tube", "Reference Interval")
        widths = [45, 210, 115, 75, 65, 65, 70, 75, 135, 155]
        self.cat_tree = self._create_scrolled_treeview(t_frame, cols, widths, left_align_cols=("Assay Name",))

    def add_assay(self):
        name = self.c_name.get().strip()
        ref = self.c_ref.get().strip()
        if not name or not ref:
            messagebox.showwarning("Required", "Assay Name and Display Range are required.")
            return
        try:
            low = float(self.c_low.get().strip()) if self.c_low.get().strip() else None
            high = float(self.c_high.get().strip()) if self.c_high.get().strip() else None
            chigh = float(self.c_crit_high.get().strip()) if self.c_crit_high.get().strip() else None
        except ValueError:
            messagebox.showwarning("Invalid Number", "Low, High, and Panic High must be numeric.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO test_catalog (test_name, department, unit, low_val, high_val, crit_low, crit_high, delta_pct, tube_type, ref_range)
                VALUES (?, ?, ?, ?, ?, NULL, ?, 35.0, ?, ?)
            """, (name, self.c_dept.get(), self.c_unit.get().strip(), low, high, chigh, self.c_tube.get().strip() or "Gold (SST)", ref))
            conn.commit()
            log_audit(self.current_user, self.current_role, "ADD_ASSAY", name, ref)
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "An assay with that name already exists.")
        conn.close()

        for e in (self.c_name, self.c_unit, self.c_low, self.c_high, self.c_crit_high, self.c_tube, self.c_ref):
            e.delete(0, "end")
        self.refresh_catalog()

    def refresh_catalog(self):
        for r in self.cat_tree.get_children():
            self.cat_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT test_id, test_name, department, unit, low_val, high_val, crit_low, crit_high, tube_type, ref_range FROM test_catalog ORDER BY department, test_name")
        for row in cur.fetchall():
            self.cat_tree.insert("", "end", values=row)
        conn.close()

    # ==========================================
    # VIEW 6: AUDIT TRAIL, STAFF ROSTER & DB ADMIN
    # ==========================================
    def build_audit_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["audit"] = frame
        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(top_bar, text="Chain-of-Custody Audit Log & Staff Roster", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=16, pady=14)
        ctk.CTkButton(top_bar, text="Backup Database (.db)", fg_color="#10b981", hover_color="#059669", command=self.backup_database).pack(side="right", padx=16, pady=12)

        # Left: Audit Log Table
        t_frame = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        t_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        cols = ("Audit ID", "Timestamp", "Operator", "Role", "Action", "Reference ID", "Details")
        widths = [65, 145, 175, 170, 130, 130, 260]
        self.audit_tree = self._create_scrolled_treeview(t_frame, cols, widths, left_align_cols=("Operator", "Role", "Details"))

        # Right: Staff & PIN Manager (Pathologist / Admin Control)
        staff_card = ctk.CTkFrame(frame, corner_radius=12, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        staff_card.grid(row=1, column=1, sticky="nsew")
        staff_card.grid_rowconfigure(3, weight=1)
        staff_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(staff_card, text="Registered Laboratory Staff", font=ctk.CTkFont(size=14, weight="bold"), text_color="#818cf8").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        add_box = ctk.CTkFrame(staff_card, fg_color="transparent")
        add_box.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        self.s_pin = ctk.CTkEntry(add_box, placeholder_text="PIN", width=70)
        self.s_pin.pack(side="left", padx=(0, 4))
        self.s_name = ctk.CTkEntry(add_box, placeholder_text="Full Name & Title", width=155)
        self.s_name.pack(side="left", padx=4)
        self.s_role = ctk.CTkOptionMenu(add_box, values=["Medical Technologist (RMT)", "Pathologist"], width=120)
        self.s_role.pack(side="left", padx=(4, 0))

        ctk.CTkButton(staff_card, text="+ Add / Update Staff PIN", height=30, fg_color="#4f46e5", hover_color="#4338ca", command=self.add_staff_member).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))

        s_table_wrap = ctk.CTkFrame(staff_card, fg_color="transparent")
        s_table_wrap.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.staff_tree = self._create_scrolled_treeview(s_table_wrap, ("PIN", "Staff Member", "Role"), [60, 180, 165], left_align_cols=("Staff Member", "Role"))

    def add_staff_member(self):
        if "Pathologist" not in self.current_role:
            messagebox.showwarning("Pathologist Required", "Only the Pathologist (Gaia Aubrey Manalo, MD) can add or modify staff PINs.")
            return
        pin = self.s_pin.get().strip()
        name = self.s_name.get().strip()
        role = self.s_role.get()
        if not pin or not name:
            messagebox.showwarning("Required", "Both PIN and Full Name are required.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO staff (pin, full_name, role) VALUES (?, ?, ?)", (pin, name, role))
        conn.commit()
        conn.close()

        log_audit(self.current_user, self.current_role, "UPDATE_STAFF", f"PIN-{pin[:2]}**", f"{name} ({role})")
        self.s_pin.delete(0, "end")
        self.s_name.delete(0, "end")
        self.refresh_staff_list()
        self.refresh_audit()

    def refresh_staff_list(self):
        for r in self.staff_tree.get_children():
            self.staff_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT pin, full_name, role FROM staff ORDER BY pin ASC")
        for pin, name, role in cur.fetchall():
            masked = f"{pin[:2]}**" if "Pathologist" not in self.current_role else pin
            self.staff_tree.insert("", "end", values=(masked, name, role))
        conn.close()

    def refresh_audit(self):
        for r in self.audit_tree.get_children():
            self.audit_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 250")
        for row in cur.fetchall():
            self.audit_tree.insert("", "end", values=row)
        conn.close()

    def backup_database(self):
        dest = filedialog.asksaveasfilename(
            defaultextension=".db",
            initialfile=f"MonocytesLIS_Backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
            filetypes=[("SQLite Database", "*.db")]
        )
        if dest:
            shutil.copy2(DB_NAME, dest)
            log_audit(self.current_user, self.current_role, "DB_BACKUP", os.path.basename(dest), "Full database snapshot saved")
            self.refresh_audit()
            messagebox.showinfo("Backup Complete", f"Database safely backed up to:\n{dest}")

if __name__ == "__main__":
    init_db()
    app = MonocytesDelegatesLIS()
    app.mainloop()
