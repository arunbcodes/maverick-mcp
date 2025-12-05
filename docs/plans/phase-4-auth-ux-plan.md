# Phase 4: Auth Flow & User Experience Plan

## Overview

Complete the authentication experience and user onboarding flow, from basic auth testing through demo mode and onboarding.

## Phase 4A: Auth Flow Testing & Polish

### Scope
Ensure core authentication works end-to-end in Docker environment.

### Tasks

#### 4A.1: Database Migration Setup
- [ ] Create migration script for Docker initialization
- [ ] Ensure `users` table exists with proper schema
- [ ] Add `api_keys` table migration
- [ ] Create `portfolios` and `positions` tables
- [ ] Add migration to docker-compose startup

#### 4A.2: Registration Flow
- [ ] Test registration form validation (email, password strength)
- [ ] Verify user creation in PostgreSQL
- [ ] Test duplicate email handling
- [ ] Add password confirmation field
- [ ] Implement proper error messages

#### 4A.3: Login Flow
- [ ] Test login with valid credentials
- [ ] Test login with invalid credentials
- [ ] Verify JWT token generation and storage
- [ ] Test session persistence (refresh tokens)
- [ ] Add "Remember me" functionality

#### 4A.4: Protected Routes
- [ ] Verify redirect to login for unauthenticated users
- [ ] Test redirect back to original page after login
- [ ] Verify logout clears session properly
- [ ] Test token expiration handling

#### 4A.5: Password Reset (New Feature)
- [ ] Add "Forgot Password" link on login page
- [ ] Create password reset request endpoint
- [ ] Implement reset token generation (time-limited)
- [ ] Create password reset form
- [ ] Add email notification (or console log for dev)

### Deliverables
- Working registration → login → dashboard flow
- Password reset functionality
- Proper error handling and user feedback

---

## Phase 4B: Demo Mode / Guest Access

### Scope
Allow users to explore the app without creating an account.

### Tasks

#### 4B.1: Demo User Setup
- [ ] Create seeded demo user in database
- [ ] Pre-populate demo portfolio with sample positions
- [ ] Add sample watchlist for demo user
- [ ] Create demo screening results

#### 4B.2: Guest Access Flow
- [ ] Add "View Demo" button on home page
- [ ] Create guest session (read-only token)
- [ ] Implement demo user auto-login
- [ ] Add "Demo Mode" banner in dashboard
- [ ] Disable destructive actions in demo mode

#### 4B.3: Demo Data
- [ ] Sample portfolio: 5-10 diverse positions
  - AAPL, MSFT, GOOGL (tech)
  - JPM, BAC (finance)
  - JNJ, PFE (healthcare)
  - XOM (energy)
- [ ] Historical transactions for performance charts
- [ ] Sample API keys (masked)

#### 4B.4: Demo Restrictions
- [ ] Prevent adding/editing positions (show upgrade prompt)
- [ ] Prevent creating API keys
- [ ] Prevent changing settings
- [ ] Add "Create Account to Save" CTA buttons

### Deliverables
- One-click demo access
- Fully functional read-only experience
- Clear upgrade prompts

---

## Phase 4C: Onboarding Flow

### Scope
Guide new users through initial setup after registration.

### Tasks

#### 4C.1: Welcome Modal
- [ ] Create welcome modal component
- [ ] Show on first login (track `onboarding_completed` flag)
- [ ] Feature highlights with icons
- [ ] "Get Started" CTA

#### 4C.2: Setup Wizard
- [ ] Step 1: Profile setup (optional name, timezone)
- [ ] Step 2: Add first position (guided form)
- [ ] Step 3: Create watchlist (suggest popular stocks)
- [ ] Step 4: Explore screener (quick tour)
- [ ] Progress indicator

#### 4C.3: Contextual Help
- [ ] Add tooltip hints on first visit to each page
- [ ] "What's this?" info buttons
- [ ] Keyboard shortcut hints
- [ ] Link to documentation

