# AI Prompt: Generate Advanced Technical Documentation

If you need to generate additional documentation, deep dives, or transition guides for a senior engineer (5+ years of experience) in the future, copy and paste the prompt below into an LLM (such as Gemini 1.5 Pro, Gemini 2.0, or Claude 3.5 Sonnet).

---

### Copy/Paste Prompt:

```text
You are an expert Principal Solutions Architect. Analyze this codebase (FastAPI backend + Next.js frontend + Supabase Auth + PostgreSQL + Google Apps Script Webhook) and generate highly technical, architecture-first developer documentation. 

The target audience is senior software engineers with 5+ years of experience in distributed systems, SQL query optimization, and modern web application development. Avoid basic explanations of REST APIs, ORM concepts, or Next.js basics. Instead, focus on strict implementation details, security boundaries, race conditions, schema state machines, data synchronization patterns, and error recovery mitigation.

Please analyze the codebase and generate documentation covering the following areas:

1. **System & Process Architecture Topology:**
   - Visual architectural flow detailing request lifecycles: Client App -> Supabase JWT Validation -> FastAPI Dependency Injection Context -> SQLAlchemy Database Connection -> Transaction Management -> Google Sheets Sync Webhook.
   - Describe the asynchronous background task strategy for syncing transactions to external sheets to prevent API blocking.

2. **Relational Database Schema & Constraint Mapping:**
   - Define the tables (`employees`, `rooms`, `room_members`, `tickets`, `ticket_rooms`, `messages`, `notifications`) using an ERD format (Mermaid) or standard SQL schema definitions.
   - Detail the structural handling of cross-room tickets (`ticket_rooms`) mapping multi-tenant visibility controls.
   - Document any dynamic or calculated SQLAlchemy properties (e.g., penalty metrics and SLA breach formulas).

3. **Authentication, Claims, & Middleware Lifecycle:**
   - Document the FastAPI dependency injection context (`get_current_user` in deps.py). Explain the steps to extract and verify the Supabase JWT.
   - Detail the dynamic DB/Auth mapping: What occurs when a valid Supabase Auth UUID does not exist in the local postgres database, and how the system dynamically intercepts and self-reconciles by matching email fields and updating UUIDs in-place.

4. **Integration Webhooks & Data Reconciliations:**
   - Document the API contract of the Google Sheet Apps Script webhook.
   - Contrast the "delete-and-reset" chronological synchronization script versus the "in-place update" synchronization script, noting the API payload details and resource implications.

5. **Edge Cases & Failure Recovery Mitigation:**
   - **Ghost Account Recovery:** Detail the recovery path for handling duplicate registration errors in Supabase Auth (when an email is registered in Supabase but lacks a Postgres DB record). Explain the list-update-create sequence of operations.
   - **Dynamic Sequence Generation:** Explain how the codebase resolves PostgreSQL serial sequence (`staff_id_seq`) drift caused by manual backfills or reorder operations by implementing application-level dynamic scalar queries: COALESCE(MAX(CAST(staff_id AS INTEGER)), 0) + 1.

6. **Access Control & Row-Level Authorization Matrix:**
   - Present a security matrix of the 6 roles (Owner, HR, IT Support, Executive, Manager, Staff) against actions (Ticket Create/View/Assign/Approve/Resolve, Staff CRUD).
   - Document how role-based queries are parameterized via SQLAlchemy filters to enforce security boundaries.

Make the output concise, highly technical, and packed with precise file paths, class/function references, and math/logical formulations.
```
