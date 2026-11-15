# SH Ads Desk — Full Build (self-hostable)

Meta (Facebook/Instagram) ads system for **Software Hub** (softwarehub.tech):
research, creative, campaign planning, approval-gated Meta writes, reports
aur optimisation proposals — customers (students, freelancers, creators) aur
resellers (bot owners, agencies) ke liye.

Ye Step 1 ke verified local build ka full, host-hone-layak version hai.
Hosting ke steps: **HOSTING.md**. Kuch bhi is package me Lucifer bot, kisi
VPS, ya softwarehub.tech ke code/database/payments ko nahi chhoota.

## Chalana (local / koi bhi Python host)

```bash
cp .env.example .env      # apni values bhoro (secrets sirf yahin)
python3 run.py            # koi pip install nahi — sirf stdlib (Python 3.11+)
# browser: http://127.0.0.1:8000/setup  → owner password set karo
```

Docker: `docker compose up -d --build` (Dockerfile + compose package me hai).

## Labels — imaandari se

- **VERIFIED (local tests):** Step 1 ka saara logic + is build ke naye hisse
  — auth, settings save/load, Meta client ki request shaping (stubbed HTTP,
  koi network nahi), approval → PAUSED write (mock), scheduler CLI, live web
  smoke tests (saare 14 pages + planner→approve→execute gate flow), aur
  **API Providers module** (preset pre-fill, key-only save → working adapter,
  secret storage rules, text/image/video adapters — sab stubbed HTTP par,
  koi network nahi). Kul **58 tests passed** — dekho `TEST_RESULTS.md`.
- **MOCK:** default mode. Mock Meta client, MOCK insights datasets (thin
  data, one big winner, all losers, cheap-junk, lagged, spend breach,
  fatigue), demo numbers har page par labelled.
- **UNTESTED:** asli Meta Marketing API path (`app/meta_client.py`) —
  code-complete hai lekin **kisi real ad account par kabhi test nahi hua**.
  **API Providers ke adapters bhi UNTESTED hain** — kisi real OpenAI/Claude/
  Higgsfield/Kling account par kabhi call nahi hua (is build ke paas koi
  asal key nahi thi); sirf stubbed HTTP par request shaping verify hua hai.
  API version pin `v25.0` bhi **UNVERIFIED** hai (is build environment me
  official changelog live fetch nahi ho paya; secondary sources ne Nov 2026
  me v26/v27 current aur v25.0 ko 23 Feb 2027 tak available bataya tha) —
  live use se pehle official changelog par confirm karo:
  https://developers.facebook.com/docs/marketing-api/changelog

## Hard rules — code me bandhe hue

- Default: `DRY_RUN=true`, `AUTOMATION_MODE=PROPOSE`, saare budget/threshold
  settings **khaali/zero** (koi benchmark default nahi).
- **Eligibility gate (fails closed):** `PRODUCT_ELIGIBILITY.yaml` me har
  product `resale_permission_confirmed: false` hai; proof note +
  terms-checked date ke bina web UI confirm hi nahi karti. False = us
  product ka ad ban hi nahi sakta.
- **Destination gate:** `DESTINATION_URL` khaali + `DESTINATION_READY=false`
  default — system khud destination nahi chunta.
- **Har Meta write ke liye owner approval:** PAUSED draft banana bhi write
  hai. Approval queue se APPROVED hue bina execution refuse hota hai;
  jo banta hai wo sirf **PAUSED** banta hai. Activation ka koi automatic
  path code me hai hi nahi.
- **Banned claims checker:** lifetime/guaranteed/official/%off/earnings/
  superlative/shared-account/fake-urgency jaisi claims block hoti hain.
- **Kill switch:** automation band, managed objects PAUSED, approvals aur
  execution blocked — kabhi auto-resume nahi.
- **Rollback:** fresh state padhkar + diff + owner ki alag approval
  (`app/rollback.py`) — kharch/delivery wapas nahi hota, ye note audit me
  jata hai.
- **Budgets sirf campaign/ad-set level par** — per-ad budget write code
  dono clients me ValueError se reject karta hai.
- **Secrets:** Meta token sirf `.env`/environment se padha jata hai.
  Provider API keys sirf `data/secrets.env` (chmod 600) ya env vars
  (`SH_ADS_TEXT_API_KEY` / `SH_ADS_IMAGE_API_KEY` / `SH_ADS_VIDEO_API_KEY`)
  me rehti hain — settings/DB/logs me kabhi nahi; har loaded key log
  redaction me registered hoti hai taaki galti se bhi log me na jaye.
  Logs/audit email/phone/token patterns ko redact karte hain. Lead log me
  sirf counts/status — koi personal data nahi.
