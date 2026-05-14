"""Organizational structure — departments and designations."""

import frappe

from .company import COMPANY

DEPARTMENTS = [
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Customer Success",
    "Operations",
    "Finance",
    "Human Resources",
    "Legal",
]

DESIGNATIONS = [
    # Engineering ladder
    "Software Engineer",
    "Senior Software Engineer",
    "Staff Engineer",
    "Engineering Manager",
    "VP Engineering",
    # Product ladder
    "Associate Product Manager",
    "Product Manager",
    "Senior Product Manager",
    "Head of Product",
    # Design
    "UI Designer",
    "Senior UX Designer",
    "Design Lead",
    # GTM
    "Sales Development Rep",
    "Account Executive",
    "Account Manager",
    "Sales Director",
    "Marketing Executive",
    "Marketing Manager",
    "Content Lead",
    # CS / Ops
    "Customer Success Manager",
    "Operations Executive",
    "Operations Manager",
    # G&A
    "HR Executive",
    "HR Business Partner",
    "HR Manager",
    "Accountant",
    "Finance Manager",
    "Legal Counsel",
]


def seed_departments():
    """Frappe stores departments with the company abbr suffix:
    `Engineering - INX`. We pass `department_name` and let it derive."""
    for name in DEPARTMENTS:
        full = f"{name} - {frappe.db.get_value('Company', COMPANY, 'abbr')}"
        if frappe.db.exists("Department", full):
            continue
        doc = frappe.new_doc("Department")
        doc.department_name = name
        doc.company = COMPANY
        doc.is_group = 0
        doc.insert(ignore_permissions=True)


def seed_designations():
    for title in DESIGNATIONS:
        if frappe.db.exists("Designation", title):
            continue
        doc = frappe.new_doc("Designation")
        doc.designation_name = title
        doc.insert(ignore_permissions=True)
