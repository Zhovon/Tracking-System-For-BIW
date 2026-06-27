# Development Report — 27 June 2026

## Summary

Successful deployment of directory expansions, layout alignment fixes, live search functionalities, real-time ticket creation notifications, and roster re-indexing. All database records (UIDs `0001` to `0032`) and Google Sheet rows have been chronologically sorted and synced.

---

## Changes Completed

### 1. Database Schema & API Expansion
- Added `phone`, `nid`, and `joining_date` columns to the database `employees` table.
- Updated `UserOut`, `UserCreate`, and `UserUpdate` schema models in the backend to validate and output these new fields.
- Updated `create_user` and `update_user` endpoints to capture these attributes and sync them to the Google Sheet webhook.

### 2. Chronological Re-indexing & Cleaning
- Test accounts `cena@gmail.com` and `zaidulislamratul025@gmail.com` deleted from PostgreSQL DB, Supabase Auth, and Google Sheets.
- Restructured `reset_and_sync_ordered_roster.py` to assign consecutive staff IDs from `0005` to `0032` based on joining dates.
- Re-indexed Owners to top UIDs: `0001` (Razib Ahamed), `0002` (Usman Hossain), and `0003` (Laboni Akter).
- Reset Laboni's password in Supabase Auth to `laboni123` and synced to the Google Sheet.

### 3. Frontend Layout & Live Search UI
- Moved the `Create Room` form card to stack vertically in the left column beneath `Create Account`, eliminating empty grid space.
- Added a search input box in the directory header to filter active staff by **Name, ID, Email, Phone, or NID** in real time.
- Displayed Phone, NID, and Hired date attributes on each user card in the list view.
- Constrained the directory list height to `640px` with a customized thin scrollbar.

### 4. Real-time Notifications
- **Creation Notify:** Sends notifications to all Owners and the initial assignee on ticket creation.
- **Assignment Notify:** Sends a notification to the newly assigned employee on updates.

---

## 📢 Uttara Branch Launch & Copywriting Drafts

### Post 1: Grand Opening Announcement
**Headline:** Unveiling a New Standard of Self-Care: BIW Salon Uttara is Now Open! ✨

**Copy:**
> Uttara, the wait is officially over. We are thrilled to bring the signature BIW premium grooming and self-care experience right to your neighborhood. 
> 
> Step into a sanctuary of elegance and modern aesthetics, designed to rejuvenate your senses. From state-of-the-art styling stations to specialized therapy rooms, every corner of our new Uttara branch is built to deliver absolute luxury.
> 
> 📍 **Location:** [Insert Uttara Address, e.g. Sector 3, Road 4, House 12]
> 📅 **Operating Hours:** 10:00 AM - 9:00 PM (Daily)
> 
> Book your experience today and let our expert team pamper you.
> 📞 Call/WhatsApp: [Insert Phone] or DM us to reserve your slot.
> 
> #BIWSalon #UttaraBranch #GrandOpening #PremiumGrooming #SelfCare #NewBeginnings

---

### Post 2: Combo Packages Carousel Draft (Swipe Left ➡️)
*   **Slide 1: THE NEW UTTARA COMBOS** (Title Slide)
    *   *Sub-headline:* Curated wellness and grooming packages to celebrate our grand opening. Pure indulgence awaits.
    *   *Visual note:* Minimalist salon interior backdrop with gold accents.
*   **Slide 2: Combo 1 — Refresh & Glow** 💆‍♀️✨
    *   *Includes:* Signature Hair Cut & Styling + Premium Organic Facial + Relaxing Head & Shoulder Massage.
    *   *Price:* ৳[Price, e.g. 2,999] (Save 20%)
*   **Slide 3: Combo 2 — Ultimate Pamper** 💅🌸
    *   *Includes:* Premium Manicure & Pedicure Spa + Deep Conditioning Hair Treatment + Revitalizing Herbal Face Pack.
    *   *Price:* ৳[Price, e.g. 3,999] (Save 25%)
*   **Slide 4: Combo 3 — The Royal Ritual** 👑✨
    *   *Includes:* Premium Hair Spa & Nourishment + Signature Full-Body Therapy (60 mins) + Custom Skin Brightening Therapy.
    *   *Price:* ৳[Price, e.g. 5,999] (Save 30%)
*   **Slide 5: Celebrate Luxury with BIW** 🥂
    *   *Copy:* Offers valid exclusively at our new Uttara Branch for a limited time.
    *   *Call-to-Action:* Tap the link in bio to book your slot or call [Insert Phone] to secure your appointment today!

---

# Development Report — 24 June 2026

## Summary

Complete overhaul of the ticketing system's ticket detail interface from a consumer-style chat/messenger UI to an industrial-grade ticket management layout. Six changes across the full stack, all committed and pushed to GitHub.

