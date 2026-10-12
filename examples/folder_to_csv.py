"""Extract every document in a folder and write one CSV row per document.

Top-level fields become columns. Lists and groups (such as invoice line
items) are written as JSON text in their column.

Usage:
    python examples/folder_to_csv.py <template_id> ./invoices output.csv
"""

import csv
import json
import sys
from pathlib import Path

from parserbee import InsufficientCreditsError, ParserBee, ParserBeeError

EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".heic"}


def cell(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("Usage: python folder_to_csv.py <template_id> <folder> <output.csv>")
    template_id, folder, output = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])

    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in EXTENSIONS)
    if not files:
        sys.exit(f"No PDF or image files in {folder}")

    rows = []
    with ParserBee() as client:
        for path in files:
            try:
                data = client.extract(template_id, path)["data"]
            except InsufficientCreditsError:
                print("Out of page credits; stopping.")
                break
            except ParserBeeError as exc:
                print(f"{path.name}: failed ({exc})")
                continue
            rows.append({"source_file": path.name, **{k: cell(v) for k, v in data.items()}})
            print(f"{path.name}: done")

    if not rows:
        sys.exit("Nothing was extracted.")

    columns = list(dict.fromkeys(key for row in rows for key in row))
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
