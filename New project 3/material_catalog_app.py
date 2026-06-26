import csv
import sqlite3
import subprocess
import sys
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "outputs" / "db_split" / "materials_hierarchy.sqlite3"


class MaterialCatalogApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Material Catalog")
        self.geometry("1280x760")
        self.minsize(1040, 640)

        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.type_var = tk.StringVar()
        self.group_var = tk.StringVar()
        self.sub_group_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.filter_sub_group_map = {}

        self._configure_style()
        self._build_layout()
        self._load_types()
        self._refresh_all()

    def _configure_style(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("Meta.TLabel", foreground="#4B5563")
        style.configure("Header.TFrame", background="#F3F4F6")
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_layout(self):
        header = ttk.Frame(self, padding=(12, 10, 12, 8), style="Header.TFrame")
        header.pack(fill=tk.X)

        ttk.Label(header, text="Material Catalog", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_var, style="Meta.TLabel").grid(row=0, column=1, sticky="e")
        header.columnconfigure(1, weight=1)

        filters = ttk.Frame(self, padding=(12, 8, 12, 8))
        filters.pack(fill=tk.X)

        self.type_combo = self._combo(filters, "Type", self.type_var, 0, 0, self._on_type_changed)
        self.group_combo = self._combo(filters, "Group", self.group_var, 0, 2, self._on_group_changed, width=42)
        self.sub_group_combo = self._combo(filters, "Sub-Group", self.sub_group_var, 0, 4, self._on_filter_changed, width=36)

        ttk.Label(filters, text="Search").grid(row=1, column=0, sticky="w", pady=(8, 0))
        search = ttk.Entry(filters, textvariable=self.search_var, width=42)
        search.grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=(8, 0))
        search.bind("<Return>", lambda _event: self._refresh_all())
        self.search_var.trace_add("write", lambda *_args: self.after(250, self._refresh_all))

        ttk.Button(filters, text="ค้นหา", command=self._refresh_all).grid(row=1, column=2, sticky="w", pady=(8, 0))
        ttk.Button(filters, text="ล้าง", command=self._clear_filters).grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Button(filters, text="เพิ่มข้อมูล", command=self._open_add_material_dialog).grid(row=1, column=4, sticky="w", padx=(16, 0), pady=(8, 0))
        ttk.Button(filters, text="Export CSV", command=self._export_csv).grid(row=1, column=5, sticky="w", padx=(8, 0), pady=(8, 0))
        ttk.Button(filters, text="เปิดฐานข้อมูล", command=self._open_db_folder).grid(row=1, column=6, sticky="w", padx=(8, 0), pady=(8, 0))

        for col in (1, 3, 5):
            filters.columnconfigure(col, weight=1)

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        left = ttk.Frame(body)
        right = ttk.Frame(body, width=280)
        body.add(left, weight=4)
        body.add(right, weight=1)

        self.material_tree = self._build_material_tree(left)
        self.brand_tree = self._build_brand_tree(right)

        footer = ttk.Frame(self, padding=(12, 4, 12, 10))
        footer.pack(fill=tk.X)
        ttk.Label(footer, text=str(DB_PATH), style="Meta.TLabel").pack(side=tk.LEFT)

    def _combo(self, parent, label, variable, row, col, callback, width=28):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w")
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly", width=width)
        combo.grid(row=row, column=col + 1, sticky="ew", padx=(8, 16))
        combo.bind("<<ComboboxSelected>>", callback)
        return combo

    def _build_material_tree(self, parent):
        columns = ("code", "name", "spec", "brand", "unit", "type", "group", "sub_group")
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        headings = {
            "code": ("Code", 145),
            "name": ("Product/Material", 280),
            "spec": ("Spec/Size", 220),
            "brand": ("Brand", 130),
            "unit": ("Unit", 80),
            "type": ("Type", 85),
            "group": ("Group", 260),
            "sub_group": ("Sub-Group", 230),
        }
        for col, (text, width) in headings.items():
            tree.heading(col, text=text)
            tree.column(col, width=width, minwidth=70, stretch=col in {"name", "spec", "group", "sub_group"})

        ybar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        xbar = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
        tree.grid(row=0, column=0, sticky="nsew")
        ybar.grid(row=0, column=1, sticky="ns")
        xbar.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        tree.bind("<Double-1>", self._copy_selected_code)
        return tree

    def _build_brand_tree(self, parent):
        ttk.Label(parent, text="Brand", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        tree = ttk.Treeview(parent, columns=("brand", "count"), show="headings", height=18)
        tree.heading("brand", text="Brand")
        tree.heading("count", text="Items")
        tree.column("brand", width=180, stretch=True)
        tree.column("count", width=70, anchor="e", stretch=False)
        ybar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=ybar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ybar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def _query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def _load_types(self):
        values = ["ทั้งหมด"] + [row["type_name"] for row in self._query("SELECT type_name FROM material_types ORDER BY type_name")]
        self.type_combo["values"] = values
        self.type_var.set("Product" if "Product" in values else values[0])
        self._load_groups()

    def _load_groups(self):
        params = []
        where = ""
        if self.type_var.get() != "ทั้งหมด":
            where = "WHERE type_name = ?"
            params.append(self.type_var.get())
        groups = [row["group_name"] for row in self._query(f"SELECT group_name FROM material_groups {where} ORDER BY group_name", params)]
        self.group_combo["values"] = ["ทั้งหมด"] + groups
        if self.group_var.get() not in self.group_combo["values"]:
            self.group_var.set("ทั้งหมด")
        self._load_sub_groups()

    def _load_sub_groups(self):
        where = []
        params = []
        if self.type_var.get() != "ทั้งหมด":
            where.append("mt.type_name = ?")
            params.append(self.type_var.get())
        if self.group_var.get() != "ทั้งหมด":
            where.append("mg.group_name = ?")
            params.append(self.group_var.get())
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        rows = self._query(
            f"""
            SELECT msg.category_code, msg.sub_group_name
            FROM material_sub_groups msg
            JOIN material_groups mg ON mg.group_id = msg.group_id
            JOIN material_types mt ON mt.type_name = mg.type_name
            {where_sql}
            ORDER BY msg.category_code
            """,
            params,
        )
        self.filter_sub_group_map = {
            f"{row['category_code']} - {row['sub_group_name']}": row["category_code"]
            for row in rows
        }
        values = ["ทั้งหมด"] + list(self.filter_sub_group_map)
        self.sub_group_combo["values"] = values
        if self.sub_group_var.get() not in values:
            self.sub_group_var.set("ทั้งหมด")

    def _where_clause(self):
        where = []
        params = []
        if self.type_var.get() != "ทั้งหมด":
            where.append("type = ?")
            params.append(self.type_var.get())
        if self.group_var.get() != "ทั้งหมด":
            where.append("group_name = ?")
            params.append(self.group_var.get())
        if self.sub_group_var.get() != "ทั้งหมด":
            category_code = self.filter_sub_group_map.get(self.sub_group_var.get())
            if category_code:
                where.append("category_code = ?")
                params.append(category_code)
            else:
                where.append("sub_group_name = ?")
                params.append(self.sub_group_var.get())
        search = self.search_var.get().strip()
        if search:
            like = f"%{search}%"
            where.append("(material_code LIKE ? OR material_name LIKE ? OR spec_size LIKE ? OR brand LIKE ?)")
            params.extend([like, like, like, like])
        return ("WHERE " + " AND ".join(where) if where else ""), params

    def _refresh_all(self):
        if not DB_PATH.exists():
            messagebox.showerror("ไม่พบฐานข้อมูล", str(DB_PATH))
            return
        self._refresh_materials()
        self._refresh_brands()

    def _refresh_materials(self):
        where_sql, params = self._where_clause()
        rows = self._query(
            f"""
            SELECT type, group_name, sub_group_name, material_code, material_name, spec_size, brand, unit
            FROM material_catalog
            {where_sql}
            ORDER BY type, group_name, sub_group_name, material_code
            LIMIT 1000
            """,
            params,
        )
        self.material_tree.delete(*self.material_tree.get_children())
        for row in rows:
            self.material_tree.insert(
                "",
                tk.END,
                values=(
                    row["material_code"],
                    row["material_name"] or "",
                    row["spec_size"] or "",
                    row["brand"] or "",
                    row["unit"] or "",
                    row["type"] or "",
                    row["group_name"] or "",
                    row["sub_group_name"] or "",
                ),
            )
        total = self._query(f"SELECT COUNT(*) AS total FROM material_catalog {where_sql}", params)[0]["total"]
        shown = len(rows)
        self.status_var.set(f"แสดง {shown:,} / {total:,} รายการ")

    def _refresh_brands(self):
        where_sql, params = self._where_clause()
        rows = self._query(
            f"""
            SELECT COALESCE(brand, '(ไม่ระบุ)') AS brand, COUNT(*) AS item_count
            FROM material_catalog
            {where_sql}
            GROUP BY COALESCE(brand, '(ไม่ระบุ)')
            ORDER BY item_count DESC, brand
            LIMIT 200
            """,
            params,
        )
        self.brand_tree.delete(*self.brand_tree.get_children())
        for row in rows:
            self.brand_tree.insert("", tk.END, values=(row["brand"], row["item_count"]))

    def _on_type_changed(self, _event=None):
        self._load_groups()
        self._refresh_all()

    def _on_group_changed(self, _event=None):
        self._load_sub_groups()
        self._refresh_all()

    def _on_filter_changed(self, _event=None):
        self._refresh_all()

    def _clear_filters(self):
        self.type_var.set("Product")
        self.group_var.set("ทั้งหมด")
        self.sub_group_var.set("ทั้งหมด")
        self.search_var.set("")
        self._load_groups()
        self._refresh_all()

    def _copy_selected_code(self, _event=None):
        selected = self.material_tree.selection()
        if not selected:
            return
        values = self.material_tree.item(selected[0], "values")
        if not values:
            return
        self.clipboard_clear()
        self.clipboard_append(values[0])
        self.status_var.set(f"คัดลอก {values[0]}")

    def _export_csv(self):
        where_sql, params = self._where_clause()
        rows = self._query(
            f"""
            SELECT type, group_name, sub_group_name, material_code, material_name, spec_size, brand, unit
            FROM material_catalog
            {where_sql}
            ORDER BY type, group_name, sub_group_name, material_code
            """,
            params,
        )
        if not rows:
            messagebox.showinfo("Export CSV", "ไม่มีข้อมูลสำหรับ export")
            return
        file_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="material_catalog_export.csv",
        )
        if not file_path:
            return
        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["Type", "Group", "Sub-Group", "Code", "Product/Material", "Spec/Size", "Brand", "Unit"])
            for row in rows:
                writer.writerow([row[key] or "" for key in row.keys()])
        messagebox.showinfo("Export CSV", f"บันทึกแล้ว\n{file_path}")

    def _open_db_folder(self):
        subprocess.Popen(["explorer", str(DB_PATH.parent)])

    def _open_add_material_dialog(self):
        AddMaterialDialog(self)


