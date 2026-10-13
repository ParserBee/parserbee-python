# parserbee-python

Python client for the [ParserBee](https://parserbee.com) API. Send a PDF, scan or phone photo of an invoice, purchase order, receipt or bank statement, and get back structured JSON that matches your Parser Template.

## Install

```bash
pip install parserbee
```

Requires Python 3.9 or later.

## Before you start

1. Create a free account at [app.parserbee.com](https://app.parserbee.com/create-account). New accounts get 25 free pages, no credit card.
2. Create a Parser Template: upload one sample document and the AI builds the fields for you, or pick a ready-made one from the [template library](https://parserbee.com/templates/).
3. Copy your API key from **Settings** (it starts with `pk_`) and the template ID from the template page.

```bash
export PARSERBEE_API_KEY=pk_your_api_key
```

## Quick start

```python
from parserbee import ParserBee

client = ParserBee()  # reads PARSERBEE_API_KEY

result = client.extract("your_template_id", "invoice.pdf")
print(result["data"])
# {'invoice_number': 'INV-2026-001', 'vendor_name': 'Acme Corp', 'total_amount': 1500.0, ...}
```

Extract from a public link instead of a local file:

```python
result = client.extract("your_template_id", file_url="https://example.com/invoice.pdf")
```

An open binary file works too:

```python
with open("receipt.jpg", "rb") as f:
    result = client.extract("your_template_id", f)
```

## The response

`extract()` returns the API response as a dict:

| Key | What it holds |
|---|---|
| `data` | The extracted fields, shaped like your Parser Template |
| `request_id` | The request ID (also in Activity in the dashboard) |
| `credits_remaining` | Page credits left after this call |
| `usage` | `pages_processed`, `credits_charged`, `doc_size_bytes` |
| `processing_time_ms` | Time taken |

Each extraction costs 1 page credit per page processed, with a minimum of 1.

## Other methods

```python
client.list_templates()          # every Parser Template in the account
client.get_template("tpl_id")    # one template with its fields
client.get_credits()             # balance, plan and subscription status
client.list_activity()           # the last 10 extractions
client.get_activity("req_id")    # one extraction, with its data
```

## Errors

Every error is a subclass of `parserbee.ParserBeeError`, with `.code` and `.status`:

| Exception | When |
|---|---|
| `InvalidRequestError` | 400: missing field, or a file type that is not accepted |
| `AuthenticationError` | 401: missing or invalid API key |
| `InsufficientCreditsError` | 402: no page credits left (`.credits_remaining`) |
| `PermissionDeniedError` | 403: no active subscription |
| `NotFoundError` | 404: template or request not found |
| `APIError` | Any other API error |
| `APIConnectionError` | The request did not reach the API |

```python
from parserbee import InsufficientCreditsError

try:
    client.extract("your_template_id", "invoice.pdf")
except InsufficientCreditsError:
    print("Top up page credits in the dashboard")
```

## Examples

The [examples](https://github.com/ParserBee/parserbee-python/tree/main/examples) folder has scripts you can run as they are:

- `extract_invoice.py`: one file, printed as JSON
- `extract_from_url.py`: a document that is already online
- `folder_to_csv.py`: every PDF and image in a folder, one CSV row each
- `check_credits.py`: balance and template IDs

## Supported files

PDF, PNG, JPG, WebP and HEIC, up to 50 MB. The API also reads DOC, PPT, PPTX, XLSX, CSV, TXT, RTF, ODT, HTML and EML; see the [API reference](https://app.parserbee.com/docs) for details. Scans and phone photos work, and there is no need to run OCR first. DOCX is not accepted: save it as PDF first.

## No code needed?

If you only need the data in a spreadsheet, you do not need this library. [Data Lab](https://parserbee.com/tools/bank-statement-converter/#data-lab) in the dashboard takes a batch of documents and exports one combined Excel, CSV or Google Sheets file. To try a single invoice in the browser, use the free [invoice parser](https://parserbee.com/tools/invoice-parser/).

Choosing a tool for invoices? Our comparison of [invoice OCR software](https://parserbee.com/blog/best-invoice-ocr-software/) covers 10 options, tested on real invoices, scans and phone photos.

## Links

- [ParserBee](https://parserbee.com)
- [API reference](https://app.parserbee.com/docs)
- [Pricing](https://parserbee.com/pricing/)
- Support: support@parserbee.com

## License

MIT
