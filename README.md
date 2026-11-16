# SH Ads Desk — Full Build (self-hostable)

Meta (Facebook/Instagram) ads system — **Software Hub ke liye dedicated,
lekin kisi bhi industry ke liye kaam karta hai**: research, creative,
campaign planning, approval-gated Meta writes, reports aur optimisation
proposals. Software Hub (softwarehub.tech) pehla/default profile hai —
customers (students, freelancers, creators) aur resellers (bot owners,
agencies) ke liye.

Ye Step 1 ke verified local build ka full, host-hone-layak version hai.
Hosting ke steps: **HOSTING.md**. Kuch bhi is package me Lucifer bot, kisi
VPS, ya softwarehub.tech ke code/database/payments ko nahi chhoota.

## Works for any industry — Business Profiles

Desk ek business par bandha nahi hai. **Business Profiles** page par
jitne chaaho profile banao — har profile ka apna: business name,
industry (preset ya free text), description, website/destination,
target customers (B2B/B2C/both), geography, languages, currency, sales
model (checkout / lead gen / WhatsApp / calls / footfall), **apna
offerings catalog** aur **apni settings overrides** (caps, destination,
automation mode — global settings par jeette hain). Header ke switcher
se active profile badalta hai; har page, report aur loop active profile
par chalta hai, data profiles ke beech leak nahi hota.

11 industry presets (`app/industries.py`): Software & Digital Products,
Grocery & Food, E-commerce, Manufacturing & B2B, Social Media &
Marketing Services, Education & Courses, Real Estate, Local Services,
Health & Wellness, Finance & Insurance, Generic/Other. Har preset seed
karta hai: research checklist, audience hints, 3–5 angle templates,
funnel/KPI defaults (**settings ke roop me — logic me hardcoded kabhi
nahi**), lead-quality stages, aur ek **compliance add-on pack** (jaise
health: cure/before-after claims; finance: guaranteed returns;
education: guaranteed placement/income; grocery: false health/organic
claims; real estate: guaranteed appreciation — Meta ke universal
banned claims core checker me rehte hain). Presets editable starting
points hain — **legal advice nahi**.

Catalog generic hai: name, type (product/service), category, price,
supplier/source note, **permission flag** (default false; generic
wording "eligibility permission confirmed" — software preset sakht
"resale permission" wording rakhta hai), proof note, terms date,
destination override. Gate ki strength har industry ke liye ek jitni
hai: unconfirmed offering = ad nahi banega, fails closed.

Profile #1 "Software Hub" `PRODUCT_ELIGIBILITY.yaml` (31 tools + 2
collections, saare flags false) se **lossless migration** karke seed
hua hai — Profiles page par migration proof live dikhta hai
(33 = 33, names match, saare unconfirmed).

## Growth Loop

Owner ka operating loop, first-class feature (`app/growth_loop.py`,
**Growth Loop** page + `python -m app.jobs loop`):

1. **Competitor discovery** — har profile ki apni owner-editable
   competitor list (Software Hub ke liye Damini Tripathi/Marketian
   seed sahit).
2. **Competitor best-ads research** — sirf public Meta Ad Library,
   har finding par source + date. Live pull abhi wired nahi hai, isliye
   stage honest **research-task entries** banata hai — **koi metric
   kabhi invent nahi hota**. Growth Loop page par **Competitor
   Research Board** hai: har competitor ke naam se aur har
   product/offering ke keyword se **1-click ready-made Ad Library
   search links** (saare ads + sirf active), 5-step research
   checklist, aur winner-signal rule (Ad Library me performance
   numbers milte hi nahi — winning ka signal sirf **longevity**
   hai: 3–6 mahine lagatar chal raha ad, Strategy S10). Finding
   record hote hi Stage 3 ka brief automatic banta hai, aur
   Stage 4 ka creative usi brief ke pattern (theme/hook/format/
   CTA) par banta hai — winning ad ka text ya asset kabhi copy
   nahi hota, sirf pattern use hota hai.