class AddMaterialDialog(tk.Toplevel):
    def __init__(self, app: MaterialCatalogApp):
        super().__init__(app)
        self.app = app
        self.conn = app.conn
        self.title("เพิ่มข้อมูล Material")
        self.geometry("760x520")
        self.minsize(680, 460)
        self.transient(app)
        self.grab_set()

        self.type_var = tk.StringVar(value=app.type_var.get() if app.type_var.get() != "ทั้งหมด" else "Product")
        self.group_var = tk.StringVar(value=app.group_var.get() if app.group_var.get() != "ทั้งหมด" else "")
        self.sub_group_var = tk.StringVar()
        self.prefix_var = tk.StringVar()
        self.material_part_var = tk.StringVar()
        self.spec_part_var = tk.StringVar(value="001")
        self.tail_part_var = tk.StringVar(value="0000")
        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.spec_var = tk.StringVar(value="Spec./Size")
        self.brand_var = tk.StringVar()
        self.unit_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.sub_group_map = {}
        self.material_part_var.trace_add("write", lambda *_args: self._update_generated_code())
        self.spec_part_var.trace_add("write", lambda *_args: self._update_generated_code())
        self.tail_part_var.trace_add("write", lambda *_args: self._update_generated_code())

        self._build()
        self._load_types()
        self._load_groups()
        self._load_sub_groups()

    def _build(self):
        root = ttk.Frame(self, padding=14)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="เพิ่มข้อมูลแบบแยกองค์ประกอบ", style="Title.TLabel").grid(row=0, column=0, columnspan=4, sticky="w")

        self.type_combo = self._row_combo(root, "1. Type", self.type_var, 1, self._on_type_changed)
        self.group_combo = self._row_combo(root, "2. Group", self.group_var, 2, self._on_group_changed, width=58)
        self.sub_group_combo = self._row_combo(root, "3. Sub-Group", self.sub_group_var, 3, self._on_sub_group_changed, width=58)

        ttk.Separator(root).grid(row=4, column=0, columnspan=4, sticky="ew", pady=12)

        self._row_entry(root, "4. Code Prefix", self.prefix_var, 5, state="readonly")
        self.name_combo = self._part_combo(root, "5. Product/Material", self.material_part_var, self.name_var, 6, self._on_material_name_changed)
        self.spec_combo = self._part_combo(root, "6. Spec/Size", self.spec_part_var, self.spec_var, 7, self._on_spec_changed)
        self._row_entry(root, "7. Material Code", self.code_var, 8, state="readonly")
        self.brand_combo = self._combo_entry(root, "8. Brand", self.brand_var, 9)
        self.unit_combo = self._combo_entry(root, "9. Unit", self.unit_var, 10)

        ttk.Label(root, textvariable=self.message_var, style="Meta.TLabel").grid(row=11, column=1, columnspan=3, sticky="w", pady=(8, 0))

        buttons = ttk.Frame(root)
        buttons.grid(row=12, column=0, columnspan=4, sticky="e", pady=(18, 0))
        ttk.Button(buttons, text="บันทึก", command=self._save).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="ล้างฟอร์ม", command=self._clear_detail_fields).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="ปิด", command=self.destroy).pack(side=tk.LEFT)

        root.columnconfigure(2, weight=1)

    def _row_combo(self, parent, label, variable, row, command, width=36):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly", width=width)
        combo.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
        combo.bind("<<ComboboxSelected>>", command)
        return combo

    def _row_entry(self, parent, label, variable, row, state="normal"):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable, state=state)
        entry.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
        return entry

    def _part_combo(self, parent, label, part_variable, text_variable, row, command):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        part = ttk.Entry(parent, textvariable=part_variable, width=8)
        part.grid(row=row, column=1, sticky="w", pady=5)
        combo = ttk.Combobox(parent, textvariable=text_variable, state="normal")
        combo.grid(row=row, column=2, columnspan=2, sticky="ew", padx=(8, 0), pady=5)
        combo.bind("<<ComboboxSelected>>", command)
        combo.bind("<FocusOut>", command)
        return combo

    def _combo_entry(self, parent, label, variable, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        combo = ttk.Combobox(parent, textvariable=variable, state="normal")
        combo.grid(row=row, column=1, columnspan=3, sticky="ew", pady=5)
        return combo

    def _query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def _load_types(self):
        values = [row["type_name"] for row in self._query("SELECT type_name FROM material_types ORDER BY type_name")]
        self.type_combo["values"] = values
        if self.type_var.get() not in values:
            self.type_var.set(values[0] if values else "")

    def _load_groups(self):
        rows = self._query(
            "SELECT group_name FROM material_groups WHERE type_name = ? ORDER BY group_name",
            (self.type_var.get(),),
        )
        values = [row["group_name"] for row in rows]
        self.group_combo["values"] = values
        if self.group_var.get() not in values:
            self.group_var.set(values[0] if values else "")

    def _load_sub_groups(self):
        rows = self._query(
            """
            SELECT msg.category_code, msg.sub_group_name
            FROM material_sub_groups msg
            JOIN material_groups mg ON mg.group_id = msg.group_id
            WHERE mg.type_name = ? AND mg.group_name = ?
            ORDER BY msg.category_code
            """,
            (self.type_var.get(), self.group_var.get()),
        )
        self.sub_group_map = {
            f"{row['category_code']} - {row['sub_group_name']}": row["category_code"]
            for row in rows
        }
        values = list(self.sub_group_map)
        self.sub_group_combo["values"] = values
        if self.sub_group_var.get() not in values:
            self.sub_group_var.set(values[0] if values else "")
        self._on_sub_group_changed()

    def _on_type_changed(self, _event=None):
        self._load_groups()
        self._load_sub_groups()

    def _on_group_changed(self, _event=None):
        self._load_sub_groups()

    def _on_sub_group_changed(self, _event=None):
        category_code = self._selected_category_code()
        self.prefix_var.set(category_code)
        self._load_related_dropdowns()
        if category_code:
            self.material_part_var.set(self._next_material_part(category_code))
            self.spec_part_var.set("001")
            self.tail_part_var.set("0000")
        self._update_generated_code()
        self.message_var.set(f"Code = {category_code} + Material + Spec + 0000" if category_code else "")

    def _selected_category_code(self):
        return self.sub_group_map.get(self.sub_group_var.get(), "")

    def _clear_detail_fields(self):
        category_code = self._selected_category_code()
        self.prefix_var.set(category_code)
        self.material_part_var.set(self._next_material_part(category_code) if category_code else "")
        self.spec_part_var.set("001")
        self.tail_part_var.set("0000")
        self._update_generated_code()
        self.name_var.set("")
        self.spec_var.set("Spec./Size")
        self.brand_var.set("")
        self.unit_var.set("")
        self._load_related_dropdowns()
        self.message_var.set(f"Code = {category_code} + Material + Spec + 0000" if category_code else "")

    def _digits(self, value, width):
        text = "".join(ch for ch in value.strip() if ch.isdigit())
        if not text:
            return "0" * width
        return text[-width:].zfill(width)

    def _next_material_part(self, category_code):
        rows = self._query(
            """
            SELECT material_code
            FROM materials
            WHERE category_code = ? AND material_code LIKE ?
            """,
            (category_code, f"{category_code}%"),
        )
        max_part = 0
        for row in rows:
            code = row["material_code"] or ""
            part = code[len(category_code) : len(category_code) + 3]
            if part.isdigit():
                max_part = max(max_part, int(part))
        return str(max_part + 1).zfill(3)[-3:]

    def _next_spec_part(self, category_code, material_part):
        rows = self._query(
            """
            SELECT material_code
            FROM materials
            WHERE category_code = ? AND material_code LIKE ?
            """,
            (category_code, f"{category_code}{material_part}%"),
        )
        max_part = 0
        start = len(category_code) + 3
        for row in rows:
            code = row["material_code"] or ""
            part = code[start : start + 3]
            if part.isdigit():
                max_part = max(max_part, int(part))
        return str(max_part + 1).zfill(3)[-3:]

    def _next_tail_part(self, category_code, material_part, spec_part):
        base = f"{category_code}{material_part}{spec_part}"
        rows = self._query(
            """
            SELECT material_code
            FROM materials
            WHERE category_code = ? AND material_code LIKE ?
            """,
            (category_code, f"{base}%"),
        )
        max_tail = -1
        for row in rows:
            code = row["material_code"] or ""
            tail = code[len(base) : len(base) + 4]
            if tail.isdigit():
                max_tail = max(max_tail, int(tail))
        return "0000" if max_tail < 0 else str(max_tail + 1).zfill(4)[-4:]

    def _load_related_dropdowns(self):
        category_code = self._selected_category_code()
        if not category_code:
            return
        names = [
            row["material_name"]
            for row in self._query(
                """
                SELECT DISTINCT material_name
                FROM materials
                WHERE category_code = ? AND material_name IS NOT NULL AND material_name <> ''
                ORDER BY material_name COLLATE NOCASE
                """,
                (category_code,),
            )
        ]
        specs = [
            row["spec_size"]
            for row in self._query(
                """
                SELECT DISTINCT spec_size
                FROM materials
                WHERE category_code = ? AND spec_size IS NOT NULL AND spec_size <> ''
                ORDER BY spec_size COLLATE NOCASE
                """,
                (category_code,),
            )
        ]
        brands = [
            row["brand"]
            for row in self._query(
                """
                SELECT DISTINCT brand
                FROM materials
                WHERE category_code = ? AND brand IS NOT NULL AND brand <> ''
                ORDER BY brand COLLATE NOCASE
                """,
                (category_code,),
            )
        ]
        units = [
            row["unit"]
            for row in self._query(
                """
                SELECT DISTINCT unit
                FROM materials
                WHERE category_code = ? AND unit IS NOT NULL AND unit <> ''
                ORDER BY unit COLLATE NOCASE
                """,
                (category_code,),
            )
        ]
        self.name_combo["values"] = names
        self.spec_combo["values"] = specs
        self.brand_combo["values"] = brands
        self.unit_combo["values"] = units

    def _load_specs_for_material(self):
        category_code = self._selected_category_code()
        material_name = self.name_var.get().strip()
        if not category_code:
            return
        params = [category_code]
        where_name = ""
        if material_name:
            where_name = "AND material_name = ?"
            params.append(material_name)
        specs = [
            row["spec_size"]
            for row in self._query(
                f"""
                SELECT DISTINCT spec_size
                FROM materials
                WHERE category_code = ? {where_name}
                  AND spec_size IS NOT NULL AND spec_size <> ''
                ORDER BY spec_size COLLATE NOCASE
                """,
                params,
            )
        ]
        self.spec_combo["values"] = specs

    def _on_material_name_changed(self, _event=None):
        category_code = self._selected_category_code()
        material_name = self.name_var.get().strip()
        if not category_code:
            return
        row = self.conn.execute(
            """
            SELECT material_code
            FROM materials
            WHERE category_code = ? AND material_name = ?
            ORDER BY material_code
            LIMIT 1
            """,
            (category_code, material_name),
        ).fetchone()
        if row:
            code = row["material_code"]
            self.material_part_var.set(code[len(category_code) : len(category_code) + 3])
            self.spec_part_var.set(self._next_spec_part(category_code, self.material_part_var.get()))
            self.tail_part_var.set("0000")
        else:
            self.material_part_var.set(self._next_material_part(category_code))
            self.spec_part_var.set("001")
            self.tail_part_var.set("0000")
        self._load_specs_for_material()
        self._update_generated_code()

    def _on_spec_changed(self, _event=None):
        category_code = self._selected_category_code()
        material_name = self.name_var.get().strip()
        spec_size = self.spec_var.get().strip()
        if not category_code:
            return
        row = self.conn.execute(
            """
            SELECT material_code
            FROM materials
            WHERE category_code = ?
              AND material_name = ?
              AND COALESCE(spec_size, '') = ?
            ORDER BY material_code
            LIMIT 1
            """,
            (category_code, material_name, spec_size),
        ).fetchone()
        if row:
            code = row["material_code"]
            start = len(category_code)
            self.material_part_var.set(code[start : start + 3])
            self.spec_part_var.set(code[start + 3 : start + 6])
            self.tail_part_var.set(self._next_tail_part(category_code, self.material_part_var.get(), self.spec_part_var.get()))
        else:
            self.spec_part_var.set(self._next_spec_part(category_code, self.material_part_var.get()))
            self.tail_part_var.set("0000")
        self._update_generated_code()

    def _update_generated_code(self):
        prefix = self.prefix_var.get().strip().upper()
        material_part = self._digits(self.material_part_var.get(), 3)
        spec_part = self._digits(self.spec_part_var.get(), 3)
        tail_part = self._digits(self.tail_part_var.get(), 4)
        self.code_var.set(f"{prefix}{material_part}{spec_part}{tail_part}" if prefix else "")

    def _clean(self, value):
        text = value.strip()
        return text if text else None

    def _save(self):
        category_code = self._selected_category_code()
        self._on_material_name_changed()
        self._on_spec_changed()
        self._update_generated_code()
        code = self.code_var.get().strip().upper()
        name = self.name_var.get().strip()
        spec = self.spec_var.get().strip()
        brand = self.brand_var.get().strip()
        unit = self.unit_var.get().strip()

        if not category_code:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาเลือก Sub-Group")
            return
        if not code or not name:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณากรอก Product/Material")
            return
        if not code.startswith(category_code):
            messagebox.showwarning(
                "รหัสผิดหมวด",
                f"Code ต้องขึ้นต้นด้วย {category_code}\n\nCode ที่กรอก: {code}",
            )
            return

        try:
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO materials (
                        category_code, source_no, material_code, material_name, spec_size, brand, unit
                    ) VALUES (?, NULL, ?, ?, ?, ?, ?)
                    """,
                    (
                        category_code,
                        code,
                        name,
                        self._clean(spec) or "Spec./Size",
                        self._clean(brand),
                        self._clean(unit) or "EA",
                    ),
                )
                self.conn.execute(
                    """
                    UPDATE material_sub_groups
                    SET item_count = (
                        SELECT COUNT(*)
                        FROM materials
                        WHERE materials.category_code = material_sub_groups.category_code
                    )
                    WHERE category_code = ?
                    """,
                    (category_code,),
                )
            self.app.group_var.set(self.group_var.get())
            self.app._load_groups()
            self.app._load_sub_groups()
            self.app.sub_group_var.set(self.sub_group_var.get())
            self.app.search_var.set(code)
            self.app._refresh_all()
            self.message_var.set(f"บันทึกแล้ว: {code}")
            self._clear_detail_fields()
        except sqlite3.IntegrityError:
            messagebox.showerror("Code ซ้ำ", f"มี Material Code นี้อยู่แล้ว:\n{code}")


def main():
    if not DB_PATH.exists():
        messagebox.showerror("ไม่พบฐานข้อมูล", str(DB_PATH))
        return 1
    app = MaterialCatalogApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        log_path = APP_DIR / "material_catalog_app_error.log"
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise
