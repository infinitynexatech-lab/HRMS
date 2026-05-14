# Infinity HRMS — custom image on top of Frappe's published ERPNext base.
#
# What this does:
#   1. Starts from frappe/erpnext:<version> — Frappe's production-ready
#      image already includes frappe + erpnext + nginx + gunicorn +
#      supervisord and a working bench at /home/frappe/frappe-bench.
#   2. Adds Frappe HR (`hrms`) and its dependency `payments`.
#   3. Copies in our white-label app `infinity_hrms` (branding, theme,
#      logos, install hooks).
#   4. Rebuilds the asset bundle so our CSS/JS ship to the browser.
#
# Build:
#   docker build -t infinity-hrms:v1.0.0 .
#   (or via docker compose build — see docker-compose.yml)
#
# Why a single Dockerfile instead of vendoring frappe_docker:
#   Frappe Technologies publishes a stable, security-patched base image
#   monthly. Layering on top of it keeps our custom surface tiny —
#   exactly the three apps + ~10 files of branding we actually own.

ARG FRAPPE_VERSION=version-15
FROM frappe/erpnext:${FRAPPE_VERSION}

# Re-declare ARG inside the FROM scope so RUN can see it
ARG FRAPPE_VERSION

USER frappe
WORKDIR /home/frappe/frappe-bench

# ── Add upstream apps ────────────────────────────────────────────────
# `bench get-app` clones the repo into apps/<name> and pip-installs it
# into the bench's venv. Branch must match the frappe/erpnext base or
# you will get a "frappe version mismatch" error at runtime.
RUN bench get-app --branch ${FRAPPE_VERSION} https://github.com/frappe/payments \
 && bench get-app --branch ${FRAPPE_VERSION} https://github.com/frappe/hrms

# ── Add our white-label app ──────────────────────────────────────────
# Copy first, then pip-install editable so `bench build` finds it on
# the path and our hooks.py registers app_include_css etc.
COPY --chown=frappe:frappe apps/infinity_hrms apps/infinity_hrms
RUN env/bin/pip install --no-cache-dir -e apps/infinity_hrms

# ── Rebuild asset bundle ─────────────────────────────────────────────
# Frappe compiles a single CSS/JS bundle at build time. Without this
# step our infinity_hrms.css would 404 in the browser.
# --production minifies + adds cache-bust hashes.
RUN bench build --production

# The base image's CMD (supervisord + nginx + gunicorn) is reused as-is.
