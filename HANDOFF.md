# North Orlando Handyman — System Handoff Guide

*Built by Waypoint Systems (Tyler Blankenship + Atlas AI) | Last updated: 2026-03-28*

---

## Live URL

**`north-orlando-handyman.onrender.com`**

Admin login: `admin` / `handyman2026` *(change this before going live — see Step 1)*

---

## What's Built and Working Right Now

### Customer-Facing Pages

**`/book`** — Public booking page (this is your homepage)
- Hero with two clear paths: flat-rate booking or custom estimate
- 16 flat-rate services organized by category (Bathroom, Kitchen, Electrical, Doors/Walls)
- Each service card has photo, description, time estimate, and flat price
- "Book This →" pre-fills the request form for that specific service
- How It Works (4 steps)
- Customer reviews section (3 placeholder reviews — replace with your real Google reviews)
- Service area section (Seminole County cities)
- 1-Year Workmanship Guarantee section
- FAQ
- "Got a bigger project?" banner linking to estimate form

**`/request`** — Lead capture / estimate request form
- Works for both flat-rate bookings and custom quote requests
- Flat-rate bookings show a "Flat-Rate Booking" banner with the confirmed price
- Upload up to 5 photos (stored in database, no external storage needed)
- Mobile-friendly, works on iPhone and Android

**`/quote/<token>`** — Customer quote approval page
- Customer sees line items, total, and notes
- One tap to Approve or Decline
- Approved quotes trigger job creation in admin

**`/invoice/<token>`** — Customer invoice and payment page
- Shows invoice total
- Mock payment flow (replace with Square — see Step 4)

### Admin Panel (`/admin`)

- **Dashboard** — stat cards (new leads, open jobs, pending quotes, revenue), recent leads with phone numbers, quick action buttons, one-tap booking link copy
- **Leads** — full lead list with phone, status filters, view/edit each lead
- **Lead Detail** — view all customer photos (grid), update status, add notes, convert to quote
- **Quote Builder** — pre-populated line items per service type, editable, tax field, notes
- **Quote Detail** — view quote, edit quote, discard quote (resets lead to queue), send link
- **Jobs** — track job status from pending → complete
- **Invoices** — track payment status
- **Customers** — full customer history

### Infrastructure

- Hosted on Render Starter plan ($7/month) — always on, no cold starts
- Persistent disk at `/data` ($0.25/month) — database survives every code deploy
- GitHub: `github.com/tblankenship87/north-orlando-handyman` (public — fork to own it)
- Auto-deploys on every push to `main` branch
- Stack: Python/Flask + SQLite + Bootstrap 5 (no frameworks, easy to extend)

---

## What You Need to Plug In

### Step 1 — Change Admin Password (5 min)
Go to `dashboard.render.com` → north-orlando-handyman → Environment → add:
- `ADMIN_PASS` = your chosen password

---

### Step 2 — Connect n8n Webhook (15 min)
Every lead submission fires a POST to your n8n webhook automatically.

Add to Render environment variables:
- `N8N_WEBHOOK_URL` = your n8n webhook URL

**Payload sent to n8n on every lead:**
```json
{
  "id": 42,
  "name": "Jane Smith",
  "phone": "4075550100",
  "email": "jane@example.com",
  "address": "123 Main St, Lake Mary FL",
  "service_type": "Bathroom Fan Replacement",
  "description": "Fan is noisy and slow",
  "preferred_date": "2026-04-05",
  "tier": "1",
  "photo_count": 3,
  "submitted_at": "2026-03-28T14:00:00",
  "admin_url": "https://north-orlando-handyman.onrender.com/admin/leads/42"
}
```

From n8n you can wire this to: Google Sheets, SMS via Twilio, Google Calendar, Square, email — whatever your workflow needs.

---

### Step 3 — Add Your Real Content (1 hour)

**Service prices** — in `app.py`, find `FLAT_RATE_SERVICES`. Update the `"price"` value on each service to match what you actually charge.

