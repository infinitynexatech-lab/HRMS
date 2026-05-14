"""Demo company — Infinity Nexatech Pvt Ltd."""

import frappe

COMPANY = "Infinity Nexatech Pvt Ltd"
ABBR = "INX"


def seed_company():
    if frappe.db.exists("Company", COMPANY):
        return
    doc = frappe.new_doc("Company")
    doc.company_name = COMPANY
    doc.abbr = ABBR
    doc.default_currency = "INR"
    doc.country = "India"
    doc.create_chart_of_accounts_based_on = "Standard Template"
    doc.chart_of_accounts = "Standard"
    doc.domain = "Services"
    doc.insert(ignore_permissions=True)
