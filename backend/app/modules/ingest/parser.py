"""
Input parser — reads CSV/XLSX files and returns validated DataFrames.
Phase 0: Stub that returns minimal structure so the app starts.
Full implementation in Phase 2.
"""
import io
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class ParsedData:
    sales: pd.DataFrame
    expenses: pd.DataFrame
    udhaar: pd.DataFrame
    month: str
    parse_errors: list[str]


def parse_files(
    sales_bytes: bytes,
    sales_filename: str,
    expenses_bytes: bytes,
    expenses_filename: str,
    udhaar_bytes: bytes,
    udhaar_filename: str,
    month: str,
) -> ParsedData:
    """Parse and sanitize all three input files. G1 formula sanitization applied."""
    errors = []

    sales = _parse_one(sales_bytes, sales_filename, errors, "sales")
    expenses = _parse_one(expenses_bytes, expenses_filename, errors, "expenses")
    udhaar = _parse_one(udhaar_bytes, udhaar_filename, errors, "udhaar")

    return ParsedData(sales=sales, expenses=expenses, udhaar=udhaar, month=month, parse_errors=errors)


def _parse_one(data: bytes, filename: str, errors: list, name: str) -> pd.DataFrame:
    """Parse a single file, applying formula injection sanitization."""
    try:
        buf = io.BytesIO(data)
        if filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(buf, engine="openpyxl")
        else:
            df = pd.read_csv(buf)

        # G1: Escape formula injection in string columns
        df = _sanitize_formulas(df)
        return df
    except Exception as e:
        errors.append(f"FILE_PARSE_ERROR:{name}:{str(e)}")
        return pd.DataFrame()


def _sanitize_formulas(df: pd.DataFrame) -> pd.DataFrame:
    """Prefix cells starting with = + - @ with ' to neutralize formula injection."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(
            lambda v: f"'{v}" if isinstance(v, str) and v and v[0] in ("=", "+", "-", "@") else v
        )
    return df
