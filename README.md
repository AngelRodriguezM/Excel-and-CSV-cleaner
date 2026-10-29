# SQL cleaner to BI

A small Python tool that takes messy CSV / Excel exports from a folder, cleans and renames their columns according to a YAML mapping, and produces tidy, correctly typed tables ready to load into SQL or a BI tool.

It can be run from the command line (`app.py`) or through a Tkinter desktop UI (`ui.py`).

## How it works

```
folder of .csv / .xlsx files
        │
        ▼
Input/readFolderFiles.py   find every csv/xls/xlsx/xlsm in the folder
Input/readFiles.py         read each file, detect the header row (skips title rows)
        │   {filename: DataFrame}
        ▼
Config/columnMapping.py    match each file to a mapping in Config/mapping.yaml,
Config/normalize.py        normalise values, rename columns, cast to target types
        │   {filename: mapped DataFrame}
        ▼
preview in the UI / export to <name>_clean.csv
```

### Pipeline stages

1. **Read** – `readFolderFiles()` scans a folder (or opens a folder dialog if no path is given) and reads every `.csv`, `.xlsx`, `.xls` and `.xlsm` file. CSVs are read as strings; `findHeaderRow` picks the first fully filled, all-text row within the first 10 rows as the header, so title rows above the real header are skipped.
2. **Match** – each file name is matched (case-insensitive glob, first match wins) against the `source_file` patterns in `Config/mapping.yaml`. Files that failed to read or have no mapping are skipped with a message.
3. **Normalise** – values are cleaned *before* casting (`Config/normalize.py`):
   - text: trims spaces, replaces non-breaking spaces, collapses inner whitespace, optional `case` (`lower` / `upper` / `title`)
   - numbers: extracts the leading number and strips units (`"12 pcs"` → `12`), handles Danish (`1.234,56`) or English decimal formats via the `decimal` option
   - dates: parses ISO (`yyyy-mm-dd`) and day-first formats, and converts Excel serial numbers
4. **Map & cast** – only the columns listed in the mapping are kept; they are renamed to `target` and cast to `type` (`int`, `float`, `str`, `bool`, `date`, `datetime`). Bad values raise an error instead of silently becoming NaN.
5. **Output** – the UI shows a preview (first 200 rows per file, one tab each) and exports each file to `<name>_clean.csv`.

## Project structure

| Path | Purpose |
| --- | --- |
| `app.py` | CLI entry point: pick a folder, read, map, print the result |
| `ui.py` | Tkinter UI: browse folder, run (in a background thread), preview tabs, log pane, export to CSV |
| `Input/readFolderFiles.py` | Finds and reads all supported files in a folder |
| `Input/readFiles.py` | `readCsv` / `readExcel` and header-row detection |
| `Config/columnMapping.py` | Loads the YAML mapping, matches files, applies renames and type casts |
| `Config/normalize.py` | Text, number and date normalisation |
| `Config/mapping.yaml` | Per-file column mapping configuration |
| `TestFolder/` | Sample data (`MOCK_DATA.csv`, `MOCK_DATA.xlsx`) for trying the tool out |

## Configuration

Mappings live in `Config/mapping.yaml`:

```yaml
mappings:
  - source_file: MOCK_DATA.*          # filename or glob, e.g. "sales_*.xlsx"
    columns:
      - {source: id,         target: customer_id, type: int}
      - {source: first_name, target: first_name,  type: str}
      - {source: email,      target: email,       type: str, case: lower}
```

Per column:

| Key | Description |
| --- | --- |
| `source` | Column name in the input file (required) |
| `target` | Output column name (defaults to `source`) |
| `type` | `int`, `float`, `str`, `bool`, `date`, `datetime` (defaults to `str`) |
| `case` | `lower`, `upper` or `title` (for `str` columns) |
| `decimal` | `","` (default, Danish) or `"."` (for `int` / `float` columns) |

Unknown types are rejected when the mapping is loaded, so typos fail early.

## Usage

Requirements: Python 3.13 (what the project is developed on), `pandas`, `pyyaml`, and `openpyxl` for Excel files. Tkinter ships with the standard Python installer.

```bash
pip install pandas pyyaml openpyxl
```

**Desktop UI**

```bash
python ui.py
```

Browse to a folder, click **Run**, inspect the preview tabs, then **Export to csv…** to write the cleaned files.

**Command line**

```bash
python app.py
```

Opens a folder dialog, then prints the files found and the mapped results.

## Status / known gaps

- Work in progress: only the sample `MOCK_DATA.*` mapping is configured so far.
- Skipping blank and total rows is not implemented yet (see the TODOs in `Input/readFolderFiles.py`).
- Output is CSV only; loading directly into SQL is not implemented yet.
