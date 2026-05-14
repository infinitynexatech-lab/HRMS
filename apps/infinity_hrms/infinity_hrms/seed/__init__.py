"""Infinity HRMS — India payroll demo seed.

Run from inside the backend container:
    bench --site hrms.infinitynexatech.com execute infinity_hrms.seed.run_all

Idempotent: every helper checks for existing records before creating.
Safe to re-run after a redeploy.
"""

import frappe

from .company import seed_company
from .holidays import seed_holiday_list
from .departments import seed_departments, seed_designations
from .leave import seed_leave_types
from .payroll_india import seed_salary_components_india, seed_salary_structure_india
from .employees import seed_employees, seed_salary_assignments
from .users import seed_demo_users


COMPANY = "Infinity Nexatech Pvt Ltd"
COMPANY_ABBR = "INX"
SALARY_STRUCTURE = "India Standard Structure"


def run_all():
    """One-shot demo seed: company → calendar → org → policies → people."""
    seed_company()
    seed_holiday_list()
    seed_departments()
    seed_designations()
    seed_leave_types()
    seed_salary_components_india()
    seed_salary_structure_india()
    seed_employees()
    seed_salary_assignments()
    seed_demo_users()
    frappe.db.commit()
    print("✓ Infinity HRMS demo seed complete")
