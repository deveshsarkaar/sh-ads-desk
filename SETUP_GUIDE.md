# SETUP_GUIDE.md — SH Ads Desk Step 2

**Owner ke manual Meta steps, screen by screen.** Ye saare steps aap
khud Meta ki apni screens par karoge. Assistant kabhi aapka password
nahi mangega, aur token kabhi chat me nahi bhejna hai — token sirf
aapke server ki `.env` file me jayega (Step 6).

Time lagega: lagbhag 30–45 minute, agar saari screens smooth khuli to.

---

## ⚠️ Pehle ye padho — suspended accounts ke baare me

Aapke maujooda Meta accounts abhi **suspended** hain. Is guide ka har
step ek **working (chal rahe) Meta account** ko chahiye.

- Agar login hi blocked hai, to pehla kaam is guide se pehle hai:
  Meta ka **appeal / account recovery** wala rasta (jo notice Meta ne
  diya hai, usi ke andar se). Jab tak ek working account nahi milta,
  neeche ke steps wahin rukenge jahan login chahiye.
- **Bilkul nahi karna:** ban ko dodge karne ke liye naya Facebook
  account, nayi Page ya naya Business portfolio banana. Ye Meta ki
  policy ke khilaf hai, is system ke brief me bhi mana hai, aur isse
  suspension aur pakki ho sakti hai. Ek hi sahi rasta hai — recovery /
  appeal, phir wahi account, phir ye guide.

---

## Step 1 — Facebook Page banao

*(Agar Software Hub ki Page pehle se hai aur working account ke paas
uska access hai, to ye step skip karo.)*

1. Browser me kholo: **facebook.com/pages/create**
2. Page ka naam likho (jaise: **Software Hub**), category chuno
   (jaise: Software / Website), aur bio me ek line likho.
3. **Create Page** dabao.
4. Profile photo aur cover photo lagao (sahi logo, sahi naam — galat
   branding wala creative baad me policy check me bhi fail hota hai).
5. Page ban gayi. Isi Page se saare ads chalenge — Page hi ad ki
   pehchan (identity) hai. (Instagram account hona zaruri nahi hai;
   Instagram par ad Page ke naam se hi dikhega. Agar ad apne Instagram
   handle se dikhana hai, to ek **Instagram professional (business/
   creator) account** ko Page se connect karna hoga — wo ad banate
   time Identity me choose hota hai. Personal Instagram account ad ki
   pehchan nahi ban sakta.)

## Step 2 — Business portfolio (Business Manager) banao

1. Kholo: **business.facebook.com** → **Create account** (ya Business
   Settings).
2. Business ka naam (jaise: **Propvance IT Solutions**), apna naam aur
   business email do → **Submit**.
3. Left menu me **Business Settings** kholo.
4. **Business Assets → Pages → Add → Add a Page** — Step 1 wali Page
   apne portfolio me jodo (full control lo).
5. **Users → People** me dekho ki aap khud **Admin** ho. Sirf aap.

## Step 3 — Ad account banao + payment method add karo

1. Business Settings → **Accounts → Ad Accounts → Add → Create a New
   Ad Account**.
2. Naam do (jaise: **Software Hub — Main**).
3. ⚠️ **Time zone: Asia/Kolkata** aur **Currency: INR** dhyaan se
   chuno — ye dono baad me badle nahi ja sakte. Galat chuna to naya ad
   account banana padega.
4. **Create** karo. Ad account ID note kar lo — ye `act_` se shuru
   hoti hai (jaise `act_1234567890`). Ye ID baad me `.env` me jayegi
   (Step 6) — ID secret nahi hai, lekin token ke saath kabhi share mat
   karna.
5. Payment method: Ad account kholo → **Payment Settings** (billing
   screen) → **Add Payment Method** → apna card/UPI jo Meta accept
   kare, wahi add karo.
   - Ye sirf **Meta ki apni billing screen** par hoga. SH Ads Desk app
     kabhi card nahi mangti, assistant kabhi card nahi mangega. Koi
     chat ya form me card number aaye to ruk jao — wo hum nahi hain.
6. (Recommended, brief ki safety rule) Yahi waqt hai Meta ke native
   limit ka: **Account Spending Limit** set kar do — ek aisi rakam
   jisse zyada Meta khud kharch rok de. Ye system ke apne caps ke
   upar ek dusri suraksha hai.