#### 4C.4: Empty States
- [ ] Design empty portfolio state with CTA
- [ ] Empty watchlist state
- [ ] Empty screener results explanation
- [ ] Encouraging copy and illustrations

### Deliverables
- Smooth first-time user experience
- Guided setup wizard
- Contextual help system

---

## Phase 4D: Admin & Data Seeding

### Scope
Administrative tools and database initialization for production readiness.

### Tasks

#### 4D.1: Admin User Creation
- [ ] Create `scripts/create-admin.py` script
- [ ] Admin role in user model
- [ ] Secure admin creation (CLI only, not API)
- [ ] Admin can view all users (future admin panel)

#### 4D.2: Database Seeding Scripts
- [ ] `scripts/seed-demo-data.py` - Demo user and portfolio
- [ ] `scripts/seed-stocks.py` - S&P 500 stock metadata
- [ ] `scripts/seed-screening.py` - Pre-calculated screening results
- [ ] Make seeding idempotent (safe to run multiple times)

#### 4D.3: Docker Initialization
- [ ] Add init container or entrypoint script
- [ ] Run migrations on startup
- [ ] Seed demo data if empty
- [ ] Health check waits for seeding

#### 4D.4: Data Management
- [ ] Add `make seed-db` command
- [ ] Add `make reset-db` command (dev only)
- [ ] Add `make backup-db` command
- [ ] Document data management in README

### Deliverables
- Admin user management
- Automated database seeding
- Production-ready initialization

---

## Implementation Order

```
Phase 4A (Auth Flow)     ████████░░░░░░░░  ~2-3 days
Phase 4B (Demo Mode)     ░░░░░░░░████░░░░  ~1-2 days
Phase 4C (Onboarding)    ░░░░░░░░░░░░████  ~2-3 days
Phase 4D (Admin/Seeding) ░░░░░░░░░░░░░░██  ~1 day
                         ─────────────────
                         Total: ~6-9 days
```

## Technical Considerations

### Database Schema Additions

```sql
-- User flags for onboarding
ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN is_demo_user BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints to Add

```
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
POST /api/v1/auth/demo-login
GET  /api/v1/users/me/onboarding
POST /api/v1/users/me/onboarding/complete
```

### Frontend Components to Create

```
components/
├── auth/
│   ├── forgot-password-form.tsx
│   ├── reset-password-form.tsx
│   └── demo-login-button.tsx
├── onboarding/
│   ├── welcome-modal.tsx
│   ├── setup-wizard.tsx
│   ├── step-profile.tsx
│   ├── step-first-position.tsx
│   ├── step-watchlist.tsx
│   └── step-explore.tsx
└── ui/
    ├── empty-state.tsx
    ├── demo-banner.tsx
    └── tooltip-hint.tsx
```

## Success Criteria

### Phase 4A
- [ ] User can register and login successfully
- [ ] Invalid credentials show proper error
- [ ] Password reset flow works end-to-end
- [ ] Protected routes redirect correctly

### Phase 4B
- [ ] "View Demo" works with one click
- [ ] Demo portfolio shows realistic data
- [ ] Demo restrictions prevent modifications
- [ ] Clear upgrade prompts displayed

### Phase 4C
- [ ] New users see welcome modal
- [ ] Setup wizard completes successfully
- [ ] Onboarding can be skipped
- [ ] Empty states guide users

### Phase 4D
- [ ] Admin user can be created via script
- [ ] Docker starts with seeded data
- [ ] Migrations run automatically
- [ ] Data management commands work

## Dependencies

- PostgreSQL with proper schema
- Redis for session management
- Email service (optional, can use console for dev)
- Frontend state management for onboarding

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Email delivery issues | Use console logging in dev, defer email to later phase |
| Demo data gets corrupted | Reset demo data nightly or on-demand |
| Onboarding too long | Allow skip at any step |
| Admin access abuse | CLI-only admin creation, audit logging |

---

## Next Steps

1. Start with Phase 4A.1 - Database migrations
2. Test existing auth flow in Docker
3. Identify and fix any issues
4. Proceed through phases sequentially

Ready to begin Phase 4A?
