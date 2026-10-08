# Skillentra AI — Resume & Skill Studio

A complete source-code project using **Python/Django + React + MongoDB**, styled around the supplied Skillentra screenshots. Registration opens the resume analyzer. The backend stores all application records and sessions in MongoDB using PyMongo; it does not use SQLite, PostgreSQL, Djongo, or Django ORM migrations.

## Start quickly with Docker Desktop

1. Extract this ZIP. Open a terminal **inside `skillentra-ai`**.
2. Run:

```sh
python setup.py
docker compose up --build -d
```

3. Open **http://localhost:8080** and create an account.

MongoDB, Django and the React production build start together. Initial image downloads require internet. MongoDB records persist in the Docker volume. `docker compose down` stops services without deleting data. Do not use `down -v` unless you intend to erase all stored data.

**Initially AI is disabled, and coding execution needs a Judge0 endpoint.** Resume checks, PDF export, authentication, curated tests, ranked leaderboards, practice interviews, question browsing, and history work without AI keys. This is explicitly labelled in the interface: curated/checklist output is never presented as AI evaluation. See the next sections to enable all AI and execution features.

## Enable AI without OpenRouter

The project calls **Ollama or Google Gemini directly**, with independent provider/model settings for resume advice, interview feedback, MCQ generation and coding generation.

### Option A: local Ollama

Edit `backend/.env`:

```env
AI_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

Then run:

```sh
docker compose --profile ai up --build -d
docker compose logs -f ollama-pull
```

Wait for the model download to finish. The local model has no per-call API charge; it needs disk space, RAM and CPU/GPU resources. A 7B model may be slow on a small laptop. You can use a smaller compatible model: change `OLLAMA_MODEL` in both root `.env` (model download) and `backend/.env` (inference), then repeat the command. Optional model overrides are shown in `backend/.env.example`.

For Ollama installed directly on Windows, run `ollama pull qwen2.5:7b`. With Docker backend, put `OLLAMA_URL=http://host.docker.internal:11434` in root `.env`. With a local Python backend, use `OLLAMA_URL=http://localhost:11434` in `backend/.env`.

### Option B: Gemini directly

Create a key at https://aistudio.google.com/apikey and choose an available model from your account. Edit **backend/.env only**:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_key
GEMINI_MODEL=your_available_generateContent_model_id
```

Restart the backend: `docker compose up -d --force-recreate backend`. Model availability, free-tier eligibility, quotas, billing and provider data terms depend on your account and may change. No API key is embedded in the frontend. The model name is deliberately configurable instead of assuming an old model remains available.

To use different models for different operations, set `RESUME_AI_PROVIDER`, `RESUME_AI_MODEL`, `INTERVIEW_AI_PROVIDER`, `INTERVIEW_AI_MODEL`, `EXAM_AI_PROVIDER`, `EXAM_AI_MODEL`, `CODING_AI_PROVIDER`, and `CODING_AI_MODEL`. Omit unused overrides. For example, use Gemini for interview feedback and an Ollama coding model for coding questions. Pull every Ollama model you configure.

## Enable secure coding execution

Set up an **isolated Judge0 CE service** or use a hosted Judge0 provider, then configure:

```env
JUDGE0_URL=https://your-judge0-endpoint
JUDGE0_AUTH_TOKEN=your_token_if_required
```

For a RapidAPI-backed Judge0 deployment, set `JUDGE0_RAPIDAPI_KEY` and `JUDGE0_RAPIDAPI_HOST` instead/as required by that provider. `JUDGE0_URL` is the base URL, without `/submissions`. Check `/languages` on your endpoint and update the four `JUDGE0_*_ID` settings to its IDs. Default IDs match common Judge0 CE installations, not every instance.

Restart Django after changing these values. **Run sample** and **Submit solution** then use the remote judge with time/memory/output limits and networking disabled. Never execute arbitrary user code with `exec`, `eval`, or an unrestricted subprocess on the Django host. Keep self-hosted execution workers on separate isolated infrastructure and follow the Judge0 maintainer's current deployment/security guidance: https://github.com/judge0/judge0 . The application package does not bundle privileged judge workers.

An AI-generated coding set contains exactly three problems. Before exposing them, the backend submits each reference solution to Judge0 against its tests. If validation fails, a curated set replaces it. Passing these checks improves consistency but does not prove a generated problem or hidden test set is complete.

## Local Windows setup (without Docker)

Install Python 3.12+, Node.js 22.12+ and MongoDB Community Server (or obtain an Atlas URI).

From the project root:

```powershell
python setup.py
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-lock.txt
python manage.py check
python manage.py runserver 8000
```

In another terminal:

```powershell
cd skillentra-ai\frontend
npm ci
npm run dev
```

Open **http://localhost:5173**. The Vite development proxy forwards `/api` to Django. On macOS/Linux activate the environment with `source .venv/bin/activate`.

`backend/.env` defaults to `MONGO_URI=mongodb://localhost:27017`. Start MongoDB before registering. For Atlas use the full authenticated `mongodb+srv://...` URI and allow your server's connection in Atlas. URL-encode special characters in URI credentials. If using only the Docker Mongo service with a local Python backend, configure its generated root credentials and `authSource=admin` in `MONGO_URI`.

