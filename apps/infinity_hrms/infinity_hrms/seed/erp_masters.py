"""ERP master data — Items, Customers, Suppliers, Bank Account, GST tax template.

Prereqs already in place from the base seed:
  - Company "Infinity Nexatech Pvt Ltd" with Standard CoA
  - Cost Centers, Warehouse Types, Fiscal Year FY 2026-27
  - Default Item Group / Customer Group / Supplier Group / Territory

We add fictional Indian company names (NOT real trademarks) so the
sales/CRM modules look populated without endorsement risk.
"""

import frappe

from .company import COMPANY, ABBR


# ── Items: services Infinity Nexatech sells ──────────────────────────
# All non-stock (services). is_sales_item = 1, is_purchase_item = 0.
ITEMS = [
    {"code": "INX-CRM-IMPL",    "name": "Infinity CRM — Implementation",     "rate": 250000,  "group": "Services"},
    {"code": "INX-HRMS-IMPL",   "name": "Infinity HRMS — Implementation",    "rate": 300000,  "group": "Services"},
    {"code": "INX-HRMS-SUB",    "name": "Infinity HRMS — Subscription / mo", "rate":  15000,  "group": "Services"},
    {"code": "INX-CUSTOM-DEV",  "name": "Custom Software Development / day", "rate":  18000,  "group": "Services"},
    {"code": "INX-CLOUD",       "name": "Cloud Hosting & DevOps / mo",       "rate":  35000,  "group": "Services"},
    {"code": "INX-AMC",         "name": "Annual Maintenance Contract",       "rate": 180000,  "group": "Services"},
    {"code": "INX-VOICE-AI",    "name": "Voice AI Agent — Setup",            "rate": 450000,  "group": "Services"},
    {"code": "INX-DATA-MIG",    "name": "Data Migration Service",            "rate":  85000,  "group": "Services"},
]

# Customer Group will fall back to "Commercial" if our preferred group isn't there.
CUSTOMERS = [
    # (name, industry/territory, gstin — fictional, payment_terms)
    ("Aether Technologies Pvt Ltd",       "India", "27AAACA0001Z1Z5"),
    ("Sapphire Systems Limited",          "India", "29AAACS1001Z2Z6"),
    ("Meridian Financial Services",       "India", "07AAACM2001Z3Z7"),
    ("Northstar Retail Ventures",         "India", "27AAACN3001Z4Z8"),
    ("Pinnacle Healthcare Group",         "India", "06AAACP4001Z5Z9"),
    ("Crimson Coatings & Materials",      "India", "24AAACC5001Z6Z0"),
    ("Velocity Capital Partners",         "India", "29AAACV6001Z7Z1"),
    ("Indus Manufacturing Co",            "India", "27AAACI7001Z8Z2"),
    ("Cobalt Software Solutions",         "India", "33AAACC8001Z9Z3"),
    ("Ranger Logistics India",            "India", "27AAACR9001Z0Z4"),
    ("Crescent Mobility Pvt Ltd",         "India", "29AAACC0001Z1Z5"),
    ("Banyan Hospitality Group",          "India", "07AAACB1001Z2Z6"),
]

SUPPLIERS = [
    ("CloudCore Infrastructure",     "India"),
    ("Quantum Workspace Tools",      "India"),
    ("Steelarm Office Supplies",     "India"),
    ("Pebble Print & Stationery",    "India"),
    ("Horizon Travel Services",      "India"),
]


# ── Tax template: India GST 18% (CGST 9% + SGST 9%) ──────────────────
GST_TEMPLATE = "GST 18% (intra-state) - " + ABBR


def _default_customer_group():
    return frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "All Customer Groups"


def _default_supplier_group():
    return frappe.db.get_value("Supplier Group", {"is_group": 0}, "name") or "All Supplier Groups"


def _default_item_group():
    """Frappe HR's Item Group tree starts with 'All Item Groups' (group)
    and 'Services' (leaf) — both auto-created. If neither, fall back to
    whatever non-group ItemGroup exists."""
    return frappe.db.get_value("Item Group", {"item_group_name": "Services"}, "name") \
        or frappe.db.get_value("Item Group", {"is_group": 0}, "name") \
        or "Services"


def seed_items():
    print("→ Seeding items")
    item_group = _default_item_group()
    for spec in ITEMS:
        if frappe.db.exists("Item", spec["code"]):
            continue
        doc = frappe.new_doc("Item")
        doc.item_code = spec["code"]
        doc.item_name = spec["name"]
        doc.item_group = item_group
        doc.stock_uom = "Nos"
        doc.is_stock_item = 0
        doc.is_sales_item = 1
        doc.is_purchase_item = 0
        doc.is_service_item = 1
        doc.include_item_in_manufacturing = 0
        doc.standard_rate = spec["rate"]
        doc.description = spec["name"]
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {spec['code']}  ₹{spec['rate']:,.0f}  {spec['name']}")
        except Exception as e:
            print(f"  ! {spec['code']}: {e}")


def seed_customers():
    print("→ Seeding customers")
    cg = _default_customer_group()
    for name, territory, gstin in CUSTOMERS:
        if frappe.db.exists("Customer", {"customer_name": name}):
            continue
        doc = frappe.new_doc("Customer")
        doc.customer_name = name
        doc.customer_type = "Company"
        doc.customer_group = cg
        doc.territory = territory if frappe.db.exists("Territory", territory) else "All Territories"
        doc.gstin = gstin
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ! {name}: {e}")


