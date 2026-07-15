from pathlib import Path

from ev_platform.ingestion.pib_ev_registration import (
    download_ev_registration_source,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    """Download the official state-wise EV registration dataset."""

    print("Starting official EV registration data acquisition...")

    try:
        result = download_ev_registration_source(PROJECT_ROOT)
    except Exception as exc:
        print("\nDownload failed.")
        print(f"Reason: {exc}")
        return 1

    metadata = result["metadata"]

    print("\nDownload completed successfully.")
    print(f"HTML source: {result['html_path']}")
    print(f"Extracted CSV: {result['csv_path']}")
    print(f"Metadata: {result['metadata_path']}")
    print(f"Rows extracted: {metadata['extracted_row_count']}")
    print(f"Tables found on webpage: {metadata['tables_found']}")
    print(f"SHA-256: {metadata['html_sha256']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
