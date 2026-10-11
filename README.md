# CertifyFlow

CertifyFlow is a FastAPI application for generating personalized certificates in
bulk. A user supplies event details and a recipient list, the application creates
one PDF per recipient, stores job progress in PostgreSQL, and provides a ZIP
download containing the successfully generated certificates.

## Features

- Browser-based workflow for creating a certificate batch.
- CSV recipient-list validation in the browser.
- Background generation so the request returns immediately with a job ID.
- Live job progress and success/failure counts.
- A4 landscape PDF certificates generated with ReportLab.
- One ZIP download containing all valid PDFs from a completed job.
- SQLAlchemy models and Alembic migrations for jobs and certificates.

## Project layout

```text
app/
  api/router/       FastAPI routes for jobs and file uploads
  assets/fonts/     Fonts used by the PDF template
  core/config/      Environment-backed application settings
  db/               SQLAlchemy engine and session dependency
  models/           GenerationJob and Certificate database models
  services/         Background processing and PDF generation
  static/           Browser UI, JavaScript, and CSS
  template/         ReportLab certificate drawing code
alembic/             Database migration scripts
requirements.txt     Python dependencies
alembic.ini          Alembic configuration
```

## Prerequisites

- Python 3.10 or newer (the code uses modern type-hint syntax).
- PostgreSQL 12 or newer, or a compatible PostgreSQL installation.
- Git, if cloning the repository.

## Setup

The commands below use PowerShell on Windows. Run them from the repository root.

1. Create and activate a virtual environment:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks script execution for the current user, run:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

2. Install the dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

3. Create a PostgreSQL database and user, or use an existing database. For
   example, from `psql`:

   ```sql
   CREATE USER certifyflow WITH PASSWORD 'change-this-password';
   CREATE DATABASE certificate_generator OWNER certifyflow;
   ```

4. Create a `.env` file in the repository root. Do not commit this file.

   ```dotenv
   DATABASE_URL=postgresql+psycopg://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME
   APP_DEBUG=true
   ```

   `DATABASE_URL` is required. The application loads it through
   `pydantic-settings`. `APP_DEBUG` is optional and defaults to `true`.

5. Ensure the `sqlalchemy.url` value in `alembic.ini` points to the same
   PostgreSQL database, then apply the migrations:

   ```powershell
   python -m alembic upgrade head
   ```

   The migrations create the `generation_jobs` and `certificates` tables.

## Run the application

Start the development server from the repository root:

```powershell
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/> in a browser. The interactive API documentation
is available at <http://127.0.0.1:8000/docs>.

The `--reload` option is intended for development. For a non-reloading local
run, omit it:

```powershell
python -m uvicorn app.main:app
```

## Run tests

Install the requirements as described above, then run:

```powershell
python -m pytest
```

There is currently no `tests/` directory in the repository, so no automated
test cases are configured yet. `pytest` is included as the intended test
runner; new tests should use an isolated test database and should cover the
job routes, background processing, PDF output, and ZIP retrieval.

## Submit a certificate generation request

### Web interface (recommended)

1. Open the application home page.
2. Enter:
   - **Certificate title**, such as `Achievement`.
   - **Event or program name**.
   - **Event date**.
   - **Issued by**.
3. Select or drag in a CSV file.
4. Make sure the first row contains a `recipient_name` column and each
   subsequent row contains one non-empty recipient name, for example:

   ```csv
   recipient_name
   Aarav Sharma
   Meera Patel
   Kabir Singh
   ```

5. Select **Generate certificates**.

The browser parses and validates the CSV, then sends a JSON request to
`POST /jobs/`. The response contains the newly created job ID. The UI polls
`GET /jobs/{job_id}/status` every two seconds until processing finishes.

### JSON API

The same operation can be submitted without the browser:

```powershell
curl.exe -X POST http://127.0.0.1:8000/jobs/ `
  -H "Content-Type: application/json" `
  -d "{\"certificate_title\":\"Achievement\",\"issuer\":\"Organizing Committee\",\"event_name\":\"Annual Tech Summit 2026\",\"event_date\":\"2026-10-11\",\"recipients\":[{\"recipient_name\":\"Aarav Sharma\"},{\"recipient_name\":\"Meera Patel\"}]}"
```