3. **Top-creative inspiration** — window configurable 7/10 din
   (`TOP_CREATIVE_WINDOW_DAYS`); output = inspiration brief (theme,
   hook, format, CTA style). **Inspiration only** — kisi aur ka ad
   verbatim copy karna ya assets reuse karna mana hai.
4. **Creative production** — brief se templates + API Providers ke
   through; gates (eligibility/policy/destination) bilkul waise hi.
5. **Optimisation plan** — PRACTICES.md ke hisaab se proposals.
6. **Go-live** — maujooda approval-gated execute hi; saath me
   `AUTOMATION_MODE=AUTO_WITHIN_RULES` support: sirf tab jab owner ne
   written rules + caps settings me approve kiye hon
   (`AUTO_RULES_APPROVED` + `AUTO_RULES_TEXT`). Shipped default
   **PROPOSE** hi hai; safety stop ke baad auto-resume kabhi nahi.
7. **Monitoring** — per-creative winners vs losers (weak CTA = falling
   CTR + high spend + low responses) → loser-pause / winner-scale
   proposals, `MAX_BUDGET_CHANGE_PCT` + caps ke andar.
8. **Refresh** — winner par bhi fatigue/decay dikhe to fresh
   inspiration brief — loop wapas stage 3 se.

## Guardrails — CPC/CPL killer mistakes, system-enforced

`app/guardrails.py` + `app/guardrail_catalogue.py`: data-driven
registry (har entry: mistake, CPC/CPL mechanism, automatic check,
BLOCK/WARN severity, controlling setting key). Har draft/plan approval
queue se **pehle** pre-flight se guzarta hai — BLOCK fail = entry
refuse (kaaran dikhta hai), WARN = warnings item ke saath attach.
Optimiser bhi wahi registry consult karta hai — BLOCK wali action
kabhi propose nahi hoti. Catalogue winner-patterns research ke 26
mistakes (D1–D26) + 8-item pre-flight checklist se seeded hai;
thresholds saare **owner settings** hain (khaali/0 = inactive) —
research ke numbers sirf Settings me labelled reference hain,
defaults kabhi nahi. Guardrails page par har guardrail, uski setting
aur on/off toggle dikhta hai. (Guardrails galtiyaan rok sakte hain —
CPC/CPL ki guarantee koi system nahi de sakta; auction/market bhi
matter karta hai.)

## Knowledge, Policies aur Strategy Library

- **Meta Knowledge register** (Knowledge page): 2026 ke Meta
  features/changes — har entry par official source URL + date read +
  VERIFIED/UNVERIFIED flag. Jo entries is environment me official page
  fetch na hone (403) par secondary sources se verify hain, wo
  **UNVERIFIED-until-rechecked** hi rehti hain. Weekly job register
  review karta hai; strategy changes sirf proposals hote hain.
- **Policies register** (`app/policies_register.py`): Meta Advertising
  Policies ka digest — 10 sections (prohibited/restricted content,
  personal attributes — **dono official lists ka UNION enforce hota
  hai**, Special Ad Categories, review process, Account Quality,
  AI-content labelling, 2026 Ad Terms, India layer). Flags bilkul
  waise hi preserve hain jaise research me mile: "OFFICIAL (via
  secondary — flagged)" flagged hi rehte hain; **2026 Ad Terms
  DISPUTED hai** (ek tracker: update 5 Nov 2026 ko bina nayi date ke
  pause). Legal advice nahi.
- **Strategy Library** (`app/strategy_library.py`): Damini Tripathi /
  Marketian ki 35 strategies (S1–S35, practitioner-labelled, policy
  screening ke baad; jo tactic policy se takrayi wo DO-NOT-APPLY —
  jaise S20 ki inflated-anchor "reverse discount" display), 21
  practitioner playbook entries (P1–P21, contradictions flagged),
  4 book-derived (B1–B4), 14 winner habits (W1–W14) + 9 viral
  creative patterns (V1–V9, PRACTITIONER/CASE), 9 DO-NOT-APPLY
  entries (D1–D9), **aur owner ke bheje teen YouTube training
  videos se 23 strategies (YT1-* Sabri Suby, YT2-* HBA Services,
  YT3-* WsCube Tech) + 1 screening entry (YT-DNA)** — per-video
  notes `YOUTUBE_LEARNINGS.md` me. **Kisi ki bhi unverified
  performance claims (ROAS/CTR/earnings numbers) benchmarks ya
  defaults ke roop me kahin seed nahi hain.** Library data-driven
  hai — nayi entries bina code change ke DB/file se jud sakti hain.

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
  koi network nahi). Kul **81 tests passed** — dekho `TEST_RESULTS.md`.
