"""India payroll — Salary Components and Salary Structure.

Implements the standard private-sector pay structure:
  Earnings:    Basic + HRA + Special Allowance
  Deductions:  EPF (employee) + ESIC (employee, conditional) + PT + TDS
  Statistical: EPF Employer + ESIC Employer (employer cost, not paid)

EPF rules:
  - Employee contribution: 12% of Basic, capped at 12% of ₹15,000 = ₹1,800
  - Employer contribution: 12% of Basic (split EPS 8.33% + EPF 3.67%)

ESIC rules:
  - Applies when gross monthly wage ≤ ₹21,000
  - Employee: 0.75% of gross
  - Employer: 3.25% of gross

Professional Tax: state-specific. We use ₹200/month (typical for
Maharashtra/Karnataka). Adjust per Company state of registration.

TDS: handled via Income Tax Slab — Frappe computes automatically when
the salary structure marks the component as variable_based_on_taxable_salary.
"""

import frappe

from .company import COMPANY

STRUCTURE_NAME = "India Standard Structure"
PT_AMOUNT = 200  # ₹/month — adjust per state
EPF_BASIC_CAP = 15000
ESIC_GROSS_CAP = 21000


COMPONENTS = [
    # Earnings (in base pay)
    {
        "name": "Basic",
        "abbr": "B",
        "type": "Earning",
        "amount_based_on_formula": 1,
        "formula": "base * 0.50",
        "depends_on_payment_days": 1,
        "is_tax_applicable": 1,
    },
    {
        "name": "House Rent Allowance",
        "abbr": "HRA",
        "type": "Earning",
        "amount_based_on_formula": 1,
        "formula": "B * 0.40",
        "depends_on_payment_days": 1,
        "is_tax_applicable": 1,
    },
    {
        "name": "Special Allowance",
        "abbr": "SA",
        "type": "Earning",
        "amount_based_on_formula": 1,
        "formula": "base - B - HRA",
        "depends_on_payment_days": 1,
        "is_tax_applicable": 1,
    },
    # Deductions (paid out of gross)
    {
        "name": "EPF Employee",
        "abbr": "EPF_EE",
        "type": "Deduction",
        "amount_based_on_formula": 1,
        "formula": f"min(B, {EPF_BASIC_CAP}) * 0.12",
        "depends_on_payment_days": 0,
    },
    {
        "name": "ESIC Employee",
        "abbr": "ESIC_EE",
        "type": "Deduction",
        "amount_based_on_formula": 1,
        "formula": f"((gross_pay <= {ESIC_GROSS_CAP}) and (gross_pay * 0.0075) or 0)",
        "depends_on_payment_days": 0,
    },
    {
        "name": "Professional Tax",
        "abbr": "PT",
        "type": "Deduction",
        "amount_based_on_formula": 0,
        "amount": PT_AMOUNT,
        "depends_on_payment_days": 0,
    },
    {
        "name": "TDS",
        "abbr": "TDS",
        "type": "Deduction",
        "variable_based_on_taxable_salary": 1,
        "is_income_tax_component": 1,
        "deduct_full_tax_on_selected_payroll_date": 0,
    },
    # Statistical (employer side — tracked but not in net pay)
    {
        "name": "EPF Employer",
        "abbr": "EPF_ER",
        "type": "Earning",
        "amount_based_on_formula": 1,
        "formula": f"min(B, {EPF_BASIC_CAP}) * 0.12",
        "statistical_component": 1,
        "do_not_include_in_total": 1,
    },
    {
        "name": "ESIC Employer",
        "abbr": "ESIC_ER",
        "type": "Earning",
        "amount_based_on_formula": 1,
        "formula": f"((gross_pay <= {ESIC_GROSS_CAP}) and (gross_pay * 0.0325) or 0)",
        "statistical_component": 1,
        "do_not_include_in_total": 1,
    },
]


def seed_salary_components_india():
    for spec in COMPONENTS:
        name = spec["name"]
        if frappe.db.exists("Salary Component", name):
            continue
        doc = frappe.new_doc("Salary Component")
        doc.salary_component = name
        doc.salary_component_abbr = spec["abbr"]
        doc.type = spec["type"]
        for key, value in spec.items():
            if key in {"name", "abbr", "type"}:
                continue
            if hasattr(doc, key):
                setattr(doc, key, value)
        doc.insert(ignore_permissions=True)


def seed_salary_structure_india():
    if frappe.db.exists("Salary Structure", STRUCTURE_NAME):
        return

    doc = frappe.new_doc("Salary Structure")
    doc.name = STRUCTURE_NAME
    doc.company = COMPANY
    doc.currency = "INR"
    doc.payroll_frequency = "Monthly"
    doc.is_active = "Yes"

    # Earnings rows
    for name in ["Basic", "House Rent Allowance", "Special Allowance",
                 "EPF Employer", "ESIC Employer"]:
        row = doc.append("earnings", {})
        row.salary_component = name

    # Deduction rows
    for name in ["EPF Employee", "ESIC Employee", "Professional Tax", "TDS"]:
        row = doc.append("deductions", {})
        row.salary_component = name

    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True)
    doc.submit()
