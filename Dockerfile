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
#
# --skip-assets is critical: without it, get-app auto-runs `bench build
# --app <name>` per app, which fails when later apps haven't been
# installed yet (the build sees all .bundle.js files but only some
# apps' Python imports are resolvable). We do ONE bench build at the
# end, matching frappe_docker's official pattern.
RUN bench get-app --skip-assets --branch ${FRAPPE_VERSION} https://github.com/frappe/payments \
 && bench get-app --skip-assets --branch ${FRAPPE_VERSION} https://github.com/frappe/hrms

# ── Add our white-label app ──────────────────────────────────────────
# Copy first, then pip-install editable so `bench build` finds it on
# the path and our hooks.py registers app_include_css etc.
COPY --chown=frappe:frappe apps/infinity_hrms apps/infinity_hrms
RUN env/bin/pip install --no-cache-dir -e apps/infinity_hrms

# ── Install node deps for newly-added apps ───────────────────────────
# bench get-app --skip-assets does not run yarn install in the new
# apps' folders. bench setup requirements --node walks every app in
# sites/apps.txt and runs yarn install. Without it, bench build fails
# with "yarn run production --run-build-command exit 1" because
# node_modules don't exist for hrms / payments / infinity_hrms.
RUN bench setup requirements --node

# ── Pre-seed common_site_config.json for the HR PWA build ────────────
# Frappe HR ships a separate Vue 3 PWA frontend at apps/hrms/frontend/
# whose socket.js does:
#   import { socketio_port } from ".../sites/common_site_config.json"
# This is a NAMED JSON import (Rollup style) that requires the key to
# exist at build time. In production this file is written by the
# `configurator` service at runtime, not at image-build time, so we
# pre-seed the minimum vite needs. The runtime configurator's
# `bench set-config -g` calls merge into this file, preserving keys.
RUN node -e "const fs=require('fs');const p='sites/common_site_config.json';const c=fs.existsSync(p)?JSON.parse(fs.readFileSync(p)):{};c.socketio_port=9000;fs.writeFileSync(p,JSON.stringify(c,null,2));"

# ── Build all assets + sync the manifest into the baked dir ──────────
# Frappe compiles JS/CSS bundles at build time and writes:
#   - bundle FILES to apps/<app>/<app>/public/dist/<type>/<bundle>.<hash>.<ext>
#     (persists — apps/ is not a volume)
#   - manifest to sites/assets/assets.json
#     (DISCARDED — sites/ is declared VOLUME in the base image, so
#     build-time writes there don't persist into the final image)
#
# Meanwhile the entrypoint at runtime replaces `sites/assets` with a
# symlink to `/home/frappe/frappe-bench/assets/` (the BAKED dir), so
# at runtime Frappe reads the manifest from the baked location.
#
# Symptom of getting this wrong: every desk page renders as plain
# unstyled HTML, because the manifest points to <hash>.css but only
# the OLD-hash files exist on disk. The fix is to copy the freshly
# written manifest from sites/assets/ to the baked dir so it matches
# the on-disk bundle filenames.
RUN bench build --production \
 && cp sites/assets/assets.json     /home/frappe/frappe-bench/assets/assets.json \
 && cp sites/assets/assets-rtl.json /home/frappe/frappe-bench/assets/assets-rtl.json

# ── Link per-app public/ dirs into the BAKED assets path ─────────────
# The base image's /usr/local/bin/entrypoint.sh runs on every container
# start and does:
#   rm -rf /home/frappe/frappe-bench/sites/assets
#   ln -s /home/frappe/frappe-bench/assets /home/frappe/frappe-bench/sites/assets
# So `sites/assets/` at runtime is a symlink to /home/frappe/frappe-bench/assets/,
# the BAKED dir embedded in the image — NOT the runtime sites/ volume.
# Our per-app symlinks must be created in the baked dir at image-build
# time so they exist for every container that starts from this image
# (especially the frontend, which nginx serves from).
# The base image already has links for frappe + erpnext; we add the
# three we layered on. `ln -sfn` is idempotent so safe to re-run.
RUN for app in payments hrms infinity_hrms; do \
      ln -sfn /home/frappe/frappe-bench/apps/$app/$app/public \
              /home/frappe/frappe-bench/assets/$app; \
    done

# The base image's CMD (supervisord + nginx + gunicorn) is reused as-is.
