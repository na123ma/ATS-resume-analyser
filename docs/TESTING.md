# Verification

The source package was checked on Python 3.12 and Node.js 24 during creation.

## Passed

- Django system check: no issues.
- React/Vite production build: completed successfully.
- 30 backend tests: all passed. These cover CSRF, authentication, session revocation, password hashing, duplicate registration, record ownership, all three PDF templates and text extraction, malformed/scanned PDF rejection, server-owned exam scoring, deadline enforcement, idempotent submission, one active exam, daily ranked limits, event deduplication and rank exclusion, leaderboard privacy, interview turn order and explicit non-AI grading, three coding problems across all 12 language/level combinations, runner-not-configured behavior, hidden case secrecy, mock runner scoring, AI schema failure fallback, and account data deletion.

Tests use **mongomock**, not a real MongoDB server. Runner/model boundaries are mocked where needed; the code runner test does not execute untrusted code locally.

Run them locally:

```sh
cd backend
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python manage.py check
cd ../frontend
npm ci
npm run build
```

## Not verified in this environment

- Docker Compose startup and real MongoDB integration: Docker/MongoDB executables were unavailable.
- Live Gemini/Ollama calls and Judge0 program execution: no configured model/runner credentials or local model were available.
- Browser visual and microphone/camera/full-screen end-to-end behavior: the browser runtime download was unavailable in this environment. The JavaScript production build passed, but a successful browser smoke test is not claimed.

Before sharing a deployed installation, run these checks with your own services:

1. Register two users; verify that neither can fetch the other's draft/report/exam by ID.
2. Save a resume, export it, select the text in the PDF, then upload it for analysis.
3. Enable a model, accept AI sharing, and verify that the displayed source is your configured model rather than fallback.
4. Conduct a five-turn voice interview in Chrome or Edge on localhost/HTTPS, including permission denial and typed-answer fallback.
5. Complete a ranked assessment in full-screen mode. Test tab/full-screen events, autosave, expiry, refresh, and opt-in leaderboard visibility.
6. Configure Judge0; run a correct and an incorrect solution, a syntax error and an infinite loop. Confirm limits are enforced by the judge and hidden inputs/outputs remain private.
7. Restart services and confirm saved history persists in MongoDB. Verify backup/restore and HTTPS cookie settings for your hosting setup.

This is a functional development implementation with explicit external service setup, not a claim of audited production readiness or invigilated-exam integrity.
