# HOSTING.md — SH Ads Desk ko khud host karna (Hostinger)

Do raste hain. **Path A (Docker on VPS)** sabse bharosemand hai.
**Path B (hPanel Python app)** hosting plan par nirbhar hai.

> ⚠️ **UNVERIFIED note:** Hostinger ke hPanel ke andar ke exact menu naam aur
> steps is build me live verify NAHI hue hain. Jahan "check in your hPanel"
> likha hai, wahan apne panel me wahi option dhoondho — naam thoda alag ho
> sakta hai. Python version 3.11+ zaroori hai; agar plan me Python app support
> nahi hai to Path A (VPS) hi chalega.

---

## Path A — Hostinger VPS + Docker (recommended)

1. VPS par SSH se login karo (Hostinger hPanel → VPS → SSH access —
   *check in your hPanel*).
2. Docker aur Docker Compose install karo (Ubuntu par aam taur par:
   `sudo apt update && sudo apt install -y docker.io docker-compose-v2` —
   apne OS ke hisaab se official Docker docs dekho).
3. Is ZIP ko server par le jao aur unzip karo:
   ```bash
   unzip sh-ads-desk-full.zip
   cd sh-ads-desk-full
   ```
4. Env file banao:
   ```bash
   cp .env.example .env
   nano .env        # COOKIE_SECURE aur baki values apne hisaab se
   ```
   `.env` ko kabhi share/commit mat karo.
5. Chalao:
   ```bash
   docker compose up -d --build
   docker compose logs -f        # "SH Ads Desk running" dikhna chahiye
   # Teen services uthte hain: web (8000), worker (24x7 engine —
   # collect/optimise/reports/loop apne aap, restart: unless-stopped)
   # aur redis (queue ki fast lane; band ho jaye to system SQLite
   # queue par chal padta hai). Worker ki sehat app ke Settings
   # page par "24x7 Worker — sthiti" card me dikhti hai. Cron ki
   # zaroorat nahi — schedule worker ke paas hai.
   ```
6. Browser me `http://<server-ip>:8000/setup` kholo aur owner password set
   karo (kam se kam 10 characters). **Setup ke baad ye page band ho jata hai.**
7. HTTPS ke liye VPS par ek reverse proxy (jaise Caddy ya Nginx) domain ke
   saath lagao aur `.env` me `COOKIE_SECURE=1` karke `docker compose restart`.
   Domain/DNS steps Hostinger panel se hote hain — *check in your hPanel*.

## Path B — hPanel Python app (bina Docker)

1. hPanel me Python app ka option dhoondho (*check in your hPanel* — har plan
   me ye feature nahi hota; kuch shared plans par Python sirf CGI/limited
   hota hai).
2. App root me is folder ki files upload karo (File Manager ya FTP se) —
   `.env` apni values ke saath server par hi banao, ZIP wali `.env.example`
   se copy karke.
3. Python version 3.11+ chuno. Startup file/command:
   - Command: `python run.py`
   - Ya WSGI-style setup ho to working directory app folder rakho aur
     environment me `HOST`/`PORT` panel ke diye port par rakho
     (*check in your hPanel* — panel aksar apna port deta hai).
4. `data/` folder ko writable rakho — database wahi banta hai.
5. Browser me apne domain par `/setup` kholo, owner password set karo.

> Agar panel ka Python app feature long-running process allow nahi karta,
> app band ho jayegi — us sthiti me Path A hi sahi hai. (UNVERIFIED — apne
> plan ki details hPanel me check karo.)

## API keys jodna (generation providers — OpenAI/Claude/Higgsfield/Kling)

Do tareeke hain — ek hi use karo:

**Tareeka 1 — hosted UI se (aasaan):**
1. App kholo → **API Providers** page.
2. Har capability (Text / Image / Video) ke card me preset chuno — known
   presets (OpenAI, Claude, Higgsfield, Kling) me **base URL aur default
   model pehle se bhara hai, bas API key paste karke "Connection save karo"**
   dabao. Base URL sirf "Custom" preset me khud bharna padta hai.
3. "Test connection" dabakar dekho — green matlab endpoint ne jawab diya
   (generation ki guarantee nahi; adapters real accounts par UNTESTED hain).
4. Key server par `data/secrets.env` me save hoti hai (chmod 600). UI use
   kabhi wapas nahi dikhata.

**Tareeka 2 — environment variables se:**
`.env` (Docker) ya server ke environment me ye rakho — env wali key UI
wali par jeet-ti hai:
```bash
SH_ADS_TEXT_API_KEY=...
SH_ADS_IMAGE_API_KEY=...
SH_ADS_VIDEO_API_KEY=...
```
Docker Compose `env_file: .env` se ye apne aap app ko mil jayenge; app
restart karo (`docker compose restart`) taaki naye env lagein.

> ⚠️ **Higgsfield key ka format:** key wale khane me `KEY_ID:KEY_SECRET`
> dono ek saath paste karo (unka auth `Authorization: Key ...` hai, preset
> me set hai). **Kling note:** official Kling API JWT auth use karta hai —
> simple key sirf Kling-compatible gateway par chalegi (README dekho).

## Scheduled jobs (cron) — always-on agent NAHI hai

Hostinger cron jobs (*check in your hPanel* → Advanced → Cron Jobs) ya VPS
crontab me:

```cron
0 */6 * * *  cd /path/to/sh-ads-desk-full && python3 -m app.jobs collect
30 9 * * *   cd /path/to/sh-ads-desk-full && python3 -m app.jobs optimise
0 9 * * *    cd /path/to/sh-ads-desk-full && python3 -m app.jobs daily
0 9 * * 1    cd /path/to/sh-ads-desk-full && python3 -m app.jobs weekly
```

Docker use kar rahe ho to: `docker compose exec sh-ads-desk python -m app.jobs daily`
jaisi command cron me rakho.

## Backup

- **Code:** poora folder (`.env` aur `data/secrets.env` ko chhodkar) —
  ZIP/git private repo.
- **Data (koi secret nahi):** `data/state.db` + `data/settings.json` +
  `data/provider_config.json` + `data/generated/` (generated posters/videos)
  + root ki `PRODUCT_ELIGIBILITY.yaml` (agar web UI se confirmations hue hain).
- ⚠️ **Secrets wala backup (alag, surakshit jagah):** `.env` AUR
  `data/secrets.env` — dusri wali me tumhari provider API keys hain. In
  dono ka backup code backup ke saath kabhi share/commit mat karo; kho
  jayein to keys provider ke console se dobara banani padegi aur app me
  phir se paste karni hogi.
- Restore: files wapas rakho, `docker compose up -d`, ho gaya. Database
  SQLite hai — koi alag DB server nahi chahiye.

## Update karna

Naya ZIP aaye to: purana folder backup karo → nayi files overwrite karo
(`data/` aur `.env` ko haath mat lagao) → `docker compose up -d --build`
(ya Python app restart).
