"""Reporting hierarchy — sets reports_to on existing Employee records.

Without this, every employee reports to nobody and the Org Chart
dashboard shows a flat list instead of a tree. With it, the chart
populates and manager-flow demos (leave approval, team analytics)
have realistic structure.
"""

import frappe


# email_of_employee → email_of_their_manager (None = top of tree)
HIERARCHY = {
    # Engineering
    "arjun.sharma@infinitynexatech.com":    None,
    "priya.iyer@infinitynexatech.com":      "arjun.sharma@infinitynexatech.com",
    "rahul.verma@infinitynexatech.com":     "priya.iyer@infinitynexatech.com",
    "sneha.reddy@infinitynexatech.com":     "priya.iyer@infinitynexatech.com",
    "karthik.nair@infinitynexatech.com":    "priya.iyer@infinitynexatech.com",
    "ananya.joshi@infinitynexatech.com":    "priya.iyer@infinitynexatech.com",

    # Product
    "vikram.kapoor@infinitynexatech.com":   None,
    "meera.pillai@infinitynexatech.com":    "vikram.kapoor@infinitynexatech.com",
    "aditya.mehta@infinitynexatech.com":    "vikram.kapoor@infinitynexatech.com",

    # Design (rolls up to Product)
    "riya.khanna@infinitynexatech.com":     "vikram.kapoor@infinitynexatech.com",
    "sahil.bhatia@infinitynexatech.com":    "riya.khanna@infinitynexatech.com",

    # Sales
    "neha.singh@infinitynexatech.com":      None,
    "rohan.gupta@infinitynexatech.com":     "neha.singh@infinitynexatech.com",
    "pooja.desai@infinitynexatech.com":     "rohan.gupta@infinitynexatech.com",

    # Marketing (rolls up to Sales)
    "manish.agarwal@infinitynexatech.com":  "neha.singh@infinitynexatech.com",
    "tanya.saxena@infinitynexatech.com":    "manish.agarwal@infinitynexatech.com",

    # CS / Ops / G&A — all department heads, no further structure
    "kavya.krishnan@infinitynexatech.com":  None,
    "suresh.patel@infinitynexatech.com":    None,
    "divya.menon@infinitynexatech.com":     None,
    "amit.choudhary@infinitynexatech.com":  None,
}


def seed_hierarchy():
    print("→ Wiring reporting hierarchy")
    set_count = 0
    for emp_email, mgr_email in HIERARCHY.items():
        emp_name = frappe.db.get_value("Employee", {"personal_email": emp_email}, "name")
        if not emp_name:
            continue
        if mgr_email is None:
            mgr_name = None
        else:
            mgr_name = frappe.db.get_value("Employee", {"personal_email": mgr_email}, "name")
            if not mgr_name:
                print(f"  ! {emp_email} → manager {mgr_email} not found")
                continue
        current = frappe.db.get_value("Employee", emp_name, "reports_to")
        if current != mgr_name:
            frappe.db.set_value("Employee", emp_name, "reports_to", mgr_name)
            set_count += 1
    print(f"  ✓ updated {set_count} reports_to fields")
