# Maathavam Innovation Labs — Enterprise Project Dashboard v3

Flask + SQLite executive portfolio dashboard for deep-tech concepts and their artifacts.

## Release status

This package is populated with the supplied **21 real concept folders and 51 artifact files**. The demo concept records have been removed. Artifact files are stored under `uploads/imported/<project_id>/...` and linked to their concept through the SQLite foreign key.

## Release changes

- Maathavam Innovation Labs SVG wordmark and favicon
- Executive **Project** field with A→Z / Z→A sorting
- Live artifact counts per concept and total artifact metric
- Concept ↔ artifact foreign-key relationship
- Unicode-preserving artifact paths (NFC normalization; no ASCII transliteration)
- Canonical SQLite schema + safe migration
- Database-level duplicate protection
- Idempotent recursive artifact importer
- Ignores Windows `desktop.ini` and Office temporary `~$...` files
- Role-protected write operations
- Physical artifact file cleanup on deletion
- Canonical project status values
- Environment-based Flask secret key and bootstrap password
- Search/filter and live executive metrics

## Supplied data validation

- Concept folders imported: **21**
- Artifact files imported: **51**
- Placeholder/demo concept records: **0**
- Placeholder/demo artifact records: **0**
- Artifact files are SHA-256 indexed and linked to their project

See `DATA_INTEGRATION.md` for the imported concept/artifact manifest and notes on source-folder naming.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

For deployment, set `MAATHAVAM_SECRET_KEY` and change `MAATHAVAM_BOOTSTRAP_PASSWORD` before first startup.
