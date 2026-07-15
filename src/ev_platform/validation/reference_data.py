from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "state_id",
    "state_name",
    "entity_type",
    "region",
    "is_union_territory",
}

VALID_ENTITY_TYPES = {"STATE", "UNION_TERRITORY"}
VALID_REGIONS = {"North", "South", "East", "West", "Central", "Northeast", "Islands"}

EXPECTED_TOTAL_ENTITIES = 36
EXPECTED_STATE_COUNT = 28
EXPECTED_UNION_TERRITORY_COUNT = 8


def validate_states_reference(file_path: str | Path) -> list[str]:
    """Validate the Indian states and Union Territories reference file."""

    path = Path(file_path)
    errors: list[str] = []

    if not path.exists():
        return [f"Reference file does not exist: {path}"]

    try:
        dataframe = pd.read_csv(path)
    except Exception as exc:
        return [f"Unable to read reference file: {exc}"]

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)

    if missing_columns:
        errors.append("Missing required columns: " + ", ".join(sorted(missing_columns)))
        return errors

    if len(dataframe) != EXPECTED_TOTAL_ENTITIES:
        errors.append(
            f"Expected {EXPECTED_TOTAL_ENTITIES} rows, but found {len(dataframe)}."
        )

    if dataframe["state_id"].isna().any():
        errors.append("state_id contains null values.")

    if dataframe["state_id"].duplicated().any():
        errors.append("state_id contains duplicate values.")

    if dataframe["state_name"].isna().any():
        errors.append("state_name contains null values.")

    if dataframe["state_name"].duplicated().any():
        duplicates = (
            dataframe.loc[
                dataframe["state_name"].duplicated(keep=False),
                "state_name",
            ]
            .drop_duplicates()
            .tolist()
        )
        errors.append("Duplicate state names found: " + ", ".join(duplicates))

    blank_names = dataframe["state_name"].astype(str).str.strip().eq("")

    if blank_names.any():
        errors.append("state_name contains blank values.")

    unexpected_entity_types = set(dataframe["entity_type"]) - VALID_ENTITY_TYPES

    if unexpected_entity_types:
        errors.append(
            "Unexpected entity types: " + ", ".join(sorted(unexpected_entity_types))
        )

    unexpected_regions = set(dataframe["region"]) - VALID_REGIONS

    if unexpected_regions:
        errors.append("Unexpected regions: " + ", ".join(sorted(unexpected_regions)))

    state_count = dataframe["entity_type"].eq("STATE").sum()
    union_territory_count = dataframe["entity_type"].eq("UNION_TERRITORY").sum()

    if state_count != EXPECTED_STATE_COUNT:
        errors.append(
            f"Expected {EXPECTED_STATE_COUNT} states, but found {state_count}."
        )

    if union_territory_count != EXPECTED_UNION_TERRITORY_COUNT:
        errors.append(
            f"Expected {EXPECTED_UNION_TERRITORY_COUNT} Union Territories, "
            f"but found {union_territory_count}."
        )

    actual_flags = dataframe["is_union_territory"].astype(str).str.strip().str.lower()

    invalid_flags = set(actual_flags) - {"true", "false"}

    if invalid_flags:
        errors.append(
            "Invalid is_union_territory values: " + ", ".join(sorted(invalid_flags))
        )

    expected_flags = dataframe["entity_type"].map(
        {
            "STATE": "false",
            "UNION_TERRITORY": "true",
        }
    )

    mismatched_flags = actual_flags.ne(expected_flags)

    if mismatched_flags.any():
        mismatched_names = dataframe.loc[
            mismatched_flags,
            "state_name",
        ].tolist()

        errors.append(
            "Union Territory flag does not match entity_type for: "
            + ", ".join(mismatched_names)
        )

    expected_ids = set(range(1, EXPECTED_TOTAL_ENTITIES + 1))
    actual_ids = set(dataframe["state_id"].dropna().astype(int))

    if actual_ids != expected_ids:
        errors.append("state_id must contain every integer from 1 to 36 exactly once.")

    return errors
