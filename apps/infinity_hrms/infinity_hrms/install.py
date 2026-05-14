"""Idempotent branding application — survives install + every migrate."""

import frappe


BRAND_NAME = "Infinity HRMS"
BRAND_HTML = (
    '<span style="display:inline-flex;align-items:center;gap:.5rem;'
    'font-weight:700;letter-spacing:.02em;">'
    '<img src="/assets/infinity_hrms/images/logo-mark.svg" '
    'style="height:20px;width:20px;" alt=""/>'
    "Infinity HRMS</span>"
)
LOGO_URL = "/assets/infinity_hrms/images/logo.svg"
FAVICON_URL = "/assets/infinity_hrms/images/favicon.svg"
SPLASH_URL = "/assets/infinity_hrms/images/logo.svg"
SUPPORT_EMAIL = "support@infinitynexatech.com"


def apply_branding():
    """Write our brand settings into the four Frappe singletons that
    actually drive the rendered UI. Idempotent — safe to re-run."""
    _website_settings()
    _navbar_settings()
    _system_settings()
    _website_theme()
    frappe.db.commit()


def _website_settings():
    """Brand bar HTML, favicon, title prefix — portal + Desk both read this."""
    ws = frappe.get_single("Website Settings")
    ws.app_name = BRAND_NAME
    ws.brand_html = BRAND_HTML
    ws.banner_html = ""
    ws.favicon = FAVICON_URL
    ws.splash_image = SPLASH_URL
    ws.title_prefix = BRAND_NAME
    ws.save(ignore_permissions=True)


def _navbar_settings():
    """The navbar logo on the Desk (admin app) is set here, not in hooks
    on every Frappe version. Set both so it survives major upgrades."""
    try:
        nb = frappe.get_single("Navbar Settings")
    except frappe.DoesNotExistError:
        return
    nb.app_logo = LOGO_URL
    nb.logo_width = 28
    # Frappe v14+ has a "Logo" type setting; older versions ignore unknown fields
    if hasattr(nb, "brand_html"):
        nb.brand_html = BRAND_HTML
    nb.save(ignore_permissions=True)


def _system_settings():
    """System-wide niceties: country defaults, currency, language.
    Also marks setup_complete=1 so the Frappe setup wizard does not
    intercept logins for our pre-seeded site."""
    ss = frappe.get_single("System Settings")
    ss.country = ss.country or "India"
    ss.language = ss.language or "en"
    ss.time_zone = ss.time_zone or "Asia/Kolkata"
    ss.currency = ss.currency or "INR"
    ss.setup_complete = 1
    ss.save(ignore_permissions=True)


def _website_theme():
    """Indigo theme (matches Infinity CRM #6366F1) applied via a Website
    Theme record + set as default."""
    name = "Infinity Indigo"
    if frappe.db.exists("Website Theme", name):
        theme = frappe.get_doc("Website Theme", name)
    else:
        theme = frappe.new_doc("Website Theme")
        theme.theme = name
        theme.module = "Website"

    theme.custom_scss = _scss()
    theme.button_rounded_corners = 1
    # NB: assign attribute on flags (a frappe._dict). Replacing the
    # whole flags dict breaks downstream `self.flags.in_print` access.
    theme.flags.ignore_validate = True
    theme.save(ignore_permissions=True)

    # set_as_default() does three things we can't do by hand:
    #   1. Compiles custom_scss → /files/website_theme/<name>_<hash>.css
    #   2. Updates Website Settings.website_theme to point at this record
    #   3. Caches the compiled CSS path so web.html renders <link href>
    # Skipping this leaves the rendered HTML with <link href="None"> for
    # the website theme stylesheet, which breaks the portal navbar/layout.
    theme.set_as_default()


def _scss():
    """SCSS variable overrides — these flow through Frappe's bootstrap
    theme into both Desk and Web rendered pages."""
    return """
$primary: #6366F1;
$primary-light: #E0E7FF;
$secondary: #64748B;
$success: #10B981;
$warning: #F59E0B;
$danger: #EF4444;
$info: #3B82F6;
$body-bg: #F8FAFC;
$navbar-bg: #FFFFFF;
$sidebar-bg: #FFFFFF;
$link-color: #4F46E5;
$btn-primary-bg: #6366F1;
$btn-primary-border: #6366F1;
$btn-primary-hover-bg: #4F46E5;
""".strip()
