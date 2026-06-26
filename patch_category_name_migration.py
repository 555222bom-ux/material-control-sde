import json
import pathlib
import re
import sqlite3


BASE_DIR = pathlib.Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "New project 3" / "outputs" / "db_split" / "materials_hierarchy.sqlite3"
APP_FILES = [
    BASE_DIR / "MaterialControlApp.html",
    BASE_DIR / "MaterialControlApp_stable_allow_negative_issue_from_master.html",
    BASE_DIR / "index.html",
]


def build_mapping():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "select category_code, coalesce(sub_group_name, category_code) from material_sub_groups order by category_code"
    ).fetchall()
    con.close()
    return {code: name for code, name in rows}


def patch_file(path, mapping):
    text = path.read_text(encoding="utf-8")
    helper = (
        "const CATEGORY_CODE_NAME_MAP = "
        + json.dumps(mapping, ensure_ascii=False, indent=12)
        + """;
        const normalizeCategoryName = (value) => {
            const raw = trimOrEmpty(value);
            return CATEGORY_CODE_NAME_MAP[raw] || raw;
        };
        const normalizeCategoryAbbr = (name, abbr) => {
            const rawName = trimOrEmpty(name);
            const rawAbbr = trimOrEmpty(abbr);
            if (CATEGORY_CODE_NAME_MAP[rawName]) return rawName;
            return rawAbbr || rawName.substring(0, 2).toUpperCase() || 'GN';
        };"""
    )

    anchor_start = "const cleanString = (str) => str ? str.toString().trim().replace(/\\s+/g, '').toLowerCase() : '';"
    anchor_end = "const safeLower = (str) => str ? String(str).toLowerCase() : '';"

    idx_start = text.find(anchor_start)
    idx_end = text.find(anchor_end)
    if idx_start != -1 and idx_end != -1:
        text = text[:idx_start + len(anchor_start)] + "\n        " + helper + "\n        " + text[idx_end:]

    text = text.replace(
        "category: trimOrEmpty(m.category) || 'General',",
        "category: normalizeCategoryName(m.category) || 'General',",
    )
    text = text.replace(
        "const name = trimOrEmpty(c?.name) || (idx === 0 ? 'General' : '');",
        "const rawName = trimOrEmpty(c?.name) || (idx === 0 ? 'General' : '');\n                const name = normalizeCategoryName(rawName);",
    )
    text = text.replace(
        "const abbrRaw = trimOrEmpty(c?.abbr) || name.substring(0, 2).toUpperCase() || 'GN';",
        "const abbrRaw = normalizeCategoryAbbr(rawName, c?.abbr);",
    )

    path.write_text(text, encoding="utf-8")


def main():
    mapping = build_mapping()
    for path in APP_FILES:
        patch_file(path, mapping)
        print(f"patched {path}")


if __name__ == "__main__":
    main()
