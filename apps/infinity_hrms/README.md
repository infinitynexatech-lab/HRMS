# infinity_hrms

White-label branding overlay for Frappe HR. Installs on top of `frappe`,
`erpnext`, and `hrms`.

What it sets:

- Brand name / wordmark / favicon / login splash
- Navbar logo + brand HTML
- Indigo (`#6366F1`) Bootstrap theme via a Website Theme record
- System defaults: country IN, currency INR, timezone Asia/Kolkata, language en

Idempotent — `bench migrate` re-applies, so manual UI edits do not drift.
