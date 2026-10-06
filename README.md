# Bulk Certificate Generator API

A FastAPI backend for creating, processing, tracking, and retrieving bulk PDF
certificates.

The API accepts event details and a list of recipients, creates a generation
job, stores one recipient record per certificate, processes the certificates in
the background, tracks job progress, and returns generated PDFs for completed
recipients.

## Features

- Bulk certificate job creation.
- Pydantic validation for request bodies and email addresses.
- PostgreSQL persistence through SQLAlchemy.
- Alembic migration for the current database schema.
- `GenerationJob` to `Recipient` one-to-many database model.
- Background processing with FastAPI `BackgroundTasks`.
- Per-recipient status and error tracking.
- Job-level completed, failed, and progress counts.
- Individual recipient failure isolation.
- PDF certificate generation with ReportLab.
- Certificate retrieval for completed recipients.
- Health endpoint and automated tests.

## Technology Stack

Python, FastAPI, Uvicorn, PostgreSQL, SQLAlchemy, Pydantic, Alembic, ReportLab,
and Pytest.

## Architecture

```text
Client
  |
  | POST /api/jobs
  v
FastAPI route
  |
  | Pydantic validation
  v
GenerationJob + Recipient rows
  |
  | FastAPI BackgroundTasks
  v
Certificate worker
  |
  | generate PDFs with ReportLab
  | update recipient status, certificate path, and error message
  | update job counters and final job status
  v
PostgreSQL
  |
  | GET /api/jobs/{job_id}
  | GET /api/certificates/{certificate_id}
  v
Client
```

## Project Structure

```text
.
|-- alembic/                         # Alembic environment and migration files
|-- app/api/routes/                  # FastAPI route modules
|-- app/core/config.py               # .env settings
|-- app/db/                          # SQLAlchemy engine, sessions, models
|-- app/schemas/                     # Pydantic request/response schemas
|-- app/services/certificate_service.py
|-- app/workers/certificate_worker.py
|-- app/main.py                      # FastAPI app and health route
|-- generated/                       # Generated certificate PDFs
|-- templates/certificate_template.py
|-- tests/
|-- .env.example
|-- alembic.ini
|-- pytest.ini
`-- requirements.txt
```

## Database Design

The database contains two SQLAlchemy models with a one-to-many relationship:
one `GenerationJob` has many `Recipient` records.

`GenerationJob` maps to `generation_jobs` and stores `id`, `event_name`,
`certificate_title`, `organization`, `event_date`, `status`,
`total_recipients`, `completed_count`, `failed_count`, `created_at`, and
`updated_at`.

`Recipient` maps to `recipients` and stores `id`, `job_id`, `name`, `email`,
`status`, nullable `certificate_path`, nullable `error_message`, `created_at`,
and `updated_at`.

`GenerationJob.recipients` uses `cascade="all, delete-orphan"`.
`Recipient.job` points back to the parent job.

## Status Values

Job statuses: `QUEUED`, `PROCESSING`, `COMPLETED`,
`COMPLETED_WITH_ERRORS`, and `FAILED`.

Recipient statuses: `QUEUED`, `PROCESSING`, `COMPLETED`, and `FAILED`.

`COMPLETED_WITH_ERRORS` is used when at least one recipient succeeds and at
least one recipient fails.

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
```

Update `.env` with your PostgreSQL connection string.

## PostgreSQL Configuration

The application requires `DATABASE_URL`.

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/certificates
```

Create the database before running migrations:

```sql
CREATE DATABASE certificates;
```

`app/core/config.py` loads `.env` with `pydantic-settings`. Alembic reads the
same `DATABASE_URL` from application settings.

Environment variables from `.env.example`: `DATABASE_URL` is required by the
code and contains the SQLAlchemy database URL. `APP_NAME` is present in the
example file but is not read by the current settings class.

## Database Migrations

Run migrations:

```bash
alembic upgrade head
```

Current migration head:

```text
8ad2dc43fb33
```

The current migration creates `generation_jobs` and `recipients`.

## Running the API

```bash
uvicorn app.main:app --reload
```

API base URL: `http://127.0.0.1:8000`

Interactive docs: `http://127.0.0.1:8000/docs`

## API Endpoints

### `GET /health`

Response:

```json
{"status": "ok"}
```

### `POST /api/jobs`

Creates a job, stores recipients, and schedules background processing.

Status code: `202 Accepted`

Request:

```json
{
  "event_name": "Python Workshop",
  "certificate_title": "Certificate of Completion",
  "organization": "Aereo Learning",
  "event_date": "2026-10-06",
  "recipients": [
    {"name": "Mayur Pawar", "email": "mayur@example.com"},
    {"name": "Rahul Sharma", "email": "rahul@example.com"}
  ]
}
```

Validation: `event_name`, `certificate_title`, and `organization` are required
strings from 1 to 255 characters. `event_date` is a required date.
`recipients` is required and must contain 1 to 5000 items. Each recipient needs
a `name` from 1 to 255 characters and a valid `email`.

