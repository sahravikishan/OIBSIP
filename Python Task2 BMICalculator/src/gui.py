"""
Desktop GUI Module for BMI Calculator.

Implements a professional Tkinter/ttk desktop user interface with side-by-side
input/result panels, interactive SQLite history Treeview, and embedded Matplotlib
trend charts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Dict, Any

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from src.bmi_calculator import (
    validate_name,
    validate_measurement,
    calculate_bmi,
    classify_bmi,
    ValidationError,
    CATEGORY_COLORS,
)
from src.database import DatabaseManager, DatabaseError
from src.chart import create_trend_figure, InsufficientDataError


class BMICalculatorApp:
    """
    Main Tkinter application class for the Advanced BMI Calculator.
    """

    def __init__(self, root: tk.Tk, db_manager: Optional[DatabaseManager] = None):
        self.root = root
        self.root.title("BMI Calculator & Health Tracker — OIBSIP Task 2")
        self.root.geometry("1020x680")
        self.root.minsize(920, 600)

        # Database manager initialization
        try:
            self.db = db_manager if db_manager else DatabaseManager()
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to initialize database:\n{e}")
            self.db = None

        self.current_user_id: Optional[int] = None
        self.current_user_name: str = ""

        # Configure style and theme
        self._setup_styles()

        # Build interface layout
        self._build_ui()

        # Populate user dropdown
        self._refresh_users_list()

    def _setup_styles(self) -> None:
        """Configure ttk theme and custom widget styles."""
        self.style = ttk.Style()
        # Use 'clam' or standard theme for consistent cross-platform styling
        available_themes = self.style.theme_names()
        if "clam" in available_themes:
            self.style.theme_use("clam")

        # Palette definition
        self.bg_color = "#F4F6F9"
        self.card_bg = "#FFFFFF"
        self.primary_color = "#1565C0"
        self.text_dark = "#212121"

        self.root.configure(bg=self.bg_color)

        # Custom TLabelframe style
        self.style.configure(
            "Card.TLabelframe",
            background=self.card_bg,
            foreground=self.text_dark,
            relief="solid",
            borderwidth=1,
        )
        self.style.configure(
            "Card.TLabelframe.Label",
            background=self.card_bg,
            foreground=self.primary_color,
            font=("Segoe UI", 10, "bold"),
        )
        self.style.configure("Card.TFrame", background=self.card_bg)

        # Buttons
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            foreground="#FFFFFF",
            background="#1976D2",
            padding=(10, 6),
        )
        self.style.map("Accent.TButton", background=[("active", "#1565C0")])

        self.style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            padding=(8, 5),
        )

        # Treeview styling
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=26,
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E0E0E0",
            foreground="#212121",
        )

    def _build_ui(self) -> None:
        """Construct main window components."""
        # Top banner frame
        header_frame = tk.Frame(self.root, bg="#0D47A1", height=65)
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)

        title_lbl = tk.Label(
            header_frame,
            text="BMI CALCULATOR & HEALTH TRACKER",
            font=("Segoe UI", 15, "bold"),
            fg="#FFFFFF",
            bg="#0D47A1",
        )
        title_lbl.pack(side="left", padx=20, pady=8)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Advanced Desktop Edition • Multi-User Persistent Tracking",
            font=("Segoe UI", 9),
            fg="#BBDEFB",
            bg="#0D47A1",
        )
        subtitle_lbl.pack(side="right", padx=20, pady=12)

        # Main content container
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill="both", expand=True, padx=15, pady=12)

        # Left Column: Input Form & Result Card (fixed reasonable width)
        left_pane = tk.Frame(content_frame, bg=self.bg_color, width=380)
        left_pane.pack(side="left", fill="y", padx=(0, 10))
        left_pane.pack_propagate(False)

        # Right Column: History Records Table & Trend Visualization
        right_pane = tk.Frame(content_frame, bg=self.bg_color)
        right_pane.pack(side="right", fill="both", expand=True)

        self._build_input_card(left_pane)
        self._build_result_card(left_pane)
        self._build_history_view(right_pane)

    def _build_input_card(self, parent: tk.Widget) -> None:
        """Build the input controls for user profile and measurements."""
        input_card = ttk.LabelFrame(parent, text="  User & Measurement Inputs  ", style="Card.TLabelframe")
        input_card.pack(fill="x", pady=(0, 10))

        inner = ttk.Frame(input_card, style="Card.TFrame", padding=12)
        inner.pack(fill="both", expand=True)

        # 1. User Name / Selection
        lbl_user = ttk.Label(inner, text="User Name:", font=("Segoe UI", 9, "bold"), background=self.card_bg)
        lbl_user.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.user_var = tk.StringVar()
        self.user_combobox = ttk.Combobox(inner, textvariable=self.user_var, font=("Segoe UI", 10))
        self.user_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.user_combobox.bind("<<ComboboxSelected>>", self._on_user_selected)

        # 2. Weight input (kg)
        lbl_weight = ttk.Label(inner, text="Weight (kg):", font=("Segoe UI", 9, "bold"), background=self.card_bg)
        lbl_weight.grid(row=2, column=0, sticky="w", pady=(0, 4))

        self.weight_var = tk.StringVar()
        self.weight_entry = ttk.Entry(inner, textvariable=self.weight_var, font=("Segoe UI", 10))
        self.weight_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        # 3. Height input (m)
        lbl_height = ttk.Label(inner, text="Height (m):", font=("Segoe UI", 9, "bold"), background=self.card_bg)
        lbl_height.grid(row=4, column=0, sticky="w", pady=(0, 4))

        self.height_var = tk.StringVar()
        self.height_entry = ttk.Entry(inner, textvariable=self.height_var, font=("Segoe UI", 10))
        self.height_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # Action Buttons
        btn_frame = ttk.Frame(inner, style="Card.TFrame")
        btn_frame.grid(row=6, column=0, columnspan=2, sticky="ew")

        self.btn_calculate = ttk.Button(
            btn_frame,
            text="Calculate & Save",
            style="Accent.TButton",
            command=self._handle_calculate_and_save,
        )
        self.btn_calculate.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_clear = ttk.Button(
            btn_frame,
            text="Reset",
            style="Secondary.TButton",
            command=self._handle_reset_fields,
        )
        self.btn_clear.pack(side="right", padx=(5, 0))

        inner.columnconfigure(0, weight=1)

    def _build_result_card(self, parent: tk.Widget) -> None:
        """Build the dynamic result display card with colour coding."""
        result_card = ttk.LabelFrame(parent, text="  BMI Result & Category  ", style="Card.TLabelframe")
        result_card.pack(fill="x", pady=(0, 10))

        inner = ttk.Frame(result_card, style="Card.TFrame", padding=14)
        inner.pack(fill="both", expand=True)

        self.lbl_bmi_value = tk.Label(
            inner,
            text="--.--",
            font=("Segoe UI", 28, "bold"),
            fg="#607D8B",
            bg=self.card_bg,
        )
        self.lbl_bmi_value.pack(anchor="center", pady=(0, 2))

        self.lbl_bmi_unit = tk.Label(
            inner,
            text="Body Mass Index (kg/m²)",
            font=("Segoe UI", 8),
            fg="#78909C",
            bg=self.card_bg,
        )
        self.lbl_bmi_unit.pack(anchor="center", pady=(0, 8))

        # Category Badge Frame
        self.badge_frame = tk.Frame(inner, bg="#ECEFF1", padx=14, pady=6)
        self.badge_frame.pack(anchor="center", pady=(0, 10))

        self.lbl_category = tk.Label(
            self.badge_frame,
            text="Category: Pending Input",
            font=("Segoe UI", 11, "bold"),
            fg="#455A64",
            bg="#ECEFF1",
        )
        self.lbl_category.pack()

        # WHO Standard Reference Chart
        ref_frame = tk.LabelFrame(inner, text=" WHO BMI Classification Standard ", bg=self.card_bg, font=("Segoe UI", 8, "italic"))
        ref_frame.pack(fill="x", pady=(4, 0))

        ranges = [
            ("Underweight", "< 18.5", CATEGORY_COLORS["Underweight"]),
            ("Normal", "18.5 – 24.9", CATEGORY_COLORS["Normal"]),
            ("Overweight", "25 – 29.9", CATEGORY_COLORS["Overweight"]),
            ("Obese", "≥ 30", CATEGORY_COLORS["Obese"]),
        ]
        for idx, (cat_name, cat_range, cat_color) in enumerate(ranges):
            row_f = tk.Frame(ref_frame, bg=self.card_bg)
            row_f.pack(fill="x", padx=6, pady=2)

            dot = tk.Label(row_f, text="■", fg=cat_color, bg=self.card_bg, font=("Segoe UI", 9))
            dot.pack(side="left")

            txt = tk.Label(
                row_f,
                text=f"{cat_name}: {cat_range}",
                fg="#37474F",
                bg=self.card_bg,
                font=("Segoe UI", 8),
            )
            txt.pack(side="left", padx=5)

    def _build_history_view(self, parent: tk.Widget) -> None:
        """Build the historical records table and management toolbar."""
        history_card = ttk.LabelFrame(parent, text="  BMI Historical Records  ", style="Card.TLabelframe")
        history_card.pack(fill="both", expand=True)

        container = ttk.Frame(history_card, style="Card.TFrame", padding=10)
        container.pack(fill="both", expand=True)

        # Header with user label and refresh
        top_bar = ttk.Frame(container, style="Card.TFrame")
        top_bar.pack(fill="x", pady=(0, 8))

        self.lbl_history_user = ttk.Label(
            top_bar,
            text="Displaying records for: (No User Selected)",
            font=("Segoe UI", 10, "bold"),
            background=self.card_bg,
            foreground=self.primary_color,
        )
        self.lbl_history_user.pack(side="left")

        # Treeview for records
        table_frame = ttk.Frame(container, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "date", "weight", "height", "bmi", "category")
        self.history_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )

        self.history_tree.heading("id", text="ID")
        self.history_tree.heading("date", text="Date & Time")
        self.history_tree.heading("weight", text="Weight (kg)")
        self.history_tree.heading("height", text="Height (m)")
        self.history_tree.heading("bmi", text="BMI")
        self.history_tree.heading("category", text="Category")

        self.history_tree.column("id", width=45, anchor="center")
        self.history_tree.column("date", width=145, anchor="center")
        self.history_tree.column("weight", width=85, anchor="e")
        self.history_tree.column("height", width=85, anchor="e")
        self.history_tree.column("bmi", width=75, anchor="center")
        self.history_tree.column("category", width=110, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Configure category tags for colored text in table rows
        self.history_tree.tag_configure("Underweight", foreground=CATEGORY_COLORS["Underweight"])
        self.history_tree.tag_configure("Normal", foreground=CATEGORY_COLORS["Normal"])
        self.history_tree.tag_configure("Overweight", foreground=CATEGORY_COLORS["Overweight"])
        self.history_tree.tag_configure("Obese", foreground=CATEGORY_COLORS["Obese"])

        # Bottom Action Toolbar
        toolbar = ttk.Frame(container, style="Card.TFrame")
        toolbar.pack(fill="x", pady=(10, 0))

        self.btn_trend = ttk.Button(
            toolbar,
            text="📈  View BMI Trend Graph",
            style="Accent.TButton",
            command=self._handle_view_trend_graph,
        )
        self.btn_trend.pack(side="left", padx=(0, 6))

        self.btn_delete = ttk.Button(
            toolbar,
            text="Delete Selected Record",
            style="Secondary.TButton",
            command=self._handle_delete_record,
        )
        self.btn_delete.pack(side="left", padx=6)

        self.btn_refresh = ttk.Button(
            toolbar,
            text="Refresh History",
            style="Secondary.TButton",
            command=self._load_user_history,
        )
        self.btn_refresh.pack(side="left", padx=6)

        self.btn_exit = ttk.Button(
            toolbar,
            text="Exit",
            style="Secondary.TButton",
            command=self.root.quit,
        )
        self.btn_exit.pack(side="right")

    def _refresh_users_list(self) -> None:
        """Fetch all users from SQLite and refresh the user combobox."""
        if not self.db:
            return
        try:
            users = self.db.get_all_users()
            user_names = [u["name"] for u in users]
            self.user_combobox["values"] = user_names

            if user_names and not self.user_var.get():
                # Default to first user if available
                self.user_var.set(user_names[0])
                self._on_user_selected(None)
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Could not load users list:\n{e}")

    def _on_user_selected(self, _event) -> None:
        """Handle user selection from combobox."""
        selected_name = self.user_var.get().strip()
        if not selected_name:
            return

        try:
            user_id, _ = self.db.get_or_create_user(selected_name)
            self.current_user_id = user_id
            self.current_user_name = selected_name
            self.lbl_history_user.config(text=f"Displaying records for: {selected_name}")
            self._load_user_history()
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Could not load user records:\n{e}")

    def _load_user_history(self) -> None:
        """Query and display BMI records for the currently active user."""
        # Clear existing rows
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if not self.current_user_id or not self.db:
            return

        try:
            records = self.db.get_user_records(self.current_user_id, order_desc=True)
            for r in records:
                self.history_tree.insert(
                    "",
                    "end",
                    values=(
                        r["id"],
                        r["recorded_at"],
                        f"{r['weight']:.1f} kg",
                        f"{r['height']:.2f} m",
                        f"{r['bmi']:.2f}",
                        r["category"],
                    ),
                    tags=(r["category"],),
                )
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to retrieve history:\n{e}")

    def _handle_calculate_and_save(self) -> None:
        """Validate inputs, calculate BMI, save record to SQLite, and update UI."""
        raw_name = self.user_var.get()
        raw_weight = self.weight_var.get()
        raw_height = self.height_var.get()

        # Step 1: Input Validation
        try:
            valid_name = validate_name(raw_name)
            weight = validate_measurement(raw_weight, "Weight")
            height = validate_measurement(raw_height, "Height")
        except ValidationError as e:
            messagebox.showwarning("Validation Error", str(e))
            return

        # Step 2: BMI Calculation & Classification
        try:
            bmi = calculate_bmi(weight, height)
            category, color_hex = classify_bmi(bmi)
        except ValidationError as e:
            messagebox.showerror("Calculation Error", str(e))
            return

        # Step 3: Database Persistence
        if not self.db:
            messagebox.showerror("Database Error", "Database service is unavailable. Record cannot be saved.")
            return

        try:
            user_id, created = self.db.get_or_create_user(valid_name)
            self.current_user_id = user_id
            self.current_user_name = valid_name
            self.user_var.set(valid_name)

            # Insert measurement record
            self.db.insert_record(user_id, weight, height, bmi, category)

            # Refresh user dropdown list if a new user was created
            if created:
                self._refresh_users_list()
                self.user_var.set(valid_name)

        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to save record to database:\n{e}")
            return

        # Step 4: Update UI Feedback
        self._display_result(bmi, category, color_hex)
        self.lbl_history_user.config(text=f"Displaying records for: {valid_name}")
        self._load_user_history()

    def _display_result(self, bmi: float, category: str, color_hex: str) -> None:
        """Update result label, category badge, and styling."""
        self.lbl_bmi_value.config(text=f"{bmi:.2f}", fg=color_hex)
        self.badge_frame.config(bg=color_hex)
        self.lbl_category.config(
            text=f"Category: {category}",
            fg="#FFFFFF",
            bg=color_hex,
        )

    def _handle_reset_fields(self) -> None:
        """Reset measurement inputs and result card."""
        self.weight_var.set("")
        self.height_var.set("")
        self.lbl_bmi_value.config(text="--.--", fg="#607D8B")
        self.badge_frame.config(bg="#ECEFF1")
        self.lbl_category.config(
            text="Category: Pending Input",
            fg="#455A64",
            bg="#ECEFF1",
        )

    def _handle_delete_record(self) -> None:
        """Delete selected record from Treeview and SQLite database."""
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showinfo("Delete Record", "Please select a record from the history table to delete.")
            return

        record_values = self.history_tree.item(selected_item[0], "values")
        record_id = int(record_values[0])

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete record ID #{record_id}?",
        )
        if not confirm:
            return

        try:
            self.db.delete_record(record_id)
            self._load_user_history()
            messagebox.showinfo("Success", f"Record ID #{record_id} successfully deleted.")
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Could not delete record:\n{e}")

    def _handle_view_trend_graph(self) -> None:
        """Open a Matplotlib window displaying the selected user's BMI trajectory."""
        if not self.current_user_id or not self.db:
            messagebox.showinfo("Trend Graph", "Please select or calculate a record for a user first.")
            return

        try:
            records = self.db.get_user_records(self.current_user_id, order_desc=False)
        except DatabaseError as e:
            messagebox.showerror("Database Error", f"Failed to retrieve user records:\n{e}")
            return

        try:
            fig = create_trend_figure(self.current_user_name, records)
        except InsufficientDataError as e:
            messagebox.showinfo("Insufficient Data", str(e))
            return
        except Exception as e:
            messagebox.showerror("Graph Error", f"Failed to generate trend graph:\n{e}")
            return

        # Open Toplevel window to embed Matplotlib canvas
        graph_window = tk.Toplevel(self.root)
        graph_window.title(f"BMI Trend for {self.current_user_name}")
        graph_window.geometry("820x560")
        graph_window.minsize(700, 480)

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()

        toolbar = NavigationToolbar2Tk(canvas, graph_window)
        toolbar.update()

        toolbar.pack(side="top", fill="x")
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)


def run_app():
    """Application launcher function."""
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
