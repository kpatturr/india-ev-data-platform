from pathlib import Path

from ev_platform.validation.reference_data import validate_states_reference


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATES_FILE = PROJECT_ROOT / "data" / "reference" / "states.csv"


def main() -> int:
    """Validate project reference datasets."""

    print(f"Validating: {STATES_FILE}")

    errors = validate_states_reference(STATES_FILE)

    if errors:
        print("\nReference data validation failed:\n")

        for error in errors:
            print(f"- {error}")

        return 1

    print("\nReference data validation passed.")
    print("Validated 28 states and 8 Union Territories.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