Response:

```json
{
  "job_id": 7,
  "status": "QUEUED",
  "total_recipients": 2
}
```

### `GET /api/jobs/{job_id}`

Returns job progress and per-recipient statuses.

Response:

```json
{
  "job_id": 7,
  "status": "COMPLETED_WITH_ERRORS",
  "total_recipients": 4,
  "completed_count": 3,
  "failed_count": 1,
  "progress": 100.0,
  "recipients": [
    {
      "recipient_id": 1,
      "name": "Mayur Pawar",
      "email": "mayur@example.com",
      "status": "COMPLETED",
      "error_message": null
    },
    {
      "recipient_id": 2,
      "name": "Priya Singh",
      "email": "priya@example.com",
      "status": "FAILED",
      "error_message": "Certificate generation failed"
    }
  ]
}
```

Progress is calculated as `(completed_count + failed_count) /
total_recipients * 100` and rounded to two decimal places.

Missing job response:

```json
{"detail": "Job not found"}
```

### `GET /api/certificates/{certificate_id}`

Returns the generated certificate PDF for a completed recipient.

`certificate_id` is the recipient ID. The route looks up `Recipient.id` and only
returns a file when the recipient status is `COMPLETED`.

Success response: `200 OK`, `Content-Type: application/pdf`, and
`Content-Disposition` filename `certificate_{recipient_id}.pdf`.

Error responses: `{"detail": "Certificate not found"}`,
`{"detail": "Certificate is not available"}`, or
`{"detail": "Certificate file not found"}`.

## Bulk Processing

When `POST /api/jobs` is called, the route validates the request, creates one
`GenerationJob`, creates one queued `Recipient` per input recipient, commits the
transaction, schedules `run_certificate_job(job.id)` as a background task, and
returns the job ID immediately.

The worker loads the job, marks it `PROCESSING`, loads queued recipients ordered
by ID, and processes them one at a time. For each successful recipient, it stores
the generated certificate path, marks the recipient `COMPLETED`, and increments
`completed_count`.

After all queued recipients are processed, the job status becomes `COMPLETED`,
`COMPLETED_WITH_ERRORS`, or `FAILED` based on the completed and failed counts.

## Failure Isolation

Each recipient is processed inside its own `try`/`except` block. If one
recipient fails, the worker stores the exception message in
`recipients.error_message`, marks that recipient `FAILED`, increments
`failed_count`, and continues with the remaining recipients.

This allows partial success instead of failing the entire job because of one
recipient.

## Certificate Generation

PDF generation is implemented in `app/services/certificate_service.py` with
ReportLab. Generated certificates are stored as:

```text
generated/{job_id}/{recipient_id}.pdf
```

The renderer uses one predefined template in `templates/certificate_template.py`
and inserts recipient name, certificate title, event name, organization, and
event date formatted as `Month DD, YYYY`.

## Testing

Run the test suite:

```bash
pytest
```

The tests cover health checks, job creation and persistence, Pydantic validation
for email/required fields/empty recipients/the 5000-recipient limit, job status
responses, progress calculation, missing job behavior, PDF generation,
certificate retrieval, certificate retrieval `404` cases, and worker failure
isolation when one recipient fails.

Database-dependent tests override the FastAPI database dependency with an
in-memory SQLite database for isolation.

Latest local verification:

```text
15 passed
```

The project has also been tested against a real PostgreSQL database using the
configured `DATABASE_URL` and Alembic migration flow.

## Design Decisions

FastAPI keeps the API small while providing request validation, response models,
dependency injection, and generated API documentation.

PostgreSQL stores job and recipient state and makes progress queryable after the
create request returns.

Separate `GenerationJob` and `Recipient` records keep job-level metadata apart
from per-certificate processing state, which makes progress tracking, partial
success, and recipient-level errors straightforward.

FastAPI `BackgroundTasks` fit the assignment's local background processing
requirement because the API can return a job ID while generation continues after
the response is prepared. They are not a distributed or durable job queue. If the
process stops while a task is running, in-progress work may be interrupted.

Per-recipient failure isolation allows a job to finish as
`COMPLETED_WITH_ERRORS` when some certificates succeed and others fail.

## Current Limitations

Background processing uses FastAPI `BackgroundTasks`, not a durable queue. The
project does not currently include retries, authentication, authorization,
object storage, Docker setup, job listing, job deletion, generated file cleanup,
or multiple certificate templates.

## Possible Future Improvements

Possible improvements include a durable worker queue such as Celery/RQ with
Redis or another broker, retries for transient failures, authentication, object
storage such as S3, job listing/filtering/pagination/cancellation, multiple
certificate templates, structured logging, metrics, and Docker Compose for local
setup.

## Verification

Verified locally with:

```bash
.\.venv\Scripts\python.exe -m pytest
```

Result:

```text
15 passed
```