There is **no `migrate` or `createsuperuser` step**: this project deliberately uses MongoDB collections and its own cookie-session authentication. There is no Django Admin portal in this version.

## Features included

| Area | Implemented behavior |
| --- | --- |
| Accounts | Register/login/logout, PBKDF2 passwords, Mongo-backed expiring sessions, HttpOnly cookie, CSRF, rate limits, data deletion |
| Resume analysis | PDF-only input; six transparent score categories; passed checks; improvements; detected skills and suggested terms; optional AI recommendations; report history |
| Resume builder | Classic, Modern, Compact templates; editable details/projects/education/experience; saved drafts; real text PDF export |
| Voice interview | Technology + level; five turns; spoken questions; microphone transcription; editable answers; optional private camera preview; AI follow-ups and review |
| Tests | Technology-selected AI practice; curated fallback; ten questions; ten-minute server deadline; autosave; server-side grading; answer review |
| Ranked assessment | Shared versioned bank; one attempt per technology per UTC day; full-screen/tab/copy/paste checks and server heartbeats; review exclusions |
| Leaderboard | Best eligible ranked result per user, grouped by technology; opt-in display names; score/time tie breaks |
| Coding lab | Python, JavaScript, Java, C++; simple/medium/hard; exactly three problems per session; code editor; sample run; hidden tests; best score; isolated Judge0 integration |
| My progress | Resume, draft, interview, test and coding session history with reopening/resume links |

Supported interview and test technologies: Python, JavaScript, React, Django, SQL and Java. Coding technologies are programming languages; React and Django are covered by interviews/tests rather than sandboxed web-framework deployments.

## Important behavior

- **ATS scores are estimates**, not a score from every employer's ATS. The score uses no job description. Text extraction cannot fully verify columns, tables, reading order, typography or proprietary ATS behavior. Scanned PDFs are rejected with an OCR explanation. Only selectable-text PDFs up to 5 MB and 10 pages are accepted.
- Score weights: ATS friendliness 25%, readability 15%, structure 20%, keywords 15%, evidence 15%, consistency 10%. Exact checks are in `backend/api/services/resume.py`. Recommendations do not invent experience or guarantee hiring success.
- Voice interview uses browser SpeechRecognition + speech synthesis, not a real-time video avatar. Chrome/Edge usually provide the best experience; microphone use needs localhost or HTTPS. Browser support and voice availability vary. Audio may be processed by the browser's speech provider. The app stores text transcripts, not camera/audio recordings. Camera frames are not analyzed.
- Offline interview feedback is a communication checklist with **technical correctness ungraded**. AI interview scores are educational estimates and indicate how many answers were actually AI-graded.
- Monitoring can deter malpractice but **cannot guarantee cheating prevention** or detect a second device. Three recorded events end a ranked attempt. A final heartbeat gap over 45 seconds also excludes it from ranking. Events and connection issues are not proof of cheating. There is no human review/appeal admin interface yet; inspect records operationally before making any consequential decision.
- Ranked exams use the same curated bank version for comparability. AI-generated practice is not ranked. The board is for practice, not certified hiring decisions; answers can become familiar or be shared. Publishing a new bank version starts a new comparable cohort.
- AI adapters validate returned JSON and fall back on timeouts or invalid responses. AI-generated MCQ answer keys may still contain factual errors; use curated/reviewed content for consequential exams.
- Uploaded PDFs/raw extracted text are not retained. Reports, drafts, interview transcripts and submitted code are stored in MongoDB. Original PDF bytes are processed in memory or temporary upload files. Deleting an account deletes its records; backups/provider logs require their own retention policies.

## Structure

See `docs/FOLDER_STRUCTURE.md` for all source files and `docs/API.md` for endpoints. See `docs/TESTING.md` for what was and was not verified.

## Before a public launch

Use HTTPS, `DEBUG=false`, `COOKIE_SECURE=true`, a random secret, your real `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`. Keep the API and frontend behind one trusted origin. This package binds Docker ports to localhost for development. Configure your hosting ingress deliberately.

For HTTPS terminated at a reverse proxy, configure Django's `SECURE_PROXY_SSL_HEADER` only when that trusted proxy strips client-provided forwarding headers. This project does not blindly trust `X-Forwarded-For`/`X-Forwarded-Proto`. Add trusted ingress IP rate limiting, centralized logging, backups and operational alerts. Domain signup verification, password-reset email, paid plans, an admin review interface, and enterprise proctoring are not included. Large-scale use should move long AI/PDF work into a durable task queue and isolate PDF processing.

## Documentation used

- Django security: https://docs.djangoproject.com/en/5.2/topics/security/
- PyMongo: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/
- Ollama chat/structured JSON: https://docs.ollama.com/api/chat
- Gemini structured output / generateContent: https://ai.google.dev/gemini-api/docs/generate-content/structured-output
- Judge0 API: https://ce.judge0.com/
- Browser speech recognition: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition
