from flask import render_template, current_app
from weasyprint import HTML, CSS
from app.models import Invoice, OptionalText


def get_company_info():
    """Get company info from config."""
    return {
        "name": current_app.config.get("COMPANY_NAME"),
        "legal_name": current_app.config.get("COMPANY_LEGAL_NAME"),
        "legal_number": current_app.config.get("COMPANY_LEGAL_NUMBER"),
        "address": current_app.config.get("COMPANY_ADDRESS"),
        "city": current_app.config.get("COMPANY_CITY"),
        "zipcode": current_app.config.get("COMPANY_ZIPCODE"),
        "country": current_app.config.get("COMPANY_COUNTRY"),
        "vat_number": current_app.config.get("COMPANY_VAT_NUMBER"),
        "email": current_app.config.get("COMPANY_EMAIL"),
        "phone": current_app.config.get("COMPANY_PHONE"),
        "bank_name": current_app.config.get("COMPANY_BANK_NAME"),
        "iban": current_app.config.get("COMPANY_IBAN"),
        "swift": current_app.config.get("COMPANY_SWIFT"),
    }


def get_invoice_context(invoice):
    """Build the context dict for rendering invoice templates."""
    company = get_company_info()

    # Get enabled optional texts
    optional_text_contents = []
    if invoice.optional_texts:
        texts = OptionalText.query.filter(OptionalText.key.in_(invoice.optional_texts)).all()
        for text in texts:
            content = text.content
            # Replace placeholders with company info
            content = content.replace("{bank_name}", company.get("bank_name", ""))
            content = content.replace("{iban}", company.get("iban", ""))
            content = content.replace("{swift}", company.get("swift", ""))
            optional_text_contents.append(content)

    items = list(invoice.items.order_by("position").all())

    return {
        "invoice": {
            "number": invoice.number,
            "issue_date": invoice.issue_date,
            "delivery_date": invoice.delivery_date,
            "due_date": invoice.due_date,
            "currency": invoice.currency,
            "notes": invoice.notes,
            "status": invoice.status,
        },
        "customer": invoice.customer.to_dict(),
        "items": [item.to_dict() for item in items],
        "totals": {
            "subtotal": float(invoice.subtotal),
            "tax": float(invoice.tax_total),
            "total": float(invoice.total),
        },
        "optional_texts": optional_text_contents,
        "company": company,
    }


def render_invoice_html(invoice):
    """Render invoice to HTML string."""
    context = get_invoice_context(invoice)
    template_name = f"pdf/{invoice.template}.html"
    return render_template(template_name, **context)


def generate_invoice_pdf(invoice):
    """Generate PDF bytes from an invoice."""
    html_content = render_invoice_html(invoice)
    html = HTML(string=html_content, base_url=current_app.root_path)
    return html.write_pdf()
