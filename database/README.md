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
