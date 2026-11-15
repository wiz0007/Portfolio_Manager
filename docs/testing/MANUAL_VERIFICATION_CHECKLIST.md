# Manual Verification & Human Inspection Checklist
**Project:** Portfolio Manager — Financial Intelligence Platform  
**Scope:** Browser, UI, Environment, and Provider Verification Tracker  
**Last Updated:** Sprint 2 (2026-11-15)

---

## 1. Manual Verification Status Legend

- **Verified**: Confirmed working through interactive browser inspection.
- **Implementation complete — manual verification pending**: Automated tests passing; awaiting physical browser run or user inspection.
- **Not started**: Deferred to future sprints.
- **Blocked**: Environmental or external dependency blocker.

---

## 2. Verification Checklist

| Item ID | Category | Description | Verification Method | Status | Notes |
|---|---|---|---|---|---|
| **MAN-001** | UI / Responsive | Mobile navbar collapses to icon only on narrow viewport (<640px) | Browser viewport resize | Verified | Addressed in UI revamp turn |
| **MAN-002** | UI / Styling | Profile icon on navbar and sidebar without visible dividing lines | Visual inspection | Verified | Verified in previous turn |
| **MAN-003** | Forms / UI | Bank selection SearchSelect dropdown renders below input trigger without page overflow | Click trigger in browser | Verified | Container positioning fixed |
| **MAN-004** | Forms / Real Estate | Agricultural Land form inputs render for Uttarakhand / Delhi plot | Form walkthrough in `/investments/new` | Implementation complete — manual verification pending | Automated unit & mapping test passed |
| **MAN-005** | Auth / Email | Physical email delivery with verification link | SMTP server / Inbucket | Implementation complete — manual verification pending | Mocked & outbox verified in test suite |
| **MAN-006** | Auth / Google | Live Google OAuth Popup / Redirect login | Google Identity Services | Implementation complete — manual verification pending | Backend endpoint verified with test tokens |
| **MAN-007** | Database / Neon | Persistent cloud database sync on Neon PostgreSQL instance | Cloud connection | Implementation complete — manual verification pending | Sandbox runs offline test DB; production settings verified |
| **MAN-008** | Portfolio / UI | Holdings list table and modal inspection after creating investment | Interactive holding CRUD | Implementation complete — manual verification pending | Unit & integration tests pass with 100% assertions |