The request must contain at least one recipient. `certificate_title`,
`issuer`, and `event_name` must be between 1 and 255 characters. `event_date`
must be an ISO date (`YYYY-MM-DD`). A successful request returns HTTP `201`
and a response similar to:

```json
{
  "id": 1,
  "certificate_title": "Achievement",
  "issuer": "Organizing Committee",
  "event_name": "Annual Tech Summit 2026",
  "event_date": "2026-10-11",
  "status": "Pending",
  "total_count": 2,
  "success": 0,
  "failure": 0,
  "created_at": "2026-10-11T12:00:00"
}
```

The API creates the job and its pending certificate records before scheduling
the generation work as a FastAPI background task.

## Retrieve generated certificates

### Check job status

```powershell
curl.exe http://127.0.0.1:8000/jobs/1/status
```

The status response includes:

- `status`: `Pending`, `Processing`, `Completed`, `Partially Completed`, or
  `Failed`.
- `total`, `success`, `failed`, `processing`, and `pending` counts.
- `progress_percentage`.

Continue polling until the status is `Completed`, `Partially Completed`, or
`Failed`.

### Download all successful certificates

When at least one certificate is complete, download the ZIP archive:

```powershell
curl.exe -L http://127.0.0.1:8000/jobs/1/download-all `
  -o certificates.zip
```

The endpoint returns `404` if the job does not exist, if it has no completed
certificates, or if no generated files can be found. For a partially completed
job, the ZIP contains only the successful certificates. The generated PDFs are
also stored on disk beneath:

```text
app/generated/bulk_certificate_generator_<job_id>/
```

The application does not currently expose a public endpoint for downloading an
individual certificate; use the ZIP endpoint or inspect that job directory
when working locally.

## Important implementation and design decisions

### Asynchronous batch processing

`POST /jobs/` persists the job and all recipient records first, then schedules
`process_job` as a FastAPI background task. This keeps the submission request
fast and lets clients observe progress through a separate status endpoint.
The background task creates a fresh database session rather than reusing the
request session.

### Per-recipient failure isolation

Recipients are processed in ID order. Each certificate transitions through
`Pending`, `Processing`, and either `Completed` or `Failed`. A generation error
is stored on that certificate and does not stop the rest of the batch. The job
finishes as `Completed`, `Partially Completed`, or `Failed` based on the
aggregate outcomes.

### Relational persistence and migrations

`generation_jobs` stores event metadata and aggregate counters. `certificates`
stores one row per recipient, its status, generated relative path, and any
error message. SQLAlchemy manages the relationship, while Alembic keeps schema
changes reproducible.

### Deterministic, filesystem-safe output

Each job gets an `app/generated/bulk_certificate_generator_<job_id>` directory.
Recipient names are sanitized before becoming filenames, and the certificate
ID is appended to avoid collisions between duplicate names. The download
route resolves paths and verifies they remain within the generated directory
before adding them to the ZIP.

### PDF template and bundled fonts

ReportLab draws an A4 landscape certificate from vector shapes and text. The
template registers the bundled Cinzel, Allura, and Montserrat fonts, so
generated documents do not depend on fonts installed on the host machine.

### Current input surfaces

The browser workflow intentionally uses CSV and sends JSON to `/jobs/`. The
codebase also contains a multipart `POST /upload/` route intended for CSV/XLSX
imports. It is not used by the current UI and should be treated as an
alternative integration surface until it is covered by tests and brought into
parity with the primary background-job workflow.

## Operational notes

- Keep `.env` and database credentials out of source control.
- `app/generated/` is runtime output and is ignored by Git.
- The current background task runs in the API process. For durable production
  queues, retries, and horizontal scaling, replace it with a dedicated worker
  system and external object storage.
- Generated files are local to the application host; deploy shared storage if
  multiple application instances must serve the same certificates.
