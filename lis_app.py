import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("lis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            patient_age INTEGER,
            patient_sex TEXT,
            test_name TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            result TEXT DEFAULT 'Awaiting Result',
            order_date TEXT
        )
    """)
    conn.commit()
    conn.close()

# --- Main Application ---
class LISApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Laboratory Information System (LIS)")
        self.root.geometry("850x550")
        self.root.configure(padx=15, pady=15)

        # Title
        tk.Label(root, text="Laboratory Information System", font=("Arial", 16, "bold")).pack(pady=(0, 15))

        # --- Top Frame: New Order Entry ---
        entry_frame = tk.LabelFrame(root, text="Register Patient & Order Test", padx=10, pady=10)
        entry_frame.pack(fill="x", pady=(0, 15))

        tk.Label(entry_frame, text="Patient Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.name_entry = tk.Entry(entry_frame, width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(entry_frame, text="Age:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.age_entry = tk.Entry(entry_frame, width=8)
        self.age_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(entry_frame, text="Sex:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        self.sex_combo = ttk.Combobox(entry_frame, values=["Male", "Female", "Other"], width=10, state="readonly")
        self.sex_combo.grid(row=0, column=5, padx=5, pady=5)
        self.sex_combo.current(0)

        tk.Label(entry_frame, text="Lab Test:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.test_combo = ttk.Combobox(entry_frame, values=[
            "Complete Blood Count (CBC)", 
            "Urinalysis", 
            "Basic Metabolic Panel (BMP)", 
            "Lipid Panel", 
            "HbA1c", 
            "Blood Typing"
        ], width=25)
        self.test_combo.grid(row=1, column=1, padx=5, pady=5)

        add_btn = tk.Button(entry_frame, text="Create Lab Order", bg="#2e7d32", fg="white", font=("Arial", 9, "bold"), command=self.add_order)
        add_btn.grid(row=1, column=4, columnspan=2, sticky="ew", padx=5, pady=5)

        # --- Middle Frame: Records Table ---
        table_frame = tk.Frame(root)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Patient Name", "Age/Sex", "Test Ordered", "Status", "Result", "Date")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        col_widths = [40, 160, 70, 180, 90, 160, 110]
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor="center" if col in ["ID", "Age/Sex", "Status", "Date"] else "w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Bottom Frame: Result Entry & Actions ---
        action_frame = tk.LabelFrame(root, text="Update Selected Order", padx=10, pady=10)
        action_frame.pack(fill="x", pady=(15, 0))

        tk.Label(action_frame, text="Enter Result:").pack(side="left", padx=5)
        self.result_entry = tk.Entry(action_frame, width=40)
        self.result_entry.pack(side="left", padx=5)

        update_btn = tk.Button(action_frame, text="Save Result & Complete", bg="#1565c0", fg="white", command=self.update_result)
        update_btn.pack(side="left", padx=5)

        delete_btn = tk.Button(action_frame, text="Delete Order", bg="#c62828", fg="white", command=self.delete_order)
        delete_btn.pack(side="right", padx=5)

        self.load_data()

    def add_order(self):
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        sex = self.sex_combo.get()
        test = self.test_combo.get().strip()

        if not name or not test:
            messagebox.showwarning("Input Error", "Patient Name and Lab Test are required.")
            return

        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = sqlite3.connect("lis_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lab_orders (patient_name, patient_age, patient_sex, test_name, order_date) VALUES (?, ?, ?, ?, ?)",
            (name, age if age else "N/A", sex, test, date_str)
        )
        conn.commit()
        conn.close()

        self.name_entry.delete(0, tk.END)
        self.age_entry.delete(0, tk.END)
        self.test_combo.set("")
        self.load_data()

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("lis_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lab_orders ORDER BY order_id DESC")
        for row in cursor.fetchall():
            age_sex = f"{row[2]}/{row[3][0]}" if row[3] else str(row[2])
            self.tree.insert("", tk.END, values=(row[0], row[1], age_sex, row[4], row[5], row[6], row[7]))
        conn.close()

    def update_result(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a lab order from the table first.")
            return

        result_text = self.result_entry.get().strip()
        if not result_text:
            messagebox.showwarning("Input Error", "Please enter a result value.")
            return

        order_id = self.tree.item(selected[0])["values"][0]
        conn = sqlite3.connect("lis_database.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE lab_orders SET result = ?, status = 'Completed' WHERE order_id = ?",
            (result_text, order_id)
        )
        conn.commit()
        conn.close()

        self.result_entry.delete(0, tk.END)
        self.load_data()

    def delete_order(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an order to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
            order_id = self.tree.item(selected[0])["values"][0]
            conn = sqlite3.connect("lis_database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM lab_orders WHERE order_id = ?", (order_id,))
            conn.commit()
            conn.close()
            self.load_data()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = LISApp(root)
    root.mainloop()
