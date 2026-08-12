import sys

from pipeline import run_pipeline


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_pipeline(topic)
    print("\n--- DAILY NEWS DIGEST ---")
    print(result["digest"])
    print("\n--- DISTRIBUTION ---")
    print(f"Slack:       {result['distribution']['slack']}")
    print(f"Google Sheets: {result['distribution']['google_sheets']}")


if __name__ == "__main__":
    main()
