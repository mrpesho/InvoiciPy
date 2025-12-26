from datetime import datetime, date
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    legal_name = db.Column(db.String(255))
    legal_number = db.Column(db.String(100))
    vat_number = db.Column(db.String(50))
    email = db.Column(db.String(255))
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    country = db.Column(db.String(100))
    payment_terms = db.Column(db.Integer, default=14)  # Days until due
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    invoices = db.relationship("Invoice", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "legal_name": self.legal_name,
            "legal_number": self.legal_number,
            "vat_number": self.vat_number,
            "email": self.email,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "zipcode": self.zipcode,
            "country": self.country,
            "payment_terms": self.payment_terms,
        }


class Invoice(db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=True)  # Null for drafts
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    template = db.Column(db.String(50), default="default")
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    delivery_date = db.Column(db.Date)
    due_date = db.Column(db.Date, nullable=False)
    currency = db.Column(db.String(3), default="EUR")
    exchange_rate = db.Column(db.Numeric(10, 6), default=1.0)  # Rate to EUR (1 USD = X EUR)
    notes = db.Column(db.Text)
    optional_texts = db.Column(db.JSON, default=list)
    status = db.Column(db.String(20), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship(
        "InvoiceItem", backref="invoice", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice {self.number or f'Draft #{self.id}'}>"

    @property
    def display_number(self):
        """Return invoice number or 'Draft #ID' for drafts."""
        return self.number if self.number else f"Draft #{self.id}"

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items)

    @property
    def tax_total(self):
        return sum(item.tax_amount for item in self.items)

    @property
    def total(self):
        return self.subtotal + self.tax_total

    @property
    def native_total(self):
        """Return total converted to native currency using the stored exchange rate."""
        rate = Decimal(str(self.exchange_rate)) if self.exchange_rate else Decimal("1")
        return self.total * rate

    def to_dict(self):
        return {
            "id": self.id,
            "number": self.number,
            "customer_id": self.customer_id,
            "template": self.template,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "delivery_date": self.delivery_date.isoformat() if self.delivery_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "currency": self.currency,
            "notes": self.notes,
            "optional_texts": self.optional_texts,
            "status": self.status,
        }


class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unit = db.Column(db.String(20), default="pcs")
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)
    position = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<InvoiceItem {self.description[:30]}>"

    @property
    def line_total(self):
        return Decimal(str(self.quantity)) * Decimal(str(self.unit_price))

    @property
    def tax_amount(self):
        return self.line_total * (Decimal(str(self.tax_rate)) / Decimal("100"))

    @property
    def total_with_tax(self):
        return self.line_total + self.tax_amount

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "description": self.description,
            "quantity": float(self.quantity),
            "unit": self.unit,
            "unit_price": float(self.unit_price),
            "tax_rate": float(self.tax_rate),
            "position": self.position,
            "line_total": float(self.line_total),
            "tax_amount": float(self.tax_amount),
        }


class OptionalText(db.Model):
    __tablename__ = "optional_texts"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    default_enabled = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<OptionalText {self.key}>"

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "label": self.label,
            "content": self.content,
            "default_enabled": self.default_enabled,
        }
