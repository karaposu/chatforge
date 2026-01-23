# Docker Options for LibreOffice Access

Since LibreOffice UNO doesn't work reliably on macOS, we run it in a Docker container (Linux) where it works perfectly.

---

## The Goal

We need to:
1. **Read** presentation structure (slides, shapes, text)
2. **Edit** content (modify text, styles, elements)
3. **Render** slides to images (PNG)

All via API from our macOS/Windows host.

---

## Options Overview

| Option | What it is | Edit Support | Render Support | Complexity |
|--------|------------|--------------|----------------|------------|
| **unoserver** | Pre-built REST API for LibreOffice | ❌ Convert only | ✅ Yes | Low |
| **gotenberg** | Document conversion microservice | ❌ Convert only | ✅ Yes | Low |
| **Custom FastAPI + UNO** | Build our own service with full UNO access | ✅ Full | ✅ Yes | Medium |
| **linuxserver/libreoffice** | Full LibreOffice GUI in browser | ✅ Manual | ✅ Manual | Low |

---

## Option 1: unoserver

**What:** A Python server that exposes LibreOffice via REST API.

**Capabilities:**
- Convert between formats (PPTX → PDF, DOCX → PNG, etc.)
- Render documents to images

**Limitations:**
- No programmatic editing (can't change text/shapes via API)
- Conversion only

**Best for:** If you only need rendering, not editing.

**Links:**
- GitHub: https://github.com/unoconv/unoserver
- Docker: `libreofficedocker/libreoffice-unoserver`

---

## Option 2: gotenberg

**What:** A Docker-based API for document conversions using LibreOffice under the hood.

**Capabilities:**
- Convert Office documents to PDF
- Convert HTML to PDF
- Merge PDFs

**Limitations:**
- No editing capabilities
- No direct image export (PDF only, would need extra step)

**Best for:** PDF generation pipelines.

**Links:**
- https://gotenberg.dev/
- Docker: `gotenberg/gotenberg`

---

## Option 3: Custom FastAPI + UNO (Recommended)

**What:** Build our own Docker image with LibreOffice + Python UNO + FastAPI service.

**Capabilities:**
- Full UNO API access
- Read slide structure
- Edit text, shapes, styles programmatically
- Render to images
- Complete control

**Limitations:**
- Need to build and maintain the service
- More initial setup

**Best for:** Our use case — we need edit + render.

**Architecture:**
```
┌─────────────────────┐         ┌─────────────────────────────────┐
│   Host (macOS)      │         │   Docker Container (Linux)      │
│                     │  HTTP   │                                 │
│   Your Python App   │ ──────▶ │   FastAPI  ──▶  LibreOffice    │
│                     │         │   Server        UNO API         │
└─────────────────────┘         └─────────────────────────────────┘
```

---

## Option 4: linuxserver/libreoffice

**What:** Full LibreOffice with GUI accessible via web browser.

**Capabilities:**
- Complete LibreOffice experience in browser
- All features available manually

**Limitations:**
- No API — requires manual interaction
- Not suitable for automation

**Best for:** Manual testing, not programmatic access.

---

## Recommendation

For our Render Perception use case:

| Requirement | Solution |
|-------------|----------|
| Need to edit slides programmatically | **Option 3: Custom FastAPI + UNO** |
| Only need to render (no editing) | Option 1: unoserver |

**Option 3** is the only one that gives us full edit + render via API.

---

## Next Steps

1. Decide if Option 3 is acceptable
2. If yes, create implementation plan for Custom FastAPI + UNO service
3. Define the API endpoints we need
4. Build and test the Docker image
