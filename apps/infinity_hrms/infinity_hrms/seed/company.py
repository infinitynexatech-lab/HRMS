"""Demo company — Infinity Nexatech Pvt Ltd.

On a fresh Frappe site (no setup wizard run), ERPNext's `Company`
doctype tries to auto-create Warehouses (Stores, Work in Progress,
etc.) and Accounts, which validate their `Warehouse Type` link
against fixtures normally installed by the setup wizard. Without
those fixtures the Company insert fails with:
    LinkValidationError: Could not find Warehouse Type: Transit
So we pre-create the Warehouse Type rows before the Company. Same
for other tiny ERPNext fixtures we rely on. All steps idempotent.
"""

import frappe

COMPANY = "Infinity Nexatech Pvt Ltd"
ABBR = "INX"

WAREHOUSE_TYPES = ["Default", "Transit", "Stores", "Work In Progress", "Finished Goods"]
GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
EMPLOYMENT_TYPES = ["Full-time", "Part-time", "Probation", "Contract", "Intern"]


def seed_company():
    _ensure_warehouse_types()
    _ensure_genders()
    _ensure_employment_types()
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


def _ensure_warehouse_types():
    for wh_type in WAREHOUSE_TYPES:
        if frappe.db.exists("Warehouse Type", wh_type):
            continue
        frappe.get_doc({
            "doctype": "Warehouse Type",
            "name": wh_type,
        }).insert(ignore_permissions=True)


def _ensure_genders():
    for g in GENDERS:
        if frappe.db.exists("Gender", g):
            continue
        frappe.get_doc({"doctype": "Gender", "gender": g}).insert(ignore_permissions=True)


def _ensure_employment_types():
    for t in EMPLOYMENT_TYPES:
        if frappe.db.exists("Employment Type", t):
            continue
        frappe.get_doc({
            "doctype": "Employment Type",
            "employee_type_name": t,
        }).insert(ignore_permissions=True)
