"""Past 30 days of attendance for every active employee.

Marks Present for all working days (Mon-Sat) and skips Sunday (the
weekly off in our seeded Holiday List). Random ~5% of slots become
"Half Day" or "On Leave" so reports don't look too clean.

Without this, the Attendance dashboard and reports are empty — no
demo of headcount/utilization/punctuality is possible.
"""

import random
from datetime import timedelta

import frappe
from frappe.utils import getdate, add_days, today


DAYS_BACK = 30
WORKING_DAYS = {0, 1, 2, 3, 4, 5}   # Mon-Sat (0 = Monday in Python)
WEEKLY_OFF   = 6                    # Sunday

# Realistic noise — small fraction of days off
HALF_DAY_PROB = 0.03
LEAVE_PROB    = 0.02


def seed_attendance():
    print("→ Marking past 30 days of attendance")
    rng = random.Random(20260514)   # deterministic so reruns are stable
    employees = frappe.get_all(
        "Employee",
        {"status": "Active"},
        ["name", "company", "date_of_joining"],
    )
    end = getdate(today())
    start = add_days(end, -DAYS_BACK)

    created = 0
    for emp in employees:
        doj = getdate(emp.date_of_joining)
        cursor = max(start, doj)
        while cursor <= end:
            if cursor.weekday() == WEEKLY_OFF:
                cursor += timedelta(days=1)
                continue
            if cursor.weekday() not in WORKING_DAYS:
                cursor += timedelta(days=1)
                continue
            if frappe.db.exists("Attendance", {"employee": emp.name, "attendance_date": cursor}):
                cursor += timedelta(days=1)
                continue

            r = rng.random()
            if r < LEAVE_PROB:
                status = "On Leave"
            elif r < LEAVE_PROB + HALF_DAY_PROB:
                status = "Half Day"
            else:
                status = "Present"

            doc = frappe.new_doc("Attendance")
            doc.employee = emp.name
            doc.attendance_date = cursor
            doc.status = status
            doc.company = emp.company
            try:
                doc.insert(ignore_permissions=True)
                doc.submit()
                created += 1
            except Exception as e:
                # likely "Attendance already marked" — fine
                pass
            cursor += timedelta(days=1)

    print(f"  ✓ {created} attendance records inserted")
