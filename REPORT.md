# Progress Report - June 28, 2026

## 1. Accomplishments & Technical Updates

### 1.1 Ghost Account Auto-Recovery Flow
*   **Problem:** Manual account testing or database wipes resulted in "Ghost Accounts"—situations where a user email existed in Supabase Auth but had no matching record in the local PostgreSQL `employees` table. Subsequent signup attempts via the admin interface threw a `duplicate email` exception.
*   **Resolution:** Modified the user creation endpoint (`backend/app/domains/users/router.py`) to intercept Supabase duplicate email exceptions. The backend now lists users via the Supabase Admin interface, grabs the existing Auth UUID, updates its password/metadata to match the admin's request, and successfully inserts the local database record using the same UUID.

### 1.2 Database Sequence Drift Resolution
*   **Problem:** Manual chronological re-sorting or csv backfills of employee data caused the PostgreSQL `staff_id_seq` sequence to drift behind the actual max `staff_id` in the table, resulting in database integrity constraint violations on subsequent creations.
*   **Resolution:** Deprecated the Postgres `staff_id_seq` sequence entirely across both `router.py` and `deps.py` (which processes automatic onboarding updates). Replaced it with a dynamic scalar query:
    $$\text{staff\_id} = \text{pad\_left}(\text{COALESCE}(\text{MAX}(\text{CAST}(\text{staff\_id AS INTEGER})), 0) + 1, 4)$$
    This ensures `staff_id` sequence generation is always based on the highest numerical key currently in the table, preventing drift or collision issues.

