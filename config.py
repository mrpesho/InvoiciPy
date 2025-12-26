import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{os.path.join(basedir, 'invoicing.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Your company details (shown on invoices)
    COMPANY_NAME = os.environ.get("COMPANY_NAME", "Your Company Name")
    COMPANY_LEGAL_NAME = os.environ.get("COMPANY_LEGAL_NAME", "Your Company Ltd.")
    COMPANY_LEGAL_NUMBER = os.environ.get("COMPANY_LEGAL_NUMBER", "")
    COMPANY_ADDRESS = os.environ.get("COMPANY_ADDRESS", "123 Main Street")
    COMPANY_CITY = os.environ.get("COMPANY_CITY", "City")
    COMPANY_ZIPCODE = os.environ.get("COMPANY_ZIPCODE", "12345")
    COMPANY_COUNTRY = os.environ.get("COMPANY_COUNTRY", "Country")
    COMPANY_VAT_NUMBER = os.environ.get("COMPANY_VAT_NUMBER", "XX123456789")
    COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "billing@example.com")
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")
    COMPANY_BANK_NAME = os.environ.get("COMPANY_BANK_NAME", "Bank Name")
    COMPANY_IBAN = os.environ.get("COMPANY_IBAN", "XX00 0000 0000 0000 0000 00")
    COMPANY_SWIFT = os.environ.get("COMPANY_SWIFT", "XXXXXX00")

    # Native currency for accounting (exchange rates convert to this)
    NATIVE_CURRENCY = os.environ.get("NATIVE_CURRENCY", "EUR")
