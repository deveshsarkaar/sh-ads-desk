# TEST_RESULTS.md — SH Ads Desk (Full Build + API Providers)

**Result: 58 passed, 0 failed** (pytest 9.2.0, Python 3.12.3, run 2026-11-16)
Command: `python3 -m pytest tests/ -q`

## Step 1 tests (18) — carried over from the verified Step 1 build
- Eligibility gate: unknown product fails closed; listed product with
  `resale_permission_confirmed=false` blocked; all 33 catalog entries
  default false with empty supplier.
- Banned claims blocked (≥3 reasons); clean Hinglish copy passes;
  destination gate closed by default.
- Optimiser: thin data → "not enough data" (0 proposals); one big winner →
  budget-increase proposal on the **ad-set** object (+20% cap, 1000→1200);
  all losers → 3 pause proposals; cheap-junk → loser; lagged conversions
  not judged; spend breach → safety stop; fatigue → creative-refresh proposal.
- Mock Meta: duplicate retry with the same idempotency key creates no
  duplicate; per-ad budget write rejected.
- Rollback restores the previous budget (1500→1000) and is blocked without
  approval; kill switch pauses everything and disables automation;
  approval queue add/edit/approve flow.

## Full-build tests (13)
- **Auth:** owner creation; wrong password rejected; correct password
  accepted; password hash format is PBKDF2 (password never stored plain).
- **Settings:** save/load roundtrip; no token field ever persisted.
- **Real Meta client, stubbed HTTP (no network):** insights request hits
  `/v25.0/act_<id>/insights` with `level=ad` and captures the request ID;
  write without `owner_approved` raises and sends NOTHING; approved draft
  creates campaign+adset+ad all with `status=PAUSED`; same idempotency key
  creates no duplicate; per-ad budget rejected on the live client too.
- **Approval → PAUSED write:** unapproved item refused ("not APPROVED");
  approved CAMPAIGN_DRAFT executes on the MOCK client, records one
  `meta_writes` row with status PAUSED; with an empty eligibility list the
  same approved item is blocked by the gate (fails closed).
- **Scheduler CLI:** `collect`, `optimise`, `daily`, `weekly` all exit 0 and
  daily+weekly reports are stored.
- **Web smoke (live server, in-process):** /setup renders; owner creation
  logs in; all pages return 200; a POST without the CSRF token is 403.
- **ZIP hygiene:** no `.env` in the package, no `state.db` in package
  sources, and a scan of package sources finds no hardcoded
  credential-looking assignments.

## API Providers tests (27) — stubbed HTTP only, NO real provider called
- **Preset pre-fill:** OpenAI text (`https://api.openai.com/v1`,
  `gpt-4o-mini`, `/chat/completions`), Anthropic (`https://api.anthropic.com`,
  `/v1/messages`, x-api-key, `claude-sonnet-4-5`), Higgsfield video
  (`https://api.higgsfield.ai`, auth prefix `Key `, poll
  `/requests/{id}/status`), Kling video (`https://api.klingai.com`,
  `/v1/videos/text2video`, `data.task_id`) — base URL + default model
  pehle se bhare milte hain.
- **Key-only save → working adapter (owner refinement):** sirf API key
  save karke (base URL untouched) Text adapter stub par
  `https://api.openai.com/v1/chat/completions` ko `Bearer` key aur default
  model ke saath call karke copy laata hai.
- **Custom preset:** bina base URL ke save refuse (ValueError); base URL
  ke saath kaam karta hai. Galat extra-headers JSON refuse.
- **Secret storage:** key sirf `data/secrets.env` me (file mode 0600);
  provider_config.json, settings file aur SQLite DB ke raw bytes me key
  kahin nahi — audit me key mention hone par bhi redaction use pehle
  scrub karta hai (DB me `[REDACTED]` jata hai). Blank key save karne se
  purani key bani rehti hai; remove-key kaam karta hai; env var
  (`SH_ADS_TEXT_API_KEY`) file wali key par jeet-ti hai.
- **Test connection (stub):** 200 → ok + status; 401 → failed + status,
  key result me kahin nahi; key na ho to bina call kiye failed.
- **Text adapters:** OpenAI shape (URL, Bearer header, model/messages) aur
  Anthropic shape (x-api-key + anthropic-version headers, alag `system`,
  content-blocks parse) dono verify.
- **Image adapter:** OpenAI shape (prompt/model/size fields) + URL
  response → file `data/generated/` me save; b64 response → decode karke
  save; Custom preset me badle hue field names (`prompt_text`) aur
  response path (`result.image.url`) sahi parse.
- **Video adapter:** Kling submit → poll `processing` → poll `succeed` →
  result URL (`data.task_result.videos.0.url`); `failed` status sahi
  report; Higgsfield submit par `Authorization: Key ID:SECRET` header aur
  `request_id` se job id.
- **Creative wiring:** provider na ho to copy templates par fallback
  (saaf "API not connected" label ke saath) aur image/video helpers
  `NotConfigured` dete hain (kuch break nahi hota); provider stub ho to
  API copy banti hai aur policy gate phir bhi block karta hai
  (unconfirmed product + band destination) — gates unchanged.
- **Web smoke (providers):** /providers page par pre-filled base URLs
  dikhte hain; save flow ke baad page par "Key set hai" aata hai aur key
  page me kahin echo nahi hoti; /creative par "Generate with API" section
  aur Connected status dikhta hai.
- **Package hygiene:** package me kahin `secrets.env` file nahi;
  `.gitignore` me `data/secrets.env` aur `data/generated/*` hai.

## Also verified manually in earlier build sessions (live local server)
- Full browser-less flow against a running server: setup → login → all
  pages 200 → Planner created a CAMPAIGN_DRAFT → Approve → Execute was
  correctly **BLOCKED** by the policy gate (product unconfirmed +
  destination gate closed) → kill switch ON showed the banner and blocked,
  OFF released it manually → lead add, daily report generate, roles run and
  the banned-claims policy check all returned success.

## Honest labels
- **VERIFIED:** everything above (local only, stubbed HTTP for all
  external APIs — Meta and providers alike).
- **MOCK:** mock Meta client, mock insights, all demo numbers.
- **UNTESTED:** the real Meta API path against a live account (Steps 2–4
  are the owner's manual Meta steps), the pinned API version v25.0 against
  Meta's official changelog, Hostinger hPanel-specific steps in
  HOSTING.md, PRACTICES.md guidance, **aur API Providers ke saare adapters
  kisi real provider (OpenAI/Claude/Higgsfield/Kling) account ke against**
  — preset base URLs official docs se liye gaye hain (Higgsfield ka
  `https://api.higgsfield.ai` + `Authorization: Key ...` docs.higgsfield.ai
  se verify hua), lekin pehli asal generation owner ko apni key ke saath
  khud test karni hogi. Kling ke official JWT auth par README me note hai.
