"""
data_janitor.py — NEO CSV/XLSX Cleaning Engine
Profile, auto-clean, NL commands (Groq->safe JSON op), undo, export.

Powers the Fiverr gig: client sends messy CSV -> clean + deliver fast.
Also importable as a NEO tool (DataJanitor class).

Dependencies: pandas, openpyxl (xlsx), python-dotenv; groq (optional, for NL)
Install: pip install pandas openpyxl python-dotenv groq
Run (interactive): python data_janitor.py path/to/file.csv
Run (batch):       python data_janitor.py --batch folder/ [--out output_folder/]

RAM: pandas loads the whole file into memory. Fine for typical freelance CSVs
(<100k rows / a few MB). Large files (>200k rows) on 8GB risk swap — see guard.
Undo keeps up to MAX_UNDO full copies; bounded to protect RAM.

SECURITY: NL commands are compiled by Groq into a whitelisted JSON operation
and dispatched to fixed handlers. No model-generated code is ever executed.
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Optional Groq for natural-language commands
try:
    from groq import Groq
    _GROQ = Groq(api_key=os.getenv("GROQ_API_KEY")) if os.getenv("GROQ_API_KEY") else None
except Exception:
    _GROQ = None

GROQ_MODEL   = "openai/gpt-oss-120b"
MAX_UNDO     = 5
LARGE_ROWS   = 200_000   # warn above this
SNAPSHOT_CAP = 100_000   # skip undo snapshots above this row count (RAM guard)

# ── Whitelisted operation schema (the ONLY ops Groq may emit) ───────────────

OP_SCHEMA = """
Return exactly ONE JSON object, no markdown, no prose. Choose one op:
{"op":"drop_columns","columns":["name",...]}
{"op":"keep_columns","columns":["name",...]}
{"op":"filter_rows","column":"col","comparator":">|<|>=|<=|==|!=|contains","value":<num or str>}
{"op":"to_datetime","column":"col"}
{"op":"rename_column","old":"a","new":"b"}
{"op":"drop_duplicates"}
{"op":"drop_na","subset":["col",...] or null}
{"op":"fill_na","column":"col","value":<num or str>}
{"op":"lowercase_values","column":"col"}
{"op":"title_case","column":"col"}
{"op":"standardize_phone","column":"col"}
{"op":"sort","column":"col","ascending":true|false}
"""


class DataJanitor:
    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.path: Path | None = None
        self._undo: list[pd.DataFrame] = []
        self._last_clean: dict | None = None
        self._batch_results: list | None = None

    # ── Load ────────────────────────────────────────────────────────────────
    def load(self, path: str) -> str:
        p = Path(path)
        if not p.exists():
            return f"File not found: {path}"
        ext = p.suffix.lower()
        try:
            if ext in (".xlsx", ".xls"):
                self.df = pd.read_excel(p)
            elif ext in (".csv", ".tsv"):
                sep = "\t" if ext == ".tsv" else ","
                self.df = pd.read_csv(p, sep=sep, dtype=str, keep_default_na=True,
                                      skip_blank_lines=True, on_bad_lines="warn")
            else:
                return f"Unsupported type: {ext} (use csv/tsv/xlsx)"
        except Exception as e:
            return f"Load failed: {e}"
        self.path = p
        rows = len(self.df)
        warn = f"  ⚠️  {rows:,} rows — large; ops may be slow on 8GB." if rows > LARGE_ROWS else ""
        return f"Loaded {p.name}: {rows:,} rows × {len(self.df.columns)} cols.{warn}"

    # ── Profile ───────────────────────────────────────────────────────────────
    def profile(self) -> str:
        if self.df is None:
            return "No data loaded."
        df = self.df
        lines = [f"Shape: {len(df):,} rows × {len(df.columns)} cols",
                 f"Duplicate rows: {df.duplicated().sum():,}", "", "Columns:"]
        for c in df.columns:
            miss = df[c].isna().sum()
            pct = (miss / len(df) * 100) if len(df) else 0
            uniq = df[c].nunique(dropna=True)
            lines.append(f"  {c:<28} miss={miss:>6,} ({pct:4.1f}%)  unique={uniq:,}")
        return "\n".join(lines)

    # ── Undo plumbing ─────────────────────────────────────────────────────────
    def _snapshot(self):
        if self.df is not None and len(self.df) <= SNAPSHOT_CAP:
            self._undo.append(self.df.copy())
            if len(self._undo) > MAX_UNDO:
                self._undo.pop(0)

    def undo(self) -> str:
        if not self._undo:
            return "Nothing to undo."
        self.df = self._undo.pop()
        return f"Reverted. Now {len(self.df):,} rows × {len(self.df.columns)} cols."

    # ── Auto-clean (deterministic, safe) ──────────────────────────────────────
    def auto_clean(self) -> str:
        if self.df is None:
            return "No data loaded."
        self._snapshot()
        df = self.df.copy()
        r0, c0 = df.shape
        col_names_before = list(df.columns)
        missing_before = int(df.isna().sum().sum())
        report = []

        # 1. snake_case headers
        df.columns = [re.sub(r"[^\w]+", "_", str(c).strip().lower()).strip("_") for c in df.columns]
        report.append("headers normalised to snake_case")

        # 2. strip whitespace — count affected cells
        ws_count = 0
        for c in [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]:
            stripped = df[c].str.strip()
            ws_count += int((df[c].fillna("") != stripped.fillna("")).sum())
            df[c] = stripped
        report.append(f"whitespace stripped ({ws_count:,} cells affected)")

        # 3. drop fully-empty cols and rows
        cols_before_drop = set(df.columns)
        shape_before_drop = df.shape
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
        empty_cols_dropped = shape_before_drop[1] - df.shape[1]
        empty_rows_dropped = shape_before_drop[0] - df.shape[0]
        dropped_empty_cols = sorted(cols_before_drop - set(df.columns))
        suffix = f": {', '.join(dropped_empty_cols)}" if dropped_empty_cols else ""
        report.append(
            f"dropped {empty_cols_dropped} empty col(s) and {empty_rows_dropped:,} empty row(s){suffix}"
        )

        # 4. drop exact duplicate rows
        dup = int(df.duplicated().sum())
        df = df.drop_duplicates()
        report.append(f"removed {dup:,} duplicate rows")

        # 5. coerce numeric-looking object cols — whole numbers -> nullable Int64
        numeric_coerced_names = []
        for c in [c for c in df.columns if pd.api.types.is_string_dtype(df[c])]:
            converted = pd.to_numeric(df[c], errors="coerce")
            if df[c].notna().sum() > 0 and converted.notna().sum() >= 0.9 * df[c].notna().sum():
                nonnull = converted.dropna()
                if len(nonnull) and (nonnull == nonnull.round()).all():
                    df[c] = converted.astype("Int64")
                else:
                    df[c] = converted
                numeric_coerced_names.append(c)
        if numeric_coerced_names:
            report.append(
                f"coerced {len(numeric_coerced_names)} col(s) to numeric: {', '.join(numeric_coerced_names)}"
            )
        else:
            report.append("no numeric coercion needed")

        self.df = df
        r1, c1 = df.shape
        missing_after = int(df.isna().sum().sum())
        rows_pct = f"{(r0 - r1) / r0 * 100:.1f}%" if r0 else "0.0%"

        self._last_clean = {
            "source_file": self.path.name if self.path else "N/A",
            "cleaned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rows_before": r0, "rows_after": r1,
            "cols_before": c0, "cols_after": c1,
            "rows_removed": r0 - r1, "rows_pct": rows_pct,
            "dupes_removed": dup,
            "empty_rows_dropped": empty_rows_dropped,
            "empty_cols_dropped": empty_cols_dropped,
            "dropped_empty_col_names": dropped_empty_cols,
            "ws_cells_trimmed": ws_count,
            "numeric_cols_coerced": numeric_coerced_names,
            "missing_before": missing_before,
            "missing_after": missing_after,
            "col_names_before": col_names_before,
            "col_names_after": list(self.df.columns),
            "actions": report,
        }
        return (
            f"Auto-cleaned: {r0:,}×{c0} -> {r1:,}×{c1} ({rows_pct} rows removed)\n  "
            + "\n  ".join(report)
        )

    # ── NL command -> safe JSON op ─────────────────────────────────────────────
    def run_command(self, nl: str) -> str:
        if self.df is None:
            return "No data loaded."
        if _GROQ is None:
            return "NL commands need GROQ_API_KEY + `pip install groq`. Use deterministic ops instead."
        cols = list(self.df.columns)
        prompt = (f"You translate a data-cleaning instruction into ONE JSON op.\n{OP_SCHEMA}\n"
                  f"Available columns: {cols}\nInstruction: \"{nl}\"\nJSON:")
        try:
            resp = _GROQ.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0, max_tokens=200,
                reasoning_effort="low",
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.I | re.M).strip()
            op = json.loads(raw)
        except Exception as e:
            return f"Could not parse command: {e}"
        return self._dispatch(op)

    def _dispatch(self, op: dict) -> str:
        name = op.get("op")
        handlers = {
            "drop_columns", "keep_columns", "filter_rows", "to_datetime",
            "rename_column", "drop_duplicates", "drop_na", "fill_na",
            "lowercase_values", "title_case", "standardize_phone", "sort",
        }
        if name not in handlers:
            return f"Rejected unknown op: {name!r}"
        self._snapshot()
        df = self.df.copy()
        try:
            if name == "drop_columns":
                df = df.drop(columns=[c for c in op["columns"] if c in df.columns])
            elif name == "keep_columns":
                df = df[[c for c in op["columns"] if c in df.columns]]
            elif name == "filter_rows":
                col, cmp, val = op["column"], op["comparator"], op["value"]
                if col not in df.columns:
                    return f"No such column: {col}"
                s = df[col]
                if cmp != "contains":
                    num = pd.to_numeric(s, errors="coerce")
                    if num.notna().any():
                        s, val = num, float(val)
                ops_map = {">": s > val, "<": s < val, ">=": s >= val, "<=": s <= val,
                           "==": s == val, "!=": s != val,
                           "contains": s.astype(str).str.contains(str(val), case=False, na=False)}
                df = df[ops_map[cmp]]
            elif name == "to_datetime":
                df[op["column"]] = pd.to_datetime(df[op["column"]], errors="coerce")
            elif name == "rename_column":
                df = df.rename(columns={op["old"]: op["new"]})
            elif name == "drop_duplicates":
                df = df.drop_duplicates()
            elif name == "drop_na":
                df = df.dropna(subset=op.get("subset"))
            elif name == "fill_na":
                df[op["column"]] = df[op["column"]].fillna(op["value"])
            elif name == "lowercase_values":
                df[op["column"]] = df[op["column"]].astype(str).str.lower()
            elif name == "title_case":
                df[op["column"]] = df[op["column"]].astype(str).str.title()
            elif name == "standardize_phone":
                df[op["column"]] = (df[op["column"]].astype(str)
                                    .str.replace(r"[^\d+]", "", regex=True))
            elif name == "sort":
                df = df.sort_values(op["column"], ascending=op.get("ascending", True))
        except Exception as e:
            self._undo.pop()  # roll back the snapshot we took
            return f"Op failed: {e}"
        self.df = df
        return f"OK [{name}] -> {len(df):,} rows × {len(df.columns)} cols."

    # ── Client-facing report ───────────────────────────────────────────────────
    def export_report(self, path: str = None) -> str:
        c = self._last_clean
        if not c:
            return "Run `clean` first."
        if path is None:
            stem = self.path.stem if self.path else "data"
            path = f"{stem}_cleaning_report.md"

        # Quality score: penalise remaining missing % and original dupe %
        total_cells = c["rows_after"] * c["cols_after"]
        miss_pct = (c["missing_after"] / total_cells * 100) if total_cells else 0
        dup_pct = (c["dupes_removed"] / c["rows_before"] * 100) if c["rows_before"] else 0
        quality = max(0, min(100, round(100 - miss_pct - dup_pct)))

        col_delta = c["cols_after"] - c["cols_before"]   # negative = removed
        col_change_str = f"{col_delta:+}" if col_delta else "0"

        miss_delta = c["missing_after"] - c["missing_before"]

        lines = [
            "# Data Cleaning Report",
            "",
            f"**File:** {c['source_file']}  ",
            f"**Cleaned:** {c['cleaned_at']}  ",
            f"**Quality Score:** {quality}/100",
            "",
            "## Before / After",
            "",
            "| Metric | Before | After | Change |",
            "|--------|--------|-------|--------|",
            f"| Rows | {c['rows_before']:,} | {c['rows_after']:,} | -{c['rows_removed']:,} ({c['rows_pct']} reduction) |",
            f"| Columns | {c['cols_before']} | {c['cols_after']} | {col_change_str} |",
            f"| Duplicate rows | {c['dupes_removed']:,} | 0 | -{c['dupes_removed']:,} |",
            f"| Missing cells | {c['missing_before']:,} | {c['missing_after']:,} | {miss_delta:+,} |",
            f"| Whitespace cells fixed | — | — | {c['ws_cells_trimmed']:,} |",
            "",
            "## Column Changes",
            "",
        ]
        if c["dropped_empty_col_names"]:
            quoted = ", ".join(f"`{n}`" for n in c["dropped_empty_col_names"])
            lines.append(f"**Removed (fully empty):** {quoted}  ")
        if c["numeric_cols_coerced"]:
            quoted = ", ".join(f"`{n}`" for n in c["numeric_cols_coerced"])
            lines.append(f"**Coerced to numeric:** {quoted}  ")
        lines += [
            f"**Headers normalised:** snake_case applied to all {c['cols_before']} columns  ",
            "",
            "## Operations Applied",
            "",
        ]
        for i, action in enumerate(c["actions"], 1):
            lines.append(f"{i}. {action}")
        lines += [
            "",
            "---",
            "*Generated by NEO Data Janitor*",
        ]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return f"Report saved -> {path}"

    # ── Batch processing ───────────────────────────────────────────────────────
    def batch_clean(self, folder: str, out_folder: str = None) -> str:
        folder_path = Path(folder)
        if not folder_path.is_dir():
            return f"Not a directory: {folder}"
        exts = {".csv", ".tsv", ".xlsx", ".xls"}
        files = sorted(f for f in folder_path.iterdir() if f.suffix.lower() in exts)
        if not files:
            return f"No CSV/XLSX/TSV files found in {folder}"
        out_path = Path(out_folder) if out_folder else folder_path / "cleaned"
        out_path.mkdir(parents=True, exist_ok=True)

        results = []
        for f in files:
            j = DataJanitor()
            load_msg = j.load(str(f))
            if "not found" in load_msg.lower() or "failed" in load_msg.lower():
                results.append({"file": f.name, "status": "FAIL", "error": load_msg})
                print(f"  FAIL  {f.name}: {load_msg}")
                continue
            j.auto_clean()
            out_file = out_path / (f.stem + "_cleaned" + f.suffix)
            j.export(str(out_file))
            c = j._last_clean
            results.append({
                "file": f.name,
                "status": "OK",
                "rows_before": c["rows_before"],
                "rows_after": c["rows_after"],
                "rows_removed": c["rows_removed"],
                "rows_pct": c["rows_pct"],
                "dupes": c["dupes_removed"],
                "cols_before": c["cols_before"],
                "cols_after": c["cols_after"],
                "out": out_file.name,
            })
            print(f"  OK    {f.name} -> {out_file.name}")

        self._batch_results = results
        return self._format_batch_summary(results, out_path)

    def _format_batch_summary(self, results: list, out_path: Path = None) -> str:
        ok = [r for r in results if r["status"] == "OK"]
        fail = [r for r in results if r["status"] != "OK"]
        header = (
            f"\nBatch complete — {len(results)} file(s) processed "
            f"({len(ok)} OK, {len(fail)} failed)"
        )
        loc = f"\nOutput folder: {out_path}" if out_path else ""
        col_w = 32
        lines = [
            header, loc, "",
            f"{'File':<{col_w}} {'Rows In':>9} {'Rows Out':>9} {'Removed':>8} {'Dupes':>6} {'Cols':>7}  Status",
            "-" * 82,
        ]
        for r in results:
            if r["status"] == "OK":
                cols = f"{r['cols_before']}->{r['cols_after']}"
                name = r["file"][:col_w]
                lines.append(
                    f"{name:<{col_w}} {r['rows_before']:>9,} {r['rows_after']:>9,} "
                    f"{r['rows_removed']:>8,} {r['dupes']:>6,} {cols:>7}  OK"
                )
            else:
                name = r["file"][:col_w]
                lines.append(f"{name:<{col_w}} {'':>9} {'':>9} {'':>8} {'':>6} {'':>7}  FAIL: {r.get('error','')}")

        if ok:
            total_in = sum(r["rows_before"] for r in ok)
            total_out = sum(r["rows_after"] for r in ok)
            lines += [
                "-" * 82,
                f"{'TOTAL':<{col_w}} {total_in:>9,} {total_out:>9,} {total_in - total_out:>8,}",
                "",
                "Tip: run `batch_report` to export a combined client-ready .md",
            ]
        return "\n".join(lines)

    def export_batch_report(self, path: str = None) -> str:
        if not self._batch_results:
            return "Run batch_clean first."
        if path is None:
            path = "batch_cleaning_report.md"
        ok = [r for r in self._batch_results if r["status"] == "OK"]
        fail = [r for r in self._batch_results if r["status"] != "OK"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_in = sum(r["rows_before"] for r in ok)
        total_out = sum(r["rows_after"] for r in ok)
        reduction = f"{(total_in - total_out) / total_in * 100:.1f}%" if total_in else "—"

        lines = [
            "# Batch Data Cleaning Report",
            "",
            f"**Generated:** {now}  ",
            f"**Files processed:** {len(self._batch_results)} "
            f"({len(ok)} succeeded, {len(fail)} failed)  ",
            "",
            "## Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Total rows in | {total_in:,} |",
            f"| Total rows out | {total_out:,} |",
            f"| Total rows removed | {total_in - total_out:,} |",
            f"| Overall reduction | {reduction} |",
            "",
            "## Per-File Results",
            "",
            "| File | Rows In | Rows Out | Removed | Dupes | Cols |",
            "|------|---------|----------|---------|-------|------|",
        ]
        for r in ok:
            lines.append(
                f"| {r['file']} | {r['rows_before']:,} | {r['rows_after']:,} | "
                f"{r['rows_removed']:,} ({r['rows_pct']}) | {r['dupes']:,} | "
                f"{r['cols_before']}→{r['cols_after']} |"
            )
        if fail:
            lines += ["", "## Failures", ""]
            for r in fail:
                lines.append(f"- **{r['file']}**: {r.get('error', 'unknown error')}")
        lines += ["", "---", "*Generated by NEO Data Janitor*"]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        return f"Batch report saved -> {path}"

    # ── Export ────────────────────────────────────────────────────────────────
    def export(self, path: str = None) -> str:
        if self.df is None:
            return "No data loaded."
        if path is None:
            stem = self.path.stem if self.path else "cleaned"
            path = f"{stem}_cleaned.csv"
        try:
            if path.lower().endswith((".xlsx", ".xls")):
                self.df.to_excel(path, index=False)
            else:
                self.df.to_csv(path, index=False)
        except PermissionError:
            return f"PermissionError: close {path} in Excel and retry."
        except Exception as e:
            return f"Export failed: {e}"
        return f"Exported {len(self.df):,} rows -> {path}"


# ── Interactive CLI ────────────────────────────────────────────────────────────

HELP = """
Commands:
  profile               show dataset insights
  clean                 one-click auto-clean
  <natural language>    e.g. "drop the salary column", "filter rows where age > 30"
  undo                  revert last action
  export [path]         save to CSV/XLSX (default: <name>_cleaned.csv)
  report [path]         write client-facing cleaning report (.md)
  batch_report [path]   write combined batch report (after --batch run)
  help                  this menu
  quit                  exit

