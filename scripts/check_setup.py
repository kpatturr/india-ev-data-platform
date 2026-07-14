from pathlib import Path

import pandas as pd
from faker import Faker


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    fake = Faker("en_IN")

    sample_data = pd.DataFrame(
        [
            {
                "vehicle_id": "EV000001",
                "owner_name": fake.name(),
                "state": "Karnataka",
                "fuel_type": "Electric",
            },
            {
                "vehicle_id": "EV000002",
                "owner_name": fake.name(),
                "state": "Tamil Nadu",
                "fuel_type": "Electric",
            },
        ]
    )

    print(f"Project root: {project_root}")
    print("\nPython setup is working.\n")
    print(sample_data)


if __name__ == "__main__":
    main()
