# -*- coding: utf-8 -*-
"""
Material Control Fuji - Streamlit UI

เว็บเวอร์ชันคู่ขนานของโปรแกรม Tkinter เดิม โดยคงโครงหน้าจอหลักและฐานข้อมูล SQLite
ชุดเดียวกันให้มากที่สุด
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "material_control.sqlite3"
SQLITE_BUSY_TIMEOUT_MS = 30000

ROLE_REQUESTOR = "ผู้เบิก (Requestor)"
ROLE_INSPECTOR = "ผู้ตรวจ (Inspector)"
ROLE_APPROVER = "ผู้อนุมัติ (Approver)"
ROLE_DISPENSER = "ผู้จ่าย (Dispenser)"


def trim(value: Any) -> str:
    return "" if value is None else str(value).strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        text = trim(value).replace(",", "")
        return float(text) if text else default
    except Exception:
        return default


def format_qty(value: Any) -> str:
    qty = safe_float(value)
    if abs(qty - int(qty)) < 0.0000001:
        return str(int(qty))
    return f"{qty:,.2f}".rstrip("0").rstrip(".")


def today_input_date() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def normalize_date_input(value: Any) -> str:
    text = trim(value)
    if not text:
        return ""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def display_date(value: Any) -> str:
    text = trim(value)
    if not text:
        return ""
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


def row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@st.cache_resource
def get_conn() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH), timeout=SQLITE_BUSY_TIMEOUT_MS / 1000, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.DatabaseError:
        conn.execute("PRAGMA journal_mode = DELETE")
    init_schema(conn)
    seed_defaults(conn)
    return conn


def query(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    return list(get_conn().execute(sql, tuple(params)))


def execute(sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
    conn = get_conn()
    cur = conn.execute(sql, tuple(params))
    conn.commit()
    return cur


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            abbr TEXT NOT NULL DEFAULT 'GN',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS receipt_tos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS receipt_froms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, role)
        );
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            brand TEXT NOT NULL DEFAULT '',
            spec TEXT NOT NULL DEFAULT '-',
            unit TEXT NOT NULL DEFAULT 'Pcs',
            category TEXT NOT NULL DEFAULT 'General',
            drum_no TEXT NOT NULL DEFAULT '',
            boq_opening REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE UNIQUE INDEX IF NOT EXISTS ux_items_duplicate_key
            ON items(category, name, spec, brand, unit)
            WHERE lower(category || ' ' || name || ' ' || spec) NOT LIKE '%cable%'
              AND (category || ' ' || name || ' ' || spec) NOT LIKE '%สาย%';

        CREATE TABLE IF NOT EXISTS receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT NOT NULL UNIQUE,
            receipt_date TEXT NOT NULL,
            receipt_to TEXT NOT NULL DEFAULT '',
            vendor TEXT NOT NULL,
            do_no TEXT NOT NULL DEFAULT '',
            pr_no TEXT NOT NULL DEFAULT '',
            receipt_type TEXT NOT NULL DEFAULT 'MATERIAL',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id INTEGER NOT NULL,
            line_no INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty REAL NOT NULL CHECK(qty > 0),
            cable_length TEXT NOT NULL DEFAULT '',
            drum_no TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_no TEXT NOT NULL UNIQUE,
            request_date TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            requestor TEXT NOT NULL DEFAULT '',
            inspector TEXT NOT NULL DEFAULT '',
            approver TEXT NOT NULL DEFAULT '',
            dispenser TEXT NOT NULL DEFAULT '',
            work_location TEXT NOT NULL DEFAULT '',
            request_type TEXT NOT NULL DEFAULT 'MATERIAL',
            status TEXT NOT NULL DEFAULT 'Approved',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS request_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER NOT NULL,
            line_no INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            receipt_item_id INTEGER,
            qty REAL NOT NULL CHECK(qty > 0),
            cable_length TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS boq_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boq_no TEXT NOT NULL UNIQUE,
            boq_date TEXT NOT NULL,
            ref_no TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS boq_receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boq_receipt_id INTEGER NOT NULL,
            line_no INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            qty REAL NOT NULL CHECK(qty > 0),
            FOREIGN KEY(boq_receipt_id) REFERENCES boq_receipts(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    for table, columns in {
        "items": [
            ("drum_no", "TEXT NOT NULL DEFAULT ''"),
            ("boq_opening", "REAL NOT NULL DEFAULT 0"),
        ],
        "receipts": [
            ("receipt_to", "TEXT NOT NULL DEFAULT ''"),
            ("receipt_type", "TEXT NOT NULL DEFAULT 'MATERIAL'"),
        ],
        "receipt_items": [
            ("cable_length", "TEXT NOT NULL DEFAULT ''"),
            ("drum_no", "TEXT NOT NULL DEFAULT ''"),
        ],
        "requests": [("request_type", "TEXT NOT NULL DEFAULT 'MATERIAL'")],
        "request_items": [
            ("receipt_item_id", "INTEGER"),
            ("cable_length", "TEXT NOT NULL DEFAULT ''"),
        ],
    }.items():
        existing = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, definition in columns:
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    conn.commit()


def seed_defaults(conn: sqlite3.Connection) -> None:
    year = datetime.now().year + 543
    defaults = [
        ("INSERT OR IGNORE INTO categories(name, abbr) VALUES(?, ?)", ("General", "GN")),
        ("INSERT OR IGNORE INTO units(name) VALUES(?)", ("Pcs",)),
        ("INSERT OR IGNORE INTO units(name) VALUES(?)", ("unit",)),
        ("INSERT OR IGNORE INTO companies(name) VALUES(?)", ("บริษัทหลัก (Main Contractor)",)),
        ("INSERT OR IGNORE INTO receipt_tos(name) VALUES(?)", ("บริษัทหลัก (Main Contractor)",)),
        ("INSERT OR IGNORE INTO receipt_froms(name) VALUES(?)", ("Fuji",)),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("request_prefix", f"REQ-{str(year)[-2:]}-")),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("request_next_run", "1")),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("request_pad_width", "4")),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("receipt_prefix", f"REC-{str(year)[-2:]}-")),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("receipt_next_run", "1")),
        ("INSERT OR IGNORE INTO app_settings(key, value) VALUES(?, ?)", ("receipt_pad_width", "4")),
    ]
    for sql, params in defaults:
        conn.execute(sql, params)
    for role in (ROLE_REQUESTOR, ROLE_INSPECTOR, ROLE_APPROVER, ROLE_DISPENSER):
        conn.execute("INSERT OR IGNORE INTO personnel(name, role) VALUES(?, ?)", ("-", role))
    conn.commit()


def setting(key: str, default: str = "") -> str:
    row = get_conn().execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    return trim(row["value"]) if row else default


def set_setting(key: str, value: Any) -> None:
    execute(
        "INSERT INTO app_settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )


def option_values(table: str, extra_where: str = "", params: Iterable[Any] = ()) -> list[str]:
    rows = query(f"SELECT name FROM {table} {extra_where} ORDER BY name COLLATE NOCASE", params)
    return [trim(r["name"]) for r in rows if trim(r["name"])]


def next_item_code(category: str) -> str:
    category = trim(category) or "General"
    row = get_conn().execute("SELECT abbr FROM categories WHERE name=?", (category,)).fetchone()
    abbr = trim(row["abbr"] if row else category[:2].upper()) or "GN"
    prefix = abbr.upper() + "-"
    max_no = 0
    for r in query("SELECT code FROM items WHERE code LIKE ?", (prefix + "%",)):
        tail = trim(r["code"]).replace(prefix, "")
        if tail.isdigit():
            max_no = max(max_no, int(tail))
    return prefix + str(max_no + 1).zfill(3)


def next_doc_no(prefix: str, table: str, column: str) -> str:
    year = datetime.now().year + 543
    base = f"{prefix}-{str(year)[-2:]}-"
    max_no = 0
    for r in query(f"SELECT {column} AS no FROM {table} WHERE {column} LIKE ?", (base + "%",)):
        tail = trim(r["no"]).replace(base, "")
        if tail.isdigit():
            max_no = max(max_no, int(tail))
    return base + str(max_no + 1).zfill(4)


def next_config_doc_no(kind: str) -> str:
    table, column = ("requests", "request_no") if kind == "request" else ("receipts", "receipt_no")
    prefix = setting(f"{kind}_prefix", "REQ-" if kind == "request" else "REC-")
    next_run = int(safe_float(setting(f"{kind}_next_run", "1"), 1))
    pad_width = int(safe_float(setting(f"{kind}_pad_width", "4"), 4))
    max_existing = 0
    for r in query(f"SELECT {column} AS no FROM {table} WHERE {column} LIKE ?", (prefix + "%",)):
        tail = trim(r["no"])[len(prefix):]
        if tail.isdigit():
            max_existing = max(max_existing, int(tail))
    run_no = max(next_run, max_existing + 1)
    return prefix + (str(run_no).zfill(pad_width) if pad_width > 0 else str(run_no))


def advance_config_doc_no(kind: str, used_no: str) -> None:
    prefix = setting(f"{kind}_prefix", "")
    if not prefix or not trim(used_no).startswith(prefix):
        return
    tail = trim(used_no)[len(prefix):]
    if tail.isdigit():
        current = int(safe_float(setting(f"{kind}_next_run", "1"), 1))
        set_setting(f"{kind}_next_run", max(current, int(tail) + 1))


def is_cable_item(row: dict[str, Any]) -> bool:
    text = f"{row.get('category', '')} {row.get('name', '')} {row.get('spec', '')}".lower()
    if any(word in text for word in ("cable tray", "wire way", "wireway", "tray", "ราง")):
        return False
    return "cable" in text or "สาย" in text


def stock_summary(keyword: str = "", movement_only: bool = False) -> list[dict[str, Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    if trim(keyword):
        conditions.append(
            "lower(i.code||' '||i.name||' '||i.brand||' '||i.spec||' '||i.unit||' '||i.category||' '||COALESCE(i.drum_no,'')) LIKE ?"
        )
        params.append("%" + trim(keyword).lower() + "%")
    if movement_only:
        conditions.append("(COALESCE(b.boq_qty,0)<>0 OR COALESCE(r.in_qty,0)<>0 OR COALESCE(q.out_qty,0)<>0)")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    rows = query(
        f"""
        SELECT
            i.id, i.code, i.category, i.name, i.brand, i.spec, i.unit, COALESCE(i.drum_no,'') AS drum_no,
            COALESCE(b.boq_qty, 0) AS boq_qty,
            COALESCE(r.in_qty, 0) AS in_qty,
            COALESCE(q.out_qty, 0) AS out_qty,
            COALESCE(b.boq_qty, 0) - COALESCE(r.in_qty, 0) AS boq_balance_qty,
            COALESCE(r.in_qty, 0) - COALESCE(q.out_qty, 0) AS bal_qty
        FROM items i
        LEFT JOIN (SELECT item_id, SUM(qty) AS boq_qty FROM boq_receipt_items GROUP BY item_id) b ON b.item_id=i.id
        LEFT JOIN (SELECT item_id, SUM(qty) AS in_qty FROM receipt_items GROUP BY item_id) r ON r.item_id=i.id
        LEFT JOIN (SELECT item_id, SUM(qty) AS out_qty FROM request_items GROUP BY item_id) q ON q.item_id=i.id
        {where}
        ORDER BY i.category COLLATE NOCASE, i.name COLLATE NOCASE, i.spec COLLATE NOCASE, i.code COLLATE NOCASE
        """,
        params,
    )
    return [row_dict(r) for r in rows]


def item_options() -> list[dict[str, Any]]:
    return [row_dict(r) for r in query("SELECT * FROM items ORDER BY category, code, name")]


def selected_item_from_label(label: str) -> dict[str, Any] | None:
    if not label:
        return None
    item_id = int(label.split(" | ", 1)[0])
    row = get_conn().execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return row_dict(row) if row else None


def item_select(label: str, key: str) -> dict[str, Any] | None:
    items = item_options()
    labels = [f"{r['id']} | {r['code']} | {r['name']} | {r['spec']} | {r['unit']}" for r in items]
    selected = st.selectbox(label, [""] + labels, key=key)
    return selected_item_from_label(selected)


def show_table(rows: list[dict[str, Any]], height: int = 420) -> None:
    st.dataframe(rows, hide_index=True, width="stretch", height=height)


def header() -> None:
    st.set_page_config(page_title="Material Control Fuji", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
        :root { --line: #cbd5e1; --head: #e5e7eb; --ink: #0f172a; --muted: #475569; }
        .stApp { background: #f8fafc; color: var(--ink); }
        div[data-testid="stHeader"] { background: #f8fafc; }
        .main-title { font-size: 24px; font-weight: 800; margin-bottom: 0; }
        .sub-title { color: var(--muted); margin-top: 2px; margin-bottom: 14px; }
        div[data-testid="stMetric"] { background: #fff; border: 1px solid var(--line); padding: 10px 12px; border-radius: 6px; }
        div[data-testid="stDataFrame"] { border: 1px solid #94a3b8; border-radius: 4px; background: white; }
        .stTabs [data-baseweb="tab"] { font-weight: 700; padding: 10px 14px; }
        .stButton>button { border-radius: 4px; font-weight: 700; }
        section[data-testid="stSidebar"] { background: #eef2f7; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<p class="main-title">Material Control Fuji</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="sub-title">SQLite Web UI | Database: {DB_PATH}</p>',
        unsafe_allow_html=True,
    )


def dashboard_tab() -> None:
    left, right = st.columns([3, 1])
    keyword = left.text_input("Search", key="dash_search", placeholder="Code / Name / Spec / Brand / Category")
    movement_only = right.checkbox("Movement only", value=True)
    rows = stock_summary(keyword, movement_only=movement_only)
    total_boq = sum(safe_float(r["boq_qty"]) for r in rows)
    total_in = sum(safe_float(r["in_qty"]) for r in rows)
    total_out = sum(safe_float(r["out_qty"]) for r in rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("รายการ", f"{len(rows):,}")
    c2.metric("Total BOQ", format_qty(total_boq))
    c3.metric("Total In", format_qty(total_in))
    c4.metric("Total Out", format_qty(total_out))
    show_table(
        [
            {
                "Code": r["code"],
                "Category": r["category"],
                "Name": r["name"],
                "Brand": r["brand"],
                "Spec": r["spec"],
                "Unit": r["unit"],
                "BOQ": format_qty(r["boq_qty"]),
                "In": format_qty(r["in_qty"]),
                "Out": format_qty(r["out_qty"]),
                "Balance": format_qty(r["bal_qty"]),
                "BOQ Balance": format_qty(r["boq_balance_qty"]),
                "Drum No.": r["drum_no"],
            }
            for r in rows
        ]
    )


def master_tab() -> None:
    keyword = st.text_input("Search Master", key="master_search")
    rows = stock_summary(keyword)
    show_table(
        [
            {
                "ID": r["id"],
                "Code": r["code"],
                "Category": r["category"],
                "Name": r["name"],
                "Brand": r["brand"],
                "Spec": r["spec"],
                "Unit": r["unit"],
                "Drum No.": r["drum_no"],
                "BOQ": format_qty(r["boq_qty"]),
                "In": format_qty(r["in_qty"]),
                "Out": format_qty(r["out_qty"]),
                "Balance": format_qty(r["bal_qty"]),
            }
            for r in rows
        ],
        height=330,
    )
    st.divider()
    mode = st.radio("Mode", ["Add", "Edit"], horizontal=True)
    edit_row = None
    if mode == "Edit":
        edit_row = item_select("เลือกรายการที่ต้องการแก้ไข", "master_edit_item")
    with st.form("master_form", clear_on_submit=False):
        categories = option_values("categories")
        units = option_values("units")
        brands = option_values("brands")
        category_default = trim(edit_row["category"]) if edit_row else (categories[0] if categories else "General")
        unit_default = trim(edit_row["unit"]) if edit_row else (units[0] if units else "Pcs")
        brand_default = trim(edit_row["brand"]) if edit_row else ""
        c1, c2, c3 = st.columns([1, 1, 2])
        category = c1.selectbox("Category", categories or ["General"], index=max(0, (categories or ["General"]).index(category_default)) if category_default in (categories or []) else 0)
        code = c2.text_input("Code", value=trim(edit_row["code"]) if edit_row else next_item_code(category))
        name = c3.text_input("Name", value=trim(edit_row["name"]) if edit_row else "")
        c4, c5, c6 = st.columns(3)
        brand = c4.text_input("Brand", value=brand_default)
        spec = c5.text_input("Spec / Size", value=trim(edit_row["spec"]) if edit_row else "-")
        unit = c6.selectbox("Unit", units or ["Pcs"], index=max(0, (units or ["Pcs"]).index(unit_default)) if unit_default in (units or []) else 0)
        drum_no = st.text_input("Drum No.", value=trim(edit_row["drum_no"]) if edit_row else "")
        submitted = st.form_submit_button("Save Master")
    if submitted:
        if not trim(code) or not trim(name):
            st.error("กรุณากรอก Code และ Name")
        else:
            try:
                execute("INSERT OR IGNORE INTO brands(name) VALUES(?)", (brand,))
                if edit_row:
                    execute(
                        "UPDATE items SET code=?, category=?, name=?, brand=?, spec=?, unit=?, drum_no=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                        (code, category, name, brand, spec or "-", unit, drum_no, edit_row["id"]),
                    )
                    st.success("แก้ไข Master เรียบร้อย")
                else:
                    execute(
                        "INSERT INTO items(code, category, name, brand, spec, unit, drum_no) VALUES(?,?,?,?,?,?,?)",
                        (code, category, name, brand, spec or "-", unit, drum_no),
                    )
                    st.success("เพิ่ม Master เรียบร้อย")
                st.rerun()
            except sqlite3.IntegrityError as exc:
                st.error(f"ข้อมูลซ้ำหรือไม่ถูกต้อง: {exc}")
    if edit_row and st.button("Delete Master", type="secondary"):
        try:
            execute("DELETE FROM items WHERE id=?", (edit_row["id"],))
            st.success("ลบ Master เรียบร้อย")
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("ลบไม่ได้ เพราะรายการนี้มีประวัติใช้งานแล้ว")


def init_lines(key: str) -> None:
    if key not in st.session_state:
        st.session_state[key] = []


def add_line_form(key: str, qty_label: str, allow_cable_length: bool = False) -> None:
    row = item_select("เพิ่มพัสดุ", f"{key}_item")
    c1, c2 = st.columns([1, 2])
    qty = c1.number_input(qty_label, min_value=0.0, step=1.0, key=f"{key}_qty")
    cable_length = c2.text_input("ระยะสาย", key=f"{key}_cable_length") if allow_cable_length else ""
    if st.button("เพิ่มบรรทัด", key=f"{key}_add"):
        if not row or qty <= 0:
            st.error("กรุณาเลือกรายการและใส่จำนวนมากกว่า 0")
        else:
            line = {
                "item_id": row["id"],
                "code": row["code"],
                "category": row["category"],
                "name": row["name"],
                "brand": row["brand"],
                "spec": row["spec"],
                "unit": row["unit"],
                "qty": qty,
                "cable_length": cable_length,
            }
            st.session_state[key].append(line)
            st.rerun()


def lines_editor(key: str) -> None:
    lines = st.session_state.get(key, [])
    show_table(
        [
            {
                "#": idx,
                "Code": line["code"],
                "Name": line["name"],
                "Brand": line["brand"],
                "Spec": line["spec"],
                "Qty": format_qty(line["qty"]),
                "Unit": line["unit"],
                "ระยะสาย": line.get("cable_length", ""),
            }
            for idx, line in enumerate(lines, start=1)
        ],
        height=230,
    )
    c1, c2 = st.columns([1, 5])
    remove_idx = c1.number_input("ลบบรรทัดที่", min_value=0, max_value=max(0, len(lines)), step=1, key=f"{key}_remove_idx")
    if c2.button("ลบบรรทัด", key=f"{key}_remove") and remove_idx:
        st.session_state[key].pop(int(remove_idx) - 1)
        st.rerun()


def boq_tab() -> None:
    init_lines("boq_lines")
    if st.session_state.pop("boq_reset_after_save", False):
        st.session_state["boq_no"] = next_doc_no("BOQ", "boq_receipts", "boq_no")
        st.session_state["boq_date"] = today_input_date()
        st.session_state["boq_ref_no"] = ""
        st.session_state["boq_note"] = ""
    st.session_state.setdefault("boq_no", next_doc_no("BOQ", "boq_receipts", "boq_no"))
    st.session_state.setdefault("boq_date", today_input_date())
    c1, c2, c3 = st.columns(3)
    c1.text_input("BOQ No.", key="boq_no")
    c2.text_input("Date (DD/MM/YYYY)", key="boq_date")
    c3.text_input("Ref No.", key="boq_ref_no")
    st.text_input("Note", key="boq_note")
    add_line_form("boq_lines", "จำนวน BOQ")
    lines_editor("boq_lines")
    if st.button("Save BOQ Receipt", type="primary"):
        doc_date = normalize_date_input(st.session_state["boq_date"])
        if not trim(st.session_state["boq_no"]) or not doc_date or not st.session_state["boq_lines"]:
            st.error("กรุณากรอกเลขที่ วันที่ และเพิ่มรายการอย่างน้อย 1 บรรทัด")
            return
        try:
            conn = get_conn()
            cur = conn.execute(
                "INSERT INTO boq_receipts(boq_no, boq_date, ref_no, note) VALUES(?,?,?,?)",
                (
                    st.session_state["boq_no"],
                    doc_date,
                    st.session_state.get("boq_ref_no", ""),
                    st.session_state.get("boq_note", ""),
                ),
            )
            br_id = cur.lastrowid
            for idx, line in enumerate(st.session_state["boq_lines"], start=1):
                conn.execute(
                    "INSERT INTO boq_receipt_items(boq_receipt_id, line_no, item_id, qty) VALUES(?,?,?,?)",
                    (br_id, idx, line["item_id"], safe_float(line["qty"])),
                )
            conn.commit()
            st.session_state["boq_lines"] = []
            st.session_state["boq_reset_after_save"] = True
            st.success("บันทึก BOQ Receipt เรียบร้อย")
            st.rerun()
        except sqlite3.IntegrityError as exc:
            get_conn().rollback()
            st.error(f"บันทึกไม่ได้: {exc}")


def receiving_tab() -> None:
    init_lines("receipt_lines")
    if st.session_state.pop("receipt_reset_after_save", False):
        st.session_state["receipt_no"] = next_config_doc_no("receipt")
        st.session_state["receipt_date"] = today_input_date()
        st.session_state["receipt_vendor"] = ""
        st.session_state["receipt_do_no"] = ""
        st.session_state["receipt_pr_no"] = ""
        st.session_state["receipt_note"] = ""
    st.session_state.setdefault("receipt_no", next_config_doc_no("receipt"))
    st.session_state.setdefault("receipt_date", today_input_date())
    receipt_type = st.radio("Receiving Type", ["MATERIAL", "CABLE"], horizontal=True, key="receipt_type")
    c1, c2, c3, c4 = st.columns(4)
    c1.text_input("Receipt No.", key="receipt_no")
    c2.text_input("Date (DD/MM/YYYY)", key="receipt_date")
    receipt_to_options = option_values("receipt_tos") or [""]
    c3.selectbox("To", receipt_to_options, key="receipt_to")
    c4.text_input("From", key="receipt_vendor")
    c5, c6 = st.columns(2)
    c5.text_input("DO / Invoice", key="receipt_do_no")
    c6.text_input("PR / Ref", key="receipt_pr_no")
    st.text_input("Note", key="receipt_note")
    add_line_form("receipt_lines", "จำนวนรับเข้า", allow_cable_length=receipt_type == "CABLE")
    lines_editor("receipt_lines")
    if st.button("Save Receipt", type="primary"):
        doc_date = normalize_date_input(st.session_state["receipt_date"])
        if (
            not trim(st.session_state["receipt_no"])
            or not doc_date
            or not trim(st.session_state["receipt_to"])
            or not trim(st.session_state["receipt_vendor"])
        ):
            st.error("กรุณากรอก Receipt No., Date, To และ From")
            return
        if not st.session_state["receipt_lines"]:
            st.error("กรุณาเพิ่มรายการรับเข้า")
            return
        try:
            conn = get_conn()
            conn.execute("INSERT OR IGNORE INTO receipt_tos(name) VALUES(?)", (st.session_state["receipt_to"],))
            conn.execute("INSERT OR IGNORE INTO receipt_froms(name) VALUES(?)", (st.session_state["receipt_vendor"],))
            conn.execute("INSERT OR IGNORE INTO vendors(name) VALUES(?)", (st.session_state["receipt_vendor"],))
            cur = conn.execute(
                "INSERT INTO receipts(receipt_no, receipt_date, receipt_to, vendor, do_no, pr_no, receipt_type, note) VALUES(?,?,?,?,?,?,?,?)",
                (
                    st.session_state["receipt_no"],
                    doc_date,
                    st.session_state["receipt_to"],
                    st.session_state["receipt_vendor"],
                    st.session_state.get("receipt_do_no", ""),
                    st.session_state.get("receipt_pr_no", ""),
                    st.session_state["receipt_type"],
                    st.session_state.get("receipt_note", ""),
                ),
            )
            rid = cur.lastrowid
            for idx, line in enumerate(st.session_state["receipt_lines"], start=1):
                conn.execute(
                    "INSERT INTO receipt_items(receipt_id, line_no, item_id, qty, cable_length) VALUES(?,?,?,?,?)",
                    (rid, idx, line["item_id"], safe_float(line["qty"]), trim(line.get("cable_length", ""))),
                )
            conn.commit()
            advance_config_doc_no("receipt", st.session_state["receipt_no"])
            st.session_state["receipt_lines"] = []
            st.session_state["receipt_reset_after_save"] = True
            st.success("บันทึกรับเข้าเรียบร้อย")
            st.rerun()
        except sqlite3.IntegrityError as exc:
            get_conn().rollback()
            st.error(f"บันทึกไม่ได้: {exc}")


def issue_tab() -> None:
    init_lines("issue_lines")
    if st.session_state.pop("request_reset_after_save", False):
        st.session_state["request_no"] = next_config_doc_no("request")
        st.session_state["request_date"] = today_input_date()
        st.session_state["work_location"] = ""
        st.session_state["issue_note"] = ""
    st.session_state.setdefault("request_no", next_config_doc_no("request"))
    st.session_state.setdefault("request_date", today_input_date())
    request_type = st.radio("Issue Type", ["MATERIAL", "CABLE"], horizontal=True, key="request_type")
    companies = option_values("companies") or [""]
    requestors = option_values("personnel", "WHERE role=?", (ROLE_REQUESTOR,)) or [""]
    inspectors = option_values("personnel", "WHERE role=?", (ROLE_INSPECTOR,)) or [""]
    approvers = option_values("personnel", "WHERE role=?", (ROLE_APPROVER,)) or [""]
    dispensers = option_values("personnel", "WHERE role=?", (ROLE_DISPENSER,)) or [""]
    c1, c2, c3, c4 = st.columns(4)
    c1.text_input("Req No.", key="request_no")
    c2.text_input("Date (DD/MM/YYYY)", key="request_date")
    c3.selectbox("Company", companies, key="request_company")
    c4.selectbox("Requestor", requestors, key="requestor")
    c5, c6, c7, c8 = st.columns(4)
    c5.selectbox("Inspector", inspectors, key="inspector")
    c6.selectbox("Approver", approvers, key="approver")
    c7.selectbox("Dispenser", dispensers, key="dispenser")
    c8.text_input("Work / Location", key="work_location")
    st.text_input("Note", key="issue_note")
    add_line_form("issue_lines", "จำนวนเบิก", allow_cable_length=request_type == "CABLE")
    lines_editor("issue_lines")
    if st.button("Save Request", type="primary"):
        doc_date = normalize_date_input(st.session_state["request_date"])
        if not trim(st.session_state["request_no"]) or not doc_date or not st.session_state["issue_lines"]:
            st.error("กรุณากรอกเลขที่ วันที่ และเพิ่มรายการเบิก")
            return
        try:
            conn = get_conn()
            cur = conn.execute(
                """
                INSERT INTO requests(request_no, request_date, company, requestor, inspector, approver, dispenser, work_location, request_type, note)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    st.session_state["request_no"],
                    doc_date,
                    st.session_state.get("request_company", ""),
                    st.session_state.get("requestor", ""),
                    st.session_state.get("inspector", ""),
                    st.session_state.get("approver", ""),
                    st.session_state.get("dispenser", ""),
                    st.session_state.get("work_location", ""),
                    st.session_state["request_type"],
                    st.session_state.get("issue_note", ""),
                ),
            )
            req_id = cur.lastrowid
            for idx, line in enumerate(st.session_state["issue_lines"], start=1):
                conn.execute(
                    "INSERT INTO request_items(request_id, line_no, item_id, qty, cable_length) VALUES(?,?,?,?,?)",
                    (req_id, idx, line["item_id"], safe_float(line["qty"]), trim(line.get("cable_length", ""))),
                )
            conn.commit()
            advance_config_doc_no("request", st.session_state["request_no"])
            st.session_state["issue_lines"] = []
            st.session_state["request_reset_after_save"] = True
            st.success("บันทึกใบเบิกเรียบร้อย")
            st.rerun()
        except sqlite3.IntegrityError as exc:
            get_conn().rollback()
            st.error(f"บันทึกไม่ได้: {exc}")


