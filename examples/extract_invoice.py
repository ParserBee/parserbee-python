"""Extract the fields of one invoice and print them.

Usage:
    export PARSERBEE_API_KEY=pk_...
    python examples/extract_invoice.py <template_id> invoice.pdf
"""

import json
import sys

from parserbee import ParserBee


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Usage: python extract_invoice.py <template_id> <file>")
    template_id, path = sys.argv[1], sys.argv[2]

    with ParserBee() as client:
        result = client.extract(template_id, path)

    print(json.dumps(result["data"], indent=2))
    usage = result.get("usage") or {}
    print(f"\nPages: {usage.get('pages_processed')}, credits left: {result.get('credits_remaining')}")


if __name__ == "__main__":
    main()