- **MOCK:** default mode. Mock Meta client, MOCK insights datasets (thin
  data, one big winner, all losers, cheap-junk, lagged, spend breach,
  fatigue), demo numbers har page par labelled.
- **UNTESTED:** asli Meta Marketing API path (`app/meta_client.py`) —
  code-complete hai lekin **kisi real ad account par kabhi test nahi hua**.
  **API Providers ke adapters bhi UNTESTED hain** — kisi real OpenAI/Claude/
  Higgsfield/Kling account par kabhi call nahi hua (is build ke paas koi
  asal key nahi thi); sirf stubbed HTTP par request shaping verify hua hai.
  API version pin ab **`v27.0`** hai (Step 2 me verify: v27.0 released
  2026-11-04; v25.0 23 Feb 2027 tak available rehta — is environment me
  official changelog page 403 deta hai, isliye pin corroborated sources
  par based hai aur Knowledge register me UNVERIFIED-until-rechecked
  flagged hai) — live use se pehle official changelog par confirm karo:
  https://developers.facebook.com/docs/marketing-api/changelog

## Hard rules — code me bandhe hue

- Default: `DRY_RUN=true`, `AUTOMATION_MODE=PROPOSE`, saare budget/threshold
  settings **khaali/zero** (koi benchmark default nahi).
- **Eligibility gate (fails closed):** har profile ke DB catalog me har
  offering ka permission flag default `false` hai (Software Hub ka
  catalog `PRODUCT_ELIGIBILITY.yaml` se lossless migrate hua — YAML
  source ke roop me repo me rehta hai); proof note + terms-checked
  date ke bina web UI confirm hi nahi karti. False = us offering ka
  ad ban hi nahi sakta — software ho ya grocery, gate ek jitna sakht.
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
- **Scheduler, always-on agent nahi:** `python -m app.jobs collect|optimise|daily|weekly|loop`
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
Reports (daily/weekly, Hinglish) · **Business Profiles** (profiles +
switcher + migration proof) · **Growth Loop** (stage status, inspiration
brief, competitors, top creatives) · **Guardrails** (registry + toggles +
pre-flight checklist) · **Knowledge** (purana Trends page — Meta Knowledge
register + Policies register + trend watch, URL+date, UNVERIFIED items
labelled) · Errors & Audit (redacted).

UI saaf aur simple rakha gaya hai (owner directive): clean cards, ek
screen par ek saaf primary action, lambi details `<details>` sections ke
peeche, mobile-friendly. Settings ke advanced/guardrail fields
"Advanced" section me collapsed hain.

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
   Growth Loop me `AUTO_WITHIN_RULES` ka path hai — sirf tab jab owner
   exact rules + caps settings me likh kar approve kare
   (`AUTO_RULES_APPROVED` + `AUTO_RULES_TEXT`); default PROPOSE hi hai,
   aur safety stop ke baad auto-resume kabhi nahi hota. Real Meta
   account par ye path abhi UNTESTED hai.

## File map