### 1.3 Smart In-Place Chronological Reordering
*   **Problem:** The previous roster sync script cleared all sheet rows and re-added them one by one. This caused a 4-6 minute blank period on Google Sheets during execution and reset all user password cells to generic defaults.
*   **Resolution:** Implemented `backend/scripts/reorder_uids_smart.py`. This script:
    1.  Extracts all active database records.
    2.  Sorts them chronologically by joining date (preserving owners at the top).
    3.  Updates local PostgreSQL records using temporary UIDs (preventing unique key index collisions in Postgres).
    4.  Sends an `"update"` action payload to the Google Sheet Apps Script webhook for all 82 rows. The webhook updates cells in-place matching by email.
    *   **Result:** Chronological ordering complete, UIDs synchronized, passwords intact (including Sohana's password `Biw2799`), with zero data loss or sheet blank time.

### 1.4 Frontend Enhancements
*   Added `head_of_business` role to creation and editing select forms on `/dashboard/staff`.
*   Implemented `getRoleLabel` mappings in `/dashboard/layout.tsx` to handle visual rendering of custom roles in the UI sidebar and details views.

### 1.5 System Architecture Reference & Templates
*   Created `/SYSTEM_ARCHITECTURE.md`: High-fidelity engineering documentation detailing request flows, ER diagram schemas, authorization models, and webhook contracts.
*   Created `/DOCUMENTATION_GENERATOR_PROMPT.md`: An advanced developer prompt template for generating further technical documentation and onboarding materials for senior devs.

---

## 2. Roster Sync Audit & Verification

*   **Total Records Loaded:** 82 active employees.
*   **Database Reconciliation:** All records mapped to sequence range `0001` - `0002` ... `0082`.
*   **Google Sheets Sync:** 82/82 rows updated successfully.
*   **Verified New Account:** Sohana Hossain Falguni successfully assigned to `0005` (chronological joining date `21-07-2021`) and registered with password `Biw2799`.

---

## 3. Git Push Verification

*   All changes have been successfully committed to local git and pushed to the remote repository.
*   The repository is clean and ready for deployment.

---

# Progress Report - June 30, 2026

## 1. Accomplishments & Technical Updates

### 1.1 Universal & Room-based Security Refinement
*   **Problem:** Non-owner employees were restricted from viewing, commenting on, or modifying tickets within rooms they belonged to unless they were explicitly the creator or assignee. Additionally, universal room tickets triggered 403 authorization failures on details access, commenting, and attachments, and administrative roles (HR, IT Support, Executive) were incorrectly restricted by owner-only checks.
*   **Resolution:** Modified `backend/app/domains/tickets/router.py` to allow HR, IT Support, and Executive roles to bypass ticket visibility and mutation security barriers. Added room membership validation checks (`RoomMember`) across all CRUD endpoints so standard staff can view and collaborate on tickets in rooms they are members of, including all Universal room announcements.

### 1.2 Universal Room UI Controls Hiding
*   **Problem:** Universal room tickets do not require assignees or external room escalation, but the right-side properties panel and header bar still displayed the Assignee selection and Resolve/Re-open action buttons for Universal room tickets.
*   **Resolution:** Defined `isSelectedTicketUniversal` on the frontend. Wrapped the Resolve/Re-open action buttons and the right-side Assignee and Escalate selections in checks to hide them entirely for Universal room tickets.

### 1.3 Assignee Dropdown Dynamic Room Filtering
*   **Problem:** When creating a ticket or viewing properties, the assignee list showed only a manager's local branch staff instead of all members of the selected room (like IT Team or HR).
*   **Resolution:**
    1.  **Backend:** Updated `GET /api/v1/users` to accept an optional `room_id` query parameter to return all active employees belonging to that specific room.
    2.  **Frontend API:** Added the `fetchRoomMembers(roomId)` API client method.
    3.  **Frontend Components:** Updated both `CreateTicketDialog.tsx` and `page.tsx` to dynamically query `/api/v1/users?room_id=${roomId}` when a room is selected, populating the assignee dropdown with the exact list of members belonging to that room.

### 1.4 UI Copy Update
*   Renamed the `"Post Comment"` button in the ticket chat view to `"Respond"` and changed the pending status from `"Posting…"` to `"Responding..."`.

### 1.5 "All Tickets" Navigation Link & Role-Scoped Visibility
*   **Problem:** 
    1.  There was no way in the sidebar navigation (desktop sidebar or mobile drawer) to navigate back to the main "All Tickets" dashboard view (which fetches all tickets when no room parameter is in the URL).
    2.  Standard employees (Therapists/Cleaners) saw all tickets in the system's "All Tickets" view (when no room is selected), violating privacy bounds that require them to see only their assigned tickets.
*   **Resolution:**
    1.  **Frontend:** Added an "All Tickets" link with the `LayoutDashboard` icon at the top of the rooms list in both `layout.tsx` (desktop sidebar) and the mobile rooms drawer.
    2.  **Backend:** Refined the `get_tickets` endpoint security checks in `router.py`. When no `room_id` query parameter is selected:
        *   Owners, HR, IT Support, and Executives see all active tickets.
        *   Managers see tickets in their branch rooms, plus any tickets they created or are assigned to.
        *   Standard Staff/Therapists/Cleaners see ONLY tickets explicitly assigned to them (plus universal room announcements).
        *   If a specific `room_id` is passed, users continue to see room-level tickets if they have access to the room.

### 1.6 Multi-Room Escalate Assignee Support
*   **Problem:** After escalating/adding a ticket to another branch room (e.g., IT Team, Branch B), the Assignee dropdown did not show employees from the newly added room. This happened because the frontend queried users passing only the first room ID (`rooms[0].id`) to `fetchRoomMembers`.
*   **Resolution:**
    1.  **Backend:** Modified the `room_id` query parameter parsing in `users/router.py` to handle comma-separated room IDs (e.g. `room_id=uuid1,uuid2`) and return the union of all active members across those rooms (utilizing a `distinct()` query).
    2.  **Frontend:** Modified `page.tsx` to map over `selectedTicket.rooms` to compile a comma-separated list of all rooms currently linked to the ticket, feeding it into the dynamic assignee member query.

### 1.7 Searchable Assignee Selector
*   **Problem:** With large staff lists (e.g., 82+ employees), locating a specific assignee in the dropdown by scrolling was slow and tedious.
*   **Resolution:**
    *   Added a live search `<Input>` at the top of the Assignee select dropdown on both the **Ticket Details Properties Panel** (`page.tsx`) and the **Create Ticket Dialog** (`CreateTicketDialog.tsx`).
    *   Implemented client-side filtering matching typed search queries against employee `name` or `staff_id` (case-insensitive).
    *   Prevented dropdown keyboard navigation closure via `onKeyDown={(e) => e.stopPropagation()}` on the input.
    *   Automatically resets the search state on dropdown closure.

### 1.8 Case-Insensitive Search on Assignee Staff ID/Name
*   **Problem:** 
    1.  Radix UI `<SelectContent>` dropdown immediately closed when any interactive element inside it (like the search `<Input>`) was clicked.
    2.  The main ticket feed search bar only did exact match comparisons for `staff_id` on the backend, returning empty results for partial staff IDs or search queries containing employee names.
*   **Resolution:**
    1.  **Frontend Dropdown Fix:** Added pointer and mouse event propagation stops (`onPointerDown`, `onMouseDown`, `onClick`) on the search inputs inside `CreateTicketDialog.tsx` and `page.tsx` so Radix UI does not intercept clicks on the input and close the select dropdown.
    2.  **Backend Search Fix:** Updated `get_tickets` in `backend/app/domains/tickets/router.py` to perform case-insensitive partial searches (`ilike` with `%pattern%`) matching against **both** employee `staff_id` and employee `name`.
    3.  **UI Updates:** Renamed the search bar placeholder in `page.tsx` to `"Search by Staff ID or Name"`.

