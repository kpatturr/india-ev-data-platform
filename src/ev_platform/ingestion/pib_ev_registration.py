from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests
import yaml


SOURCE_CONFIG_KEY = "ev_registration_pib_2019_2024"

REQUIRED_HEADER_PHRASES = (
    "state",
    "total ev",
    "total vehicles",
)


def calculate_sha256(content: bytes) -> str:
    """Return the SHA-256 checksum of binary content."""

    return hashlib.sha256(content).hexdigest()


def load_source_config(config_path: Path) -> dict[str, Any]:
    """Load the EV registration source configuration."""

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    try:
        source_config = config["sources"][SOURCE_CONFIG_KEY]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Missing source configuration: {SOURCE_CONFIG_KEY}") from exc

    if not source_config.get("enabled", False):
        raise ValueError(f"Source is disabled: {SOURCE_CONFIG_KEY}")

    return source_config


def clean_text(value: object) -> str:
    """Convert a table value to normalised display text."""

    if pd.isna(value):
        return ""

    return " ".join(str(value).replace("\n", " ").split())


def normalize_header(value: object) -> str:
    """Normalise a possible header value for matching."""

    return clean_text(value).lower()


def flatten_columns(columns: pd.Index) -> list[str]:
    """Convert normal or multi-level table headers into strings."""

    flattened: list[str] = []

    for index, column in enumerate(columns):
        if isinstance(column, tuple):
            parts = [
                clean_text(part)
                for part in column
                if clean_text(part) and not clean_text(part).startswith("Unnamed")
            ]
            flattened_column = " ".join(parts)
        else:
            flattened_column = clean_text(column)

        if not flattened_column:
            flattened_column = f"column_{index + 1}"

        flattened.append(flattened_column)

    return flattened


def contains_required_headers(values: list[object]) -> bool:
    """Check whether values contain the expected EV table headings."""

    searchable_text = " | ".join(
        normalize_header(value) for value in values if clean_text(value)
    )

    return all(phrase in searchable_text for phrase in REQUIRED_HEADER_PHRASES)


def find_header_row(table: pd.DataFrame) -> int | None:
    """Find the row containing the EV table headings."""

    rows_to_check = min(15, len(table))

    for row_position in range(rows_to_check):
        row_values = table.iloc[row_position].tolist()

        if contains_required_headers(row_values):
            return row_position

    return None


def remove_blank_rows(table: pd.DataFrame) -> pd.DataFrame:
    """Remove rows where every field is empty."""

    blank_row_mask = table.apply(
        lambda row: all(clean_text(value) == "" for value in row),
        axis=1,
    )

    return table.loc[~blank_row_mask].reset_index(drop=True)


def find_ev_registration_table(
    tables: list[pd.DataFrame],
) -> pd.DataFrame:
    """Locate the state-wise EV registration table in the webpage."""

    inspected_tables: list[dict[str, Any]] = []

    for table_index, original_table in enumerate(tables):
        table = original_table.copy()
        flattened_columns = flatten_columns(table.columns)

        header_found_in_columns = contains_required_headers(flattened_columns)
        header_row_position = find_header_row(table)

        preview = table.head(5).fillna("").astype(str).values.tolist()

        inspected_tables.append(
            {
                "table_index": table_index,
                "shape": list(table.shape),
                "columns": flattened_columns,
                "first_rows": preview,
            }
        )

        if header_found_in_columns:
            table.columns = flattened_columns

        elif header_row_position is not None:
            heading_values = table.iloc[header_row_position].tolist()

            promoted_headers = [
                clean_text(value) or f"column_{index + 1}"
                for index, value in enumerate(heading_values)
            ]

            table = table.iloc[header_row_position + 1 :].copy()
            table.columns = promoted_headers

        else:
            continue

        table = table.dropna(axis=1, how="all")
        table = table.dropna(how="all")
        table = remove_blank_rows(table)

        if len(table) < 30:
            continue

        return table.reset_index(drop=True)

    raise RuntimeError(
        "Could not locate the EV registration table. "
        f"Tables inspected: {json.dumps(inspected_tables, indent=2)}"
    )


def download_ev_registration_source(
    project_root: Path,
) -> dict[str, Any]:
    """Download and extract the official EV registration source table."""

    config_path = project_root / "config" / "sources.yml"
    source_config = load_source_config(config_path)

    landing_directory = project_root / source_config["landing_subdirectory"]
    landing_directory.mkdir(parents=True, exist_ok=True)

    output_basename = source_config["output_basename"]

    html_path = landing_directory / f"{output_basename}_source.html"
    csv_path = landing_directory / f"{output_basename}.csv"
    metadata_path = landing_directory / f"{output_basename}_metadata.json"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124 Safari/537.36"
        )
    }

    response = requests.get(
        source_config["source_url"],
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()

    html_content = response.content
    html_checksum = calculate_sha256(html_content)

    html_path.write_bytes(html_content)

    response.encoding = response.apparent_encoding or "utf-8"

    tables = pd.read_html(StringIO(response.text))
    ev_table = find_ev_registration_table(tables)

    ev_table.to_csv(csv_path, index=False)

    metadata = {
        "source_key": SOURCE_CONFIG_KEY,
        "source_name": source_config["source_name"],
        "source_type": source_config["source_type"],
        "publisher": source_config["publisher"],
        "upstream_data_source": source_config["upstream_data_source"],
        "source_url": source_config["source_url"],
        "final_url": response.url,
        "publication_date": source_config["publication_date"],
        "reporting_period_start": source_config["reporting_period_start"],
        "reporting_period_end": source_config["reporting_period_end"],
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "http_status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "html_filename": html_path.name,
        "csv_filename": csv_path.name,
        "html_sha256": html_checksum,
        "html_size_bytes": len(html_content),
        "tables_found": len(tables),
        "extracted_row_count": len(ev_table),
        "extracted_columns": ev_table.columns.tolist(),
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "html_path": html_path,
        "csv_path": csv_path,
        "metadata_path": metadata_path,
        "metadata": metadata,
    }
