from pathlib import Path

import pandas as pd

from ev_platform.validation.reference_data import validate_states_reference


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATES_FILE = PROJECT_ROOT / "data" / "reference" / "states.csv"


def test_states_reference_passes_validation() -> None:
    errors = validate_states_reference(STATES_FILE)

    assert errors == [], "\n".join(errors)


def test_states_reference_contains_36_entities() -> None:
    dataframe = pd.read_csv(STATES_FILE)

    assert len(dataframe) == 36


def test_states_reference_contains_28_states() -> None:
    dataframe = pd.read_csv(STATES_FILE)

    state_count = dataframe["entity_type"].eq("STATE").sum()

    assert state_count == 28


def test_states_reference_contains_8_union_territories() -> None:
    dataframe = pd.read_csv(STATES_FILE)

    union_territory_count = dataframe["entity_type"].eq("UNION_TERRITORY").sum()

    assert union_territory_count == 8


def test_state_names_are_unique() -> None:
    dataframe = pd.read_csv(STATES_FILE)

    assert not dataframe["state_name"].duplicated().any()
