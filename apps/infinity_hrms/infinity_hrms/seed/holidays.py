"""India Holiday List for the current calendar year.

Includes national holidays + weekly off (Sunday). Adjust dates yearly
or use Frappe's `Holiday List` UI clone-to-new-year action.
"""

import frappe

HOLIDAY_LIST = "India 2026"
WEEKLY_OFF = "Sunday"

INDIA_HOLIDAYS_2026 = [
    ("2026-01-01", "New Year"),
    ("2026-01-14", "Makar Sankranti / Pongal"),
    ("2026-01-26", "Republic Day"),
    ("2026-03-03", "Holi"),
    ("2026-03-21", "Eid-ul-Fitr"),
    ("2026-04-02", "Ram Navami"),
    ("2026-04-14", "Ambedkar Jayanti"),
    ("2026-05-01", "Labour Day"),
    ("2026-05-28", "Eid-ul-Adha"),
    ("2026-08-15", "Independence Day"),
    ("2026-08-26", "Janmashtami"),
    ("2026-08-27", "Ganesh Chaturthi"),
    ("2026-10-02", "Gandhi Jayanti"),
    ("2026-10-20", "Dussehra"),
    ("2026-11-08", "Diwali"),
    ("2026-11-09", "Govardhan Puja"),
    ("2026-12-25", "Christmas"),
]


def seed_holiday_list():
    if frappe.db.exists("Holiday List", HOLIDAY_LIST):
        return
    doc = frappe.new_doc("Holiday List")
    doc.holiday_list_name = HOLIDAY_LIST
    doc.from_date = "2026-01-01"
    doc.to_date = "2026-12-31"
    doc.weekly_off = WEEKLY_OFF

    for date, description in INDIA_HOLIDAYS_2026:
        doc.append("holidays", {"holiday_date": date, "description": description})

    # Frappe auto-fills weekly offs when get_weekly_off_dates is called
    doc.flags.ignore_validate = True
    doc.insert(ignore_permissions=True)
    doc.get_weekly_off_dates()
    doc.save(ignore_permissions=True)
