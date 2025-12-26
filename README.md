# InvoiciPy

Lightweight self-hosted invoicing system for generating PDF invoices with Flask and WeasyPrint.

## Features

- **Customer database** — store and manage client information
- **PDF invoices** — 3 templates (default, detailed, minimal)
- **Invoice numbering** — automatic YY-NNNN format (e.g., 25-0001)
- **Optional text blocks** — configurable sections like VAT notes, bank details
- **Status workflow** — draft → issued → paid
- **Multi-currency** — EUR, USD, etc. with exchange rates

## Tech Stack

- Python + Flask
- SQLAlchemy + SQLite
- WeasyPrint (HTML/CSS → PDF)
- Pure CSS frontend (no frameworks)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/mrpesho/invoicipy.git
cd invoicipy
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# WeasyPrint system deps (macOS)
brew install cairo pango gdk-pixbuf libffi

# Initialize database
flask db upgrade

# Configure your company details
cp .env.example .env
# Edit .env with your company info

# Run
flask run
```

Open http://localhost:5000

## Configuration

Set your company details in `.env` or `config.py`:

```
COMPANY_NAME=Your Company
COMPANY_VAT_NUMBER=XX123456789
COMPANY_IBAN=XX00 0000 0000 0000
# ... see config.py for all options
```

## License

BSL 1.1 (Business Source License) — see [LICENSE.md](LICENSE.md)

**Free for:** Freelancers and sole proprietors with ≤ €100k annual revenue.

**Commercial license required for:** Companies with employees, agencies, SaaS providers.