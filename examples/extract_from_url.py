"""Extract data from a document that is already online.

The link must open without a login.

Usage:
    python examples/extract_from_url.py <template_id> https://example.com/invoice.pdf
"""

import json
import sys

from parserbee import ParserBee


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: python extract_from_url.py <template_id> <url>")

    with ParserBee() as client:
        result = client.extract(sys.argv[1], file_url=sys.argv[2])

    print(json.dumps(result["data"], indent=2))


if __name__ == "__main__":
    main()
