# InvoiciPy

A lightweight self-hosted invoicing system for generating PDF invoices with customizable layouts.

**Name origin:** "invoice" + "Py" (Python) — follows the NumPy/SciPy naming convention.

## Requirements

### Core Features
- **Multiple PDF layouts** — configurable table columns for different scenarios
- **Customer database** — easy selection when issuing invoices
- **Toggle-able text sections** — e.g., "VAT reverse charge under Article 44 of VAT Directive 2006/112/ES."
- **Date tracking** — issue date, delivery date, due date
- **Custom invoice number format** — e.g., `YY-NNNN` (24-0001, 24-0002, ...)

### Non-goals
- Subscription billing
- Usage-based metering
- Payment processing
- Complex tax calculations

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + Flask |
| ORM | SQLAlchemy |
| Database | SQLite (default, single file) |
| PDF Generation | WeasyPrint (HTML/CSS → PDF) |
| Frontend | Simple HTML forms (Jinja2 templates) |

## Database Schema

### customers
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR | Display name |
| legal_name | VARCHAR | Official registered name |
| legal_number | VARCHAR | Company registration number |
| vat_number | VARCHAR | Tax/VAT identification |
| email | VARCHAR | Contact email |
| address_line1 | VARCHAR | Street address |
| address_line2 | VARCHAR | Additional address |
| city | VARCHAR | City |
| zipcode | VARCHAR | Postal code |
| country | VARCHAR | Country code (ISO) |
| created_at | DATETIME | Record creation time |

### invoices
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| number | VARCHAR | Custom invoice number (e.g., "24-0001") |
| customer_id | INTEGER | Foreign key → customers |
| template | VARCHAR | Template name (e.g., "default", "detailed") |
| issue_date | DATE | When invoice was issued |
| delivery_date | DATE | When service/goods delivered |
| due_date | DATE | Payment due date |
| currency | VARCHAR | Currency code (EUR, USD) |
| notes | TEXT | Optional notes on invoice |
| optional_texts | JSON | Array of enabled optional text keys |
| status | VARCHAR | draft, issued, paid |
| created_at | DATETIME | Record creation time |

### invoice_items
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| invoice_id | INTEGER | Foreign key → invoices |
| description | VARCHAR | Item description |
| quantity | DECIMAL | Quantity |
| unit | VARCHAR | Unit (pcs, hours, etc.) |
| unit_price | DECIMAL | Price per unit |
| tax_rate | DECIMAL | Tax percentage (0, 20, etc.) |
| position | INTEGER | Sort order |

### optional_texts (configurable text blocks)
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| key | VARCHAR | Unique identifier |
| label | VARCHAR | Display label in UI |
| content | TEXT | Full text to display on invoice |
| default_enabled | BOOLEAN | Enabled by default on new invoices |

Example optional texts:
- `vat_reverse_charge`: "VAT reverse charge under Article 44 of VAT Directive 2006/112/ES."
- `bank_details`: "Bank: ...\nIBAN: ...\nSWIFT: ..."
- `payment_terms`: "Payment due within 14 days."

## Invoice Number Format

Format: `YY-NNNN` (2-digit year + 4-digit sequence)

Examples:
- First invoice of 2024: `24-0001`
- Second invoice of 2024: `24-0002`
- First invoice of 2025: `25-0001`

Logic:
```python
def generate_invoice_number():
    year = datetime.now().strftime("%y")
    last_invoice = Invoice.query.filter(
        Invoice.number.like(f"{year}-%")
    ).order_by(Invoice.number.desc()).first()

    if last_invoice:
        last_seq = int(last_invoice.number.split("-")[1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{year}-{new_seq:04d}"
```

## PDF Templates

Templates are HTML/CSS files rendered to PDF via WeasyPrint.

### Template structure
```
templates/
├── invoices/
│   ├── base.html          # Common layout (header, footer, styles)
│   ├── default.html       # Standard invoice
│   ├── detailed.html      # With additional columns (hours, rate)
│   └── minimal.html       # Simplified layout
```

