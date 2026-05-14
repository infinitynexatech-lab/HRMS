"""Leads + Opportunities for the ERPNext CRM module.

Note: this is ERPNext's built-in CRM, NOT the standalone Frappe CRM
app. It conflicts with your Corteza-based Infinity CRM positioning,
but populates the CRM workspace for demos where you're selling the
suite as a single platform.
"""

import frappe
from frappe.utils import add_days, today

from .company import COMPANY


# (name, email, company, source, status)
# Status options in this ERPNext: Lead, Open, Replied, Opportunity,
# Quotation, Lost Quotation, Interested, Converted, Do Not Contact
LEADS = [
    ("Rajesh Khurana",   "rajesh@aether-tech.in",       "Aether Technologies",     "Website",        "Open"),
    ("Priya Sundaram",   "psundaram@sapphire-sys.com",  "Sapphire Systems",        "Reference",      "Replied"),
    ("Vikash Kothari",   "vikash@meridian-fin.com",     "Meridian Financial",      "Cold Email",     "Open"),
    ("Arpita Sengupta",  "arpita@northstar.in",         "Northstar Retail",        "LinkedIn",       "Interested"),
    ("Imran Sheikh",     "imran@pinnacle-health.com",   "Pinnacle Healthcare",     "Event",          "Interested"),
    ("Tanvi Rajagopal",  "tanvi@crimson-coatings.in",   "Crimson Coatings",        "Website",        "Open"),
    ("Hemant Awasthi",   "hemant@velocity-cap.in",      "Velocity Capital",        "Reference",      "Replied"),
    ("Sneha Pandey",     "sneha@indus-mfg.com",         "Indus Manufacturing",     "Cold Email",     "Do Not Contact"),
    ("Karan Bhalla",     "karan@cobalt-soft.in",        "Cobalt Software",         "LinkedIn",       "Converted"),
    ("Aakanksha Joshi",  "aakanksha@ranger-log.com",    "Ranger Logistics",        "Website",        "Open"),
]


# (lead_email, opportunity_amount, stage, expected_close_days_out)
# Opportunity statuses: Open, Quotation, Converted, Lost, Replied, Closed
OPPS = [
    ("psundaram@sapphire-sys.com",  450000, "Open",      30),
    ("arpita@northstar.in",         320000, "Quotation", 14),
    ("imran@pinnacle-health.com",   780000, "Quotation", 21),
    ("hemant@velocity-cap.in",      210000, "Open",      45),
]


def seed_leads():
    print("→ Seeding leads")
    for lead_name, email, company, source, status in LEADS:
        if frappe.db.exists("Lead", {"email_id": email}):
            continue
        doc = frappe.new_doc("Lead")
        doc.lead_name = lead_name
        doc.email_id = email
        doc.company_name = company
        doc.source = source if frappe.db.exists("Lead Source", source) else None
        doc.status = status
        doc.no_of_employees = "11-50"
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {lead_name:20} → {company} ({status})")
        except Exception as e:
            print(f"  ! {lead_name}: {e}")


def seed_opportunities():
    print("→ Seeding opportunities")
    for lead_email, amount, stage, days_out in OPPS:
        lead = frappe.db.get_value("Lead", {"email_id": lead_email}, "name")
        if not lead:
            continue
        if frappe.db.exists("Opportunity", {"party_name": lead}):
            continue

        doc = frappe.new_doc("Opportunity")
        doc.opportunity_from = "Lead"
        doc.party_name = lead
        doc.status = stage
        doc.transaction_date = today()
        doc.expected_closing = add_days(today(), days_out)
        doc.company = COMPANY
        doc.opportunity_amount = amount
        doc.currency = "INR"
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {lead_email:40} ₹{amount:,.0f}  ({stage})")
        except Exception as e:
            print(f"  ! {lead_email}: {e}")


def seed_erp_crm():
    frappe.set_user("Administrator")
    seed_leads()
    frappe.db.commit()
    seed_opportunities()
    frappe.db.commit()