def seed_suppliers():
    print("→ Seeding suppliers")
    sg = _default_supplier_group()
    for name, country in SUPPLIERS:
        if frappe.db.exists("Supplier", {"supplier_name": name}):
            continue
        doc = frappe.new_doc("Supplier")
        doc.supplier_name = name
        doc.supplier_type = "Company"
        doc.supplier_group = sg
        doc.country = country
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ! {name}: {e}")


def seed_gst_tax_template():
    """Sales Taxes and Charges Template for India GST 18% intra-state.
    Charges CGST 9% + SGST 9% on the net total."""
    if frappe.db.exists("Sales Taxes and Charges Template", GST_TEMPLATE):
        return

    # Look up the system-default CGST / SGST accounts created with the
    # chart of accounts. Fall back to creating placeholders if missing.
    def _tax_account(account_name):
        return frappe.db.get_value("Account", {
            "company": COMPANY,
            "account_name": account_name,
            "is_group": 0,
        }, "name")

    cgst = _tax_account("Output Tax CGST") or _tax_account("CGST")
    sgst = _tax_account("Output Tax SGST") or _tax_account("SGST")
    if not cgst or not sgst:
        print(f"  ! GST accounts missing — cgst={cgst} sgst={sgst}, skipping tax template")
        return

    doc = frappe.new_doc("Sales Taxes and Charges Template")
    doc.title = GST_TEMPLATE
    doc.company = COMPANY
    doc.append("taxes", {
        "charge_type": "On Net Total",
        "account_head": cgst,
        "description": "CGST 9%",
        "rate": 9,
    })
    doc.append("taxes", {
        "charge_type": "On Net Total",
        "account_head": sgst,
        "description": "SGST 9%",
        "rate": 9,
    })
    try:
        doc.insert(ignore_permissions=True)
        print(f"  ✓ {GST_TEMPLATE}")
    except Exception as e:
        print(f"  ! GST template: {e}")


def _ensure_mode_of_payment():
    """Mode of Payment 'Bank Draft' / 'Wire Transfer' — needed for
    Payment Entries. Defaults usually exist."""
    if not frappe.db.exists("Mode of Payment", "Bank Draft"):
        doc = frappe.new_doc("Mode of Payment")
        doc.mode_of_payment = "Bank Draft"
        doc.type = "Bank"
        doc.insert(ignore_permissions=True)


def seed_bank_account():
    """Create a Bank + Bank Account so Payment Entries have somewhere
    to land. Bank Account in ERPNext requires a corresponding Account
    in the chart of accounts (Asset, Bank type)."""
    print("→ Seeding bank account")
    bank_name = "HDFC Bank"
    if not frappe.db.exists("Bank", bank_name):
        b = frappe.new_doc("Bank")
        b.bank_name = bank_name
        b.insert(ignore_permissions=True)

    # Find or create the GL account
    parent = frappe.db.get_value("Account", {
        "company": COMPANY,
        "account_name": "Bank Accounts",
        "is_group": 1,
    }, "name")
    if not parent:
        print("  ! 'Bank Accounts' group not found in CoA")
        return

    gl_account_name = f"HDFC Bank - {ABBR}"
    if not frappe.db.exists("Account", gl_account_name):
        a = frappe.new_doc("Account")
        a.account_name = "HDFC Bank"
        a.account_type = "Bank"
        a.account_currency = "INR"
        a.parent_account = parent
        a.company = COMPANY
        a.is_group = 0
        a.insert(ignore_permissions=True)

    bank_account_label = "HDFC Bank — Current Account"
    if not frappe.db.exists("Bank Account", {"account_name": bank_account_label}):
        ba = frappe.new_doc("Bank Account")
        ba.account_name = bank_account_label
        ba.bank = bank_name
        ba.account = gl_account_name
        ba.account_number = "50100123456789"
        ba.branch_code = "HDFC0001234"
        ba.is_default = 1
        ba.is_company_account = 1
        ba.company = COMPANY
        try:
            ba.insert(ignore_permissions=True)
            print(f"  ✓ {bank_account_label}")
        except Exception as e:
            print(f"  ! Bank Account: {e}")

    _ensure_mode_of_payment()


def _ensure_erpnext_fixtures():
    """ERPNext's setup wizard normally bootstraps root masters
    (Customer/Supplier/Item Groups, Territories, 239 UOMs, etc.).
    We skipped the wizard so all four are empty — Item/Customer/Supplier
    inserts fail with `Could not find Item Group: Services` etc.
    Call ERPNext's install_fixtures.install(country) idempotently to
    populate them. The function checks for existing records before
    creating, so re-runs are safe."""
    if frappe.db.count("Customer Group") < 3 or frappe.db.count("Territory") < 2:
        from erpnext.setup.setup_wizard.operations import install_fixtures
        install_fixtures.install("India")

    # install_fixtures doesn't create the standard Price Lists — those
    # are normally added by ERPNext's setup_complete with the Company.
    # Sales/Purchase Invoice REQUIRES selling_price_list/buying_price_list,
    # so create them now.
    for name, buying, selling in [("Standard Selling", 0, 1), ("Standard Buying", 1, 0)]:
        if frappe.db.exists("Price List", name):
            continue
        pl = frappe.new_doc("Price List")
        pl.price_list_name = name
        pl.currency = "INR"
        pl.buying = buying
        pl.selling = selling
        pl.enabled = 1
        pl.insert(ignore_permissions=True)


def seed_erp_masters():
    frappe.set_user("Administrator")
    _ensure_erpnext_fixtures()
    seed_items()
    seed_customers()
    seed_suppliers()
    seed_gst_tax_template()
    seed_bank_account()
