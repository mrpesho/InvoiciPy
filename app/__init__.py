from flask import Flask
from flask_migrate import Migrate
from config import Config
from app.models import db, OptionalText

__version__ = "0.1.0"

migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes import invoices, customers, settings

    app.register_blueprint(invoices.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(settings.bp)

    # Register main route
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("invoices.list_invoices"))

    with app.app_context():
        # Only seed if tables exist (after migrations have run)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if inspector.has_table("optional_texts"):
            _seed_default_optional_texts()

    return app


def _seed_default_optional_texts():
    defaults = [
        {
            "key": "vat_reverse_charge",
            "label": "VAT Reverse Charge",
            "content": "VAT reverse charge under Article 44 of VAT Directive 2006/112/ES.",
            "default_enabled": False,
        },
        {
            "key": "bank_details",
            "label": "Bank Details",
            "content": "Bank: {bank_name}\nIBAN: {iban}\nSWIFT: {swift}",
            "default_enabled": True,
        },
        {
            "key": "payment_terms",
            "label": "Payment Terms",
            "content": "Payment due within 14 days.",
            "default_enabled": True,
        },
    ]

    for text_data in defaults:
        existing = OptionalText.query.filter_by(key=text_data["key"]).first()
        if not existing:
            text = OptionalText(**text_data)
            db.session.add(text)

    db.session.commit()
