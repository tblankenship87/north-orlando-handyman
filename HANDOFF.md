# Your Business CRM — Ownership Handoff Guide

Welcome. This document covers everything you own, where it lives, and how to manage it.

---

## What You Have

A custom web application built specifically for your business. It handles:

- Lead capture (customers submit job requests from their phone)
- Admin dashboard (you see every lead the moment it comes in)
- Quote builder (build and send estimates with a shareable link)
- Customer approval (customer taps Approve on their phone)
- Invoicing and payment collection
- Customer and job history database

Everything is yours. The code, the data, the domain. Nobody else has access.

---

## The Three Things You Own

### 1. The Code — GitHub
**Where:** github.com/[your-username]/[your-repo]

GitHub is where your code lives. Think of it like Google Drive for code. Every change ever made is saved and reversible. You don't need to touch this unless you're making changes.

**What you can do here:**
- Browse every file in the app
- See the history of every change ever made
- Share access with a developer if you ever hire one
- Fork (copy) the entire codebase

**Your login:** Create a free account at github.com if you don't have one. Tyler will transfer the repo to you.

---

### 2. The Hosting — Render
**Where:** dashboard.render.com

Render is what keeps your app running 24/7 on the internet. It's like renting a computer in the cloud that never turns off.

**Cost:** $7/month (billed to your credit card)

**What you can do here:**
- See if your app is online (green = running)
- View logs if something breaks
- Set environment variables (passwords, API keys — never put these in code)
- Redeploy manually if needed

**Your environment variables (the important ones):**

| Variable | What it does |
|---|---|
| `SECRET_KEY` | Encrypts your session data. Never share this. |
| `ADMIN_USER` | Your admin login username |
| `ADMIN_PASS` | Your admin login password — change this from the default |
| `DATABASE_URL` | Where your database lives |

**To change your admin password:** Go to Render dashboard → your service → Environment → find `ADMIN_PASS` → update it → Save. App restarts in 30 seconds.

---

### 3. The Database — SQLite (upgradeable to PostgreSQL)

Your data (leads, customers, quotes, invoices) lives in a database file. The current setup uses SQLite — simple and reliable for getting started.

**Important:** On the current plan, the database resets if Render redeploys. To make it permanent, upgrade to PostgreSQL (free via Supabase). Ask your developer when you're ready.

---

## Your Admin Panel

**URL:** your-app-url.onrender.com/admin

**Default login:**
- Username: `admin`
- Password: `handyman2026`

**Change your password immediately** via Render environment variables (see above).

---

## How Updates Work

If you ever want to change something in the app (add a service, change wording, add a feature):

1. A developer makes the change in the GitHub repo
2. Render detects the change automatically
3. App redeploys in about 2 minutes
4. Your live URL updates with no downtime

You never have to touch a server. That's handled automatically.

---

## Things You Can Change Yourself (No Developer Needed)

**Change your admin password:** Render dashboard → Environment variables

**Add/remove services from the request form:** Requires a one-line code edit in `app.py` — any developer or AI assistant can do this in 5 minutes

**Change the business name or phone number:** Small edit in the HTML templates — again, 5 minutes with AI help

---

## If Something Breaks

1. Go to dashboard.render.com
2. Click your service
3. Click "Logs"
4. Screenshot the red error text
5. Send it to your developer

90% of issues show up clearly in the logs.

---

## What's Not Built Yet (Future Add-Ons)

These can be added when you're ready:

- **Text notification when a lead comes in** — Twilio, ~$5/month
- **Auto-email the quote link to customers** — SendGrid, free tier
- **Real Stripe payments** — 2.9% + 30 cents per transaction, no monthly fee
- **Persistent database** — Supabase free tier (upgrade from SQLite)
- **Custom domain** — point your existing domain to this app, ~$10/year

---

## Monthly Cost Summary

| Item | Cost |
|---|---|
| Render hosting | $7/month |
| Domain (optional) | ~$1/month |
| Twilio SMS (optional) | ~$5/month |
| Stripe (optional) | 2.9% per payment |
| **Total to start** | **$7/month** |

---

## Transfer Checklist (Tyler to Customer)

- [ ] Customer creates GitHub account
- [ ] Tyler transfers repo ownership (Settings → Transfer in GitHub)
- [ ] Customer creates Render account at render.com
- [ ] Customer connects GitHub repo to new Render account
- [ ] Customer adds payment method to Render ($7/month)
- [ ] Customer deletes Tyler's Render service (stops billing Tyler)
- [ ] Customer changes ADMIN_PASS in Render environment variables
- [ ] Customer confirms app is live at their Render URL
- [ ] Optional: Customer points their domain to the Render URL

---

*Built by Waypoint Systems. Questions? Contact Tyler Blankenship.*
