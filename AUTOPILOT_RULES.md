# AUTOPILOT_RULES.md — SH Ads Desk ko "almost automatic" chalana

Owner ki demand simple hai: **"humko kuch nahi karna pade, bas budget
edit kar dein, baaki sab automatic ho aur reporting milti rahe."**
Ye file usi ka naksha hai — kya automatic hai, kya ek baar connect
karna padega, aur control kahan-kahan owner ke paas rahega.

> **STATUS: DRAFT — UNAPPROVED.** Jab tak owner Settings me jaake
> (1) neeche ke caps bharta nahi, (2) `AUTO_RULES_TEXT` me rules
> daalta nahi, (3) `AUTO_RULES_APPROVED` tick nahi karta aur
> (4) `AUTOMATION_MODE=AUTO_WITHIN_RULES` nahi karta — tab tak
> system **PROPOSE** mode me hi chalega (sab kuch proposal, koi
> auto-apply nahi). Ye jaan-bujh kar aisa hai: paisa owner ka hai.

---

## Connect wala sach (MCP wali baat)

- Meta Business Suite / Ads Manager ke liye Meta ne **koi MCP-jaisa
  plug-and-play connector nahi diya** hai jisse account ek click me
  jud jaye. Meta ka ekmatra official rasta hai: **Marketing API**.
- Isiliye connect **ek baar ka kaam** hai (`SETUP_GUIDE.md`):
  Page → Business portfolio → Ad Account → Developer app → token
  server ki `.env` me. **Uske baad** system API se khud data
  kheenchta hai, drafts banata hai, reports bhejta hai — baar-baar
  login nahi karna padta.
- **Meta Ad Library ke liye koi connect hota hi nahi — kisi ke
  liye bhi nahi.** Meta ne commercial ads ke liye Library ki API
  di hi nahi hai. Isiliye wahan ka sabse zyada automation hai:
  Research Board ke 1-click links + finding record hote hi brief
  aur creative automatic. Jo tool Library ko "auto-pull" karne ka
  daava kare, wo scraping karta hai — account ke liye khatarnak,
  aur is system ke brief me mana hai.
- Aur abhi ki sthiti: **owner ka Meta account suspended hai** —
  connect tabhi hoga jab working account (appeal/recovery se)
  milega. Tab tak automation research/creative/planning/reporting
  (MOCK data) par chalegi.

## Hissa A — Hamesha automatic (koi paisa nahi, koi Meta write nahi)

Ye sab cron jobs se khud chalta hai, owner ko haath nahi lagana:

- [x] Data collect (Meta connect ke baad har 6 ghante; abhi MOCK)
- [x] Competitor research tasks + Research Board links refresh
- [x] Inspiration brief (recorded top creatives se)
- [x] Creative drafts banana (templates; API providers jude hon to
      unse copy/poster/reel bhi) — visual check owner ka rahega
- [x] Har draft par policy check + 39 guardrails ki jaanch
- [x] Optimisation analysis — winner/loser/fatigue pehchanna
- [x] Daily + weekly report (Hinglish) — apne aap banti hai
- [x] Winner thakne par fresh brief (loop restart)
- [x] Har action ka audit log

## Hissa B — Rules sign karne par, caps ke ANDAR automatic

Sirf ye teen Meta-writes auto ho sakte hain, sirf tab jab neeche ke
caps bhare hon aur rules approve hon:

1. **Loser pause** — jo ad `MIN_SPEND` se zyada kharch karke,
   `EVALUATION_WINDOW_DAYS` ke baad bhi target cost par koi
   qualified lead nahi de raha, use pause karna.
2. **Winner scale** — jo ad target cost ke andar qualified leads
   de raha hai, uska budget ek baar me zyada se zyada
   `MAX_BUDGET_CHANGE_PCT`% badhana, `MIN_DAYS_BETWEEN_CHANGES`
   din ke gap se, `PER_CAMPAIGN_CAP` aur `TOTAL_DAILY_BUDGET_CAP`
   ke andar rehte hue.
3. **Naya PAUSED draft banana** — sirf un products ke liye jinki
   permission owner ne pehle se confirm ki ho, aur destination
   ready ho. **Draft PAUSED hi banega.**

### Kabhi automatic NAHI hoga (ye control hamesha owner ka)

- ❌ Kisi ad ko **PAUSED se LIVE** karna — hamesha alag manual
  approval (ye autopilot me bhi nahi hai)
- ❌ Naye product ka **pehla** ad, naya product confirm karna
- ❌ Budget **caps** badhana, destination badalna
- ❌ Kill switch off karna; safety stop ke baad **auto-resume**
- ❌ Meta ki taraf se koi flag/rejection aaye to use dodge karke
  aage badhna — system rukega aur owner ko batayega

## Owner ke controls — kahan-kahan haath rahega

| Control | Kahan | Kaam |
|---|---|---|
| Budget edit | Settings | Daily/per-campaign caps — owner ka roz ka ekmatra kaam yahi rakha hai |
| Kill switch | Settings | Ek click — sab managed ads pause, automation band |
| Mode wapas PROPOSE | Settings → `AUTOMATION_MODE` | Kabhi bhi autopilot band, sirf proposals |
| Approval Queue | Approvals page | Jo auto nahi hua, wahan padh ke approve/reject |
| Audit + Reports | Reports / Errors & Audit | Auto ne kya kiya, roz report me dikhega |
| Rollback | Approval se | Galat auto-change fresh state padh ke, diff dikha ke, approval se wapas |

## Caps — owner bharega (khali = autopilot band rahega)

| Setting | Value (owner bhare) |
|---|---|
| `TOTAL_DAILY_BUDGET_CAP` (₹/din, sab campaigns) | ______ |
| `PER_CAMPAIGN_CAP` (₹/din) | ______ |
| `MAX_BUDGET_CHANGE_PCT` (ek baar me max % badlav) | ______ |
| `TARGET_COST_PER_QUALIFIED_LEAD` (₹) | ______ |
| `MIN_SPEND` (₹ — isse pehle koi verdict nahi) | ______ |
| `MIN_EVENTS` (qualified leads) | ______ |
| `EVALUATION_WINDOW_DAYS` | ______ |
| `MIN_DAYS_BETWEEN_CHANGES` | ______ |

## Ready-to-paste rules draft (Settings → AUTO_RULES_TEXT me daalo)

```
Main, owner, ye rules approve karta hu. In caps ke ANDAR system
khud apply kar sakta hai: (1) target cost se upar kharch karke
bina qualified lead wala loser ad pause karna; (2) target cost ke
andar perform karne wale winner ka budget ek baar me max
MAX_BUDGET_CHANGE_PCT% tak, caps ke andar, badhana; (3) pehle se
confirmed products ke liye naye PAUSED drafts banana. Koi bhi ad
LIVE karna, caps badhana, naya product confirm karna aur safety
stop ke baad resume karna mere alag approval ke bina NAHI hoga.
Koi Meta flag aaye to automation turant rukegi aur mujhe report
milegi.
```

Upar ke caps bhar ke, ye text daal ke, `AUTO_RULES_APPROVED` tick
karke `AUTOMATION_MODE=AUTO_WITHIN_RULES` karna hi autopilot ON
karna hai — aur wapas PROPOSE karna hi OFF. Iske alawa koi hidden
switch kahin nahi hai.
