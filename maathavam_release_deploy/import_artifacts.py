"""
One-time recursive artifact importer for Maathavam Project Dashboard.

Source structure:
    Artifacts folders/
        <Concept Name>/
            <any number of nested folders>/
                <artifact files>

Usage:
    python import_artifacts.py                 # DRY RUN (no files copied)
    python import_artifacts.py --execute      # perform import
    python import_artifacts.py --execute --source "C:\\path\\Artifacts folders"

The importer:
- Treats every immediate child folder as a concept name.
- Recursively discovers files beneath each concept.
- Creates missing concepts.
- Copies files into the dashboard's uploads/imported/<project_id>/...
- Preserves relative folder structure.
- Records original relative path, file size and SHA-256.
- Is idempotent: an identical file for the same concept is skipped.
- Never modifies or deletes the source folder.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
import unicodedata

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = Path(r"C:\Users\Yoga\Desktop\Sundar\Meetings\Artifacts folders")
DB_PATH = BASE_DIR / "project_dashboard.db"
UPLOAD_ROOT = BASE_DIR / "uploads" / "imported"


def now():
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def safe_component(part: str) -> str:
    """Preserve Unicode while removing path traversal/control characters."""
    part = unicodedata.normalize("NFC", part).strip()
    if not part or part in {".", ".."}:
        return "unnamed"
    forbidden = '<>:"/\\|?*'
    cleaned = "".join("_" if ch in forbidden or ord(ch) < 32 else ch for ch in part)
    return cleaned or "unnamed"

def safe_relative_path(rel: Path) -> Path:
    return Path(*[safe_component(part) for part in rel.parts]) if rel.parts else Path("unnamed")


def ensure_schema(conn):
    # Importer can be run against a v2 DB; make artifact metadata migration safe.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()}
    for column, definition in [
        ("original_path", "TEXT"),
        ("file_size", "INTEGER DEFAULT 0"),
        ("sha256", "TEXT"),
    ]:
        if column not in columns:
            conn.execute(f"ALTER TABLE artifacts ADD COLUMN {column} {definition}")
    conn.commit()


def get_project(conn, concept_name):
    return conn.execute(
        "SELECT id FROM projects WHERE lower(project_name)=lower(?) LIMIT 1",
        (concept_name,),
    ).fetchone()


def create_project(conn, concept_name):
    cur = conn.execute(
        """INSERT INTO projects
        (project_name, domain, provisional_patent_status, sensor,
         planned_organisation, status, eta, comments, total_spend,
         created_at, updated_at)
        VALUES (?, '', '', 'N', '', 'Planned', '', '', 0, ?, ?)""",
        (concept_name, now(), now()),
    )
    return cur.lastrowid


def find_existing(conn, project_id, rel_path, digest):
    return conn.execute(
        """SELECT id, file_path FROM artifacts
           WHERE project_id=? AND original_path=? AND sha256=? LIMIT 1""",
        (project_id, str(rel_path), digest),
    ).fetchone()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()

    print("=" * 72)
    print("MAATHAVAM PROJECT DASHBOARD - ARTIFACT IMPORT")
    print("=" * 72)
    print(f"Source : {source}")
    print(f"Mode   : {'EXECUTE' if args.execute else 'DRY RUN'}")
    print()

    if not source.exists() or not source.is_dir():
        print("ERROR: Source folder does not exist:")
        print(source)
        return 2

    concepts = sorted([p for p in source.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
    print(f"Concept folders found: {len(concepts)}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    ensure_schema(conn)

    stats = {
        "concepts_found": len(concepts),
        "concepts_created": 0,
        "files_found": 0,
        "files_imported": 0,
        "files_skipped": 0,
        "errors": 0,
    }
    errors = []

    for concept_dir in concepts:
        concept_name = concept_dir.name.strip()
        if not concept_name:
            continue

        row = get_project(conn, concept_name)
        if row:
            project_id = row[0]
            concept_created = False
        else:
            project_id = None
            concept_created = True
            if args.execute:
                project_id = create_project(conn, concept_name)
                stats["concepts_created"] += 1
                conn.commit()

        files = sorted([p for p in concept_dir.rglob("*")
                        if p.is_file()
                        and p.name.lower() != "desktop.ini"
                        and not p.name.startswith("~$")],
                       key=lambda p: str(p).lower())

        print(f"\n[{concept_name}]")
        print(f"  Files: {len(files)}" + ("  (new concept)" if concept_created else ""))

        for file_path in files:
            stats["files_found"] += 1
            try:
                rel = file_path.relative_to(concept_dir)
                rel_safe = safe_relative_path(rel)
                digest = sha256_file(file_path)
                size = file_path.stat().st_size

                if not args.execute:
                    print(f"  [WOULD IMPORT] {rel}")
                    continue

                existing = find_existing(conn, project_id, rel, digest)
                if existing:
                    stats["files_skipped"] += 1
                    print(f"  [SKIP] {rel} (already imported)")
                    continue

                destination = UPLOAD_ROOT / str(project_id) / rel_safe
                destination.parent.mkdir(parents=True, exist_ok=True)

                # Avoid overwriting an unrelated file with the same sanitized name.
                if destination.exists():
                    stem, suffix = destination.stem, destination.suffix
                    destination = destination.with_name(f"{stem}_{digest[:10]}{suffix}")

                shutil.copy2(file_path, destination)

                conn.execute(
                    """INSERT INTO artifacts
                       (project_id, name, description, file_path,
                        original_path, file_size, sha256, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        project_id,
                        str(rel),
                        f"Imported from artifact repository: {rel.parent}" if str(rel.parent) != "." else "Imported from artifact repository",
                        str(destination.relative_to(BASE_DIR)),
                        str(rel),
                        size,
                        digest,
                        now(),
                    ),
                )
                conn.commit()
                stats["files_imported"] += 1
                print(f"  [IMPORTED] {rel}")

            except Exception as exc:
                stats["errors"] += 1
                errors.append((concept_name, str(file_path), str(exc)))
                print(f"  [ERROR] {file_path}: {exc}")

    conn.close()

    print("\n" + "=" * 72)
    print("IMPORT SUMMARY")
    print("=" * 72)
    for k, v in stats.items():
        print(f"{k.replace('_', ' ').title():22}: {v}")

    if errors:
        print("\nERROR DETAILS:")
        for concept, path, error in errors:
            print(f"- [{concept}] {path}: {error}")

    if not args.execute:
        print("\nDRY RUN ONLY - no files or database records were changed.")
        print("Run with --execute to perform the import.")
    else:
        print("\nImport completed. Original source files were not modified.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
