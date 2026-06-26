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

    text = re.sub(
        r"\n\s*const CATEGORY_CODE_NAME_MAP = \{.*?\};\n\s*const normalizeCategoryName = .*?\n\s*\};",
        "",
        text,
        flags=re.S,
    )

    anchor = "const cleanString = (str) => str ? str.toString().trim().replace(/\\s+/g, '').toLowerCase() : '';"
    if helper not in text:
        text = text.replace(anchor, anchor + "\n        " + helper, 1)

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