Batch mode (no interactive prompt):
  python data_janitor.py --batch folder/ [--out output_folder/]
"""


def main():
    argv = sys.argv[1:]

    # Batch mode: python data_janitor.py --batch folder/ [--out output/]
    if argv and argv[0] == "--batch":
        folder = argv[1] if len(argv) > 1 and not argv[1].startswith("-") else None
        if not folder:
            folder = input("Folder to batch-clean: ").strip().strip('"')
        out_folder = None
        if "--out" in argv:
            idx = argv.index("--out")
            if idx + 1 < len(argv):
                out_folder = argv[idx + 1]
        j = DataJanitor()
        print(j.batch_clean(folder, out_folder))
        try:
            ans = input("\nExport batch report? [y/N]: ").strip().lower()
            if ans == "y":
                print(j.export_batch_report())
        except (EOFError, KeyboardInterrupt):
            pass
        return

    # Single-file interactive mode
    j = DataJanitor()
    if argv:
        print(j.load(argv[0]))
    else:
        print(j.load(input("CSV/XLSX path: ").strip().strip('"')))
    print(HELP)
    while True:
        try:
            cmd = input("janitor> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye"); break
        if not cmd:
            continue
        low = cmd.lower()
        if low in ("quit", "exit", "q"):
            break
        elif low == "help":
            print(HELP)
        elif low == "profile":
            print(j.profile())
        elif low == "clean":
            print(j.auto_clean())
        elif low == "undo":
            print(j.undo())
        elif low.startswith("batch_report"):
            parts = cmd.split(maxsplit=1)
            print(j.export_batch_report(parts[1].strip() if len(parts) > 1 else None))
        elif low.startswith("report"):
            parts = cmd.split(maxsplit=1)
            print(j.export_report(parts[1].strip() if len(parts) > 1 else None))
        elif low.startswith("export"):
            parts = cmd.split(maxsplit=1)
            print(j.export(parts[1].strip() if len(parts) > 1 else None))
        else:
            print(j.run_command(cmd))


if __name__ == "__main__":
    main()
