import sqlite3
import os
import csv
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from fpdf import FPDF

# --- UI Theme Setup ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = "monocytes_delegates_lis.db"

DEFAULT_TESTS = [
    ("White Blood Cell Count (WBC)", "Hematology", "x10^9/L", 4.5, 11.0, "4.5 - 11.0 x10^9/L"),
    ("Hemoglobin (Hgb)", "Hematology", "g/dL", 12.0, 17.5, "12.0 - 17.5 g/dL"),
    ("Platelet Count (PLT)", "Hematology", "x10^9/L", 150.0, 450.0, "150 - 450 x10^9/L"),
    ("Monocytes (Absolute)", "Hematology", "x10^9/L", 0.2, 0.8, "0.2 - 0.8 x10^9/L"),
    ("Fasting Blood Glucose", "Chemistry", "mg/dL", 70.0, 99.0, "70 - 99 mg/dL"),
    ("HbA1c", "Chemistry", "%", 4.0, 5.6, "4.0 - 5.6 %"),
    ("Total Cholesterol", "Chemistry", "mg/dL", 0.0, 200.0, "< 200 mg/dL"),
    ("Creatinine (Serum)", "Chemistry", "mg/dL", 0.6, 1.3, "0.6 - 1.3 mg/dL"),
    ("ALT (SGPT)", "Chemistry", "U/L", 7.0, 56.0, "7 - 56 U/L"),
    ("Urinalysis (Complete)", "Microscopy", "", None, None, "Negative / Normal"),
    ("Blood Typing (ABO/Rh)", "Immunohematology", "", None, None, "Qualitative")
]

def safe_pdf_text(text):
    """Sanitizes text so FPDF2 Helvetica never crashes on special Unicode characters."""
    if text is None:
        return ""
    cleaned = str(text).replace("—", "-").replace("–", "-").replace("•", "-")
    return cleaned.encode("latin-1", "replace").decode("latin-1")

