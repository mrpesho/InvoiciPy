from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.models import db, OptionalText

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/")
def index():
    optional_texts = OptionalText.query.all()
    company = {
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
    return render_template("settings/index.html", optional_texts=optional_texts, company=company)


@bp.route("/optional-texts/new", methods=["GET", "POST"])
def create_optional_text():
    if request.method == "POST":
        key = request.form["key"].strip().lower().replace(" ", "_")

        if OptionalText.query.filter_by(key=key).first():
            flash(f"Optional text with key '{key}' already exists.", "error")
            return render_template("settings/optional_text_form.html", text=None)

        text = OptionalText(
            key=key,
            label=request.form["label"],
            content=request.form["content"],
            default_enabled=request.form.get("default_enabled") == "on",
        )
        db.session.add(text)
        db.session.commit()
        flash(f"Optional text '{text.label}' created.", "success")
        return redirect(url_for("settings.index"))

    return render_template("settings/optional_text_form.html", text=None)


@bp.route("/optional-texts/<int:id>/edit", methods=["GET", "POST"])
def edit_optional_text(id):
    text = OptionalText.query.get_or_404(id)

    if request.method == "POST":
        text.label = request.form["label"]
        text.content = request.form["content"]
        text.default_enabled = request.form.get("default_enabled") == "on"

        db.session.commit()
        flash(f"Optional text '{text.label}' updated.", "success")
        return redirect(url_for("settings.index"))

    return render_template("settings/optional_text_form.html", text=text)


@bp.route("/optional-texts/<int:id>/delete", methods=["POST"])
def delete_optional_text(id):
    text = OptionalText.query.get_or_404(id)
    label = text.label
    db.session.delete(text)
    db.session.commit()
    flash(f"Optional text '{label}' deleted.", "success")
    return redirect(url_for("settings.index"))
