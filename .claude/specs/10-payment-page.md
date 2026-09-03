# Spec: Payment Page

## Overview
The Payment Page allows Spendly users to explore subscription plans (Free vs Spendly Pro), select an upgrade tier, and complete a checkout flow to activate premium account features. Premium status unlocks advanced financial capabilities such as unlimited expense tracking, multi-category budgeting, receipt attachments, CSV/PDF export, and priority analytics. This feature introduces monetization and plan management to the Spendly platform.

## Depends on
- Step 1: Database Setup (`database/db.py`, `users` table)
- Step 2: Registration (User account creation)
- Step 3: Login & Logout (Session management and protected routes)
- Step 4: User Profile (Viewing and managing account details)

## Routes
- `GET /pricing` — Displays subscription plans (Free vs Pro) and pricing tiers — public/logged-in
- `GET /checkout/<plan_id>` — Displays checkout page with selected plan details and payment form — logged-in
- `POST /checkout/<plan_id>` — Processes payment details, activates Pro subscription, and redirects to confirmation — logged-in
- `GET /payment/success` — Displays payment confirmation, transaction receipt, and updated account status — logged-in

## Database changes
Add `subscriptions` table in `database/db.py`:
- `subscriptions` table:
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `user_id` INTEGER NOT NULL (FK -> `users(id)` ON DELETE CASCADE)
  - `plan_id` TEXT NOT NULL
  - `amount` REAL NOT NULL
  - `payment_method` TEXT NOT NULL
  - `status` TEXT NOT NULL DEFAULT 'active'
  - `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Templates
- **Create:**
  - `templates/pricing.html` — Subscription plan comparison (Free vs Pro) with features checklist and upgrade buttons.
  - `templates/checkout.html` — Order summary, billing details, payment method selection (Card / UPI), and submit button.
  - `templates/payment_success.html` — Confirmation page with payment receipt summary and link to profile.
- **Modify:**
  - `templates/base.html` — Add "Pricing" / "Upgrade" link in navbar.
  - `templates/profile.html` — Display active subscription badge (Free / Pro) with upgrade button.

## Files to change
- `app.py` — Add `/pricing`, `/checkout/<plan_id>`, and `/payment/success` route handlers with validation and session protection.
- `database/db.py` — Add `subscriptions` table schema to `init_db()`.
- `static/css/style.css` — Add styles for pricing cards, checkout summary, payment form fields, plan badges, and confirmation receipt.
- `templates/base.html` — Update navigation with pricing link.
- `templates/profile.html` — Display plan tier badge.

## Files to create
- `templates/pricing.html` — Pricing plans comparison page.
- `templates/checkout.html` — Payment checkout template.
- `templates/payment_success.html` — Payment confirmation template.
- `tests/test_payment.py` — Test suite for pricing display, checkout authentication guard, payment validation, subscription persistence, and success receipt.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Protect checkout routes: redirect unauthenticated users to `/login`
- Validate payment input fields (Card Number, Expiry, CVV, or UPI ID) before processing
- Automatically insert transaction record in `subscriptions` table upon successful payment
- Ensure responsive layout for pricing cards and checkout form across mobile and desktop

## Definition of done
- [ ] Navigating to `GET /pricing` renders the pricing plans with Free and Pro feature comparisons.
- [ ] Clicking "Upgrade to Pro" while unauthenticated redirects to `/login`.
- [ ] Navigating to `GET /checkout/pro` while logged in displays plan summary and payment form.
- [ ] Submitting invalid payment form fields on `POST /checkout/pro` displays descriptive validation errors.
- [ ] Submitting valid payment form upgrades the user's subscription and records the transaction in `subscriptions` table.
- [ ] Successful checkout redirects to `GET /payment/success` showing transaction details and receipt.
- [ ] User profile page reflects updated "Pro Member" badge.
- [ ] All automated tests in `tests/test_payment.py` pass.
