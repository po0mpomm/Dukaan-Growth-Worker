"""
Input parser — reads CSV/XLSX files, maps aliases, sanitizes formulas,
and returns validated DataFrames for sales, expenses, and udhaar.
PRD §8.1, TRD §6, §10 (G1)
"""

import io
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

from app.modules.ingest.schemas import (
    SALES_COLUMN_ALIASES,
    EXPENSES_COLUMN_ALIASES,
    UDHAAR_COLUMN_ALIASES,
)
from app.modules.ingest.sanitizer import (
    sanitize_string,
    normalize_payment_mode,
    parse_float_safe,
)


@dataclass
class ParsedData:
    sales: pd.DataFrame
    expenses: pd.DataFrame
    udhaar: pd.DataFrame
    month: str
    parse_errors: List[str]


def parse_files(
    sales_bytes: bytes,
    sales_filename: str,
    expenses_bytes: bytes,
    expenses_filename: str,
    udhaar_bytes: bytes,
    udhaar_filename: str,
    month: str,
) -> ParsedData:
    """Parse, alias-normalize, and sanitize all three input files."""
    errors: List[str] = []

    sales = _parse_sales(sales_bytes, sales_filename, errors)
    expenses = _parse_expenses(expenses_bytes, expenses_filename, errors)
    udhaar = _parse_udhaar(udhaar_bytes, udhaar_filename, errors)

    return ParsedData(
        sales=sales,
        expenses=expenses,
        udhaar=udhaar,
        month=month,
        parse_errors=errors,
    )


def _read_raw_dataframe(data: bytes, filename: str) -> pd.DataFrame:
    """Reads raw bytes into DataFrame using openpyxl for Excel or read_csv for CSV."""
    buf = io.BytesIO(data)
    if filename.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(buf, engine="openpyxl")
    return pd.read_csv(buf)


def _map_columns(df: pd.DataFrame, alias_dict: Dict[str, str]) -> pd.DataFrame:
    """Renames columns based on alias mapping (case-insensitive, trimmed)."""
    rename_map = {}
    for col in df.columns:
        cleaned = str(col).strip().lower()
        if cleaned in alias_dict:
            rename_map[col] = alias_dict[cleaned]
    return df.rename(columns=rename_map)


def _sanitize_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """G1 Guardrail: Neutralizes any string starting with =, +, -, @."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(sanitize_string)
    return df


def _parse_sales(data: bytes, filename: str, errors: List[str]) -> pd.DataFrame:
    try:
        df = _read_raw_dataframe(data, filename)
        df = _map_columns(df, SALES_COLUMN_ALIASES)
        df = _sanitize_string_columns(df)

        if "amount" in df.columns:
            df["amount"] = df["amount"].apply(parse_float_safe)
        if "payment_mode" in df.columns:
            df["payment_mode"] = df["payment_mode"].apply(normalize_payment_mode)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        return df
    except Exception as e:
        errors.append(f"FILE_PARSE_ERROR:sales:{str(e)}")
        return pd.DataFrame()


def _parse_expenses(data: bytes, filename: str, errors: List[str]) -> pd.DataFrame:
    try:
        df = _read_raw_dataframe(data, filename)
        df = _map_columns(df, EXPENSES_COLUMN_ALIASES)
        df = _sanitize_string_columns(df)

        if "amount" in df.columns:
            df["amount"] = df["amount"].apply(parse_float_safe)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        return df
    except Exception as e:
        errors.append(f"FILE_PARSE_ERROR:expenses:{str(e)}")
        return pd.DataFrame()


def _parse_udhaar(data: bytes, filename: str, errors: List[str]) -> pd.DataFrame:
    try:
        df = _read_raw_dataframe(data, filename)
        df = _map_columns(df, UDHAAR_COLUMN_ALIASES)
        df = _sanitize_string_columns(df)

        for col in ("opening_balance", "credit_taken", "repaid_amount"):
            if col in df.columns:
                df[col] = df[col].apply(parse_float_safe)

        return df
    except Exception as e:
        errors.append(f"FILE_PARSE_ERROR:udhaar:{str(e)}")
        return pd.DataFrame()
