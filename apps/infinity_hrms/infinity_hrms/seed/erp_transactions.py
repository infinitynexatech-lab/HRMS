"""Sales invoices + purchase invoices + payment entries.

Sales: 8 invoices across last 90 days. Mix of states:
  - 5 submitted + paid (Payment Entry against HDFC bank account)
  - 2 submitted + outstanding
  - 1 draft (still being prepared)

Purchase: 4 invoices, all submitted + paid.

This gives Accounts Receivable / Payable a populated state for the
demo. Sales Invoice List, Customer Statement, Aging Report, P&L —
all become demoable.
"""

import random
from datetime import date, timedelta

import frappe
from frappe.utils import add_days, getdate, today, flt

from .company import COMPANY, ABBR


SALES_PLAN = [
    # (customer, days_ago, item_code, qty, paid)
    ("Aether Technologies Pvt Ltd",       72, "INX-HRMS-IMPL",   1, True),
    ("Sapphire Systems Limited",          61, "INX-CRM-IMPL",    1, True),
    ("Meridian Financial Services",       55, "INX-VOICE-AI",    1, True),
    ("Northstar Retail Ventures",         44, "INX-CUSTOM-DEV", 12, True),
    ("Pinnacle Healthcare Group",         38, "INX-AMC",         1, True),
    ("Crimson Coatings & Materials",      22, "INX-DATA-MIG",    1, False),  # outstanding
    ("Velocity Capital Partners",         18, "INX-CLOUD",       3, False),  # outstanding
    ("Cobalt Software Solutions",          5, "INX-HRMS-SUB",   12, None),   # draft
]


PURCHASE_PLAN = [
    # (supplier, days_ago, item_name, qty, rate)
    ("CloudCore Infrastructure",     65, "Cloud Infrastructure - Q1",       1,  85000),
    ("Quantum Workspace Tools",      42, "Annual SaaS Licenses",            1, 120000),
    ("Pebble Print & Stationery",    20, "Office Stationery & Print",       1,   8500),
    ("Horizon Travel Services",       9, "Team Offsite Travel",             1,  45000),
]


def _find_income_account():
    """Default Income / Sales account for the company."""
    for name in ["Sales", "Service", "Income"]:
        acc = frappe.db.get_value("Account", {
            "company": COMPANY,
            "account_name": ["like", f"%{name}%"],
            "is_group": 0,
            "root_type": "Income",
        }, "name")
        if acc:
            return acc
    return frappe.db.get_value("Account", {
        "company": COMPANY,
        "root_type": "Income",
        "is_group": 0,
    }, "name")


def _find_expense_account():
    return frappe.db.get_value("Account", {
        "company": COMPANY,
        "root_type": "Expense",
        "is_group": 0,
    }, "name")


def _find_debtors_account():
    return frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_type": "Receivable",
        "is_group": 0,
    }, "name")


def _find_creditors_account():
    return frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_type": "Payable",
        "is_group": 0,
    }, "name") or frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_name": "Creditors",
        "is_group": 0,
    }, "name")


def _bank_gl_account():
    return frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_type": "Bank",
        "is_group": 0,
    }, "name")


def _cost_center():
    return frappe.db.get_value("Cost Center", {
        "company": COMPANY,
        "cost_center_name": "Main",
    }, "name")


def seed_sales_invoices():
    print("→ Seeding sales invoices")
    income_account = _find_income_account()
    debtors = _find_debtors_account()
    bank = _bank_gl_account()
    cc = _cost_center()
    if not all([income_account, debtors, bank, cc]):
        print(f"  ! missing accounts: income={income_account} debtors={debtors} bank={bank} cc={cc}")
        return

    for customer_name, days_ago, item_code, qty, paid in SALES_PLAN:
        customer = frappe.db.get_value("Customer", {"customer_name": customer_name}, "name")
        if not customer:
            print(f"  ! customer not found: {customer_name}")
            continue
        if not frappe.db.exists("Item", item_code):
            print(f"  ! item not found: {item_code}")
            continue

        posting = add_days(today(), -days_ago)
        rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
        # Skip if we already have one for the same customer/posting/item
        if frappe.db.exists("Sales Invoice", {
            "customer": customer,
            "posting_date": posting,
            "docstatus": ["!=", 2],
        }):
            continue

        inv = frappe.new_doc("Sales Invoice")
        inv.customer = customer
        inv.company = COMPANY
        inv.posting_date = posting
        inv.due_date = add_days(posting, 30)
        inv.set_posting_time = 1
        inv.debit_to = debtors
        # Sales Invoice mandates a Selling Price List. ERPNext's
        # install_fixtures creates "Standard Selling" by default.
        inv.selling_price_list = "Standard Selling"
        inv.price_list_currency = "INR"
        inv.plc_conversion_rate = 1.0
        inv.currency = "INR"
        inv.conversion_rate = 1.0
        inv.append("items", {
            "item_code": item_code,
            "qty": qty,
            "rate": rate,
            "income_account": income_account,
            "cost_center": cc,
        })
        try:
            inv.insert(ignore_permissions=True)
            if paid is None:
                # leave as draft
                print(f"  ◯ draft   {customer_name[:30]:30} {item_code:14} ₹{rate*qty:,.0f}")
                continue
            inv.submit()
            label = "paid" if paid else "due "
            print(f"  ✓ {label}  {customer_name[:30]:30} {item_code:14} ₹{rate*qty:,.0f}")
            if paid:
                _record_payment_in(inv, bank, debtors, posting)
        except Exception as e:
            print(f"  ! {customer_name}: {e}")