**Service photos** — replace the `"photo_url"` Unsplash links with real photos of your work. Upload to Google Drive or Imgur and paste the direct URL.

**Reviews** — in `templates/book.html`, find the reviews section. Replace the 3 placeholder reviews with real quotes from your Google reviews.

**Phone number** — search `templates/book.html` for `(407) 123-4567` and replace with your real number.

**Service area** — in `templates/book.html`, update the city tags if you serve areas outside Seminole County.

---

### Step 4 — Square Payments for Deposits (1-2 hours)
You said you use Square. When you're ready to collect deposits at booking:

1. Get your Square API credentials from `developer.squareup.com`
2. Add to Render env vars: `SQUARE_ACCESS_TOKEN`, `SQUARE_LOCATION_ID`
3. Tell your AI agent: *"Wire up Square Checkout in the request form for tier-1 flat-rate bookings. Charge a $50 deposit at booking time using Square. Credentials are in the env vars."*

---

### Step 5 — Google Calendar Integration (via n8n)
Since you're using n8n — handle calendar from there. When a lead comes in with `tier: "1"`:
- n8n creates a Google Calendar event
- n8n sends a confirmation SMS to the customer
- No code changes needed on this side

---

### Step 6 — Point Your Domain (15 min)

**Option A — Subdomain (keep existing WordPress site):**
Add a CNAME in your DNS:
- Name: `book` (or `app`)
- Target: `north-orlando-handyman.onrender.com`
Result: customers go to `book.northorlandohandyman.com`

**Option B — Replace your main site:**
Point `northorlandohandyman.com` directly to this app. Your WordPress site goes away.

---

### Step 7 — Postgres + DigitalOcean Spaces (when you're ready to scale)
You mentioned wanting Postgres and DO Spaces eventually. Current setup handles hundreds of leads fine on SQLite. When you hit volume:

- **Postgres**: Render has a free Postgres tier. Tell your AI agent: *"Migrate the app from SQLite to Postgres. Add DATABASE_URL env var pointing to Render Postgres."*
- **DO Spaces**: For photo storage outside the DB. Tell your AI agent: *"Move photo storage from base64-in-SQLite to DigitalOcean Spaces. Use boto3 with DO endpoint."*

---

## Taking Full Ownership

1. Create a GitHub account if you don't have one
2. Go to `github.com/tblankenship87/north-orlando-handyman` → **Fork**
3. Create a Render account → connect your forked repo → new web service
4. Add the persistent disk (Disks → `/data`, 1GB)
5. Add your env vars
6. Done — you own it, Tyler's copy is just the demo

---

## Monthly Cost (fully operational)

| Item | Cost |
|---|---|
| Render hosting | $7.00/month |
| Render disk | $0.25/month |
| Square | 2.6% + 10¢ per transaction |
| n8n cloud (optional) | $20/month or self-host free |
| **Total fixed** | **~$7.25/month** |

---

## How to Brief Your AI Agent

Paste this at the start of any new session:

> "I have a Flask web app at github.com/[your-username]/north-orlando-handyman. Stack: Python/Flask, SQLAlchemy, SQLite (persistent on Render disk at /data), Bootstrap 5. The main file is app.py. It's a handyman booking and CRM system for North Orlando Handyman. Current env vars on Render: SECRET_KEY, DATABASE_URL, N8N_WEBHOOK_URL. I need you to [describe what you want]."

---

## What to Build Next

Ask your AI agent for any of these — each is 1-3 hours:

- **SMS confirmation to customer** on form submit (Twilio, ~30 min)
- **Google Review request SMS** after job marked complete
- **Embeddable booking widget** for your WordPress site (iframe or JS embed)
- **Multi-service cart** — let customers book multiple services in one request (like North Seattle)
- **Before/after photo uploads** by admin on job completion
- **Customer portal** — repeat customers log in to see job history
- **Automated follow-up** — if lead hasn't heard back in 24h, auto-text

---

*Codebase is clean, well-commented, and fully yours. Any AI agent or developer can pick it up from this doc.*
