from datetime import date, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, current_app
from app.models import db, Invoice, InvoiceItem, Customer, OptionalText
from app.services.numbering import generate_invoice_number
from app.services.pdf import generate_invoice_pdf, render_invoice_html

bp = Blueprint("invoices", __name__, url_prefix="/invoices")


@bp.route("/")
def list_invoices():
    from sqlalchemy import extract, func

    status = request.args.get("status", "")
    search = request.args.get("search", "")

    # Get all years that have invoices, plus current year
    current_year = date.today().year
    years_query = db.session.query(
        extract("year", Invoice.issue_date).label("year")
    ).distinct().order_by(extract("year", Invoice.issue_date).desc()).all()
    years = [int(y.year) for y in years_query if y.year]
    if current_year not in years:
        years.insert(0, current_year)
    years.sort(reverse=True)

    # Selected year (default to current)
    selected_year = request.args.get("year", type=int, default=current_year)
    if selected_year not in years:
        selected_year = current_year

    # Base query for selected year
    query = Invoice.query.join(Customer).filter(
        extract("year", Invoice.issue_date) == selected_year
    )

    if status:
        query = query.filter(Invoice.status == status)

    if search:
        query = query.filter(
            Invoice.number.ilike(f"%{search}%") | Customer.name.ilike(f"%{search}%")
        )

    # Order by invoice number DESC (drafts without numbers go to end)
    invoices = query.order_by(Invoice.number.desc().nullslast(), Invoice.created_at.desc()).all()

    # Financial sums for selected year (in native currency)
    year_invoices = Invoice.query.filter(
        extract("year", Invoice.issue_date) == selected_year
    ).all()

    native_currency = current_app.config["NATIVE_CURRENCY"]
    sums = {
        "paid": sum(inv.native_total for inv in year_invoices if inv.status == "paid"),
        "pending": sum(inv.native_total for inv in year_invoices if inv.status == "issued"),
        "draft": sum(inv.native_total for inv in year_invoices if inv.status == "draft"),
        "total": sum(inv.native_total for inv in year_invoices),
    }

    # Count stats for selected year
    stats = {
        "total": len(year_invoices),
        "draft": sum(1 for inv in year_invoices if inv.status == "draft"),
        "issued": sum(1 for inv in year_invoices if inv.status == "issued"),
        "paid": sum(1 for inv in year_invoices if inv.status == "paid"),
    }

    return render_template(
        "invoices/list.html",
        invoices=invoices,
        status=status,
        search=search,
        stats=stats,
        sums=sums,
        years=years,
        selected_year=selected_year,
        native_currency=native_currency,
    )


@bp.route("/new", methods=["GET", "POST"])
def create_invoice():
    customers = Customer.query.order_by(Customer.name).all()
    optional_texts = OptionalText.query.all()
    templates = ["default", "detailed", "minimal"]

    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        if not customer_id:
            flash("Please select a customer.", "error")
            return render_template(
                "invoices/form.html",
                invoice=None,
                customers=customers,
                optional_texts=optional_texts,
                templates=templates,
                native_currency=current_app.config["NATIVE_CURRENCY"],
            )

        # Get enabled optional texts from form
        enabled_texts = request.form.getlist("optional_texts")

        # Parse issue date
        issue_date = date.fromisoformat(request.form["issue_date"])

        # Check action: save as draft or create & issue
        action = request.form.get("action", "save")
        is_issuing = action == "issue"

        # Assign invoice number only when issuing
        invoice_number = None
        if is_issuing:
            # Use provided number or auto-generate
            provided_number = request.form.get("invoice_number", "").strip()
            invoice_number = provided_number if provided_number else generate_invoice_number(issue_date)

        # Parse exchange rate
        currency = request.form.get("currency", "EUR")
        native_currency = current_app.config["NATIVE_CURRENCY"]
        if currency == native_currency:
            exchange_rate = Decimal("1.0")
        else:
            exchange_rate = Decimal(request.form.get("exchange_rate") or "1.0")

        invoice = Invoice(
            number=invoice_number,
            customer_id=int(customer_id),
            template=request.form.get("template", "default"),
            issue_date=issue_date,
            delivery_date=(
                date.fromisoformat(request.form["delivery_date"])
                if request.form.get("delivery_date")
                else None
            ),
            due_date=date.fromisoformat(request.form["due_date"]),
            currency=currency,
            exchange_rate=exchange_rate,
            notes=request.form.get("notes"),
            optional_texts=enabled_texts,
            status="issued" if is_issuing else "draft",
        )

        db.session.add(invoice)
        db.session.flush()

        # Add items
        descriptions = request.form.getlist("item_description[]")
        quantities = request.form.getlist("item_quantity[]")
        units = request.form.getlist("item_unit[]")
        prices = request.form.getlist("item_price[]")
        tax_rates = request.form.getlist("item_tax[]")

        for i, desc in enumerate(descriptions):
            if desc.strip():
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=desc,
                    quantity=float(quantities[i]) if quantities[i] else 1,
                    unit=units[i] if units[i] else "pcs",
                    unit_price=float(prices[i]) if prices[i] else 0,
                    tax_rate=float(tax_rates[i]) if tax_rates[i] else 0,
                    position=i,
                )
                db.session.add(item)

        db.session.commit()

        if is_issuing:
            flash(f"Invoice {invoice.number} created and issued.", "success")
        else:
            flash(f"Draft #{invoice.id} saved.", "success")
        return redirect(url_for("invoices.get_invoice", id=invoice.id))

    # Default dates
    today = date.today()
    default_payment_days = 14
    default_due = today + timedelta(days=default_payment_days)

    # Get default enabled texts
    default_enabled = [t.key for t in optional_texts if t.default_enabled]

    # Generate suggested next invoice number
    next_number = generate_invoice_number(today)

    return render_template(
        "invoices/form.html",
        invoice=None,
        customers=customers,
        optional_texts=optional_texts,
        templates=templates,
        today=today,
        default_due=default_due,
        default_enabled=default_enabled,
        next_number=next_number,
        default_payment_days=default_payment_days,
        native_currency=current_app.config["NATIVE_CURRENCY"],
    )


