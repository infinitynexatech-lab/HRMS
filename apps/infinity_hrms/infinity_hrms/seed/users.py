"""Demo login users mapped to existing employees.

Five personas covering the perspectives a buyer will want to see:
  - HR Lead          (HR Manager + HR User + Leave Approver + Employee)
  - Department Head  (Employee + Leave Approver + Expense Approver)
  - Team Manager     (Employee + Leave Approver)
  - Individual       (Employee — self-service portal only)
  - Recruiter        (Recruiter + Employee)

Each user is linked to an existing Employee record (via personal_email
match) so logging in lands on a real employee profile. Passwords are
intentionally memorable for demo use — not production-grade.

Idempotent — running twice updates passwords + roles to match the spec.
"""

import frappe


DEMO_USERS = [
    {
        "email": "divya.menon@infinitynexatech.com",
        "password": "DemoHR@2026",
        "roles": ["HR Manager", "HR User", "Leave Approver", "Employee"],
        "persona": "HR Lead",
    },
    {
        "email": "arjun.sharma@infinitynexatech.com",
        "password": "DemoVP@2026",
        "roles": ["Employee", "Leave Approver", "Expense Approver"],
        "persona": "Engineering VP",
    },
    {
        "email": "priya.iyer@infinitynexatech.com",
        "password": "DemoMgr@2026",
        "roles": ["Employee", "Leave Approver"],
        "persona": "Engineering Manager",
    },
    {
        "email": "karthik.nair@infinitynexatech.com",
        "password": "DemoEmp@2026",
        "roles": ["Employee"],
        "persona": "Software Engineer (IC)",
    },
    {
        # Frappe HR doesn't ship a standalone "Recruiter" role; recruitment
        # is gated by HR User + Interviewer (manage Job Openings/Applicants
        # + score interviews). Pairing here gives the persona realistic
        # ATS access without HR Manager's wider payroll/employee writes.
        "email": "tanya.saxena@infinitynexatech.com",
        "password": "DemoRec@2026",
        "roles": ["HR User", "Interviewer", "Employee"],
        "persona": "Recruiter / Content Lead",
    },
]


def seed_demo_users():
    print("→ Seeding demo users")
    for spec in DEMO_USERS:
        email = spec["email"]
        emp = frappe.db.get_value(
            "Employee",
            {"personal_email": email},
            ["name", "first_name", "last_name"],
            as_dict=True,
        )
        if not emp:
            print(f"  ! skip {email} — no Employee with that personal_email")
            continue

        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.new_doc("User")
            user.email = email
            user.send_welcome_email = 0

        user.first_name = emp.first_name
        user.last_name = emp.last_name
        user.user_type = "System User"
        user.enabled = 1
        user.language = "en"
        user.time_zone = "Asia/Kolkata"

        # Replace roles wholesale to match the spec (idempotent on re-run).
        user.set("roles", [])
        for role in spec["roles"]:
            user.append("roles", {"role": role})

        user.new_password = spec["password"]
        # Demo passwords are intentionally weak — bypass the policy.
        user.flags.ignore_password_policy = True
        user.save(ignore_permissions=True)

        # Link the User back to the Employee so /me lands on their profile
        # and self-service ("Apply Leave", "View Payslip") works.
        if frappe.db.get_value("Employee", emp.name, "user_id") != email:
            frappe.db.set_value("Employee", emp.name, "user_id", email)

        print(f"  ✓ {spec['persona']:25} {email}  /  {spec['password']}")