## Step 4 — Developer app banao (Marketing API)

1. Kholo: **developers.facebook.com** → **My Apps** → **Create App**.
2. App ka naam do (jaise: **SH Ads Desk**), contact email do, aur app
   ko apne **Business portfolio** se connect karo (Settings me option
   aata hai: business portfolio connect karna).
   - Note: Meta kehta hai unverified business portfolio add ho sakta
     hai, **lekin ads chalane se pehle portfolio verified hona
     chahiye**. Agar Meta verification mange (business documents /
     email-domain check), to wahi Meta ki screens par pura karo.
3. App dashboard me **Use Cases** kholo. Pehle sirf **ek** use case
   add karo:
   - ✅ **"Measure ad performance data"** — ye read-only hai, Step 3 ke
     liye. Isse app ko `ads_read` milta hai.
   - ⏸️ **"Create & manage ads"** — abhi **nahi**. Ye Step 4 me, jab
     aap approve karoge, tab add hoga (isse `ads_management` — likhne
     ki permission — aati hai).
   - ⏸️ **"Capture & manage ad leads"** — sirf tab, jab Instant-Form
     leads lene ka faisla ho (isse `leads_retrieval` bhi lagta hai).
4. **App Roles** (Settings / Roles) me khud ko **Admin** rakho. Kisi
   aur ko abhi mat jodo; zarurat pade to baad me **Tester** banao.
5. **Kuch bhi "Advanced access" ya App Review ke liye submit mat
   karo.** Meta ke docs saaf kehte hain: apne khud ke ad account ke
   liye `ads_read`/`ads_management` ka **standard access kaafi hai**.
   App Review sirf dusro ke accounts manage karne par lagta hai — wo
   humara kaam hi nahi hai. (Details: `META_ACCESS.md`.)

## Step 5 — Token banao (Meta ki screen par)

Ye Step 3 ke time hoga, abhi sirf samajh lo:

1. App dashboard ya **Graph API Explorer** (developers.facebook.com/tools/explorer)
   me **Generate Access Token** karo aur sirf **`ads_read`** permission
   do (Step 3 ke liye).
2. Meta ka token **time-limited** hota hai (Quickstart wala token Meta
   2 months valid batata hai) — expire ho to yahi step dobara.
3. Token ko **kahin likhna ya bhejna nahi hai** — seedha apne server
   par Step 6 wala kaam.

## Step 6 — Token ko SH Ads Desk se connect karo (.env)

Server par jahan SH Ads Desk chal raha hai, wahan `.env` file me ye
teen cheezein rakho (`.env.example` me bhi di hain):

```
META_ACCESS_TOKEN=<token jo Step 5 me Meta ki screen se mila>
META_AD_ACCOUNT_ID=act_<Step 3 wali ad account ID>
META_PAGE_ID=<Step 1 wali Page ki ID>
META_MODE=MOCK
```

- `META_MODE` ko **MOCK hi rakho** jab tak Step 3 ka read-only compare
  (API ke numbers vs Ads Manager ke numbers) pass na ho. Uske baad hi
  `LIVE` hoga.
- Token sirf `.env` me rehta hai — app ke andar type nahi hota, repo
  me nahi jata, chat me kabhi nahi. Galti se kahin share ho jaye to
  Meta ki screen se token revoke karke naya banao.

---

## Sirf live par chalne wali cheezein (imaandari se)

- Upar ke **saare steps sirf aapke asal Meta account par** honge —
  inka koi mock version nahi hai. Assistant in screens ko aapke liye
  operate nahi kar sakta; password/token hamesha aapke haath me rahega.
- **Step 3** (read-only API connect + Ads Manager se number compare)
  tabhi hoga jab Step 5–6 ka token `.env` me hoga.
- **Step 4** (pehla PAUSED draft) tabhi hoga jab aap ek specific draft
  ko approval queue me approve karoge. Activation hamesha alag
  approval hai.
- **Step 5** (unattended jobs) ke liye agar token-expiry takleef de,
  to Meta ka **system user** wala rasta hai — Business Settings me ek
  system user banakar sirf apne ad account + Page ka access dena.
  Wo faisla tab ka hai, abhi ka nahi. (Details: `META_ACCESS.md` §5.)

*Step 2 guide, 2026-11-16. Is guide ke technical daave (permissions,
access tiers, token validity) `META_ACCESS.md` me official sources ke
saath verify kiye gaye hain.*
