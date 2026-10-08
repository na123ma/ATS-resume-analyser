# API reference

Base path `/api`, **no trailing slash**. JSON for all bodies except PDF upload. Use the browser/Vite/nginx same-origin proxy. Fetch `/auth/csrf` first, retain cookies, and send its `csrfToken` as `X-CSRFToken` on every POST/PUT/PATCH/DELETE. Registration/login rotate the token and return the new one. Authenticated routes require the `skillentra_session` cookie.

| Method | Path | Body / purpose |
| --- | --- | --- |
| GET | /health | MongoDB connectivity |
| GET | /catalog | Technologies, models configured, runner configuration |
| GET | /auth/csrf | Obtain CSRF token |
| POST | /auth/register | full_name, email, password, confirm_password, leaderboard_opt_in (optional boolean) |
| POST | /auth/login | email, password |
| POST | /auth/logout | Revoke current session |
| GET | /auth/me | Current user |
| PATCH | /auth/me | leaderboard_opt_in |
| DELETE | /auth/me | password; permanently delete own records |
| GET | /resumes | Recent own analysis reports |
| POST | /resumes | Multipart: resume (PDF), technology (optional), use_ai ("true"/"false") |
| GET/DELETE | /resumes/{id} | Read/delete own report |
| GET/POST | /drafts | List/create resume draft |
| GET/PUT/DELETE | /drafts/{id} | Read/update/delete own draft |
| GET | /drafts/{id}/pdf | Download text PDF |
| POST | /interviews | technology, difficulty, use_ai |
| GET | /interviews/{id} | Resume/review own interview |
| POST | /interviews/{id}/answers | answer, turn (zero-based 0–4) |
| POST | /exams | technology, mode (practice/ranked), use_ai, monitoring_consent, fullscreen |
| GET | /exams/active | Current active exam if any |
| GET | /exams/{id} | Exam state; answer keys only after completion |
| POST | /exams/{id}/answers | question_id, option (integer 0–3); saves one answer |
| POST | /exams/{id}/events | event_id (unique nonce), kind |
| POST | /exams/{id}/heartbeat | Keep alive every 15 seconds |
| POST | /exams/{id}/submit | Freeze and grade saved answers; idempotent |
| GET | /leaderboard?technology=Python | Best eligible ranked scores |
| POST | /coding | language, difficulty, use_ai |
| GET | /coding/{id} | Poll reference validation / read own problem set |
| POST | /coding/{id}/submissions | question_id, source, mode (run/submit) |
| GET | /submissions/{id} | Poll remote execution; hidden case inputs/outputs omitted |
| GET | /progress | Recent records and totals for current account |

Draft fields: `title`, `template` (classic/modern/compact), `full_name`, `email`, `phone`, `location`, `links`, `summary`, `skills` (string array), `education`, `experience`, `projects` (entry arrays), `certifications` (string array). Each entry contains `title`, `organization`, `location`, `start`, `end`, `details` (newline-separated bullets).

Difficulty values: `easy`, `medium`, `hard`. Frontend displays `easy` as Simple.
Event kinds: `visibility_lost`, `fullscreen_exit`, `paste_attempt`, `copy_attempt`, `connection_gap`. Client flags are deterrence signals, never authentication of honest behavior.

Example requests (after keeping a session cookie and CSRF token):

```json
{"technology":"Python","mode":"practice","use_ai":true}
```

```json
{"language":"Python","difficulty":"medium","use_ai":true}
```

Typical responses: 400 validation/input error, 401 sign-in required, 403 CSRF failure, 404 missing/not-owned record, 409 completed/duplicate attempt, 429 rate limit, 503 database/runner unavailable. Error shape: `{"error":"Message","details":["optional validation detail"]}`.

## MongoDB collections

`users`, `sessions`, `limits`, `reports`, `drafts`, `interviews`, `exams`, `coding`, `submissions`.

Indexes are created on first connection. They include unique email, hashed session token, expiring sessions/rate buckets, one active exam per user, and one ranked attempt per user/technology/UTC day/bank version. All resource lookups include the authenticated owner. No raw client MongoDB filter is accepted.