- **Provider calls kabhi Meta write nahi karte:** generation sirf padhna/
  banana hai; Meta execution ka rasta (`app/execute.py`) providers ko
  import hi nahi karta.
- **Scheduler, always-on agent nahi:** `python -m app.jobs collect|optimise|daily|weekly`
  cron se chalao (HOSTING.md me crontab diya hai).

## Pages (web UI)

Today · Connect wizard (Meta setup ke manual steps + env-based status) ·
Roles (20 roles ki asal status) · Settings (saari settings + kill switch) ·
Eligibility & destination gate · Creative Studio (angles/copy/poster brief/
reel script = TEXT; asset upload + visual-check checklist; **Generate with
API** — owner ki connected API se copy/poster/carousel/reel, har generated
asset visual-check PENDING ke saath) · **API Providers** (apni generation
APIs connect karo — neeche wala section) · Planner
(AUD_ANGLE_FORMAT_DATE_VERSION, customer/reseller alag) · Approval Queue
(Approve/Edit/Reject/Execute — approve se pehle dikhta hai exactly kya hoga) ·
Budget (caps vs reported spend + reporting-delay note) · Leads (counts only) ·
Reports (daily/weekly, Hinglish) · Trends (official sources, URL+date,
UNVERIFIED items labelled) · Errors & Audit (redacted).

## API Providers — apni generation APIs connect karna

System khud koi vendor select nahi karta. **API Providers** page par owner
apni APIs jodta hai, phir Creative Studio ke "Generate with API" buttons
unhi se kaam karte hain: Text API → ad copy, Image API → poster + carousel,
Video API → reel (submit + poll). Generated copy bhi policy check se
guzarti hai; generated files asset bankar visual-check PENDING ke saath
save hoti hain — checklist PASS + approval ke bina queue me nahi jati.
Generation ka cost app me hamesha **"unknown — provider billing"** likha
aata hai — koi price invent nahi hota.

**Known presets me base URL + default model PEHLE SE bhara hai — bas key
paste karni hai:**

| Capability | Preset | Pre-filled base URL (source) | Default model | Key kahan milegi |
|---|---|---|---|---|
| Text | OpenAI (ChatGPT models) | `https://api.openai.com/v1` (official, OpenAI API docs) | `gpt-4o-mini` | platform.openai.com → API keys |
| Text | Anthropic Claude | `https://api.anthropic.com` (official, Anthropic API docs) | `claude-sonnet-4-5` | console.anthropic.com → API keys |
| Image | OpenAI-compatible | `https://api.openai.com/v1` (official) | `gpt-image-1` | upar wala hi OpenAI key chalega |
| Video | Higgsfield | `https://api.higgsfield.ai` (official — docs.higgsfield.ai) | workflow path ke hisaab se (submit path hi model hai) | open.higgsfield.ai console — key `KEY_ID:KEY_SECRET` ek saath paste karo (auth: `Authorization: Key ...`) |
| Video | Kling (official API shape) | `https://api.klingai.com` (Kling open platform docs) | `kling-v1-6` | ⚠️ Kling ka official auth JWT (Access Key + Secret Key se sign hota hai) hai — simple pasted key sirf Kling-compatible gateways par chalegi; official ke liye paths/fields docs se verify karo |
| Koi bhi | Custom | owner khud bharega — **sirf yahan base URL mandatory hai** | owner ki pasand | apne provider ke docs |

Base URL har card me "Advanced (optional)" ke andar visible/editable hai —
koi aur endpoint (proxy/gateway/dusra region) ho to wahan badal sakte ho.
Har preset ke paths aur field names bhi wahi se badalte hain (jaise kisi
provider ka response shape alag ho). **Test connection** button sirf ek
harmless GET (models/list type) karta hai — green ka matlab hai endpoint
ne jawab diya, generation ki guarantee nahi.

**Keys kahan rehti hain (hard rule):**
- UI me paste ki gayi key sirf server ki **`data/secrets.env`** file me
  jaati hai (chmod 600, `.gitignore` me hai) — settings.json,
  provider_config.json, database, logs/audit me **kabhi nahi**, aur UI me
  kabhi wapas dikhti nahi (sirf "Key set / not set" dikhta hai). Key khaali
  chhodkar save karne se purani key bani rehti hai; "Key hatao" alag button
  hai.
