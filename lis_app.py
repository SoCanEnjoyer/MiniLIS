import sqlite3
import os
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from fpdf import FPDF

# --- Theme & Appearance ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

DB_NAME = "full_lis_database.db"

# Standard Clinical Reference Ranges (Test Name -> (Unit, Low, High, Display Range))
TEST_CATALOG = {
    "Complete Blood Count (WBC)": ("x10^9/L", 4.5, 11.0, "4.5 - 11.0 x10^9/L"),
    "Hemoglobin (Hgb)": ("g/dL", 12.0, 17.5, "12.0 - 17.5 g/dL"),
    "Platelet Count": ("x10^9/L", 150.0, 450.0, "150 - 450 x10^9/L"),
    "Fasting Blood Glucose": ("mg/dL", 70.0, 99.0, "70 - 99 mg/dL"),
    "HbA1c": ("%", 4.0, 5.6, "4.0 - 5.6 %"),
    "Total Cholesterol": ("mg/dL", 0.0, 200.0, "< 200 mg/dL"),
    "Creatinine (Serum)": ("mg/dL", 0.6, 1.3, "0.6 - 1.3 mg/dL"),
    "ALT (SGPT)": ("U/L", 7.0, 56.0, "7 - 56 U/L"),
    "Urinalysis (Qualitative)": ("", None, None, "Negative / Normal"),
    "Blood Typing (ABO/Rh)": ("", None, None, "Qualitative")
}

