
# Value normalisation applied to a column BEFORE it is cast to its target type.
# trim spaces, unify case, Danish decimal commas, mixed date formats / Excel serials, strip units.
import re

import pandas as pd

NUM_RE = re.compile(r"^\s*([-+]?\d[\d.,\s]*)")  # leading number; anything after it (the unit) is ignored
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")      # yyyy-mm-dd, must never be read day-first


def trim(s: pd.Series) -> pd.Series:
    """Strip outer spaces, turn non-breaking spaces (common in Excel) into normal ones, collapse inner runs."""
    return (s.astype("string")
             .str.replace(" ", " ", regex=False)
             .str.strip()
             .str.replace(r"\s+", " ", regex=True))


def toText(s: pd.Series, case: str = None) -> pd.Series:
    """Trim, then optionally unify case. case: lower | upper | title (None leaves case alone)."""
    s = trim(s)
    if case == "lower":
        return s.str.lower()
    if case == "upper":
        return s.str.upper()
    if case == "title":
        return s.str.title()
    return s


def toNumber(s: pd.Series, decimal: str = ",") -> pd.Series:
    """Extract the leading number and return floats. "12 pcs" -> 12, "1.234,56" -> 1234.56.

    decimal="," is Danish (dot = thousands); decimal="." is English (comma = thousands).
    Values with no leading number become NaN, so count nulls before/after if that matters.
    """
    num = trim(s).str.extract(NUM_RE)[0].str.replace(" ", "", regex=False)
    if decimal == ",":
        num = num.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    else:
        num = num.str.replace(",", "", regex=False)
    return pd.to_numeric(num)


def parseDate(v):
    """Parse one date string. ISO first; otherwise day-first (05-03-2024 = 5 March)."""
    if pd.isna(v):
        return pd.NaT
    if ISO_RE.match(v):
        return pd.to_datetime(v, format="ISO8601")
    return pd.to_datetime(v, dayfirst=True)


def toDate(s: pd.Series) -> pd.Series:
    """Return datetime64. Handles Excel serials (numbers 1-80000) and common string formats.

    A bare number in that range is always treated as a serial, so a plain
    year such as 2024 would be misread; only use this on real date columns.
    """
    s = trim(s)
    serial = pd.to_numeric(s, errors="coerce")
    isSerial = serial.between(1, 80000).fillna(False).astype(bool)  # nullable mask -> plain bool
    parsed = pd.to_datetime(s.where(~isSerial).map(parseDate))
    fromSerial = pd.to_datetime(serial.where(isSerial), unit="D", origin="1899-12-30")
    return parsed.where(~isSerial, fromSerial)


def normalize(s: pd.Series, col: dict) -> pd.Series:
    """Pick the normaliser for a mapping column by its type. Options come from the YAML: case, decimal."""
    t = col.get("type", "str")
    if t in ("int", "float"):
        return toNumber(s, col.get("decimal", ","))
    if t in ("date", "datetime"):
        return toDate(s)
    if t == "str":
        return toText(s, col.get("case"))
    return trim(s)  # bool
