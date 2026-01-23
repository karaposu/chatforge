# High Level Plan: LibreOffice UNO Docker Service

## Goal

Create a Docker-based microservice that exposes LibreOffice UNO capabilities via HTTP API.

---

## Phase 1: Docker Environment ✅

- [x] Create Dockerfile with:
  - Python 3.11 base image
  - LibreOffice installation
  - python3-uno package
  - Required fonts for proper rendering
  - FastAPI and dependencies

- [x] Create docker-compose.yml for easy local development

- [x] Verify UNO imports work inside container (verified in Dockerfile build)

**Location:** `devdocs/enhancements/libreofficeadapter/LibreServer/`

---

## Phase 2: LibreOffice Server Management ✅

- [x] Script to start LibreOffice in headless server mode (`start.py`)
- [x] Connection manager to establish UNO bridge (`LibreOfficeConnection` class)
- [x] Health check to verify LibreOffice is responding (`/health` endpoint)
- [x] Request queue with position tracking (`RequestQueue` class)
- [ ] Auto-restart if LibreOffice crashes (deferred — not critical for prototype)

---

## Phase 3: Core API Endpoints ✅

### Read Operations
- [x] `GET /health` — Check service status
- [x] `POST /info` — Get presentation structure (slides, shapes, text content)
- [x] `POST /slide/{index}` — Get single slide details

### Render Operations
- [x] `POST /render` — Render all slides to images
- [x] `POST /render/slide/{index}` — Render single slide to image
- [x] Support configurable DPI and format (PNG, JPEG)

### Edit Operations
- [x] `POST /edit/text` — Modify text in shapes
- [x] `POST /edit/style` — Modify text styles (font, size, color)
- [ ] `POST /edit/shape` — Modify shape properties (deferred)
- [ ] `PUT /save` — Save modified document (deferred)

---

## Phase 4: Python Client Library ✅

- [x] Create `LibreOfficeClient` class for host-side usage
- [x] Methods mirroring API endpoints
- [x] Handle file upload/download
- [x] Base64 encoding/decoding for binary data
- [x] Async support (`AsyncLibreOfficeClient`)

**Location:** `devdocs/enhancements/libreofficeadapter/LibreServer/client.py`

---

## Phase 5: Integration with Chatforge

- [ ] Create `DockerLibreOfficeAdapter` implementing `RenderToVisualPort`
- [ ] Integrate with `RenderPerceptionService`
- [ ] Handle artifact upload → render → return images flow

---

## Phase 6: Testing & Reliability

- [ ] Unit tests for API endpoints
- [ ] Integration tests with sample PPTX files
- [ ] Load testing (concurrent requests)
- [ ] Error handling for corrupted files
- [ ] Timeout handling for large documents

---

## Phase 7: Documentation

- [ ] API documentation (OpenAPI/Swagger auto-generated)
- [ ] Usage examples
- [ ] Deployment guide
- [ ] Troubleshooting guide

---

## Deliverables

| Deliverable | Description |
|-------------|-------------|
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Local dev setup |
| `server.py` | FastAPI application |
| `client.py` | Python client library |
| `DockerLibreOfficeAdapter` | Chatforge adapter |
| Tests | pytest test suite |
| Docs | API and usage documentation |

---

## Decisions Made

| Question | Decision |
|----------|----------|
| **Concurrency** | Single LibreOffice instance with request queue. API returns queue position. |
| **File storage** | In-memory only (prototype). No temp file persistence. |
| **Authentication** | Not needed. Internal service only. |
| **Caching** | Not needed. |

---

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1-2 (Docker + LO setup) | 1-2 days |
| Phase 3 (API endpoints) | 2-3 days |
| Phase 4 (Client library) | 1 day |
| Phase 5 (Chatforge integration) | 1 day |
| Phase 6-7 (Testing + Docs) | 1-2 days |
| **Total** | **~1 week** |
