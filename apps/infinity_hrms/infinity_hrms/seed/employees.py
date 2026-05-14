"""Sample employees + their Salary Structure Assignments.

20 realistic Indian-name employees across departments. Each gets:
  - Employee record with department, designation, joining date
  - Salary Structure Assignment with a base monthly CTC
"""

import frappe
from frappe.utils import getdate

from .company import COMPANY
from .holidays import HOLIDAY_LIST
from .payroll_india import STRUCTURE_NAME


# (first, last, gender, dept, designation, joining_date, base_ctc_per_month)
EMPLOYEES = [
    # Engineering
    ("Arjun",   "Sharma",     "Male",   "Engineering",      "VP Engineering",          "2024-01-15", 350000),
    ("Priya",   "Iyer",       "Female", "Engineering",      "Engineering Manager",     "2024-03-04", 220000),
    ("Rahul",   "Verma",      "Male",   "Engineering",      "Staff Engineer",          "2024-06-12", 180000),
    ("Sneha",   "Reddy",      "Female", "Engineering",      "Senior Software Engineer","2024-08-20", 140000),
    ("Karthik", "Nair",       "Male",   "Engineering",      "Software Engineer",       "2025-02-01",  90000),
    ("Ananya",  "Joshi",      "Female", "Engineering",      "Software Engineer",       "2025-04-15",  85000),
    # Product
    ("Vikram",  "Kapoor",     "Male",   "Product",          "Head of Product",         "2024-02-10", 280000),
    ("Meera",   "Pillai",     "Female", "Product",          "Senior Product Manager",  "2024-05-20", 200000),
    ("Aditya",  "Mehta",      "Male",   "Product",          "Product Manager",         "2024-09-01", 150000),
    # Design
    ("Riya",    "Khanna",     "Female", "Design",           "Design Lead",             "2024-04-08", 180000),
    ("Sahil",   "Bhatia",     "Male",   "Design",           "Senior UX Designer",      "2024-11-12", 120000),
    # Sales / Marketing
    ("Neha",    "Singh",      "Female", "Sales",            "Sales Director",          "2024-01-22", 240000),
    ("Rohan",   "Gupta",      "Male",   "Sales",            "Account Executive",       "2024-07-05",  95000),
    ("Pooja",   "Desai",      "Female", "Sales",            "Sales Development Rep",   "2025-01-10",  65000),
    ("Manish",  "Agarwal",    "Male",   "Marketing",        "Marketing Manager",       "2024-06-01", 160000),
    ("Tanya",   "Saxena",     "Female", "Marketing",        "Content Lead",            "2024-10-15", 110000),
    # CS / Ops / G&A
    ("Kavya",   "Krishnan",   "Female", "Customer Success", "Customer Success Manager","2024-08-12", 130000),
    ("Suresh",  "Patel",      "Male",   "Operations",       "Operations Manager",      "2024-03-25", 145000),
    ("Divya",   "Menon",      "Female", "Human Resources",  "HR Business Partner",     "2024-05-15", 150000),
    ("Amit",    "Choudhary",  "Male",   "Finance",          "Finance Manager",         "2024-02-28", 170000),
]


def _abbr():
    return frappe.db.get_value("Company", COMPANY, "abbr")


def _email(first, last):
    return f"{first.lower()}.{last.lower()}@infinitynexatech.com"


def seed_employees():
    abbr = _abbr()

    for first, last, gender, dept, designation, doj, _ctc in EMPLOYEES:
        email = _email(first, last)
        if frappe.db.exists("Employee", {"personal_email": email}):
            continue

        doc = frappe.new_doc("Employee")
        doc.first_name = first
        doc.last_name = last
        doc.employee_name = f"{first} {last}"
        doc.gender = gender
        doc.date_of_joining = getdate(doj)
        doc.date_of_birth = getdate("1992-01-01")  # placeholder
        doc.status = "Active"
        doc.company = COMPANY
        doc.department = f"{dept} - {abbr}"
        doc.designation = designation
        doc.holiday_list = HOLIDAY_LIST
        doc.personal_email = email
        doc.company_email = email
        doc.prefered_email = "Company Email"
        doc.prefered_contact_email = "Company Email"
        doc.employment_type = "Full-time"
        doc.insert(ignore_permissions=True)


def seed_salary_assignments():
    """Assign every employee to India Standard Structure with their CTC."""
    for first, last, _gender, _dept, _designation, doj, ctc in EMPLOYEES:
        email = _email(first, last)
        emp_id = frappe.db.get_value("Employee", {"personal_email": email}, "name")
        if not emp_id:
            continue

        # Skip if assignment already exists
        if frappe.db.exists("Salary Structure Assignment", {
            "employee": emp_id,
            "salary_structure": STRUCTURE_NAME,
        }):
            continue

        doc = frappe.new_doc("Salary Structure Assignment")
        doc.employee = emp_id
        doc.salary_structure = STRUCTURE_NAME
        doc.from_date = getdate(doj)
        doc.base = ctc
        doc.company = COMPANY
        doc.insert(ignore_permissions=True)
        doc.submit()
