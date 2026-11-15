# STEP3_5_PREP.md — Steps 3–5 ki taiyari (bina Meta account ke)

Ye document un teen steps ki **taiyari** hai jo asal Meta account
chahte hain. Taiyari abhi ho gayi hai taaki jis din working Meta
account mile (recovery/appeal ke baad), usi din bina ruke Step 3
shuru ho jaye. **Is document se koi Meta write authorise nahi hota** —
har asal write ke liye brief ke niyam waisi hi rahenge: specific
draft ki owner approval, PAUSED-only creation, activation ki alag
approval.

Pehle padho: **SETUP_GUIDE.md** (Step 2 — Page, Business portfolio,
ad account, developer app, token) aur **META_ACCESS.md** (permissions,
tiers, rate limits ka verified hisaab).

---

## Part A — Step 3: Read-only connect checklist

**Lakshya:** system sirf PADI hui (read-only) haalat me Meta se jude,
aur API ke numbers Ads Manager ke numbers se milaye jayein. Is step
me **koi write nahi** hoga — na PAUSED draft bhi nahi.

Shuru karne se pehle (saare hone chahiye):

- [ ] Working Meta account hai (suspended nahi) — SETUP_GUIDE Step 0
- [ ] Page + Business portfolio + ad account ban chuke hain (SETUP_GUIDE 1–3)
- [ ] Developer app bana hai, token generate hua hai (SETUP_GUIDE 4–5)
- [ ] Token sirf server ki `.env` me hai (`META_ACCESS_TOKEN`),
      `META_AD_ACCOUNT_ID` aur `META_PAGE_ID` bhi `.env` me hain
- [ ] `.env` me `META_MODE` abhi bhi **MOCK** hai — checklist pass
      hue bina LIVE nahi karna

Read-only verification (isi order me):

1. **Token check** — token kis account ke liye hai, kaun si
   permissions mili hain, expiry kab hai. Bekar/expired token yahin
   ruk jayega, aage nahi badhega.
2. **Ad account check** — account ka naam, currency (INR), timezone
   (Asia/Kolkata), status ACTIVE hai ya nahi. Currency/timezone
   galat mile to pehle Meta me theek karo — system ke reports inhi
   par chalte hain.
3. **Page check** — Page ID wahi hai jo SETUP_GUIDE me banayi thi;
   system ki identity (Page) yahi rahegi.
4. **Insights pull (sirf read)** — pichhle 7 din ke account-level
   numbers kheecho: spend, impressions, clicks, results.
5. **Ads Manager se milan** — wahi 7 din Ads Manager me kholo aur
   neeche wali table bharo:

   | Cheez | API se aaya | Ads Manager me dikha | Fark? |
   |---|---|---|---|
   | Spend (₹) | | | |
   | Impressions | | | |
   | Clicks | | | |
   | Results (objective ke hisaab se) | | | |
   | CPM | | | |

   Chhota fark samajh sakte ho: reporting lag (numbers der se
   pakke hote hain) aur attribution window ka antar. **Bada ya
   ulta-seedha fark = FAIL** — pehle kaaran dhundho (galat account?
   galat dates? galat timezone?), Step 4 par mat badho.
6. **Rate-limit vyavhaar** — Meta ka score-based model hai
   (META_ACCESS.md dekho). Client 429 aur rate-limit error codes
   (17, 32, 613, 80000, 80004) par exponential backoff karta hai;
   request ID har call ke saath audit log me jata hai. Agar is
   checklist ke dauraan hi baar-baar rate limit aaye, to ruko —
   access tier ki seema ho sakti hai (META_ACCESS.md, Limited tier).

**Step 3 PASS ka matlab:** upar ke 6 points pure, milan table me koi
unexplained bada fark nahi. Uske baad hi Step 4 ki sochna hai.

---

## Part B — Step 4: PAUSED draft templates

**Lakshya:** pehla asal draft — lekin sirf **PAUSED** haalat me, aur
sirf us specific draft ki owner approval ke baad. Activation is
step ka hissa **nahi** hai; wo alag approval hai.

Har draft in templates me se ek par banega (ODAX ke 6 objectives;
naming hamesha `AUD_ANGLE_FORMAT_DATE_VERSION`):

### Template 1 — Sales (website par kharid)
- Campaign: objective = Sales, budget campaign level (CBO) ya ad-set
  level (ABO) — ek hi, dono nahi; planner pehle hi detect karta hai
