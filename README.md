# Chemical Plant Hazardous Waste Management System

Course-style **full-stack** delivery for **COMP3030J Software Engineering Project**: RBAC, batch lifecycle with a **server-enforced state machine**, **audit logging**, **rule-based alerts**, **dashboard charts**, **CSV/PDF exports**, **QR traceability**, **REST API** (API key) with **mock ERP/LIMS** hooks, **Docker** deployment, and **health check** for remote grading.

> The original campus recycling codebase was **replaced** with this domain. Use a fresh DB file `hazard_waste.db` (default). Remove it to re-run first-time seed.

## Roles (RBAC)

| Role | Username (seed) | Password | Capabilities |
|------|-----------------|----------|--------------|
| Administrator | `admin` | `Admin123!` | Users, alert rules, all operational data, audit, exports |
| Environmental Safety Officer | `es_officer` | `Eso123!` | Compliance oversight, alerts, transitions, exports, audit |
| Operator | `operator1` | `Op123!` | Create/edit batches (non-terminal), transitions, transfers |
| Operator (extra demo) | `operator2` | `Op123!` | Same as operator; created by timeline seed for multi-user audit trails |
| Auditor | `auditor1` | `Audit123!` | Read-only UI + audit log + exports |

**First startup simulation:** after users and alert rules are seeded, `run_month_operation_simulation()` replays about **34 simulated days** of operations: operators register batches, advance statuses through the **real state machine**, record **transfers** when entering `in_transit`, append **audit** entries (same shape as the live UI), run **alert rule evaluation** each evening, resolve part of the queue as EHS, and add periodic **report exports** / **ERP–LIMS sync** rows. Timestamps are back-dated so charts look like a plant that has been active for several weeks. The run is **idempotent** (a marker row in the audit log prevents a second replay). Delete `hazard_waste.db` (or remove the `SimulationMarker` / `month_simulation_complete` audit row) to regenerate. To skip simulation, remove the call in `run.py` / `docker-entrypoint.sh`.

## Local run

```bash
cd webproject0
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open **http://127.0.0.1:5001** (port **5001** avoids macOS AirPlay on 5000).

## Sign in & Register

- **Sign in:** `/auth/login` (navbar **Sign in**).
- **Register:** `/auth/register`. Choose **Role**: Operator (no code), Environmental safety officer, or Auditor. ES officer and Auditor must enter the team **invite code** (defaults in `config.py`: `UCD-ES-2026`, `UCD-AUDIT-2026`; override with env `REGISTRATION_INVITE_ES` / `REGISTRATION_INVITE_AUDITOR`). **Administrator** is not self-service — create under **Users** when logged in as admin.

## Docker (remote testing)

```bash
docker compose up --build
```

- Binds **5001**. SQLite stored in volume `hazwaste_data` at `/data/hazard_waste.db`.
- Set `SECRET_KEY` and `EXTERNAL_API_KEY` in environment for production-like deploys.

## API (external integration)

Header: `X-API-Key: <same as EXTERNAL_API_KEY default demo-hazwaste-api-key>`

- `GET /api/v1/health`
- `GET /api/v1/batches`
- `GET /api/v1/batches/<batch_code>`
- `POST /api/v1/integration/erp/person` — mock responsible-person lookup (logged in `external_sync_record`)
- `POST /api/v1/integration/lims/result` — mock lab result callback
- `GET /api/v1/me` — JSON probe when logged in via browser session

## Tests

```bash
pytest tests/
```

## Documentation pack (for Overleaf)

Use this README for **deployment & test accounts**. For formal **System** and **User** documents, copy sections into Overleaf and extend with: architecture diagram, ER diagram, full API tables, AI usage policy, and per-member contributions (course requirement).

### Suggested user-test script (graders)

1. Sign in as `operator1` → **Batches** → create a batch → confirm status `registered`.
2. Advance status along the chain until `stored` / `pending_transfer` (illegal jumps blocked).
3. Open **QR** on batch detail → scan or open public **trace** URL.
4. Sign in as `es_officer` → **Dashboard** → **Run alert rules** → **Alerts**.
5. Sign in as `auditor1` → **Audit log** → **Reports** → download CSV/PDF.
6. Sign in as `admin` → **Users** / **Alert rules**.

## Generative AI

Document in your report: this codebase was produced/refactored with AI assistance; list modules reviewed manually (state machine, RBAC, audit, deployment) and validation steps (pytest, manual walkthrough).