# --- Database Layer ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            dob TEXT,
            sex TEXT,
            phone TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            specimen_id TEXT UNIQUE,
            patient_id INTEGER,
            test_name TEXT NOT NULL,
            priority TEXT DEFAULT 'Routine',
            status TEXT DEFAULT 'Pending',
            result_value TEXT DEFAULT '',
            flag TEXT DEFAULT '',
            reference_range TEXT,
            verified_by TEXT DEFAULT '',
            order_date TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
        )
    """)
    conn.commit()
    conn.close()

# --- PDF Report Generator ---
class LabReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "CLINICAL DIAGNOSTIC LABORATORY", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Official Laboratory Examination Report", ln=True, align="C")
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Confidential Medical Record", align="C")

def generate_pdf(order_data, save_path):
    pdf = LabReportPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)

    # Patient & Specimen Block
    pdf.cell(95, 8, f"Patient Name: {order_data['patient_name']}", border=0)
    pdf.cell(95, 8, f"Specimen ID: {order_data['specimen_id']}", border=0, ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(95, 8, f"DOB / Sex: {order_data['dob']} / {order_data['sex']}", border=0)
    pdf.cell(95, 8, f"Collection Date: {order_data['order_date']}", border=0, ln=True)
    pdf.cell(95, 8, f"Priority: {order_data['priority']}", border=0)
    pdf.cell(95, 8, f"Status: {order_data['status']}", border=0, ln=True)
    pdf.ln(8)

    # Results Table Header
    pdf.set_fill_color(30, 64, 175)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(65, 10, "Test Name", border=1, fill=True)
    pdf.cell(40, 10, "Result", border=1, fill=True, align="C")
    pdf.cell(30, 10, "Flag", border=1, fill=True, align="C")
    pdf.cell(55, 10, "Reference Range", border=1, fill=True, align="C", ln=True)

    # Results Row
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 10, order_data['test_name'], border=1)
    pdf.cell(40, 10, order_data['result_value'], border=1, align="C")
    
    if order_data['flag'] in ["HIGH", "LOW"]:
        pdf.set_text_color(200, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 10, order_data['flag'], border=1, align="C")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(55, 10, order_data['reference_range'], border=1, align="C", ln=True)

    pdf.ln(20)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 8, f"Verified & Released By: {order_data['verified_by']}", ln=True)
    pdf.output(save_path)

# --- Main Application ---
class FullLISApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CoreLIS Pro — Clinical Laboratory Information System")
        self.geometry("1150x700")
        self.minsize(1000, 620)

        # Configure Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar Navigation ---
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="CoreLIS Pro", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(25, 5))
        ctk.CTkLabel(self.sidebar, text="Lab Management Suite", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=20, pady=(0, 25))

        self.btn_orders = ctk.CTkButton(self.sidebar, text="Orders & Worklist", height=40, command=lambda: self.show_frame("orders"))
        self.btn_orders.grid(row=2, column=0, padx=20, pady=8, sticky="ew")

        self.btn_patients = ctk.CTkButton(self.sidebar, text="Patient Directory", height=40, command=lambda: self.show_frame("patients"))
        self.btn_patients.grid(row=3, column=0, padx=20, pady=8, sticky="ew")

        self.btn_new = ctk.CTkButton(self.sidebar, text="+ New Lab Order", height=40, fg_color="#16a34a", hover_color="#15803d", command=lambda: self.show_frame("new_order"))
        self.btn_new.grid(row=4, column=0, padx=20, pady=8, sticky="ew")

        # Theme Switcher at bottom of sidebar
        ctk.CTkLabel(self.sidebar, text="Appearance Mode:", anchor="w").grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar, values=["Dark", "Light", "System"], command=ctk.set_appearance_mode)
        self.theme_menu.grid(row=7, column=0, padx=20, pady=(5, 20), sticky="ew")

        # --- Main Content Frames ---
        self.frames = {}
        self.build_orders_frame()
        self.build_patients_frame()
        self.build_new_order_frame()

        self.show_frame("orders")

    def show_frame(self, name):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[name].grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        if name == "orders":
            self.refresh_orders()
        elif name == "patients":
            self.refresh_patients()
        elif name == "new_order":
            self.refresh_patient_dropdown()

    # ==========================================
    # VIEW 1: WORKLIST & RESULT ENTRY
    # ==========================================
    def build_orders_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["orders"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)

        # Top KPI Stats Bar
        stats_frame = ctk.CTkFrame(frame)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.lbl_total = ctk.CTkLabel(stats_frame, text="Total Orders: 0", font=ctk.CTkFont(size=15, weight="bold"))
        self.lbl_total.grid(row=0, column=0, pady=12)
        self.lbl_pending = ctk.CTkLabel(stats_frame, text="Pending: 0", font=ctk.CTkFont(size=15, weight="bold"), text_color="#f59e0b")
        self.lbl_pending.grid(row=0, column=1, pady=12)
        self.lbl_completed = ctk.CTkLabel(stats_frame, text="Completed: 0", font=ctk.CTkFont(size=15, weight="bold"), text_color="#22c55e")
        self.lbl_completed.grid(row=0, column=2, pady=12)

        # Search & Filter Bar
        filter_bar = ctk.CTkFrame(frame, fg_color="transparent")
        filter_bar.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_orders())
        ctk.CTkEntry(filter_bar, placeholder_text="Search by Patient Name or Specimen ID...", textvariable=self.search_var, width=320).pack(side="left", padx=(0, 10))

        self.status_filter = ctk.CTkSegmentedButton(filter_bar, values=["All", "Pending", "Completed"], command=lambda _: self.refresh_orders())
        self.status_filter.set("All")
        self.status_filter.pack(side="left")

        # Treeview Table (Styled)
        table_container = ctk.CTkFrame(frame)
        table_container.grid(row=2, column=0, sticky="nsew")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#1e293b", foreground="white", fieldbackground="#1e293b", rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#0f172a", foreground="white", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#2563eb")])

        cols = ("ID", "Specimen ID", "Patient", "Test", "Priority", "Status", "Result", "Flag", "Ref Range")
        self.order_tree = ttk.Treeview(table_container, columns=cols, show="headings")
        widths = [40, 130, 150, 180, 75, 85, 90, 75, 130]
        for c, w in zip(cols, widths):
            self.order_tree.heading(c, text=c)
            self.order_tree.column(c, width=w, anchor="center" if c not in ["Patient", "Test"] else "w")

        self.order_tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(table_container, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Bottom Result Verification Panel
        verify_panel = ctk.CTkFrame(frame)
        verify_panel.grid(row=3, column=0, sticky="ew", pady=(15, 0))

        ctk.CTkLabel(verify_panel, text="Result Value:").pack(side="left", padx=(15, 5), pady=12)
        self.res_input = ctk.CTkEntry(verify_panel, placeholder_text="e.g. 6.8 or Negative", width=150)
        self.res_input.pack(side="left", padx=5)

        ctk.CTkLabel(verify_panel, text="Tech Initials:").pack(side="left", padx=(10, 5))
        self.tech_input = ctk.CTkEntry(verify_panel, placeholder_text="e.g. J.D., RMT", width=110)
        self.tech_input.pack(side="left", padx=5)

        ctk.CTkButton(verify_panel, text="Verify & Release", command=self.verify_result).pack(side="left", padx=10)
        ctk.CTkButton(verify_panel, text="Export PDF Report", fg_color="#0284c7", hover_color="#0369a1", command=self.export_selected_pdf).pack(side="right", padx=15)

    def refresh_orders(self):
        for r in self.order_tree.get_children():
            self.order_tree.delete(r)

        query_text = f"%{self.search_var.get().strip()}%"
        status_val = self.status_filter.get()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # KPI counts
        cursor.execute("SELECT COUNT(*) FROM orders")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'")
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status='Completed'")
        completed = cursor.fetchone()[0]

        self.lbl_total.configure(text=f"Total Orders: {total}")
        self.lbl_pending.configure(text=f"Pending: {pending}")
        self.lbl_completed.configure(text=f"Completed: {completed}")

        sql = """
            SELECT o.order_id, o.specimen_id, p.full_name, o.test_name, o.priority, o.status, o.result_value, o.flag, o.reference_range
            FROM orders o
            JOIN patients p ON o.patient_id = p.patient_id
            WHERE (p.full_name LIKE ? OR o.specimen_id LIKE ?)
        """
        params = [query_text, query_text]
        if status_val != "All":
            sql += " AND o.status = ?"
            params.append(status_val)
        sql += " ORDER BY o.order_id DESC"

        cursor.execute(sql, params)
        for row in cursor.fetchall():
            self.order_tree.insert("", "end", values=row)
        conn.close()

    def verify_result(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select an order from the worklist first.")
            return

        val = self.res_input.get().strip()
        tech = self.tech_input.get().strip() or "Lab Staff"
        if not val:
            messagebox.showwarning("Missing Result", "Enter a test result value.")
            return

        item = self.order_tree.item(sel[0])["values"]
        order_id, test_name = item[0], item[3]

        # Auto-calculate High/Low flag if numeric range exists
        flag = "NORMAL"
        if test_name in TEST_CATALOG:
            unit, low, high, _ = TEST_CATALOG[test_name]
            try:
                num_val = float(val)
                if low is not None and num_val < low:
                    flag = "LOW"
                elif high is not None and num_val > high:
                    flag = "HIGH"
                val_display = f"{val} {unit}".strip()
            except ValueError:
                val_display = val
        else:
            val_display = val

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders SET result_value = ?, flag = ?, status = 'Completed', verified_by = ?
            WHERE order_id = ?
        """, (val_display, flag, tech, order_id))
        conn.commit()
        conn.close()

        self.res_input.delete(0, "end")
        self.refresh_orders()

    def export_selected_pdf(self):
        sel = self.order_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a completed order to export.")
            return

        order_id = self.order_tree.item(sel[0])["values"][0]
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.specimen_id, p.full_name, p.dob, p.sex, o.test_name, o.priority, o.status, o.result_value, o.flag, o.reference_range, o.verified_by, o.order_date
            FROM orders o JOIN patients p ON o.patient_id = p.patient_id
            WHERE o.order_id = ?
        """, (order_id,))
        r = cursor.fetchone()
        conn.close()

        if r[6] != "Completed":
            messagebox.showwarning("Pending Order", "Please verify and complete the result before generating a PDF report.")
            return

        order_dict = {
            "specimen_id": r[0], "patient_name": r[1], "dob": r[2], "sex": r[3],
            "test_name": r[4], "priority": r[5], "status": r[6], "result_value": r[7],
            "flag": r[8], "reference_range": r[9], "verified_by": r[10], "order_date": r[11]
        }

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"LabReport_{r[0]}_{r[1].replace(' ', '_')}.pdf",
            filetypes=[("PDF Documents", "*.pdf")]
        )
        if file_path:
            generate_pdf(order_dict, file_path)
            messagebox.showinfo("Success", "PDF Report generated successfully!")
            webbrowser.open(file_path)

    # ==========================================
    # VIEW 2: PATIENT DIRECTORY
    # ==========================================
    def build_patients_frame(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        self.frames["patients"] = frame
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        reg_box = ctk.CTkFrame(frame)
        reg_box.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(reg_box, text="Register New Patient", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, sticky="w", padx=15, pady=(10, 5))

        self.p_name = ctk.CTkEntry(reg_box, placeholder_text="Full Name", width=220)
        self.p_name.grid(row=1, column=0, padx=15, pady=10)

        self.p_dob = ctk.CTkEntry(reg_box, placeholder_text="DOB (YYYY-MM-DD)", width=150)
        self.p_dob.grid(row=1, column=1, padx=10, pady=10)

        self.p_sex = ctk.CTkOptionMenu(reg_box, values=["Male", "Female", "Other"], width=110)
        self.p_sex.grid(row=1, column=2, padx=10, pady=10)

        self.p_phone = ctk.CTkEntry(reg_box, placeholder_text="Contact Number", width=160)
        self.p_phone.grid(row=1, column=3, padx=10, pady=10)

        ctk.CTkButton(reg_box, text="Add Patient", fg_color="#16a34a", hover_color="#15803d", command=self.add_patient).grid(row=1, column=4, padx=15, pady=10)

        # Patient Table
        p_table_frame = ctk.CTkFrame(frame)
        p_table_frame.grid(row=1, column=0, sticky="nsew")
        cols = ("Patient ID", "Full Name", "DOB", "Sex", "Phone")
        self.patient_tree = ttk.Treeview(p_table_frame, columns=cols, show="headings")
        for c in cols:
            self.patient_tree.heading(c, text=c)
            self.patient_tree.column(c, anchor="center" if c != "Full Name" else "w")
        self.patient_tree.pack(fill="both", expand=True)

    def add_patient(self):
        name = self.p_name.get().strip()
        if not name:
            messagebox.showwarning("Required", "Patient Full Name is required.")
            return
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patients (full_name, dob, sex, phone) VALUES (?, ?, ?, ?)",
                       (name, self.p_dob.get().strip() or "N/A", self.p_sex.get(), self.p_phone.get().strip() or "N/A"))
        conn.commit()
        conn.close()
        self.p_name.delete(0, "end")
        self.p_dob.delete(0, "end")
        self.p_phone.delete(0, "end")
        self.refresh_patients()

    def refresh_patients(self):
        for r in self.patient_tree.get_children():
            self.patient_tree.delete(r)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients ORDER BY patient_id DESC")
        for row in cursor.fetchall():
            self.patient_tree.insert("", "end", values=row)
        conn.close()

    # ==========================================
    # VIEW 3: NEW LAB ORDER / ACCESSIONING
    # ==========================================
    def build_new_order_frame(self):
        frame = ctk.CTkFrame(self)
        self.frames["new_order"] = frame

        ctk.CTkLabel(frame, text="Create Lab Requisition & Accession Specimen", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=30, pady=(25, 20))

        ctk.CTkLabel(frame, text="Select Registered Patient:").pack(anchor="w", padx=30, pady=(5, 2))
        self.order_patient_menu = ctk.CTkOptionMenu(frame, values=["No Patients Registered"], width=350)
        self.order_patient_menu.pack(anchor="w", padx=30, pady=(0, 15))

        ctk.CTkLabel(frame, text="Select Laboratory Test / Panel:").pack(anchor="w", padx=30, pady=(5, 2))
        self.order_test_menu = ctk.CTkOptionMenu(frame, values=list(TEST_CATALOG.keys()), width=350)
        self.order_test_menu.pack(anchor="w", padx=30, pady=(0, 15))

        ctk.CTkLabel(frame, text="Order Priority:").pack(anchor="w", padx=30, pady=(5, 2))
        self.order_priority = ctk.CTkSegmentedButton(frame, values=["Routine", "Urgent", "STAT"])
        self.order_priority.set("Routine")
        self.order_priority.pack(anchor="w", padx=30, pady=(0, 25))

        ctk.CTkButton(frame, text="Generate Specimen ID & Submit Order", height=42, width=350, fg_color="#16a34a", hover_color="#15803d", command=self.submit_lab_order).pack(anchor="w", padx=30)

    def refresh_patient_dropdown(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, full_name FROM patients ORDER BY full_name ASC")
        rows = cursor.fetchall()
        conn.close()

        self.patient_map = {f"{r[0]} - {r[1]}": r[0] for r in rows}
        if self.patient_map:
            self.order_patient_menu.configure(values=list(self.patient_map.keys()))
            self.order_patient_menu.set(list(self.patient_map.keys())[0])
        else:
            self.order_patient_menu.configure(values=["No Patients Registered"])
            self.order_patient_menu.set("No Patients Registered")

    def submit_lab_order(self):
        selection = self.order_patient_menu.get()
        if selection == "No Patients Registered" or selection not in self.patient_map:
            messagebox.showwarning("No Patient", "Please register a patient in the Patient Directory first.")
            return

        patient_id = self.patient_map[selection]
        test_name = self.order_test_menu.get()
        priority = self.order_priority.get()
        ref_range = TEST_CATALOG[test_name][3]
        now = datetime.now()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0] + 1
        specimen_id = f"SPEC-{now.strftime('%Y%m%d')}-{count:03d}"

        cursor.execute("""
            INSERT INTO orders (specimen_id, patient_id, test_name, priority, reference_range, order_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (specimen_id, patient_id, test_name, priority, ref_range, now.strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        messagebox.showinfo("Order Created", f"Specimen Accession Complete!\n\nSpecimen ID: {specimen_id}")
        self.show_frame("orders")

if __name__ == "__main__":
    init_db()
    app = FullLISApp()
    app.mainloop()
