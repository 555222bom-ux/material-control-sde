"""Compatibility entry point for the retired flat materials database.

The application now uses outputs/db_split/materials_hierarchy.sqlite3 only.
Running this file intentionally rebuilds that current database instead of the
old outputs/db_split/materials.sqlite3 file.
"""

from build_materials_hierarchy_sqlite import main


if __name__ == "__main__":
    print("materials.sqlite3 is retired; rebuilding materials_hierarchy.sqlite3 instead.")
    main()