@bp.route("/<int:id>")
def get_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template("invoices/detail.html", invoice=invoice)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_invoice(id):
    invoice = Invoice.query.get_or_404(id)

    if invoice.status != "draft":
        flash("Only draft invoices can be edited.", "error")
        return redirect(url_for("invoices.get_invoice", id=id))

    customers = Customer.query.order_by(Customer.name).all()
    optional_texts = OptionalText.query.all()
    templates = ["default", "detailed", "minimal"]

    if request.method == "POST":
        invoice.customer_id = int(request.form["customer_id"])
        invoice.template = request.form.get("template", "default")
        invoice.issue_date = date.fromisoformat(request.form["issue_date"])
        invoice.delivery_date = (
            date.fromisoformat(request.form["delivery_date"])
            if request.form.get("delivery_date")
            else None
        )
        invoice.due_date = date.fromisoformat(request.form["due_date"])
        invoice.currency = request.form.get("currency", "EUR")

        # Parse exchange rate
        native_currency = current_app.config["NATIVE_CURRENCY"]
        if invoice.currency == native_currency:
            invoice.exchange_rate = Decimal("1.0")
        else:
            invoice.exchange_rate = Decimal(request.form.get("exchange_rate") or "1.0")

        invoice.notes = request.form.get("notes")
        invoice.optional_texts = request.form.getlist("optional_texts")

        # Check action: save as draft or issue
        action = request.form.get("action", "save")
        is_issuing = action == "issue"

        # Assign invoice number if issuing
        if is_issuing and not invoice.number:
            # Use provided number or auto-generate
            provided_number = request.form.get("invoice_number", "").strip()
            invoice.number = provided_number if provided_number else generate_invoice_number(invoice.issue_date)
            invoice.status = "issued"

        # Remove existing items
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()

        # Add new items
        descriptions = request.form.getlist("item_description[]")
        quantities = request.form.getlist("item_quantity[]")
        units = request.form.getlist("item_unit[]")
        prices = request.form.getlist("item_price[]")
        tax_rates = request.form.getlist("item_tax[]")

        for i, desc in enumerate(descriptions):
            if desc.strip():
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=desc,
                    quantity=float(quantities[i]) if quantities[i] else 1,
                    unit=units[i] if units[i] else "pcs",
                    unit_price=float(prices[i]) if prices[i] else 0,
                    tax_rate=float(tax_rates[i]) if tax_rates[i] else 0,
                    position=i,
                )
                db.session.add(item)

        db.session.commit()

        if is_issuing:
            flash(f"Invoice {invoice.number} issued.", "success")
        else:
            flash(f"Draft #{invoice.id} updated.", "success")
        return redirect(url_for("invoices.get_invoice", id=id))

    # Calculate payment days from existing invoice dates
    if invoice.issue_date and invoice.due_date:
        default_payment_days = (invoice.due_date - invoice.issue_date).days
    else:
        default_payment_days = 14

    # Suggest next number for drafts without a number
    next_number = None
    if not invoice.number:
        next_number = generate_invoice_number(invoice.issue_date or date.today())

    return render_template(
        "invoices/form.html",
        invoice=invoice,
        customers=customers,
        optional_texts=optional_texts,
        templates=templates,
        default_enabled=invoice.optional_texts or [],
        default_payment_days=default_payment_days,
        next_number=next_number,
        native_currency=current_app.config["NATIVE_CURRENCY"],
    )


@bp.route("/<int:id>/delete", methods=["POST"])
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)

    if invoice.status != "draft":
        flash("Only draft invoices can be deleted.", "error")
        return redirect(url_for("invoices.list_invoices"))

    display = invoice.display_number
    db.session.delete(invoice)
    db.session.commit()
    flash(f"{display} deleted.", "success")
    return redirect(url_for("invoices.list_invoices"))


@bp.route("/<int:id>/pdf")
def download_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    pdf_bytes = generate_invoice_pdf(invoice)

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice-{invoice.display_number}.pdf"
        },
    )


@bp.route("/<int:id>/preview")
def preview_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    html = render_invoice_html(invoice)
    return html


@bp.route("/<int:id>/issue", methods=["POST"])
def issue_invoice(id):
    invoice = Invoice.query.get_or_404(id)

    if invoice.status != "draft":
        flash("Only draft invoices can be issued.", "error")
        return redirect(url_for("invoices.get_invoice", id=id))

    # Assign invoice number if not already assigned
    if not invoice.number:
        invoice.number = generate_invoice_number(invoice.issue_date)

    invoice.status = "issued"
    db.session.commit()
    flash(f"Invoice {invoice.number} has been issued.", "success")
    return redirect(url_for("invoices.get_invoice", id=id))


@bp.route("/<int:id>/paid", methods=["POST"])
def mark_paid(id):
    invoice = Invoice.query.get_or_404(id)

    if invoice.status == "paid":
        flash("Invoice is already marked as paid.", "error")
        return redirect(url_for("invoices.get_invoice", id=id))

    invoice.status = "paid"
    db.session.commit()
    flash(f"Invoice {invoice.number} marked as paid.", "success")
    return redirect(url_for("invoices.get_invoice", id=id))