def _record_payment_in(invoice, bank, debtors, invoice_date):
    """Create a Payment Entry that fully pays an outstanding sales invoice."""
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.company = COMPANY
    pe.posting_date = add_days(invoice_date, random.randint(3, 25))
    pe.mode_of_payment = "Bank Draft"
    pe.party_type = "Customer"
    pe.party = invoice.customer
    pe.paid_to = bank
    pe.paid_from = debtors
    pe.paid_amount = invoice.grand_total
    pe.received_amount = invoice.grand_total
    pe.reference_no = f"PMT-{invoice.name}"
    pe.reference_date = pe.posting_date
    pe.append("references", {
        "reference_doctype": "Sales Invoice",
        "reference_name": invoice.name,
        "total_amount": invoice.grand_total,
        "outstanding_amount": invoice.grand_total,
        "allocated_amount": invoice.grand_total,
    })
    try:
        pe.insert(ignore_permissions=True)
        pe.submit()
    except Exception as e:
        print(f"    ! Payment Entry for {invoice.name}: {e}")


def seed_purchase_invoices():
    print("→ Seeding purchase invoices", flush=True)
    expense_account = _find_expense_account()
    creditors = _find_creditors_account()
    bank = _bank_gl_account()
    cc = _cost_center()
    print(f"  resolved: expense={expense_account} creditors={creditors} bank={bank} cc={cc}", flush=True)
    if not all([expense_account, creditors, bank, cc]):
        print(f"  ! missing accounts", flush=True)
        return

    for supplier_name, days_ago, item_name, qty, rate in PURCHASE_PLAN:
        supplier = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
        if not supplier:
            print(f"  ! supplier not found: {supplier_name}")
            continue

        posting = add_days(today(), -days_ago)
        if frappe.db.exists("Purchase Invoice", {
            "supplier": supplier,
            "posting_date": posting,
            "docstatus": ["!=", 2],
        }):
            continue

        inv = frappe.new_doc("Purchase Invoice")
        inv.supplier = supplier
        inv.company = COMPANY
        inv.posting_date = posting
        inv.due_date = add_days(posting, 15)
        pd = getdate(posting)
        inv.bill_no = f"VEND-{supplier[:4].upper()}-{pd.month:02d}{pd.day:02d}"
        inv.bill_date = posting
        inv.set_posting_time = 1
        inv.credit_to = creditors
        inv.buying_price_list = "Standard Buying"
        inv.price_list_currency = "INR"
        inv.plc_conversion_rate = 1.0
        inv.currency = "INR"
        inv.conversion_rate = 1.0
        # Service-like item line — no Item code, just description + expense account
        inv.append("items", {
            "item_name": item_name,
            "description": item_name,
            "qty": qty,
            "rate": rate,
            "expense_account": expense_account,
            "cost_center": cc,
            "uom": "Nos",
        })
        try:
            inv.insert(ignore_permissions=True)
            inv.submit()
            print(f"  ✓ paid  {supplier_name[:30]:30} ₹{rate*qty:,.0f}", flush=True)
            _record_payment_out(inv, bank, creditors, posting)
        except Exception as e:
            import traceback
            print(f"  ! {supplier_name}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()


def _record_payment_out(invoice, bank, creditors, invoice_date):
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Pay"
    pe.company = COMPANY
    pe.posting_date = add_days(invoice_date, random.randint(2, 10))
    pe.mode_of_payment = "Bank Draft"
    pe.party_type = "Supplier"
    pe.party = invoice.supplier
    pe.paid_from = bank
    pe.paid_to = creditors
    pe.paid_amount = invoice.grand_total
    pe.received_amount = invoice.grand_total
    pe.reference_no = f"PMT-{invoice.name}"
    pe.reference_date = pe.posting_date
    pe.append("references", {
        "reference_doctype": "Purchase Invoice",
        "reference_name": invoice.name,
        "total_amount": invoice.grand_total,
        "outstanding_amount": invoice.grand_total,
        "allocated_amount": invoice.grand_total,
    })
    try:
        pe.insert(ignore_permissions=True)
        pe.submit()
    except Exception as e:
        print(f"    ! Payment Entry for {invoice.name}: {e}")


def seed_erp_transactions():
    # bench execute's PermissionError fallback path triggers a final
    # eval that NameError's, which propagates as an unhandled exception
    # — and Frappe rolls back the transaction on any unhandled exception
    # from a request. doc.submit() doesn't autocommit. Explicit commits
    # after each phase persist what we built.
    frappe.set_user("Administrator")
    random.seed(20260514)
    seed_sales_invoices()
    frappe.db.commit()
    seed_purchase_invoices()
    frappe.db.commit()