### Template variables
```python
{
    "invoice": {
        "number": "24-0001",
        "issue_date": "2024-12-24",
        "delivery_date": "2024-12-20",
        "due_date": "2025-01-07",
        "currency": "EUR",
        "notes": "...",
    },
    "customer": {
        "name": "Acme Corp",
        "legal_name": "Acme Corporation Ltd.",
        # ... all customer fields
    },
    "items": [
        {"description": "...", "quantity": 1, "unit_price": 100.00, ...},
    ],
    "totals": {
        "subtotal": 100.00,
        "tax": 0.00,
        "total": 100.00,
    },
    "optional_texts": [
        "VAT reverse charge under Article 44...",
        "Bank: ...",
    ],
    "company": {
        # Your company details (from config)
    }
}
```

## Project Structure

```
invoicipy/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # SQLAlchemy models
│   ├── routes/
│   │   ├── invoices.py    # Invoice CRUD + PDF generation
│   │   ├── customers.py   # Customer CRUD
│   │   └── settings.py    # Optional texts, company info
│   ├── services/
│   │   ├── pdf.py         # PDF generation with WeasyPrint
│   │   └── numbering.py   # Invoice number generation
│   └── templates/
│       ├── layout.html    # Base UI layout
│       ├── invoices/      # Invoice UI pages
│       ├── customers/     # Customer UI pages
│       └── pdf/           # PDF templates
├── config.py              # Configuration
├── requirements.txt
└── run.py                 # Entry point
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /customers | List customers |
| POST | /customers | Create customer |
| GET | /customers/:id | Get customer |
| PUT | /customers/:id | Update customer |
| DELETE | /customers/:id | Delete customer |
| GET | /invoices | List invoices |
| POST | /invoices | Create invoice |
| GET | /invoices/:id | Get invoice |
| PUT | /invoices/:id | Update invoice |
| DELETE | /invoices/:id | Delete invoice (draft only) |
| GET | /invoices/:id/pdf | Download PDF |
| GET | /invoices/:id/preview | Preview HTML (for template iteration) |
| POST | /invoices/:id/issue | Mark as issued |
| POST | /invoices/:id/paid | Mark as paid |

## UI Pages

1. **Dashboard** — recent invoices, quick stats
2. **Invoices list** — filter by status, search
3. **Create/Edit invoice** — form with customer dropdown, items table, optional text checkboxes
4. **Customers list** — search, add new
5. **Create/Edit customer** — form
6. **Settings** — company info, optional texts management

## Configuration

```python
# config.py
class Config:
    SECRET_KEY = "your-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///invoicing.db"

    # Your company details (shown on invoices)
    COMPANY_NAME = "Your Company Name"
    COMPANY_LEGAL_NAME = "Your Company Ltd."
    COMPANY_ADDRESS = "123 Main Street"
    COMPANY_CITY = "City"
    COMPANY_ZIPCODE = "12345"
    COMPANY_COUNTRY = "Country"
    COMPANY_VAT_NUMBER = "XX123456789"
    COMPANY_EMAIL = "billing@example.com"
    COMPANY_BANK_NAME = "Bank Name"
    COMPANY_IBAN = "XX00 0000 0000 0000 0000 00"
    COMPANY_SWIFT = "XXXXXX00"
```

## Getting Started

```bash
# Create project
mkdir invoicipy && cd invoicipy

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install flask sqlalchemy flask-sqlalchemy weasyprint

# Initialize database
flask db init
flask db migrate
flask db upgrade

# Run
flask run
```

## Dependencies

```
# requirements.txt
flask>=3.0
flask-sqlalchemy>=3.1
sqlalchemy>=2.0
weasyprint>=60.0
python-dotenv>=1.0
```

Note: WeasyPrint requires system dependencies (cairo, pango). On macOS:
```bash
brew install cairo pango gdk-pixbuf libffi
```
