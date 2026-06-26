from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "New project 3" / "outputs" / "db_split" / "materials_hierarchy.sqlite3"


@st.cache_data(show_spinner=False)
def load_filter_options() -> tuple[list[str], pd.DataFrame]:
    with sqlite3.connect(DB_PATH) as conn:
        types = [
            row[0]
            for row in conn.execute(
                "SELECT type_name FROM material_types ORDER BY type_name"
            ).fetchall()
        ]
        hierarchy = pd.read_sql_query(
            """
            SELECT
                g.type_name,
                g.group_name,
                s.category_code,
                s.sub_group_name,
                s.item_count
            FROM material_sub_groups s
            JOIN material_groups g ON g.group_id = s.group_id
            ORDER BY g.type_name, g.group_name, s.sub_group_name
            """,
            conn,
        )
    return types, hierarchy


@st.cache_data(show_spinner=False)
def load_materials(
    type_name: str | None,
    group_name: str | None,
    sub_group_name: str | None,
    search_text: str,
) -> pd.DataFrame:
    where = []
    params: list[str] = []

    if type_name:
        where.append("g.type_name = ?")
        params.append(type_name)
    if group_name:
        where.append("g.group_name = ?")
        params.append(group_name)
    if sub_group_name:
        where.append("s.sub_group_name = ?")
        params.append(sub_group_name)
    if search_text:
        like = f"%{search_text.strip()}%"
        where.append(
            """
            (
                m.material_code LIKE ?
                OR m.material_name LIKE ?
                OR m.spec_size LIKE ?
                OR m.brand LIKE ?
                OR m.unit LIKE ?
                OR m.category_code LIKE ?
            )
            """
        )
        params.extend([like] * 6)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    query = f"""
        SELECT
            g.type_name AS Type,
            g.group_name AS "Group",
            s.sub_group_name AS "Sub-Group",
            m.category_code AS Code,
            m.source_no AS No,
            m.material_code AS "Material Code",
            m.material_name AS "Material Name",
            m.spec_size AS "Spec / Size",
            m.brand AS Brand,
            m.unit AS Unit
        FROM materials m
        LEFT JOIN material_sub_groups s ON s.category_code = m.category_code
        LEFT JOIN material_groups g ON g.group_id = s.group_id
        {where_sql}
        ORDER BY g.type_name, g.group_name, s.sub_group_name, m.material_code
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


def choose(label: str, options: list[str], key: str) -> str | None:
    value = st.selectbox(label, ["ทั้งหมด", *options], key=key)
    return None if value == "ทั้งหมด" else value


st.set_page_config(
    page_title="Material Catalog SDE",
    page_icon="📦",
    layout="wide",
)

st.title("Material Catalog SDE")
st.caption("ค้นหาและกรองฐานข้อมูลวัสดุจาก SQLite")

if not DB_PATH.exists():
    st.error(f"ไม่พบฐานข้อมูล: {DB_PATH}")
    st.stop()

types, hierarchy = load_filter_options()

with st.sidebar:
    st.header("ตัวกรอง")
    selected_type = choose("Type", types, "type")

    group_df = hierarchy
    if selected_type:
        group_df = group_df[group_df["type_name"] == selected_type]
    selected_group = choose(
        "Group",
        sorted(group_df["group_name"].dropna().unique().tolist()),
        "group",
    )

    sub_group_df = group_df
    if selected_group:
        sub_group_df = sub_group_df[sub_group_df["group_name"] == selected_group]
    selected_sub_group = choose(
        "Sub-Group",
        sorted(sub_group_df["sub_group_name"].dropna().unique().tolist()),
        "sub_group",
    )

    search_text = st.text_input("ค้นหา", placeholder="รหัส, ชื่อวัสดุ, spec, brand")

materials = load_materials(
    selected_type,
    selected_group,
    selected_sub_group,
    search_text,
)

total_items = len(materials)
total_groups = materials["Group"].nunique() if not materials.empty else 0
total_sub_groups = materials["Sub-Group"].nunique() if not materials.empty else 0

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("รายการวัสดุ", f"{total_items:,}")
metric_2.metric("Groups", f"{total_groups:,}")
metric_3.metric("Sub-Groups", f"{total_sub_groups:,}")

st.dataframe(
    materials,
    use_container_width=True,
    hide_index=True,
    height=620,
)

csv_data = materials.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Download CSV",
    data=csv_data,
    file_name="material_catalog.csv",
    mime="text/csv",
)