# --- Database Layer ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_catalog (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT UNIQUE NOT NULL,
            department TEXT,
            unit TEXT,
            low_val REAL,
            high_val REAL,
            ref_range TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            specimen_id TEXT NOT NULL,
            patient_id INTEGER,
            test_name TEXT NOT NULL,
            department TEXT,
            priority TEXT DEFAULT 'Routine',
            status TEXT DEFAULT 'Pending',
            result_value TEXT DEFAULT '',
            flag TEXT DEFAULT '',
            reference_range TEXT,
            notes TEXT DEFAULT '',
            verified_by TEXT DEFAULT '',
            order_date TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM test_catalog")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO test_catalog (test_name, department, unit, low_val, high_val, ref_range)
            VALUES (?, ?, ?, ?, ?, ?)
        """, DEFAULT_TESTS)

    conn.commit()
    conn.close()

# --- Consolidated Clinical PDF Report ---
class MonocytesReportPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 32, 'F')
        self.set_xy(10, 8)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 17)
        self.cell(0, 9, "MONOCYTES DELEGATES LIS", new_x="LMARGIN", new_y="NEXT", align="L")
        self.set_x(10)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 5, "Clinical Diagnostic & Pathology Laboratory | Official Diagnostic Report", new_x="LMARGIN", new_y="NEXT", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(203, 213, 225)
        self.line(10, 275, 200, 275)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Monocytes Delegates LIS - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} - Confidential Medical Record", align="C")

def generate_specimen_pdf(patient_info, specimen_id, order_rows, save_path):
    pdf = MonocytesReportPDF()
    pdf.add_page()
    pdf.set_text_color(15, 23, 42)

    # Demographics Card
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, 38, 190, 28, 'F')
    pdf.set_xy(14, 41)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 6, safe_pdf_text(f"PATIENT: {patient_info['full_name']} (MRN: {patient_info['mrn']})"), border=0)
    pdf.cell(90, 6, safe_pdf_text(f"SPECIMEN ID: {specimen_id}"), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(95, 6, safe_pdf_text(f"DOB / Sex: {patient_info['dob']}  |  {patient_info['sex']}"), border=0)
    pdf.cell(90, 6, safe_pdf_text(f"Collection Date: {order_rows[0]['order_date']}"), border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(14)
    pdf.cell(95, 6, safe_pdf_text(f"Ordering Physician: {patient_info['physician']}"), border=0)
    pdf.cell(90, 6, safe_pdf_text(f"Priority: {order_rows[0]['priority']}"), border=0, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # Table Header
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9.5)
    pdf.cell(62, 9, "Investigation / Assay", border=1, fill=True)
    pdf.cell(32, 9, "Department", border=1, fill=True, align="C")
    pdf.cell(35, 9, "Result", border=1, fill=True, align="C")
    pdf.cell(21, 9, "Flag", border=1, fill=True, align="C")
    pdf.cell(40, 9, "Reference Interval", border=1, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")

    # Rows
    pdf.set_font("Helvetica", "", 9.5)
    for row in order_rows:
        pdf.set_text_color(15, 23, 42)
        pdf.cell(62, 9, safe_pdf_text(row['test_name']), border=1)
        pdf.cell(32, 9, safe_pdf_text(row['department']), border=1, align="C")
        pdf.cell(35, 9, safe_pdf_text(row['result_value']), border=1, align="C")

        flag_str = str(row['flag'])
        if flag_str in ["HIGH", "REJECTED"]:
            pdf.set_text_color(220, 38, 38)
            pdf.set_font("Helvetica", "B", 9.5)
        elif flag_str == "LOW":
            pdf.set_text_color(217, 119, 6)
            pdf.set_font("Helvetica", "B", 9.5)
        elif flag_str == "NORMAL":
            pdf.set_text_color(22, 163, 74)
            pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(21, 9, safe_pdf_text(flag_str), border=1, align="C")

        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.cell(40, 9, safe_pdf_text(row['reference_range']), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        if row['notes']:
            pdf.set_font("Helvetica", "I", 8.5)
            pdf.set_text_color(100, 116, 139)
            pdf.cell(190, 6, safe_pdf_text(f"   Clinical Note: {row['notes']}"), border="LRB", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9.5)

    pdf.ln(16)
    verifiers = ", ".join(sorted(set(r['verified_by'] for r in order_rows if r['verified_by'])))
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, safe_pdf_text(f"Electronically Verified By: {verifiers or 'Authorized Laboratory Personnel'}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 5, "End of Clinical Laboratory Report - Monocytes Delegates LIS", new_x="LMARGIN", new_y="NEXT")

    pdf.output(save_path)

# --- Main Application ---
class MonocytesDelegatesLIS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Monocytes Delegates LIS - Clinical Laboratory Information System")
        self.geometry("1280x790")
        self.minsize(1120, 680)

        self.anim_job = None  # Tracks active gauge animation

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Navigation Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=235, corner_radius=0, fg_color=("#f1f5f9", "#090d16"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        brand_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_box.grid(row=0, column=0, padx=20, pady=(24, 20), sticky="ew")
        ctk.CTkLabel(brand_box, text="MONOCYTES", font=ctk.CTkFont(size=20, weight="bold"), text_color=("#1e293b", "#f8fafc")).pack(anchor="w")
        ctk.CTkLabel(brand_box, text="DELEGATES LIS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#6366f1").pack(anchor="w")
        ctk.CTkLabel(brand_box, text="v2.6 Clinical Diagnostics", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", pady=(2, 0))

        self.nav_buttons = {}
        nav_items = [
            ("orders", "Worklist & Results", "transparent"),
            ("new_order", "+ New Requisition", "#4f46e5"),
            ("patients", "Patient Registry", "transparent"),
            ("catalog", "Test Catalog & Ranges", "transparent"),
        ]

        for idx, (key, label, color) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=label, height=42, anchor="w", corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold" if key == "new_order" else "normal"),
                fg_color=color,
                hover_color="#4338ca" if key == "new_order" else ("#e2e8f0", "#1e293b"),
                text_color="white" if key == "new_order" else ("#0f172a", "#e2e8f0"),
                command=lambda k=key: self.show_frame(k)
            )
            btn.grid(row=idx, column=0, padx=16, pady=5, sticky="ew")
            self.nav_buttons[key] = btn

        footer_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_box.grid(row=7, column=0, padx=18, pady=20, sticky="ew")
        ctk.CTkLabel(footer_box, text="Interface Theme", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")
        self.theme_menu = ctk.CTkOptionMenu(
            footer_box, values=["Dark", "Light"], fg_color=("#e2e8f0", "#1e293b"),
            button_color="#4f46e5", text_color=("#0f172a", "#f8fafc"),
            command=self.change_theme
        )
        self.theme_menu.pack(fill="x", pady=(4, 0))

        # --- View Containers ---
        self.frames = {}
        self.build_orders_frame()
        self.build_new_order_frame()
        self.build_patients_frame()
        self.build_catalog_frame()

        self.show_frame("orders")

    def change_theme(self, mode):
        ctk.set_appearance_mode(mode)
        self.apply_treeview_theme()

    def apply_treeview_theme(self):
        style = ttk.Style()
        style.theme_use("default")
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg = "#0f172a" if is_dark else "#ffffff"
        fg = "#f1f5f9" if is_dark else "#0f172a"
        head_bg = "#1e293b" if is_dark else "#e2e8f0"
        head_fg = "#f8fafc" if is_dark else "#0f172a"

        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=32, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=head_bg, foreground=head_fg, relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#4f46e5")], foreground=[("selected", "#ffffff")])

    def show_frame(self, name):
        for k, frame in self.frames.items():
            frame.grid_forget()
            if k != "new_order":
                self.nav_buttons[k].configure(fg_color=("#e2e8f0", "#1e293b") if k == name else "transparent")
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=24, pady=20)

        if name == "orders":
            self.refresh_orders()
        elif name == "new_order":
            self.refresh_requisition_view()
        elif name == "patients":
            self.refresh_patients()
        elif name == "catalog":
            self.refresh_catalog()

    # ==========================================
    # VIEW 1: WORKLIST & ANIMATED RESULT INSPECTOR
    # ==========================================
    def build_orders_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["orders"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # KPI Cards Row
        kpi_row = ctk.CTkFrame(frame, fg_color="transparent")
        kpi_row.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.kpi_total = self._make_kpi_card(kpi_row, 0, "TOTAL ASSAYS", "0", "#6366f1")
        self.kpi_pending = self._make_kpi_card(kpi_row, 1, "PENDING", "0", "#f59e0b")
        self.kpi_stat = self._make_kpi_card(kpi_row, 2, "STAT / URGENT", "0", "#ef4444")
        self.kpi_done = self._make_kpi_card(kpi_row, 3, "VERIFIED", "0", "#10b981")

        # Filter & Export Toolbar
        toolbar = ctk.CTkFrame(frame, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_orders())
        ctk.CTkEntry(toolbar, placeholder_text="Search Patient, MRN, Specimen ID, or Test...", textvariable=self.search_var, width=320, height=36).pack(side="left", padx=(0, 10))

        self.status_filter = ctk.CTkSegmentedButton(toolbar, values=["All", "Pending", "Completed", "Rejected"], selected_color="#4f46e5", command=lambda _: self.refresh_orders())
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=5)

        ctk.CTkButton(toolbar, text="Export CSV Log", width=120, height=36, fg_color=("#e2e8f0", "#1e293b"), text_color=("#0f172a", "#f8fafc"), hover_color="#4f46e5", command=self.export_csv).pack(side="right")

        # Worklist Table
        table_card = ctk.CTkFrame(frame, corner_radius=10)
        table_card.grid(row=2, column=0, sticky="nsew")
        self.apply_treeview_theme()

        cols = ("ID", "Specimen ID", "Patient", "Assay / Test", "Priority", "Status", "Result", "Flag", "Ref Range")
        self.order_tree = ttk.Treeview(table_card, columns=cols, show="headings")
        widths = [45, 135, 165, 195, 80, 90, 100, 80, 135]
        for c, w in zip(cols, widths):
            self.order_tree.heading(c, text=c)
            self.order_tree.column(c, width=w, anchor="center" if c not in ["Patient", "Assay / Test"] else "w")

        self.order_tree.tag_configure("stat", foreground="#f87171")
        self.order_tree.tag_configure("high", foreground="#ef4444")
        self.order_tree.tag_configure("low", foreground="#f59e0b")
        self.order_tree.tag_configure("normal", foreground="#10b981")
        self.order_tree.tag_configure("rejected", foreground="#94a3b8")

        self.order_tree.bind("<<TreeviewSelect>>", self.on_row_select)

        self.order_tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        sb = ttk.Scrollbar(table_card, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # --- Animated Result Visualizer Bar ---
        viz_card = ctk.CTkFrame(frame, corner_radius=10, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        viz_card.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        viz_card.grid_columnconfigure(1, weight=1)

        self.viz_title = ctk.CTkLabel(viz_card, text="Select an assay row above to inspect result range", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray")
        self.viz_title.grid(row=0, column=0, padx=16, pady=10, sticky="w")

        self.viz_bar = ctk.CTkProgressBar(viz_card, height=14, corner_radius=7, progress_color="#4f46e5")
        self.viz_bar.set(0)
        self.viz_bar.grid(row=0, column=1, padx=16, pady=10, sticky="ew")

        self.viz_badge = ctk.CTkLabel(
            viz_card, text="AWAITING", width=115, height=26, corner_radius=13,
            fg_color=("#e2e8f0", "#1e293b"), text_color="gray", font=ctk.CTkFont(size=11, weight="bold")
        )
        self.viz_badge.grid(row=0, column=2, padx=16, pady=10, sticky="e")

        # --- Action & Verification Dock ---
        dock = ctk.CTkFrame(frame, corner_radius=10)
        dock.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        ctk.CTkLabel(dock, text="Result:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=12)
        self.res_input = ctk.CTkEntry(dock, placeholder_text="Value (e.g. 7.4)", width=130)
        self.res_input.pack(side="left", padx=4)

        ctk.CTkLabel(dock, text="Note:").pack(side="left", padx=(8, 5))
        self.note_input = ctk.CTkEntry(dock, placeholder_text="Clinical note / rejection reason", width=200)
        self.note_input.pack(side="left", padx=4)

        ctk.CTkLabel(dock, text="Tech:").pack(side="left", padx=(8, 5))
        self.tech_input = ctk.CTkEntry(dock, placeholder_text="Initials", width=80)
        self.tech_input.pack(side="left", padx=4)

        ctk.CTkButton(dock, text="Verify Result", width=115, fg_color="#10b981", hover_color="#059669", command=self.verify_result).pack(side="left", padx=(10, 4))
        ctk.CTkButton(dock, text="Reject Sample", width=110, fg_color="#dc2626", hover_color="#b91c1c", command=self.reject_sample).pack(side="left", padx=4)
        ctk.CTkButton(dock, text="Print Specimen PDF", width=150, fg_color="#4f46e5", hover_color="#4338ca", command=self.export_specimen_report).pack(side="right", padx=15)

    def _make_kpi_card(self, parent, col, title, val, accent):
        card = ctk.CTkFrame(parent, corner_radius=10, border_width=1, border_color=("#cbd5e1", "#1e293b"))
        card.grid(row=0, column=col, padx=6 if col in (1, 2) else (0, 6) if col == 0 else (6, 0), sticky="ew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(anchor="w", padx=16, pady=(10, 0))
        lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=accent)
        lbl.pack(anchor="w", padx=16, pady=(2, 10))
        return lbl

    def on_row_select(self, _event=None):
        sel = self.order_tree.selection()
        if not sel:
            return
        vals = self.order_tree.item(sel[0])["values"]
        test_name, status, res_str, flag, ref_range = vals[3], vals[5], str(vals[6]), str(vals[7]), str(vals[8])

        if status == "Pending":
            self.viz_title.configure(text=f"{test_name}  |  Ref: {ref_range}", text_color=("#0f172a", "#f8fafc"))
            self.viz_badge.configure(text="PENDING", fg_color=("#e2e8f0", "#1e293b"), text_color="#94a3b8")
            self.animate_gauge(0.0, "#4f46e5")
            return

        if flag == "HIGH":
            color, bg_tint, badge_txt, target = "#ef4444", ("#fee2e2", "#450a0a"), "HIGH (OVER)", 0.96
        elif flag == "LOW":
            color, bg_tint, badge_txt, target = "#f59e0b", ("#fef3c7", "#451a03"), "LOW (UNDER)", 0.22
        elif flag == "REJECTED":
            color, bg_tint, badge_txt, target = "#64748b", ("#e2e8f0", "#1e293b"), "REJECTED", 0.0
        else:
            color, bg_tint, badge_txt, target = "#10b981", ("#d1fae5", "#064e3b"), "NORMAL", 0.58

        # Calculate proportional gauge position if numeric
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT low_val, high_val FROM test_catalog WHERE test_name = ?", (test_name,))
        cat = cur.fetchone()
        conn.close()

        if cat and cat[0] is not None and cat[1] is not None:
            try:
                num_val = float(res_str.split()[0])
                low, high = float(cat[0]), float(cat[1])
                span = max(high - low, 0.001)
                # Map low->0.30, high->0.75 so normal sits cleanly in the middle
                ratio = 0.30 + ((num_val - low) / span) * 0.45
                target = max(0.08, min(0.98, ratio))
            except (ValueError, IndexError):
                pass

        self.viz_title.configure(text=f"{test_name}: {res_str}   (Ref: {ref_range})", text_color=("#0f172a", "#f8fafc"))
        self.viz_badge.configure(text=badge_txt, fg_color=bg_tint, text_color=color)
        self.animate_gauge(target, color)

    def animate_gauge(self, target_val, bar_color):
        """Smoothly animates the progress gauge from 0 to the target result position."""
        if self.anim_job:
            self.after_cancel(self.anim_job)
            self.anim_job = None

        self.viz_bar.configure(progress_color=bar_color)
        self.viz_bar.set(0.0)
        steps = 18
        current_step = [0]

        def step():
            current_step[0] += 1
            t = current_step[0] / steps
            # Ease-out cubic curve for smooth deceleration
            eased = 1 - pow(1 - t, 3)
            self.viz_bar.set(target_val * eased)
            if current_step[0] < steps:
                self.anim_job = self.after(14, step)
            else:
                self.anim_job = None

        self.anim_job = self.after(10, step)

    def refresh_orders(self, reselect_id=None):
        for r in self.order_tree.get_children():
            self.order_tree.delete(r)

        q = f"%{self.search_var.get().strip()}%"
        st = self.status_filter.get()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM orders")
        self.kpi_total.configure(text=str(cur.fetchone()[0]))
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        self.kpi_pending.configure(text=str(cur.fetchone()[0]))
        cur.execute("SELECT COUNT(*) FROM orders WHERE priority='STAT' AND status='Pending'")
        self.kpi_stat.configure(text=str(cur.fetchone()[0]))
        cur.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'")
        self.kpi_done.configure(text=str(cur.fetchone()[0]))

        sql = """
            SELECT o.order_id, o.specimen_id, p.full_name, o.test_name, o.priority, o.status, o.result_value, o.flag, o.reference_range
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE (p.full_name LIKE ? OR p.mrn LIKE ? OR o.specimen_id LIKE ? OR o.test_name LIKE ?)
        """
        params = [q, q, q, q]
        if st != "All":
            sql += " AND o.status = ?"
            params.append(st)
        sql += " ORDER BY o.order_id DESC"

        cur.execute(sql, params)
        target_item = None
        for row in cur.fetchall():
            tags = ()
            if row[5] == "Rejected":
                tags = ("rejected",)
            elif row[7] == "HIGH":
                tags = ("high",)
            elif row[7] == "LOW":
                tags = ("low",)
            elif row[7] == "NORMAL":
                tags = ("normal",)
            elif row[4] == "STAT" and row[5] == "Pending":
                tags = ("stat",)
            item_id = self.order_tree.insert("", "end", values=row, tags=tags)
            if reselect_id and row[0] == reselect_id:
                target_item = item_id
        conn.close()

        if target_item:
            self.order_tree.selection_set(target_item)
            self.order_tree.focus(target_item)
            self.on_row_select()

    def verify_result(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select an order row first.")
            return

        raw_val = self.res_input.get().strip()
        if not raw_val:
            messagebox.showwarning("Input Required", "Enter a result value.")
            return

        note = self.note_input.get().strip()
        tech = self.tech_input.get().strip() or "RMT Staff"
        item = self.order_tree.item(sel[0])["values"]
        order_id, test_name = item[0], item[3]

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT unit, low_val, high_val FROM test_catalog WHERE test_name = ?", (test_name,))
        cat = cur.fetchone()

        flag = "NORMAL"
        display_val = raw_val
        if cat:
            unit, low, high = cat
            try:
                num = float(raw_val)
                if low is not None and num < low:
                    flag = "LOW"
                elif high is not None and num > high:
                    flag = "HIGH"
                display_val = f"{raw_val} {unit}".strip()
            except ValueError:
                pass

        cur.execute("""
            UPDATE orders SET result_value = ?, flag = ?, status = 'Completed', notes = ?, verified_by = ?
            WHERE order_id = ?
        """, (display_val, flag, note, tech, order_id))
        conn.commit()
        conn.close()

        self.res_input.delete(0, "end")
        self.note_input.delete(0, "end")
        self.refresh_orders(reselect_id=order_id)

    def reject_sample(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Select a specimen row to reject.")
            return
        reason = self.note_input.get().strip()
        if not reason:
            messagebox.showwarning("Reason Required", "Type the rejection reason in the Note box (e.g., Hemolyzed, QNS, Clotted).")
            return
        tech = self.tech_input.get().strip() or "RMT Staff"
        order_id = self.order_tree.item(sel[0])["values"][0]

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            UPDATE orders SET result_value = 'Specimen Rejected', flag = 'REJECTED', status = 'Rejected', notes = ?, verified_by = ?
            WHERE order_id = ?
        """, (reason, tech, order_id))
        conn.commit()
        conn.close()
        self.note_input.delete(0, "end")
        self.refresh_orders(reselect_id=order_id)

    def export_specimen_report(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("Selection Required", "Click on an order row in the table first, then click Print Specimen PDF.")
            return

        specimen_id = self.order_tree.item(sel[0])["values"][1]
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.mrn, p.full_name, p.dob, p.sex, p.physician,
                   o.test_name, o.department, o.priority, o.status, o.result_value, o.flag, o.reference_range, o.notes, o.verified_by, o.order_date
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE o.specimen_id = ?
        """, (specimen_id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            messagebox.showerror("Not Found", "No records found for this Specimen ID.")
            return

        if any(r[8] == "Pending" for r in rows):
            if not messagebox.askyesno("Pending Assays", "Some tests under this Specimen ID are still Pending. Generate partial report anyway?"):
                return

        patient_info = {
            "mrn": rows[0][0], "full_name": rows[0][1], "dob": rows[0][2],
            "sex": rows[0][3], "physician": rows[0][4]
        }
        order_dicts = [{
            "test_name": r[5], "department": r[6], "priority": r[7], "status": r[8],
            "result_value": r[9] or "Pending", "flag": r[10] or "-", "reference_range": r[11],
            "notes": r[12], "verified_by": r[13], "order_date": r[14]
        } for r in rows]

        clean_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in patient_info['full_name'])
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"MonocytesLIS_{specimen_id}_{clean_name}.pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if path:
            try:
                generate_specimen_pdf(patient_info, specimen_id, order_dicts, path)
                messagebox.showinfo("PDF Report Ready", f"Clinical PDF saved to:\n{path}")
                if os.name == "nt":
                    os.startfile(path)
                else:
                    webbrowser.open(path)
            except Exception as e:
                messagebox.showerror("PDF Error", f"Could not generate PDF:\n{e}")

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
            writer.writerow(["Order ID", "Specimen ID", "Patient", "Assay", "Priority", "Status", "Result", "Flag", "Reference Range"])
            for row_id in self.order_tree.get_children():
                writer.writerow(self.order_tree.item(row_id)["values"])
        messagebox.showinfo("Export Complete", "Worklist log exported to CSV.")

    # ==========================================
    # VIEW 2: MULTI-TEST REQUISITION BUILDER
    # ==========================================
    def build_new_order_frame(self):
        frame = ctk.CTkFrame(self, corner_radius=12)
        self.frames["new_order"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(frame, text="New Laboratory Requisition & Panel Order", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(frame, text="Select a patient and check one or more assays to accession under a unified Specimen ID.", text_color="gray").grid(row=1, column=0, sticky="w", padx=28, pady=(0, 18))

        top_controls = ctk.CTkFrame(frame, fg_color="transparent")
        top_controls.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 14))

        ctk.CTkLabel(top_controls, text="Patient:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 8))
        self.req_patient_menu = ctk.CTkOptionMenu(top_controls, values=["No Patients Registered"], width=320)
        self.req_patient_menu.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(top_controls, text="Priority:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 8))
        self.req_priority = ctk.CTkSegmentedButton(top_controls, values=["Routine", "Urgent", "STAT"], selected_color="#4f46e5")
        self.req_priority.set("Routine")
        self.req_priority.pack(side="left")

        self.test_scroll = ctk.CTkScrollableFrame(frame, label_text="Select Assays / Lab Panel")
        self.test_scroll.grid(row=3, column=0, sticky="nsew", padx=28, pady=(0, 16))
        self.test_vars = {}

        ctk.CTkButton(frame, text="Accession Specimen & Submit Panel Order", height=44, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#4f46e5", hover_color="#4338ca", command=self.submit_panel_order).grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 24))

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

        cur.execute("SELECT test_name, department, ref_range FROM test_catalog ORDER BY department, test_name")
        for idx, (t_name, dept, ref) in enumerate(cur.fetchall()):
            var = ctk.BooleanVar(value=False)
            self.test_vars[t_name] = (var, dept, ref)
            cb = ctk.CTkCheckBox(self.test_scroll, text=f"[{dept}]  {t_name}   (Ref: {ref})", variable=var, checkbox_width=20, checkbox_height=20)
            cb.grid(row=idx, column=0, sticky="w", padx=12, pady=6)
        conn.close()

    def submit_panel_order(self):
        sel_p = self.req_patient_menu.get()
        if sel_p not in self.patient_map:
            messagebox.showwarning("No Patient", "Register a patient in the Patient Registry first.")
            return

        chosen = [(name, meta[1], meta[2]) for name, meta in self.test_vars.items() if meta[0].get()]
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

        for test_name, dept, ref in chosen:
            cur.execute("""
                INSERT INTO orders (specimen_id, patient_id, test_name, department, priority, reference_range, order_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (specimen_id, patient_id, test_name, dept, priority, ref, date_str))

        conn.commit()
        conn.close()

        messagebox.showinfo("Specimen Accessioned", f"Specimen ID: {specimen_id}\nAssays Ordered: {len(chosen)}")
        self.show_frame("orders")

    # ==========================================
    # VIEW 3: PATIENT REGISTRY
    # ==========================================
    def build_patients_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["patients"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        card = ctk.CTkFrame(frame, corner_radius=10)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(card, text="Register New Patient", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=5, sticky="w", padx=16, pady=(12, 6))

        self.p_name = ctk.CTkEntry(card, placeholder_text="Full Name *", width=200)
        self.p_name.grid(row=1, column=0, padx=(16, 8), pady=(0, 14))

        self.p_dob = ctk.CTkEntry(card, placeholder_text="DOB (YYYY-MM-DD)", width=140)
        self.p_dob.grid(row=1, column=1, padx=8, pady=(0, 14))

        self.p_sex = ctk.CTkOptionMenu(card, values=["Male", "Female", "Other"], width=105)
        self.p_sex.grid(row=1, column=2, padx=8, pady=(0, 14))

        self.p_phone = ctk.CTkEntry(card, placeholder_text="Phone Number", width=140)
        self.p_phone.grid(row=1, column=3, padx=8, pady=(0, 14))

        self.p_doc = ctk.CTkEntry(card, placeholder_text="Requesting Physician", width=175)
        self.p_doc.grid(row=1, column=4, padx=8, pady=(0, 14))

        ctk.CTkButton(card, text="+ Register", width=110, fg_color="#10b981", hover_color="#059669", command=self.add_patient).grid(row=1, column=5, padx=(8, 16), pady=(0, 14))

        t_frame = ctk.CTkFrame(frame, corner_radius=10)
        t_frame.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "MRN", "Full Name", "DOB", "Sex", "Phone", "Physician")
        self.patient_tree = ttk.Treeview(t_frame, columns=cols, show="headings")
        for c in cols:
            self.patient_tree.heading(c, text=c)
            self.patient_tree.column(c, anchor="center" if c in ("ID", "MRN", "DOB", "Sex") else "w")
        self.patient_tree.pack(fill="both", expand=True, padx=2, pady=2)

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
    # VIEW 4: CUSTOM TEST CATALOG & RANGES
    # ==========================================
    def build_catalog_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["catalog"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        add_card = ctk.CTkFrame(frame, corner_radius=10)
        add_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(add_card, text="Add Custom Assay & Auto-Flag Reference Range", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=6, sticky="w", padx=16, pady=(12, 6))

        self.c_name = ctk.CTkEntry(add_card, placeholder_text="Assay Name *", width=190)
        self.c_name.grid(row=1, column=0, padx=(16, 6), pady=(0, 14))

        self.c_dept = ctk.CTkOptionMenu(add_card, values=["Hematology", "Chemistry", "Microscopy", "Immunohematology", "Serology", "Microbiology"], width=140)
        self.c_dept.grid(row=1, column=1, padx=6, pady=(0, 14))

        self.c_unit = ctk.CTkEntry(add_card, placeholder_text="Unit (e.g. mg/dL)", width=110)
        self.c_unit.grid(row=1, column=2, padx=6, pady=(0, 14))

        self.c_low = ctk.CTkEntry(add_card, placeholder_text="Low (num)", width=85)
        self.c_low.grid(row=1, column=3, padx=6, pady=(0, 14))

        self.c_high = ctk.CTkEntry(add_card, placeholder_text="High (num)", width=85)
        self.c_high.grid(row=1, column=4, padx=6, pady=(0, 14))

        self.c_ref = ctk.CTkEntry(add_card, placeholder_text="Display Range (e.g. 10 - 50 mg/dL)", width=180)
        self.c_ref.grid(row=1, column=5, padx=6, pady=(0, 14))

        ctk.CTkButton(add_card, text="+ Add Assay", width=105, fg_color="#4f46e5", hover_color="#4338ca", command=self.add_assay).grid(row=1, column=6, padx=(6, 16), pady=(0, 14))

        t_frame = ctk.CTkFrame(frame, corner_radius=10)
        t_frame.grid(row=1, column=0, sticky="nsew")
        cols = ("ID", "Assay Name", "Department", "Unit", "Low Cutoff", "High Cutoff", "Reference Interval")
        self.cat_tree = ttk.Treeview(t_frame, columns=cols, show="headings")
        for c in cols:
            self.cat_tree.heading(c, text=c)
            self.cat_tree.column(c, anchor="center" if c != "Assay Name" else "w")
        self.cat_tree.pack(fill="both", expand=True, padx=2, pady=2)

    def add_assay(self):
        name = self.c_name.get().strip()
        ref = self.c_ref.get().strip()
        if not name or not ref:
            messagebox.showwarning("Required", "Assay Name and Display Range are required.")
            return
        try:
            low = float(self.c_low.get().strip()) if self.c_low.get().strip() else None
            high = float(self.c_high.get().strip()) if self.c_high.get().strip() else None
        except ValueError:
            messagebox.showwarning("Invalid Cutoff", "Low and High cutoffs must be numbers (or left blank for qualitative tests).")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO test_catalog (test_name, department, unit, low_val, high_val, ref_range)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, self.c_dept.get(), self.c_unit.get().strip(), low, high, ref))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate", "An assay with that name already exists.")
        conn.close()

        for e in (self.c_name, self.c_unit, self.c_low, self.c_high, self.c_ref):
            e.delete(0, "end")
        self.refresh_catalog()

    def refresh_catalog(self):
        for r in self.cat_tree.get_children():
            self.cat_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT * FROM test_catalog ORDER BY department, test_name")
        for row in cur.fetchall():
            self.cat_tree.insert("", "end", values=row)
        conn.close()

if __name__ == "__main__":
    init_db()
    app = MonocytesDelegatesLIS()
    app.mainloop()
