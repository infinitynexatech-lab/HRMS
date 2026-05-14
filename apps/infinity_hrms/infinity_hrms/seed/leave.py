"""Leave Types — standard Indian SME policy.

Leave allocation actually happens via `Leave Policy` + `Leave Policy
Assignment`, but having the `Leave Type` records is the prerequisite.
"""

import frappe

LEAVE_TYPES = [
    # (name, allocation_days, is_carry_forward, is_lwp)
    ("Casual Leave",       12, True,  False),
    ("Sick Leave",         12, True,  False),
    ("Earned Leave",       21, True,  False),
    ("Maternity Leave",   182, False, False),
    ("Paternity Leave",     5, False, False),
    ("Compensatory Off",    0, False, False),
    ("Leave Without Pay",   0, False, True),
]


def seed_leave_types():
    for name, allocation, carry, lwp in LEAVE_TYPES:
        if frappe.db.exists("Leave Type", name):
            continue
        doc = frappe.new_doc("Leave Type")
        doc.leave_type_name = name
        doc.max_leaves_allowed = allocation
        doc.is_carry_forward = 1 if carry else 0
        doc.is_lwp = 1 if lwp else 0
        doc.applicable_after_work_days = 0
        doc.insert(ignore_permissions=True)
