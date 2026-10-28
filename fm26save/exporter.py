"""Multi-format Exporters (CSV, JSON, JSONL, SQLite) and Record Flattening for FM26 Saves."""

from __future__ import annotations

import csv
import dataclasses
import datetime
import enum
import json
import os
import sqlite3
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def serialize_record(obj: Any) -> Any:
    """Recursively convert dataclass, CodedValue, Enum, date, and mapping objects to JSON-ready dicts."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime.date, datetime.datetime, datetime.time)):
        return obj.isoformat()
    if isinstance(obj, enum.Enum):
        return obj.name
    if hasattr(obj, "label") and hasattr(obj, "raw") and type(obj).__name__ == "CodedValue":
        return obj.label.name if obj.label is not None and getattr(obj.label, "value", -1) != -1 else f"CODE_{obj.raw}"
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            if f.name == "raw_attributes":
                continue
            out[f.name] = serialize_record(getattr(obj, f.name))
        for prop_name in getattr(type(obj), "COMPUTED_FIELDS", ()):
            out[prop_name] = serialize_record(getattr(obj, prop_name))
        return out
    if isinstance(obj, Mapping):
        return {str(k): serialize_record(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return [serialize_record(x) for x in obj]
    return str(obj)


def flatten_record(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dataclasses/dicts into a single-level dictionary suitable for CSV & SQLite."""
    row: dict[str, Any] = {}
    data = serialize_record(obj) if not isinstance(obj, dict) else obj
    if not isinstance(data, dict):
        return {prefix or "value": data}
    for k, v in data.items():
        col = f"{prefix}{k}" if not prefix else f"{prefix}_{k}"
        if isinstance(v, dict):
            for sk, sv in v.items():
                if isinstance(sv, (dict, list)):
                    row[f"{col}_{sk}"] = json.dumps(sv, ensure_ascii=False)
                else:
                    row[f"{col}_{sk}"] = sv
        elif isinstance(v, list):
            if all(isinstance(x, (str, int, float)) for x in v):
                row[col] = ", ".join(str(x) for x in v)
            else:
                row[col] = json.dumps(v, ensure_ascii=False)
        else:
            row[col] = v
    return row


def export_to_csv(rows: Iterable[Any], output_path: str | os.PathLike[str]) -> int:
    """Export an iterable of records or dicts to a UTF-8-BOM CSV file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    iterator = iter(rows)
    try:
        first = next(iterator)
    except StopIteration:
        path.write_text("", encoding="utf-8-sig")
        return 0

    first_flat = flatten_record(first)
    fieldnames = list(first_flat.keys())
    count = 1
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerow(first_flat)
        for item in iterator:
            writer.writerow(flatten_record(item))
            count += 1
    return count


def export_to_json(rows: Iterable[Any], output_path: str | os.PathLike[str], *, jsonl: bool = False) -> int:
    """Export an iterable of records or dicts to JSON or JSON Lines (.jsonl)."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    if jsonl:
        with path.open("w", encoding="utf-8") as f:
            for item in rows:
                f.write(json.dumps(serialize_record(item), ensure_ascii=False) + "\n")
                count += 1
    else:
        serialized = [serialize_record(item) for item in rows]
        count = len(serialized)
        path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")
    return count


def export_tables_to_sqlite(
    tables_dict: Mapping[str, Iterable[Any]],
    sqlite_path: str | os.PathLike[str],
) -> dict[str, int]:
    """Export multiple tables into a single SQLite (.db) database file."""
    db_path = Path(sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        for table_name, records in tables_dict.items():
            safe_table = table_name.replace("-", "_")
            it = iter(records)
            try:
                first = next(it)
            except StopIteration:
                counts[table_name] = 0
                continue
            first_flat = flatten_record(first)
            cols = list(first_flat.keys())
            col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
            cur.execute(f'DROP TABLE IF EXISTS "{safe_table}"')
            cur.execute(f'CREATE TABLE "{safe_table}" ({col_defs})')

            placeholders = ", ".join("?" for _ in cols)
            insert_sql = f'INSERT INTO "{safe_table}" VALUES ({placeholders})'

            batch: list[tuple[Any, ...]] = [
                tuple(None if first_flat.get(c) is None else str(first_flat.get(c)) for c in cols)
            ]
            row_count = 1
            for rec in it:
                flat = flatten_record(rec)
                batch.append(tuple(None if flat.get(c) is None else str(flat.get(c)) for c in cols))
                row_count += 1
                if len(batch) >= 2000:
                    cur.executemany(insert_sql, batch)
                    batch.clear()
            if batch:
                cur.executemany(insert_sql, batch)
            conn.commit()
            counts[table_name] = row_count
    finally:
        conn.close()
    return counts