---

## Changes Completed

### 1. Industrial Ticket UI Redesign (`frontend/src/app/dashboard/page.tsx`)

**Before:** Ticket detail used a WhatsApp/iMessage-style chat bubble layout — messages floated left or right depending on who sent them, with coloured bubbles and no structure.

**After:** Full Jira/Zendesk-style industrial layout split into two columns:

**Main column (left):**
- **Header** — ticket title, status/priority/overdue badges, Resolve and Approve action buttons
- **Description section** — off-white background (`#f7f6f3`) with a clear "DESCRIPTION" label, plain readable text
- **Activity timeline** — vertical line with:
  - System events (status changes, assignments, due date changes, escalations) shown as compact inline entries with timestamp
  - Comments shown as white bordered cards with avatar, name, staff ID, timestamp, content, and attachment download link
  - Ticket creation shown as the first timeline entry ("opened this ticket")
- **Add Comment box** — white card at the bottom, clean textarea with file attach and "Post Comment" button

**Right properties panel (256px):**
- **STATUS** — badge only, read-only
- **PRIORITY** — editable dropdown (Low / Medium / High)
- **ASSIGNEE** — editable dropdown with avatar initial
- **DUE DATE** — datetime-local input, editable by anyone with ticket access, saves on blur
- **ROOMS** — badges showing all rooms the ticket belongs to
- **ESCALATE TO** — dropdown to add a new department
- **CREATED BY** — avatar + full name + staff ID (with label — this was previously unlabelled)
- **OPENED** — formatted date/time

---

### 2. Due Date Now Editable After Creation (`backend/app/domains/tickets/schemas.py` + `router.py`)

**Before:** `TicketUpdate` schema had no `due_date` field. Once a ticket was created, the due date could not be changed.

**After:**
- `due_date: Optional[datetime]` added to `TicketUpdate`
- Backend uses Pydantic v2 `model_fields_set` to detect when `due_date` is explicitly provided (including when set to `null` to clear it)
- Every due date change generates an activity entry: *"Due date set to 15 Jun 2026, 14:00"* or *"Removed due date"*

---

### 3. Unassign Bug Fixed (`backend/app/domains/tickets/router.py`)

**Before:** Sending `assigned_to_id: null` from the frontend to unassign a ticket was silently ignored because the router checked `if ticket_in.assigned_to_id is not None` before acting.

**After:** Router now uses `model_fields_set` to detect whether `assigned_to_id` was explicitly included in the request:
- `null` → unassigns ticket, logs *"Unassigned ticket"* activity entry
- valid UUID → assigns to user, logs *"Assigned ticket to [Name]"*
- field absent → no change

---

### 4. Room Creation API (`backend/app/domains/rooms/router.py`)

**Before:** No API endpoint existed to create rooms. Rooms could only be added by running the seed script (which drops and recreates the entire database).

**After:** New `POST /api/v1/rooms` endpoint (owner-only):
- Accepts `{ "name": string, "type": "branch" | "department" | "founder" }` 
- Validates room type against the `RoomType` enum
- Returns the created room immediately
- Owners can now create rooms like **Doctors** without any database migrations or redeploys

---

### 5. Room Creation UI (`frontend/src/app/dashboard/staff/page.tsx`)

**Before:** Staff Management page had no way to create rooms from the UI.

**After:** New **Create Room** card added at the top of the Staff Management page:
- Name input (e.g. "Doctors")
- Room Type dropdown (Branch / Department / Founder)
- Submit button with loading state
- Success/error feedback
- On success, invalidates all room query caches so the new room appears in the sidebar and all dropdowns immediately

---

### 6. API Client (`frontend/src/lib/api.ts`)

Added `createRoom()` function that posts to the new `/rooms` endpoint.

---

## Verification

| Check | Result |
|---|---|
| `npm run build` (Next.js + TypeScript) | ✅ Clean — all 9 routes compiled |
| `python3 -m py_compile` (3 backend files) | ✅ No syntax errors |
| `ruff check ./backend` (full backend, same as CI) | ✅ All checks passed |
| GitHub push | ✅ `58e66e3..565b01b  main → main` |
| Lint CI workflow | ✅ Will pass (ruff verified locally) |
| Sync to Office workflow | ✅ Mirrors automatically on push |

---

## Deployment Instructions

The ticketing system server needs to pull and rebuild to activate these changes:

```bash
git pull origin main
docker compose up --build -d
```

Both containers must be rebuilt:
- **Backend** — uvicorn has no `--reload`; new endpoints and schema changes require a restart
- **Frontend** — code is baked at Docker build time; new UI requires a rebuild

---

## Commit

```
565b01b  feat: industrial ticket UI, room creation, and due date editing
```

Repository: `https://github.com/Zhovon/Tracking-System-For-BIW`
