# SETUP_CHECKLIST.md — SH Ads Desk Setup (1 page, tick karte jao)

Har step ke aage wala box tick karo, agla step tabhi karo jab pichla
ho jaye. Kul 3 hisse hain. Andaz: Hissa 1 ~15 min, Hissa 2 ~10 min,
Hissa 3 ~30–45 min (sirf working Meta account ke saath).
Details kahin atke to: hosting = `HOSTING.md`, Meta screens =
`SETUP_GUIDE.md`.

---

## Hissa 1 — Software chalana (VPS + Docker)

- [ ] GitHub repo se code liya: https://github.com/deveshsarkaar/sh-ads-desk
- [ ] VPS par SSH login ho gaya (Hostinger hPanel → VPS → SSH access)
- [ ] Docker + Docker Compose install hai
      (`docker --version` chal raha hai)
- [ ] Code VPS par aa gaya (git clone ya ZIP upload + unzip)
- [ ] `.env` file bani: `cp .env.example .env` — values apne hisaab se
      bhari; `.env` kisi ke saath share/commit NAHI ki
- [ ] App chal gaya: `docker compose up -d --build`
- [ ] Log me "SH Ads Desk running" dikha: `docker compose logs -f`
- [ ] Browser me `http://<server-ip>:8000/setup` khol ke **owner
      password set** kar diya (kam se kam 10 characters) — setup ke
      baad ye page khud band ho jata hai
- [ ] (Baad me, domain jodne par) HTTPS lagaya aur `.env` me
      `COOKIE_SECURE=1` karke `docker compose restart` kiya

✅ **Hissa 1 pura = software live hai. Research, creative, planning,
reports abhi se chalenge (MOCK mode).**

## Hissa 2 — Software ke andar setup

- [ ] Login karke **Business Profile** check kiya (Software Hub
      default hai; naya business ho to naya profile banao)
- [ ] **Products/Offerings** list dekhi — sirf unhi products ko
      confirm kiya jinki permission sach me hai (proof note +
      date ke saath). Confirm nahi = uska ad ban hi nahi sakta,
      ye jaan-bujh kar aisa hai
- [ ] **Destination** set kiya: apni website ka sahi link daala aur
      `DESTINATION_READY` on kiya (bina iske ad nahi banega)
- [ ] **Settings** me apne budget caps bhare (daily/monthly limit,
      ek change me max kitna % budget badhe) — khaali chhoda to
      system kuch kharch propose hi nahi karega
- [ ] `AUTOMATION_MODE` ko **PROPOSE** hi rehne diya (default yahi
      hai — bina approval kuch auto nahi hota)
- [ ] (Optional) **API Providers** page me apni keys daali — Text
      (OpenAI/Claude), Image, Video (Higgsfield/Kling); preset me
      base URL pehle se bhara hai, sirf key paste karni hai;
      "Test connection" green dekha. Key sirf server par rehti
      hai, chat me kabhi nahi bhejni
- [ ] Ek test creative bana ke dekha: Creative Studio → copy/poster
      brief ready, policy check PASS dikha
- [ ] Cron jobs lagaye (HOSTING.md wali 4 lines) — collect /
      optimise / daily / weekly reports ke liye

✅ **Hissa 2 pura = system tumhare business ke hisaab se ready hai.**

## Hissa 3 — Meta connect (asli ad ke liye)

> ⚠️ **Pehli shart:** ek **working Meta account** chahiye. Account
> suspended hai to pehle Meta ke notice se **appeal/recovery** karo.
> Ban dodge karne ke liye naya account/Page/portfolio **bilkul
> mat banao** — ye policy ke khilaf hai aur suspension pakki
> kar dega. Screen-by-screen details: `SETUP_GUIDE.md`.

- [ ] **Facebook Page** ready hai (naam/logo sahi)
- [ ] **Business portfolio** ban gaya; Page usme add hai; tum khud
      Admin ho
- [ ] **Ad Account** ban gaya — ⚠️ **Currency: INR** aur
      **Timezone: Asia/Kolkata** sahi chune (ye baad me badalte NAHI)
- [ ] Ad Account ID (`act_...`) note kar li
- [ ] **Payment method** Meta ki apni billing screen par add kiya
      (card/UPI sirf wahi — app ya chat me kabhi nahi)
- [ ] Meta par **Account Spending Limit** set kar di (dusri suraksha)
- [ ] **Developer app** ban gaya (developers.facebook.com), business
      portfolio se connect hai
- [ ] App me sirf **"Measure ad performance data"** use case add
      kiya (`ads_read`) — "Create & manage ads" abhi NAHI
- [ ] **Token** Meta ki screen se banaya — sirf `ads_read`
- [ ] Token server ki `.env` me rakha (`META_ACCESS_TOKEN`,
      `META_AD_ACCOUNT_ID`, `META_PAGE_ID`) — chat/repo me NAHI;
      `META_MODE=MOCK` abhi waisa hi rakha
- [ ] **Read-only test:** `python -m app.jobs collect` chalaya aur
      API ke numbers **Ads Manager se match** kiye — match nahi
      to yahi rukna hai, aage nahi badhna
- [ ] Match ke baad hi `META_MODE=LIVE` kiya

✅ **Hissa 3 pura = asli data system me aane lagega.**

## Pehla asli ad (uske baad)

- [ ] Planner se campaign draft bana (PAUSED plan)
- [ ] Draft ne saare gates pass kiye: eligibility ✓ destination ✓
      policy ✓ guardrails ✓
- [ ] **Approval Queue** me draft ko khud padh ke **Approve** kiya
      (approve karne par bhi sirf PAUSED campaign banta hai)
- [ ] Execute kiya → Meta me PAUSED campaign bana, khud Ads Manager
      me jaake verify kiya
- [ ] **Live karna alag approval hai** — jab ready ho, tab soch ke
      faisla lo; pehle din chhota budget + spending limit ke saath

## Kahin atke to

- Password/token/card **kabhi chat me mat bhejo** — ye hamesha
  Meta/server ki apni screen par rehte hain.
- Kill switch hamesha Settings me hai — kuch galat lage to pehle
  wahi on karo, phir dekho.
- Backup yaad rakho: `data/state.db` + settings; `.env` aur
  `data/secrets.env` ka backup alag, surakshit jagah (HOSTING.md).
