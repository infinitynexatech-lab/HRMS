"""Recruitment seed — Job Openings + Job Applicants.

Gives the HR User / Interviewer persona an ATS pipeline to demo:
three open roles across Engineering / Sales / HR, each with 2-3
applicants in different stages. Job Applicants are the Frappe HR
record type for candidates — Job Opening is the requisition.
"""

import frappe
from frappe.utils import add_days, today

from .company import COMPANY


# Job Opening templates
JOBS = [
    {
        "name": "Backend Engineer (Python)",
        "designation": "Senior Software Engineer",
        "department": "Engineering",
        "description": "Build APIs, services, and data pipelines on Python + Postgres.",
        "vacancies": 2,
    },
    {
        "name": "Account Executive — North India",
        "designation": "Account Executive",
        "department": "Sales",
        "description": "Own the Delhi / NCR territory. 3+ years SaaS sales.",
        "vacancies": 1,
    },
    {
        "name": "HR Executive",
        "designation": "HR Executive",
        "department": "Human Resources",
        "description": "Operations + onboarding + light payroll. Day-shift, Mumbai.",
        "vacancies": 1,
    },
]


# Applicants per job — name, email, status
# Statuses: Open, Replied, Hold, Rejected, Accepted
APPLICANTS = {
    "Backend Engineer (Python)": [
        ("Rohit Bansal",    "rohit.bansal.demo@example.com",    "Open"),
        ("Anjali Kashyap",  "anjali.kashyap.demo@example.com",  "Replied"),
        ("Vivek Tripathi",  "vivek.tripathi.demo@example.com",  "Hold"),
    ],
    "Account Executive — North India": [
        ("Siddharth Rana",  "siddharth.rana.demo@example.com",  "Replied"),
        ("Nidhi Bhatt",     "nidhi.bhatt.demo@example.com",     "Open"),
    ],
    "HR Executive": [
        ("Anushree Roy",    "anushree.roy.demo@example.com",    "Replied"),
        ("Faisal Khan",     "faisal.khan.demo@example.com",     "Hold"),
    ],
}


def _abbr():
    return frappe.db.get_value("Company", COMPANY, "abbr")


def seed_job_openings():
    print("→ Seeding job openings")
    abbr = _abbr()
    for spec in JOBS:
        dept = f"{spec['department']} - {abbr}"
        if frappe.db.exists("Job Opening", {"job_title": spec["name"]}):
            continue
        doc = frappe.new_doc("Job Opening")
        doc.job_title = spec["name"]
        doc.status = "Open"
        doc.company = COMPANY
        doc.department = dept if frappe.db.exists("Department", dept) else None
        doc.designation = spec["designation"] if frappe.db.exists("Designation", spec["designation"]) else None
        doc.description = spec["description"]
        doc.posted_on = today()
        if hasattr(doc, "vacancies"):
            doc.vacancies = spec["vacancies"]
        try:
            doc.insert(ignore_permissions=True)
            print(f"  ✓ {spec['name']}")
        except Exception as e:
            print(f"  ! {spec['name']}: {e}")


def seed_applicants():
    print("→ Seeding job applicants")
    for job_title, candidates in APPLICANTS.items():
        job = frappe.db.get_value("Job Opening", {"job_title": job_title}, "name")
        if not job:
            continue
        for applicant_name, applicant_email, status in candidates:
            if frappe.db.exists("Job Applicant", {"email_id": applicant_email}):
                continue
            doc = frappe.new_doc("Job Applicant")
            doc.applicant_name = applicant_name
            doc.email_id = applicant_email
            doc.job_title = job
            doc.designation = frappe.db.get_value("Job Opening", job, "designation")
            doc.status = status
            doc.applicant_source = "Direct"
            doc.application_date = add_days(today(), -10)
            try:
                doc.insert(ignore_permissions=True)
                print(f"  ✓ {applicant_name} → {job_title} ({status})")
            except Exception as e:
                print(f"  ! {applicant_name}: {e}")


def seed_recruitment():
    seed_job_openings()
    seed_applicants()
