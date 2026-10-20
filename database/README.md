# Database Setup & Migrations

This folder contains the complete SQL schema and initial seed data for **Hospital AI Automation**.

The schema is 100% compatible with:
1. **PostgreSQL 14+**
2. **Supabase PostgreSQL**
3. **SQLite 3** (used by default in local development when DATABASE_URL is not set)

## Running the Schema on PostgreSQL / Supabase

If using Supabase or a self-hosted PostgreSQL instance:
1. Connect via `psql` or the Supabase SQL Editor.
2. Run `schema.sql`:
   ```bash
   psql -h <host> -U <user> -d <database> -f database/schema.sql
   ```
3. Run `seed.sql`:
   ```bash
   psql -h <host> -U <user> -d <database> -f database/seed.sql
   ```

## Running the Seed via Backend CLI

You can also initialize and seed your database directly using the backend Python seed runner:

```bash
cd backend
python -m app.db.seed
```

This automatically checks table structures, creates any missing tables, and seeds:
- 5 Core Medical Departments
- 10 Specialist Doctors with schedules & bios
- 15 Diverse Demo Patients
- Future Doctor Availability Slots
- Active & Historical Appointments
- Diagnostic Reports with various statuses
- Verified Patient Feedback ratings (1-5 stars)
- Sample AI Conversations & Transcripts
- Emergency Escalations & Voice Call Requests
- Sample Error Logs for audit demonstration

## Migrating from SQLite to PostgreSQL

A dedicated, non-destructive migration utility is provided in `backend/scripts/migrate_sqlite_to_postgres.py`.

> [!WARNING]
> **Production Cutover Prerequisite:** Do NOT execute live migration against production databases without prior validation on an isolated staging database.

### 1. Mandatory Backup
Before running migration, create a full physical cold backup of your source SQLite database:
```powershell
Copy-Item hospital.db "hospital.db.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
```

### 2. Dry-Run Validation (Read-Only)
Always perform a dry run first to verify schema connectivity, inspect foreign keys, and audit orphan records:
```powershell
python backend/scripts/migrate_sqlite_to_postgres.py --source sqlite:///./hospital.db --target "$env:MIGRATION_TARGET_DB_URL" --dry-run
```

### 3. Orphan Records & Options
- If source foreign keys refer to non-existent rows, the utility halts with `OrphanDataDetectedError`.
- If orphaned records are confirmed obsolete by clinical administration, `--skip-orphans` may be passed to omit them and report the exact counts.
- Target databases containing existing rows require `--allow-non-empty-target`.

### 4. Technical Assumptions
- **Naive Timestamps:** SQLite datetimes without timezone offsets are normalized to UTC. Operators must verify that legacy timestamps were generated in UTC before production cutover.
- **Transaction Atomicity:** Target writes execute inside a single atomic transaction that rolls back completely on any error.