| Path | Kya hai |
|---|---|
| `run.py`, `app/web.py` | Web app (stdlib http.server) — saare pages, clean/minimal UI |
| `app/jobs.py` | Cron CLI: collect / optimise / daily / weekly / loop |
| `app/meta_client.py` | Asli Meta adapter — **UNTESTED**, env token, backoff, idempotency, PAUSED-only writes, API pin v27.0 |
| `app/mock_meta.py`, `app/mock_insights.py` | MOCK client + MOCK edge-case datasets (default) |
| `app/policy_checker.py` | Eligibility + banned claims + personal-attributes (union) + destination gates (fails closed) |
| `app/optimiser.py` | Role 19 — proposals only, z-test confidence, "not enough data", budget-owner check, guardrail-screened |
| `app/roles.py` | 20 logical roles, alag auditable outputs (profile-parameterized) |
| `app/creative.py`, `app/planner.py`, `app/reports.py`, `app/trends.py` | Creative studio, structure planner, daily/weekly reports, trend watch + Meta Knowledge register |
| `app/profiles.py` | Business Profiles — CRUD, active switch, per-profile catalog/competitors, settings overrides, Software Hub lossless migration + proof |
| `app/industries.py` | 11 industry presets — research checklist, audience hints, angle templates, funnel/KPI defaults, compliance packs |
| `app/growth_loop.py` | Growth Loop — 8 stages, inspiration briefs, AUTO_WITHIN_RULES go-live, monitoring/refresh |
| `app/guardrails.py`, `app/guardrail_catalogue.py` | Guardrail registry + pre-flight; catalogue D1–D26 (winner-patterns research §D) seeded |
| `app/strategy_library.py` | Strategy Library — Damini S1–S35 (screened), practitioner P1–P21, books B1–B4, winner habits W1–W14, viral patterns V1–V9, YouTube YT1/YT2/YT3 (23) + YT-DNA, DO-NOT-APPLY D1–D9 + S20-DNA |
| `YOUTUBE_LEARNINGS.md` | Owner ke teen YouTube training videos — per-video kya seekha, kya add hua, kya screen-out hua |
| `SETUP_CHECKLIST.md` | 1-page setup checklist — tick karte-karte: software chalana, andar ka setup, Meta connect, pehla ad |
| `AUTOPILOT_RULES.md` | "Almost automatic" ka naksha — kya hamesha auto hai, ek-baar ka API connect (MCP wala sach), rules sign karne par caps ke andar kya auto hoga, owner ke controls, ready-to-paste AUTO_RULES_TEXT draft (STATUS: UNAPPROVED draft) |
| `CUSTOMER_EXPLAINER.md` | Customer ko samjhane ki script — connect kaise hoga, roz kaam kaise karega, paisa kaise bachega (bekaar kharch rukna, koi guarantee wala daava nahi), har industry ki ek line, do aam sawalon ke jawab, bolne ka order |
| `app/policies_register.py` | Policies register — Meta policies digest (10 sections, flags preserved, PR9 DISPUTED) + personal-attributes union |
| `app/competitor_seeds.py` | Competitor seed data (Damini Tripathi / Marketian) |
| `app/providers.py` | API Providers — presets (pre-filled base URL/model), secrets.env handling, generic HTTP client, Text/Image/Video adapters, test-connection — **UNTESTED** on real providers, stub-verified |
| `app/execute.py` | Approval → write ka ekmatra rasta (gates + DRY_RUN + kill switch) |
| `app/approval_queue.py`, `app/rollback.py` | Queue + kill switch; rollback (fresh read + approval) |
| `app/auth.py` | Single-owner login (PBKDF2 hash, /setup ya env hash) |
| `app/common.py`, `app/store.py` | Settings/eligibility IO, SQLite, redaction, lead/creative/report storage |
| `settings.json`, `PRODUCT_ELIGIBILITY.yaml` | Saari settings (defaults khaali/zero); Software Hub eligibility ka migration source (sab false) |
| `tests/` | 81 tests (Step 1 ke 18 + full-build ke 13 + API Providers ke 27 + industries/profiles/loop/guardrails/YouTube/board ke 23) |
| `Dockerfile`, `docker-compose.yml`, `HOSTING.md`, `.env.example` | Deploy pack |
| `PRACTICES.md` | Official-guidance notes — Step 2 me official docs se verify ho chuke hain |
| `META_ACCESS.md` | Meta access/setup ka verified guide (Step 2) |
| `SETUP_GUIDE.md` | Owner ke liye step-by-step setup guide (Step 2) |
| `STEP3_5_PREP.md` | Steps 3–5 ki taiyari: read-only connect checklist, PAUSED draft templates, optimisation runbook |
