from . import __version__ as app_version  # noqa: F401

# ── App identity ─────────────────────────────────────────────────────
# These strings appear in `bench list-apps`, in Setup Wizard, in About
# dialogs, and in the <title> tag of every page Frappe renders. The
# `app_title` is what the browser tab actually shows.
app_name = "infinity_hrms"
app_title = "Infinity HRMS"
app_publisher = "Infinity Nexatech"
app_description = "White-label HRMS by Infinity Nexatech, built on Frappe HR"
app_email = "support@infinitynexatech.com"
app_license = "MIT"
required_apps = ["hrms"]

# ── Branding assets ──────────────────────────────────────────────────
# Frappe v14+ reads `app_logo_url` for the navbar logo on the Desk.
# /assets/<app>/... is served by Frappe's static handler from
# infinity_hrms/public/.
app_logo_url = "/assets/infinity_hrms/images/logo.svg"
splash_image = "/assets/infinity_hrms/images/logo.svg"

# ── CSS/JS injection ─────────────────────────────────────────────────
# Desk = the admin/back-office app at /app.
# Web  = the public/portal pages (login, employee self-service portal).
# Inject in BOTH so the brand is consistent everywhere.
app_include_css = "/assets/infinity_hrms/css/infinity_hrms.css"
app_include_js = "/assets/infinity_hrms/js/infinity_hrms.js"
web_include_css = "/assets/infinity_hrms/css/infinity_hrms.css"
web_include_js = "/assets/infinity_hrms/js/infinity_hrms.js"

# ── Website context defaults ─────────────────────────────────────────
# Picked up by the Jinja layer for portal pages (favicon, splash).
website_context = {
    "favicon": "/assets/infinity_hrms/images/favicon.svg",
    "splash_image": "/assets/infinity_hrms/images/logo.svg",
    "brand_html": "Infinity HRMS",
}

# ── Lifecycle hooks ──────────────────────────────────────────────────
# after_install runs once when the app is installed onto a site.
# after_migrate runs every time `bench migrate` runs — used to re-apply
# our Website/Navbar/System settings if an admin changed them manually,
# matching the CRM playbook of "rebrand survives a redeploy".
after_install = "infinity_hrms.install.apply_branding"
after_migrate = "infinity_hrms.install.apply_branding"

# ── Boot session ─────────────────────────────────────────────────────
# extend_bootinfo lets us push extra keys to window.frappe.boot, which
# we use in public/js to override the document.title before the user
# even sees the default flash.
extend_bootinfo = "infinity_hrms.boot.extend_bootinfo"
