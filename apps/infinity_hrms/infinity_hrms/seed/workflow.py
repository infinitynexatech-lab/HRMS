"""Sample pending leave application.

Creates a leave request from Karthik (IC) to his manager Priya. Shows
up on Priya's approvals dashboard immediately on login — strongest
single moment to demo a manager workflow.

Requires:
  - seed_demo_users   (Karthik, Priya exist as users + linked to employees)
  - seed_hierarchy    (Karthik.reports_to = Priya)
  - seed_leave_setup  (Karthik has a Casual Leave allocation)
"""

import frappe
from frappe.utils import add_days, today


REQUESTER_EMAIL = "karthik.nair@infinitynexatech.com"
APPROVER_EMAIL  = "priya.iyer@infinitynexatech.com"
LEAVE_TYPE      = "Casual Leave"


def seed_pending_leave():
    emp = frappe.db.get_value("Employee", {"personal_email": REQUESTER_EMAIL}, "name")
    approver = frappe.db.get_value("Employee", {"personal_email": APPROVER_EMAIL}, ["name", "user_id"], as_dict=True)
    if not emp or not approver or not approver.user_id:
        print("  ! cannot create pending leave — employee or approver not linked")
        return

    # Set leave_approver on the requester so the application routes to Priya
    frappe.db.set_value("Employee", emp, "leave_approver", approver.user_id)

    from_d = add_days(today(), 7)
    to_d   = add_days(today(), 8)

    if frappe.db.exists("Leave Application", {
        "employee": emp,
        "from_date": from_d,
        "to_date": to_d,
        "leave_type": LEAVE_TYPE,
    }):
        print("  = pending leave already exists")
        return

    doc = frappe.new_doc("Leave Application")
    doc.employee = emp
    doc.leave_type = LEAVE_TYPE
    doc.from_date = from_d
    doc.to_date = to_d
    doc.half_day = 0
    doc.description = "Personal — friend's wedding"
    doc.leave_approver = approver.user_id
    doc.status = "Open"
    doc.posting_date = today()
    # Stay in draft so it shows as "Open / pending approval" on Priya's
    # dashboard. Submitting would mark it Applied or Approved.
    try:
        doc.insert(ignore_permissions=True)
        print(f"  ✓ pending leave: {REQUESTER_EMAIL} → {APPROVER_EMAIL} ({from_d} → {to_d})")
    except Exception as e:
        print(f"  ! pending leave: {e}")