- Ad set: conversion location = website, pixel/CAPI event = Purchase
  (ya business ke hisaab se sahi event), attribution = owner settings
  wali window
- Ad: eligibility-confirmed offering hi chalega; destination =
  profile ka DESTINATION_URL (gate pass hona chahiye); creative =
  visual-check PASS wala asset

### Template 2 — Leads (enquiry/lead form ya WhatsApp)
- Campaign: objective = Leads
- Ad set: conversion location = Instant Form / Website / WhatsApp
  (profile ke sales model ke hisaab se); lead-quality tracking ke
  liye stage names profile ke lead stages se aayenge
- Ad: koi guaranteed-result wala daava nahi (policy checker +
  guardrails pehle se rok denge)

### Template 3 — Traffic / Engagement (sirf jahan funnel me jagah ho)
- Chhote budget par awareness/traffic objective ko guardrail
  rok sakta hai (winner-patterns D-catalogue) — pehle kaaran
  likho, phir hi draft banao

### Har draft ke liye anivarya checks (ek bhi fail = draft nahi banega)
- [ ] Eligibility gate: offering ki permission confirmed hai
      (proof note + terms date ke saath)
- [ ] Destination gate: DESTINATION_URL set hai aur DESTINATION_READY=true
- [ ] Policy check PASS (banned claims, personal attributes, industry pack)
- [ ] Guardrails pre-flight: koi BLOCK nahi; WARN ho to owner ne
      dekh kar aage badhaya ho
- [ ] **v27.0 ke naye defaults khud set karo** — API v27.0 kuch naye
      objects par naye defaults ON karta hai (jaise device-reach
      expansion, product showcase — PRACTICES.md dekho). Template
      ke har aise field ko **explicitly** set karo; Meta ke default
      par bharosa karke khaali mat chhodo
- [ ] Budget caps ke andar hai (TOTAL_DAILY_BUDGET_CAP /
      PER_CAMPAIGN_CAP owner settings se)
- [ ] Draft approval queue me gaya aur owner ne **usi draft** ko
      approve kiya

Creation ke baad: object **PAUSED** milega, Ads Manager me dikhega,
audit log me request ID ke saath entry hogi. **Activation = alag
approval**, is document se nahi milti.

---

## Part C — Step 5: Optimisation runbook

**Lakshya:** asal data par optimiser ki sifarishen — pehle sirf
PROPOSE mode me. Automation (AUTO_WITHIN_RULES) tabhi, jab owner
niyam **likh kar** approve kare.

Data ki shartein (ek bhi adhuri = optimiser "not enough data" bolega,
aur wahi sahi jawab hai):

- [ ] EVALUATION_WINDOW aur CONVERSION_LAG_WINDOW owner settings me
      bhare hain (khaali = koi sifarish nahi)
- [ ] MIN_EVENTS pura hua hai — kam data par faisla lena guardrail
      D2 se BLOCK hai
- [ ] Lead-quality data aa raha hai (enquiry vs qualified alag);
      jab tak quality data nahi, metric sirf **provisional cost per
      enquiry** kahlayega
- [ ] Learning phase ka hisaab: ~50 optimisation events / 7 din
      (PRACTICES.md) — isse pehle ke "winner/loser" faisle pakke
      nahi maane jayenge

Har sifarish ki jaanch (approval se pehle):

1. Sifarish kis data par hai — window, events ki sankhya, freshness?
2. Confidence check (significance) pass hai, ya sirf raw ranking hai?
   Raw ranking par sifarish **nahi** banti.
3. Budget kis level par hai — campaign ya ad set? Sifarish usi
   owner par lagegi jahan budget asal me hai.
4. Guardrail screen: learning-phase edit, budget jump >
   MAX_BUDGET_CHANGE_PCT, fatigue wale creative ko scale — ye sab
   pehle se kate hue aayenge; phir bhi ek nazar dekho.
5. Sasta-par-junk lead = loser hai, chahe CPL kitna bhi kam ho.

Cadence: daily report (spend, enquiries, provisional cost per
enquiry, qualified cost jab data ho), weekly report (winning angle/
format, next test, budget sifarish). Har applied change audit log me
(old value, new value, request ID) — rollback hamesha fresh state
padh kar + alag approval se, aur rollback kharch wapas nahi karta.

**Kill switch** har samay upar hai: kuch bhi galat lage to pehle
kill switch, phir jaanch. System kabhi auto-resume nahi karta.
