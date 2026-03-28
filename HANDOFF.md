# North Orlando Handyman — System Handoff Guide

*Built by Waypoint Systems | Last updated: 2026-03-28*

---

## What's Built and Working Right Now

This is a custom CRM and lead management system built specifically for your business. Here's what's live today:

**Customer-facing:**
- Lead capture form at `/request` — mobile-friendly, photo upload, all your service types
- Quote approval page — customer gets a link, taps Approve or Decline
- Invoice and mock payment page (payment integration pending)

**Admin (you):**
- Dashboard with stat cards — new leads, open jobs, pending quotes, revenue
- Lead management — view, add notes, update status, convert to quote
- Quote builder — pre-loaded with suggested line items per service type (French Drain, Sprinkler, Faucet, etc.)
- Customer and job history
- Invoice management

**Infrastructure:**
- Hosted on Render Starter plan ($7/month) — never spins down
- Persistent disk at `/data` ($0.25/month) — data survives every deploy
- GitHub repo at github.com/tblankenship87/north-orlando-handyman (public — you can fork it)
- Auto-deploys when code is pushed

**Admin login:** admin / handyman2026 *(change this — see below)*

---

## What You Need to Do to Go Live

### Step 1 — Change Your Admin Password (5 minutes)
Right now the password is the default. Change it before sharing the URL with anyone.

1. Go to dashboard.render.com
2. Click north-orlando-handyman → Environment
3. Add env var: `ADMIN_PASS` → set it to whatever you want
4. Save — app restarts in 30 seconds

---

### Step 2 — Set Up Twilio for Lead Notifications (30 minutes)
Right now you get zero notification when a lead comes in. This is the most important thing to fix.

1. Sign up at twilio.com (free trial, ~$15 to fund)
2. Get a phone number (costs ~$1/month)
3. From your Twilio console, grab:
   - Account SID
   - Auth Token
   - Your Twilio phone number
4. Add these to Render environment variables:
   - `TWILIO_ACCOUNT_SID` = your SID
   - `TWILIO_AUTH_TOKEN` = your token
   - `TWILIO_FROM` = your Twilio number (format: +14075550100)
   - `TWILIO_ALERT_TO` = your personal cell (format: +14075550100)
5. Tell your developer (or AI agent) to wire up the notification in `app.py` — it's about 10 lines of code in the `request_form()` route

**What you'll get:** A text to your phone the instant a customer submits a request. Includes their name, phone number, and service type.

---

### Step 3 — Set Up SendGrid for Email (30 minutes)
So customers automatically receive their quote link by email instead of you copy-pasting it.

1. Sign up at sendgrid.com (free tier = 100 emails/day, plenty)
2. Verify your sender email (use tyler@northorlandohandyman.com or your Gmail)
3. Create an API key
4. Add to Render environment variables:
   - `SENDGRID_API_KEY` = your key
   - `SENDGRID_FROM` = your verified sender email
5. Tell your developer to wire it up in the quote send route — about 15 lines

**What you'll get:** When you hit "Send Quote" in the admin, the customer automatically gets an email with their quote link. Professional, no copy-paste.

---

### Step 4 — Set Up Stripe for Real Payments (1 hour)
Right now the Pay Now button is a demo — no real money moves.

1. Sign up at stripe.com (free — they take 2.9% + 30¢ per transaction)
2. Complete business verification
3. From your Stripe dashboard → Developers → API Keys:
   - Copy your Publishable Key and Secret Key
4. Add to Render environment variables:
   - `STRIPE_SECRET_KEY` = your secret key
   - `STRIPE_PUBLISHABLE_KEY` = your publishable key
5. Tell your developer to replace the mock payment in `invoice_view()` with a real Stripe checkout session

**What you'll get:** Customers can actually pay invoices online. Money hits your bank account via Stripe's standard payout schedule (2 business days by default).

---

### Step 5 — Set Up Calendly for Scheduling (15 minutes)
So customers can book their own appointment after approving a quote.

1. Sign up at calendly.com (free tier works)
2. Connect your Google Calendar
3. Set your availability (what days/hours you're available for jobs)
4. Copy your Calendly link (looks like calendly.com/your-name/handyman-job)
5. Add to Render environment variables:
   - `CALENDLY_URL` = your link
6. Tell your developer to add a "Schedule Your Appointment" button to the quote approval page that links to this URL

**What you'll get:** After a customer approves your quote, they see a button to pick a time slot. It books directly to your Google Calendar. No back-and-forth texting about availability.

---

### Step 6 — Point Your Domain (15 minutes)
Add a subdomain so customers can book at a real URL instead of the Render default.

Option A — **Use a subdomain** (recommended, keeps your existing site intact):
- Add a CNAME record in your domain DNS:
  - Name: `app` (or `book` or `portal`)
  - Target: `north-orlando-handyman.onrender.com`
- Add the custom domain in Render dashboard → Settings → Custom Domains
- Result: customers go to `app.northorlandohandyman.com`

Option B — **Replace your main site**:
- Point `northorlandohandyman.com` directly to this app
- Your existing site goes away — only do this if you're ready to replace it

---

### Step 7 — Update Your Service Rates (30 minutes)
The quote builder has suggested pricing but it's ballpark numbers. You need to set your actual rates.

In the GitHub repo, open `app.py` and find `SERVICE_QUOTE_TEMPLATES`. Update the `unit_price` values to match what you actually charge. You can do this with any AI agent — just paste the section and say "update these prices."

---

## Taking Full Ownership of the Code

If you want to own the codebase yourself:

1. Create a GitHub account at github.com
2. Go to github.com/tblankenship87/north-orlando-handyman
3. Click **Fork** (top right) — creates your own copy
4. Create a Render account at render.com
5. Connect your forked GitHub repo to a new Render web service
6. Add your environment variables
7. Add the persistent disk (/data, 1GB)
8. Your app is now 100% yours — Tyler's copy is just the demo

---

## Monthly Cost Summary (fully operational)

| Item | Cost |
|---|---|
| Render hosting | $7.00/month |
| Render disk (database) | $0.25/month |
| Twilio phone number | ~$1.00/month |
| Twilio SMS (~200 texts) | ~$2.00/month |
| SendGrid email | Free |
| Stripe | 2.9% + 30¢ per payment |
| Calendly | Free |
| **Total fixed** | **~$10.25/month** |

At one job per month you've paid for the whole system.

---

## What Your AI Agent Can Build Next

Once the above is done, here's what to ask your AI agent to add:

- **Google Review request** — after marking a job complete, automatically text the customer a Google Review link
- **Automated follow-up** — if a lead hasn't heard back in 24 hours, auto-text them
- **Recurring jobs** — for customers who want regular maintenance visits
- **Job photos** — let Kyle upload before/after photos to a job record
- **Customer portal login** — let repeat customers log in to see all their job history
- **Upgrade to PostgreSQL** — swap SQLite for a proper database when volume grows

Each of these is 1-3 hours of work for an AI agent with the codebase context.

---

## How to Give Your AI Agent Context

When starting a new session with your AI agent, paste this:

> "I have a Flask CRM app at github.com/[your-username]/north-orlando-handyman. It uses Flask + SQLAlchemy + SQLite + Bootstrap 5. The main file is app.py. I need you to [describe what you want]. Here are my current environment variables: [list them]."

That gives the agent everything it needs to pick up right where we left off.

---

*Questions? The codebase is clean and well-commented. Any competent developer or AI agent can extend it.*
