"""Process payroll for the previous calendar month.

Creates one Payroll Entry for the previous month + auto-generates
Salary Slips for every Active employee in the Company. After this,
every employee has a payslip to view, with Basic/HRA/Special and EPF/
ESIC/PT/TDS deductions calculated from the salary structure.
"""

import frappe
from frappe.utils import getdate, get_first_day, get_last_day, add_months, today

from .company import COMPANY, ABBR


def _ensure_payable_account():
    """Find OR create a Payable account suitable for Payroll Entry.

    ERPNext's standard chart already creates 'Payroll Payable - <ABBR>'
    when a Company with Domain=Services is set up — submitted Salary
    Structure Assignments auto-default to this account. Prefer it.
    Fall back to any leaf Payable account in the company. Create a
    'Salary Payable' under 'Current Liabilities' only as last resort.
    """
    # Most likely path: the account already exists from CoA setup.
    existing = frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_name": "Payroll Payable",
        "is_group": 0,
    }, "name")
    if existing:
        return existing

    # Any other leaf Payable account in this company.
    any_payable = frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_type": "Payable",
        "is_group": 0,
    }, "name")
    if any_payable:
        return any_payable

    # Last resort: create one.
    parent = frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_name": ["in", ["Accounts Payable", "Current Liabilities"]],
        "is_group": 1,
    }, "name")
    if not parent:
        return None
    doc = frappe.new_doc("Account")
    doc.account_name = "Salary Payable"
    doc.account_type = "Payable"
    doc.account_currency = "INR"
    doc.parent_account = parent
    doc.company = COMPANY
    doc.is_group = 0
    doc.insert(ignore_permissions=True)
    return doc.name


def _default_cost_center():
    """Prefer the company's main cost center."""
    return frappe.db.get_value("Cost Center", {
        "company": COMPANY,
        "cost_center_name": "Main",
    }, "name") or frappe.db.get_value("Company", COMPANY, "cost_center")


def _previous_month_range():
    """Returns (start, end) for the calendar month BEFORE today."""
    first_of_this_month = get_first_day(today())
    last_of_prev_month  = get_last_day(add_months(first_of_this_month, -1))
    first_of_prev_month = get_first_day(last_of_prev_month)
    return first_of_prev_month, last_of_prev_month


def _ensure_fiscal_year_for(start, end):
    """ERPNext's Salary Slip validate hook looks up an active Fiscal Year
    covering posting_date. Indian FY runs April → March. Auto-create if
    none of the existing FYs cover our payroll period."""
    covering = frappe.db.sql("""
        SELECT name FROM `tabFiscal Year`
        WHERE %s BETWEEN year_start_date AND year_end_date
          AND (disabled IS NULL OR disabled = 0)
        LIMIT 1
    """, (start,))
    if covering:
        return covering[0][0]

    # Derive FY name: April → March → "FY YYYY-YY"
    start_d = getdate(start)
    if start_d.month >= 4:
        fy_start_year = start_d.year
    else:
        fy_start_year = start_d.year - 1
    fy_name = f"FY {fy_start_year}-{str(fy_start_year+1)[-2:]}"
    fy_start = f"{fy_start_year}-04-01"
    fy_end   = f"{fy_start_year+1}-03-31"

    if frappe.db.exists("Fiscal Year", fy_name):
        return fy_name

    doc = frappe.new_doc("Fiscal Year")
    doc.year = fy_name
    doc.year_start_date = fy_start
    doc.year_end_date = fy_end
    # Frappe child table: companies — link this FY to our Company so
    # the Company-scoped FY lookup picks it up.
    doc.append("companies", {"company": COMPANY})
    doc.insert(ignore_permissions=True)
    return fy_name


def seed_payroll_run():
    # bench execute runs with frappe.session.user = the OS user (often
    # not a privileged Frappe user). Payroll Entry's child-table population
    # path goes through permission match_conditions for Employee records,
    # which can silently return 0 rows for a non-System user. Set the
    # session user to Administrator for the duration of this seed.
    frappe.set_user("Administrator")

    start, end = _previous_month_range()
    print(f"→ Running payroll for {start} → {end}")

    fy = _ensure_fiscal_year_for(start, end)
    print(f"  • fiscal year: {fy}")

    # If a Payroll Entry for this exact window already exists, skip
    existing = frappe.db.exists("Payroll Entry", {
        "company": COMPANY,
        "start_date": start,
        "end_date": end,
    })
    if existing:
        print(f"  = payroll entry already exists ({existing})")
        return

    payable_account = _ensure_payable_account()
    cost_center     = _default_cost_center()
    if not payable_account or not cost_center:
        print(f"  ! missing accounting setup: payable={payable_account} cc={cost_center}")
        return

    # Backfill payroll_payable_account on every existing SSA — Payroll
    # Entry's get_filtered_employees filters by SSA.payroll_payable_account
    # == PE.payroll_payable_account. SSAs created before the payable
    # account existed have NULL here and silently get excluded ("no
    # employees found"). One-time idempotent UPDATE.
    # Count first (before the UPDATE) so we can log how many needed it.
    stale = frappe.db.count("Salary Structure Assignment", {
        "company": COMPANY,
        "payroll_payable_account": ["in", [None, ""]],
    })
    if stale:
        frappe.db.sql("""
            UPDATE `tabSalary Structure Assignment`
            SET payroll_payable_account = %s
            WHERE company = %s
              AND (payroll_payable_account IS NULL OR payroll_payable_account = '')
        """, (payable_account, COMPANY))
        print(f"  • backfilled payable account on {stale} SSA rows")

    # Match the UI flow exactly:
    #   1. insert as draft (no employees yet — allowed)
    #   2. fill_employee_details populates the .employees child table by
    #      querying SSAs that match company/currency/frequency/payable
    #   3. save the populated draft
    #   4. submit (validates non-empty + locks)
    #   5. create_salary_slips, then submit_salary_slips
    doc = frappe.new_doc("Payroll Entry")
    doc.update({
        "company": COMPANY,
        "posting_date": end,
        "start_date": start,
        "end_date": end,
        "payroll_frequency": "Monthly",
        "currency": "INR",
        "payroll_payable_account": payable_account,
        "cost_center": cost_center,
        "exchange_rate": 1.0,
        "salary_slip_based_on_timesheet": 0,
    })

    try:
        doc.insert(ignore_permissions=True)
        # Commit the insert so subsequent code that refetches the doc by
        # name finds it. fill_employee_details/save/submit all rely on
        # the record existing in the DB.
        frappe.db.commit()
        doc.fill_employee_details()
        n = len(doc.employees or [])
        if n == 0:
            print(f"  ! fill_employee_details returned 0 employees — check SSA filters")
            return
        print(f"  • {n} employees added to entry")
        doc.save(ignore_permissions=True)
        doc.submit()
        print(f"  ✓ payroll entry {doc.name} submitted with {n} employees")
    except Exception as e:
        print(f"  ! payroll entry insert/submit failed: {e}")
        import traceback; traceback.print_exc()
        return

    # Generate Salary Slips
    try:
        doc.create_salary_slips()
        doc.submit_salary_slips()
        slips = frappe.db.count("Salary Slip", {"payroll_entry": doc.name})
        print(f"  ✓ {slips} salary slips created + submitted")
    except Exception as e:
        print(f"  ! salary slip generation: {e}")
