from datetime import date
from app.models import Invoice


def generate_invoice_number(issue_date=None):
    """Generate next invoice number in format YY-NNNN based on issue date."""
    if issue_date is None:
        issue_date = date.today()

    year = issue_date.strftime("%y")

    last_invoice = (
        Invoice.query.filter(Invoice.number.like(f"{year}-%"))
        .order_by(Invoice.number.desc())
        .first()
    )

    if last_invoice:
        last_seq = int(last_invoice.number.split("-")[1])
        new_seq = last_seq + 1
    else:
        new_seq = 1

    return f"{year}-{new_seq:04d}"
