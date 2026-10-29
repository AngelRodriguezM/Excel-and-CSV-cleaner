#AI
# Maps source columns to target columns/types, driven by Config/mapping.yaml.
# Flow: loadMapping -> mapFiles -> (findMapping + applyMapping) per file.
import fnmatch
from typing import Callable, Optional

import pandas as pd
import yaml

from Config.normalize import normalize  #AI

# Supported "type" values in mapping.yaml -> function that casts a Series to that type.
# errors="raise" makes a bad value fail loudly instead of silently becoming NaN.
TYPE_CASTS: dict[str, Callable[[pd.Series], pd.Series]] = {
    "int": lambda s: pd.to_numeric(s, errors="raise").astype("Int64"),      # nullable int (allows blanks)
    "float": lambda s: pd.to_numeric(s, errors="raise").astype("float64"),
    "str": lambda s: s.astype("string"),                                    # nullable string dtype
    "bool": lambda s: s.astype("boolean"),                                  # nullable bool
    "date": lambda s: pd.to_datetime(s, errors="raise").dt.date,            # drops the time part
    "datetime": lambda s: pd.to_datetime(s, errors="raise"),
}


def loadMapping(path: str = "Config/mapping.yaml") -> list[dict]:
    """Read the YAML config and return its list of per-file mappings.

    Validates every column's type up front so a typo in the YAML fails
    here, not halfway through processing a file.
    Raises ValueError for an unknown type.
    """
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}  # empty file -> None -> {}
    mappings = config.get("mappings", [])
    for m in mappings:
        for col in m.get("columns", []):
            # "str" is the default type when none is given (same default as applyMapping)
            if col.get("type", "str") not in TYPE_CASTS:
                raise ValueError(f"Unknown type '{col['type']}' for column '{col['source']}'")
    return mappings


def findMapping(fileName: str, mappings: list[dict]) -> Optional[dict]:
    """Return the first mapping whose source_file pattern matches fileName, else None.

    Matching is a case-insensitive glob (e.g. "MOCK_DATA.*" matches "mock_data.csv").
    Order in the YAML matters: the first match wins.
    """
    for m in mappings:
        if fnmatch.fnmatch(fileName.lower(), m["source_file"].lower()):
            return m
    return None


def applyMapping(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Build a new DataFrame containing only the mapped columns, renamed and cast.

    Columns not listed in the mapping are dropped. "target" defaults to the
    source name and "type" defaults to "str".
    Raises KeyError if a mapped source column is missing from df, and
    (via pandas) ValueError if a value can't be cast to its type.
    """
    out = pd.DataFrame(index=df.index)  # keep the original row index so rows stay aligned
    for col in mapping["columns"]:
        source = col["source"]
        if source not in df.columns:
            raise KeyError(f"Column '{source}' not found in source (has: {list(df.columns)})")
        cleaned = normalize(df[source], col)  #AI normalise first, then cast
        out[col.get("target", source)] = TYPE_CASTS[col.get("type", "str")](cleaned)
    return out


def mapFiles(foundFiles: dict[str, Optional[pd.DataFrame]], mappings: list[dict]) -> dict[str, pd.DataFrame]:
    """Apply the matching mapping to each file read by readFolderFiles.

    foundFiles: {filename: DataFrame or None}. Files that failed to read (None)
    or have no matching mapping are skipped with a message, not treated as errors.
    Returns {filename: mapped DataFrame}.
    """
    mapped = {}
    for fileName, df in foundFiles.items():
        mapping = findMapping(fileName, mappings)
        if mapping is None or df is None:
            print(f"no mapping for {fileName}, skipped")
            continue
        mapped[fileName] = applyMapping(df, mapping)
    return mapped
