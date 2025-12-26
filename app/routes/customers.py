from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import db, Customer

bp = Blueprint("customers", __name__, url_prefix="/customers")


@bp.route("/")
def list_customers():
    search = request.args.get("search", "")
    query = Customer.query

    if search:
        query = query.filter(
            Customer.name.ilike(f"%{search}%")
            | Customer.email.ilike(f"%{search}%")
            | Customer.vat_number.ilike(f"%{search}%")
        )

    customers = query.order_by(Customer.name).all()
    return render_template("customers/list.html", customers=customers, search=search)


@bp.route("/new", methods=["GET", "POST"])
def create_customer():
    if request.method == "POST":
        customer = Customer(
            name=request.form["name"],
            legal_name=request.form.get("legal_name"),
            legal_number=request.form.get("legal_number"),
            vat_number=request.form.get("vat_number"),
            email=request.form.get("email"),
            address_line1=request.form.get("address_line1"),
            address_line2=request.form.get("address_line2"),
            city=request.form.get("city"),
            state=request.form.get("state"),
            zipcode=request.form.get("zipcode"),
            country=request.form.get("country"),
            payment_terms=int(request.form.get("payment_terms") or 14),
        )
        db.session.add(customer)
        db.session.commit()
        flash(f"Customer '{customer.name}' created successfully.", "success")
        return redirect(url_for("customers.list_customers"))

    return render_template("customers/form.html", customer=None, default_payment_terms=14)


@bp.route("/<int:id>")
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return render_template("customers/detail.html", customer=customer)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_customer(id):
    customer = Customer.query.get_or_404(id)

    if request.method == "POST":
        customer.name = request.form["name"]
        customer.legal_name = request.form.get("legal_name")
        customer.legal_number = request.form.get("legal_number")
        customer.vat_number = request.form.get("vat_number")
        customer.email = request.form.get("email")
        customer.address_line1 = request.form.get("address_line1")
        customer.address_line2 = request.form.get("address_line2")
        customer.city = request.form.get("city")
        customer.state = request.form.get("state")
        customer.zipcode = request.form.get("zipcode")
        customer.country = request.form.get("country")
        customer.payment_terms = int(request.form.get("payment_terms") or 14)

        db.session.commit()
        flash(f"Customer '{customer.name}' updated successfully.", "success")
        return redirect(url_for("customers.list_customers"))

    return render_template("customers/form.html", customer=customer)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)

    if customer.invoices.count() > 0:
        flash(f"Cannot delete customer '{customer.name}' - has existing invoices.", "error")
        return redirect(url_for("customers.list_customers"))

    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    flash(f"Customer '{name}' deleted.", "success")
    return redirect(url_for("customers.list_customers"))


@bp.route("/<int:id>/json")
def get_customer_json(id):
    """API endpoint to get customer data for invoice form."""
    customer = Customer.query.get_or_404(id)
    return jsonify(customer.to_dict())
