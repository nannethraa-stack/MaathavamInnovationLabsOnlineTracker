# Data Integration — Supplied 21 Concepts / 51 Artifacts

The dashboard has now been populated from the uploaded `Artifacts folders.zip`. The importer treats each immediate child folder under `Artifacts folders/` as one concept and recursively imports its files.

## Validation

- **21 concept folders** detected.
- **51 usable artifact files** detected.
- `desktop.ini` and Office temporary `~$...` files were excluded as non-artifact system/temp files.
- **21 project rows** and **51 artifact rows** are present in `project_dashboard.db`.
- Each artifact has `project_id`, `original_path`, `file_size`, and SHA-256 metadata.
- Artifact files are physically present under `uploads/imported/<project_id>/...`.
- Unicode names are retained using NFC normalization.

## Important mapping note

Project names were taken **exactly from the supplied folder names** (including existing spelling/capitalisation such as `Behvioral Assesment`, `Craddle AI`, `MargRaksh`, and `RainWaterHarvesting`). No business names were inferred or renamed.

The `RainWaterHarvesting/MargRaksh/` nested folder was preserved as part of the `RainWaterHarvesting` concept because it is physically located inside that supplied concept folder. The separate top-level `MargRaksh` concept is therefore also retained exactly as supplied.

## Re-importing later

Run `python import_artifacts.py` for a dry run, or `python import_artifacts.py --execute --source "<source-folder>"` to import. The importer is idempotent for an identical file within the same concept and preserves relative paths.
