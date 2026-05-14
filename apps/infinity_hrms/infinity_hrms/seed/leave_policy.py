"""Leave Period + Leave Policy + per-employee Leave Allocations.

Frappe HR needs three chained records before an employee has a leave
balance to apply against:
  1. Leave Period   — the calendar window (FY26-27 = 2026-04-01 → 2027-03-31)
  2. Leave Policy   — the allocation per leave type (12 CL, 12 SL, 21 EL)
  3. Leave Policy Assignment — connects employee + period + policy and
     auto-creates Leave Allocation records with actual balances.

Without these, "Apply Leave" shows 0 days available for every leave
type and demos look anemic.
"""

import frappe
from frappe.utils import getdate

from .company import COMPANY
from .holidays import HOLIDAY_LIST


PERIOD_TITLE = "FY 2026-27"            # informational only — Frappe autonames the record
POLICY_TITLE = "Standard India Leave Policy"
PERIOD_FROM  = "2026-04-01"
PERIOD_TO    = "2027-03-31"

POLICY_ALLOCATIONS = [
    # (leave_type, annual_days)
    ("Casual Leave", 12),
    ("Sick Leave",   12),
    ("Earned Leave", 21),
]


def _find_leave_period():
    """Return the auto-named Leave Period that matches our date range,
    or None if not yet created. Leave Period uses an HR-LPR-YYYY-NNNNN
    naming series, so we can't refer to it by a human title."""
    return frappe.db.get_value("Leave Period", {
        "from_date": PERIOD_FROM,
        "to_date":   PERIOD_TO,
        "company":   COMPANY,
    }, "name")


def _find_leave_policy():
    return frappe.db.get_value("Leave Policy", {"title": POLICY_TITLE}, "name")


def seed_leave_period():
    if _find_leave_period():
        return
    doc = frappe.new_doc("Leave Period")
    doc.from_date = PERIOD_FROM
    doc.to_date = PERIOD_TO
    doc.company = COMPANY
    doc.is_active = 1
    doc.insert(ignore_permissions=True)


def seed_leave_policy():
    if _find_leave_policy():
        return
    doc = frappe.new_doc("Leave Policy")
    doc.title = POLICY_TITLE
    doc.docstatus = 0
    for leave_type, days in POLICY_ALLOCATIONS:
        if not frappe.db.exists("Leave Type", leave_type):
            continue
        row = doc.append("leave_policy_details", {})
        row.leave_type = leave_type
        row.annual_allocation = days
    doc.insert(ignore_permissions=True)
    doc.submit()


def seed_policy_assignments():
    """For every active employee, assign the policy for the period.
    Frappe's Leave Policy Assignment auto-creates Leave Allocation
    records (one per leave type) for the date range — these are what
    populate the employee's balance ledger.

    Idempotent: skips employees who already have an assignment for the
    same period.
    """
    period_name = _find_leave_period()
    policy_name = _find_leave_policy()
    if not period_name or not policy_name:
        print(f"  ! cannot assign — period={period_name} policy={policy_name}")
        return
    print(f"→ Assigning leave policy {policy_name} for period {period_name}")
    employees = frappe.get_all("Employee", {"status": "Active"}, ["name", "date_of_joining"])
    created = 0
    for emp in employees:
        if frappe.db.exists("Leave Policy Assignment", {
            "employee": emp.name,
            "leave_policy": policy_name,
            "leave_period": period_name,
        }):
            continue
        doc = frappe.new_doc("Leave Policy Assignment")
        doc.employee = emp.name
        doc.assignment_based_on = "Leave Period"
        doc.leave_policy = policy_name
        doc.leave_period = period_name
        doj = getdate(emp.date_of_joining)
        period_start = getdate(PERIOD_FROM)
        doc.effective_from = max(doj, period_start)
        doc.effective_to = PERIOD_TO
        try:
            doc.insert(ignore_permissions=True)
            # submit() internally calls grant_leave_alloc_for_employee
            # which creates the Leave Allocation records — DON'T call it
            # again afterwards or you get a "Leave already assigned" error.
            doc.submit()
            created += 1
        except Exception as e:
            print(f"  ! {emp.name}: {e}")
    print(f"  ✓ {created} new policy assignments")


def seed_leave_setup():
    seed_leave_period()
    seed_leave_policy()
    seed_policy_assignments()