- Dusra tareeka: server ke environment me rakho — `SH_ADS_TEXT_API_KEY`,
  `SH_ADS_IMAGE_API_KEY`, `SH_ADS_VIDEO_API_KEY` (`.env.example` me bhi
  diye hain). **Env wali key hamesha jeet-ti hai.**
- ⚠️ `data/secrets.env` me tumhari asal keys hain — iska backup sirf
  surakshit jagah rakho, **kabhi git/commit/chat me mat daalo**. (Dhyan do:
  `data/` ke baki backup — state.db/settings — me koi secret nahi hota,
  lekin secrets.env khud ek secret hai.)

## Monthly running cost estimate (ad spend EXCLUDED) — saare UNVERIFIED estimates

Live price verify nahi hue — ye sirf andaz hain, faisla owner ka:

| Item | Is build ki asal cost | Aage ke options (UNVERIFIED estimate) |
|---|---|---|
| Hosting | ₹0 (owner ki machine par chal sakta hai) | Chhota VPS ~₹400–₹900/mo · Docker-wala VPS plan isse upar ho sakta hai |
| Model (LLM) calls | **₹0** jab tak owner apni Text API connect na kare (roles templates par chalte hain) | Owner ki API connect hone par kharcha usi provider ke billing par — app me "unknown — provider billing" |
| Image/video generation | **₹0** jab tak owner apni Image/Video API connect na kare | Kharcha owner ke provider (Higgsfield/Kling/OpenAI wagairah) ke billing par — app kabhi price invent nahi karta |

## Owner ke manual Meta steps (Steps 2–4 checklist)

1. **Step 2 (setup):** Facebook Page banao → Business portfolio →
   ad account + Meta ki billing screen me payment method → developers
   .facebook.com par app (Marketing API use case) → permissions pehle
   sirf `ads_read`. Kaunsi permission/tier lagegi ye objective par hai —
   official doc ke saath verify karo (Connect wizard page par link + notes).
2. **Step 3 (read-only):** token `.env` me rakho, `META_MODE=LIVE` karke
   `python -m app.jobs collect` chalao aur numbers Ads Manager se compare
   karo. Mismatch ho to aage mat badho.
3. **Step 4 (pehla write):** ek specific draft approval queue me Approve
   karo → Execute sirf **PAUSED** campaign banayega. **Activation uski
   alag approval hai** — aur pehle campaigns par Meta ke native limits
   (account spend limit) lagao.
4. **Step 5 (optimisation/automation):** proposals pehle se aa rahe hain;
   `AUTO_WITHIN_RULES` tabhi jab owner exact rules + caps likh kar
   approve kare. Is build me auto-apply ka koi path hai hi nahi.

## File map

| Path | Kya hai |
|---|---|
| `run.py`, `app/web.py` | Web app (stdlib http.server) — saare pages |
| `app/jobs.py` | Cron CLI: collect / optimise / daily / weekly |
| `app/meta_client.py` | Asli Meta adapter — **UNTESTED**, env token, backoff, idempotency, PAUSED-only writes |
| `app/mock_meta.py`, `app/mock_insights.py` | MOCK client + MOCK edge-case datasets (default) |
| `app/policy_checker.py` | Eligibility + banned claims + destination gates (fails closed) |
| `app/optimiser.py` | Role 19 — proposals only, z-test confidence, "not enough data", budget-owner check |
| `app/roles.py` | 20 logical roles, alag auditable outputs |
| `app/creative.py`, `app/planner.py`, `app/reports.py`, `app/trends.py` | Creative studio, structure planner, daily/weekly reports, trend watch data |
| `app/providers.py` | API Providers — presets (pre-filled base URL/model), secrets.env handling, generic HTTP client, Text/Image/Video adapters, test-connection — **UNTESTED** on real providers, stub-verified |
| `app/execute.py` | Approval → write ka ekmatra rasta (gates + DRY_RUN + kill switch) |
| `app/approval_queue.py`, `app/rollback.py` | Queue + kill switch; rollback (fresh read + approval) |
| `app/auth.py` | Single-owner login (PBKDF2 hash, /setup ya env hash) |
| `app/common.py`, `app/store.py` | Settings/eligibility IO, SQLite, redaction, lead/creative/report storage |
| `settings.json`, `PRODUCT_ELIGIBILITY.yaml` | Saari settings (defaults khaali/zero); eligibility (sab false) |
| `tests/` | 58 tests (Step 1 ke 18 + full-build ke 13 + API Providers ke 27) |
| `Dockerfile`, `docker-compose.yml`, `HOSTING.md`, `.env.example` | Deploy pack |
| `PRACTICES.md` | Official-guidance notes — kai points UNVERIFIED, Step 2 me verify honge |