def history_tab() -> None:
    hist = st.tabs(["BOQ History", "Receiving History", "Issue History"])
    with hist[0]:
        rows = query(
            """
            SELECT br.id, br.boq_no, br.boq_date, br.ref_no, br.note,
                   COUNT(bi.id) AS lines, COALESCE(SUM(bi.qty),0) AS total_qty
            FROM boq_receipts br
            LEFT JOIN boq_receipt_items bi ON bi.boq_receipt_id=br.id
            GROUP BY br.id
            ORDER BY br.boq_date DESC, br.id DESC
            """
        )
        show_table(
            [
                {
                    "ID": r["id"],
                    "BOQ No.": r["boq_no"],
                    "Date": display_date(r["boq_date"]),
                    "Ref No.": r["ref_no"],
                    "Note": r["note"],
                    "Lines": r["lines"],
                    "Total Qty": format_qty(r["total_qty"]),
                }
                for r in rows
            ]
        )
    with hist[1]:
        rows = query(
            """
            SELECT r.id, r.receipt_no, r.receipt_date, r.receipt_to, r.vendor, r.do_no, r.pr_no, r.receipt_type,
                   COUNT(ri.id) AS lines, COALESCE(SUM(ri.qty),0) AS total_qty
            FROM receipts r
            LEFT JOIN receipt_items ri ON ri.receipt_id=r.id
            GROUP BY r.id
            ORDER BY r.receipt_date DESC, r.id DESC
            """
        )
        show_table(
            [
                {
                    "ID": r["id"],
                    "Receipt No.": r["receipt_no"],
                    "Date": display_date(r["receipt_date"]),
                    "Type": r["receipt_type"],
                    "To": r["receipt_to"],
                    "From": r["vendor"],
                    "DO/Invoice": r["do_no"],
                    "PR/Ref": r["pr_no"],
                    "Lines": r["lines"],
                    "Total Qty": format_qty(r["total_qty"]),
                }
                for r in rows
            ]
        )
    with hist[2]:
        rows = query(
            """
            SELECT r.id, r.request_no, r.request_date, r.company, r.requestor, r.work_location, r.request_type,
                   COUNT(ri.id) AS lines, COALESCE(SUM(ri.qty),0) AS total_qty
            FROM requests r
            LEFT JOIN request_items ri ON ri.request_id=r.id
            GROUP BY r.id
            ORDER BY r.request_date DESC, r.id DESC
            """
        )
        show_table(
            [
                {
                    "ID": r["id"],
                    "Req No.": r["request_no"],
                    "Date": display_date(r["request_date"]),
                    "Type": r["request_type"],
                    "Company": r["company"],
                    "Requestor": r["requestor"],
                    "Work/Location": r["work_location"],
                    "Lines": r["lines"],
                    "Total Qty": format_qty(r["total_qty"]),
                }
                for r in rows
            ]
        )


def stockcard_tab() -> None:
    row = item_select("เลือกรายการสำหรับ Stock Card", "stockcard_item")
    if not row:
        return
    rows: list[dict[str, Any]] = []
    for r in query(
        """
        SELECT br.boq_date AS doc_date, br.boq_no AS doc_no, 'BOQ' AS doc_type, bi.qty AS in_qty, 0 AS out_qty, '' AS ref
        FROM boq_receipt_items bi JOIN boq_receipts br ON br.id=bi.boq_receipt_id
        WHERE bi.item_id=?
        UNION ALL
        SELECT rc.receipt_date, rc.receipt_no, 'Receiving', ri.qty, 0, rc.vendor
        FROM receipt_items ri JOIN receipts rc ON rc.id=ri.receipt_id
        WHERE ri.item_id=?
        UNION ALL
        SELECT rq.request_date, rq.request_no, 'Issue', 0, qi.qty, rq.requestor
        FROM request_items qi JOIN requests rq ON rq.id=qi.request_id
        WHERE qi.item_id=?
        ORDER BY doc_date, doc_no
        """,
        (row["id"], row["id"], row["id"]),
    ):
        rows.append(row_dict(r))
    balance = 0.0
    view = []
    for r in rows:
        if r["doc_type"] != "BOQ":
            balance += safe_float(r["in_qty"]) - safe_float(r["out_qty"])
        view.append(
            {
                "Date": display_date(r["doc_date"]),
                "Doc Type": r["doc_type"],
                "Doc No.": r["doc_no"],
                "Ref": r["ref"],
                "In": format_qty(r["in_qty"]),
                "Out": format_qty(r["out_qty"]),
                "Balance": format_qty(balance),
            }
        )
    st.write(f"{row['code']} | {row['name']} | {row['spec']} | {row['unit']}")
    show_table(view)


