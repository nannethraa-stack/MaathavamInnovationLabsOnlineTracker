# One-time Artifact Migration

The dashboard can import the existing artifact repository:

`C:\Users\Yoga\Desktop\Sundar\Meetings\Artifacts folders`

Every immediate child folder is treated as a **concept name**. All files below it are discovered recursively.

## Safe two-step process

From the project directory:

```powershell
.venv\Scripts\Activate.ps1
python import_artifacts.py
```

The first command is a **dry run**. It does not copy anything.

If the counts and concept names look correct:

```powershell
python import_artifacts.py --execute
```

The source folder is never modified or deleted.

## What is preserved

For every imported artifact:

- Concept
- Original relative folder path
- File name
- File size
- SHA-256 checksum
- Imported timestamp
- Stored dashboard file

The concept page can then view/delete artifacts using the normal dashboard functionality.

## Re-running safely

The importer is designed to be idempotent. If you run it again, files with the same concept + relative path + SHA-256 are skipped.

## Important

Back up `project_dashboard.db` before the first production migration.

For local testing, SQLite + local `uploads/imported` storage is fine. For production, use PostgreSQL and controlled object storage such as S3/Azure Blob, with authentication, CSRF protection, upload limits and malware scanning.
