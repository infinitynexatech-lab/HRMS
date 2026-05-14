"""extend_bootinfo: pushes brand info into the bootInfo dict the
Frappe client reads on first page-load. We use it in public/js to set
document.title before the user notices the default 'Frappe' flash."""


def extend_bootinfo(bootinfo):
    bootinfo.infinity_hrms = {
        "brand": "Infinity Suite",
        "publisher": "Infinity Nexatech",
        "primary_color": "#6366F1",
        "support_email": "support@infinitynexatech.com",
    }