def setup_table(table: str, title: str, extra: str | None = None) -> None:
    st.subheader(title)
    cols = f"id, name{', ' + extra if extra else ''}"
    show_table([row_dict(r) for r in query(f"SELECT {cols} FROM {table} ORDER BY name COLLATE NOCASE")], height=180)
    with st.form(f"{table}_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", key=f"{table}_name")
        extra_value = c2.text_input(extra or "-", key=f"{table}_extra", disabled=not extra)
        submitted = st.form_submit_button("Add / Update")
    if submitted and trim(name):
        if extra:
            execute(
                f"INSERT INTO {table}(name, {extra}) VALUES(?, ?) ON CONFLICT(name) DO UPDATE SET {extra}=excluded.{extra}",
                (name, extra_value),
            )
        else:
            execute(f"INSERT OR IGNORE INTO {table}(name) VALUES(?)", (name,))
        st.success("บันทึก Setup เรียบร้อย")
        st.rerun()


def setup_tab() -> None:
    c1, c2, c3 = st.columns(3)
    with c1:
        setup_table("categories", "Categories", "abbr")
        setup_table("units", "Units")
    with c2:
        setup_table("brands", "Brands")
        setup_table("receipt_tos", "Receiving To")
    with c3:
        setup_table("receipt_froms", "Receiving From")
        setup_table("companies", "Companies")
    st.divider()
    st.subheader("Document No.")
    with st.form("doc_no_form"):
        c4, c5, c6 = st.columns(3)
        request_prefix = c4.text_input("Request Prefix", value=setting("request_prefix", "REQ-"))
        request_next = c5.number_input("Request Next Run", min_value=1, value=int(safe_float(setting("request_next_run", "1"), 1)))
        request_pad = c6.number_input("Request Pad Width", min_value=0, value=int(safe_float(setting("request_pad_width", "4"), 4)))
        c7, c8, c9 = st.columns(3)
        receipt_prefix = c7.text_input("Receipt Prefix", value=setting("receipt_prefix", "REC-"))
        receipt_next = c8.number_input("Receipt Next Run", min_value=1, value=int(safe_float(setting("receipt_next_run", "1"), 1)))
        receipt_pad = c9.number_input("Receipt Pad Width", min_value=0, value=int(safe_float(setting("receipt_pad_width", "4"), 4)))
        submitted = st.form_submit_button("Save Config")
    if submitted:
        for key, value in {
            "request_prefix": request_prefix,
            "request_next_run": request_next,
            "request_pad_width": request_pad,
            "receipt_prefix": receipt_prefix,
            "receipt_next_run": receipt_next,
            "receipt_pad_width": receipt_pad,
        }.items():
            set_setting(key, value)
        st.success("บันทึกเลขเอกสารเรียบร้อย")
        st.rerun()


def main() -> None:
    header()
    get_conn()
    tabs = st.tabs(
        [
            "Dashboard",
            "Master Data",
            "BOQ Receipt",
            "Receiving",
            "Request / Issue",
            "History",
            "Stock Card",
            "Setup",
        ]
    )
    with tabs[0]:
        dashboard_tab()
    with tabs[1]:
        master_tab()
    with tabs[2]:
        boq_tab()
    with tabs[3]:
        receiving_tab()
    with tabs[4]:
        issue_tab()
    with tabs[5]:
        history_tab()
    with tabs[6]:
        stockcard_tab()
    with tabs[7]:
        setup_tab()


if __name__ == "__main__":
    main()
