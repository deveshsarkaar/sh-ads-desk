# AUTONOMY_24X7.md — Advanced autonomy: connect once, system 24x7

Owner ki maang: software itna advance aur automatic ho ki **ek
baar connect + setup ke baad ye apne aap 24 ghante kaam kare** —
maintenance ho ya koi na ho, kisi par dependency na rahe — aur
beech-beech me owner apne hisaab se **customize** bhi kar sake,
power uske haath me rahe. Ye document batata hai wo kaise bana
hai, aur kahan imaandari ki seema hai.

## Architecture (kya-kya lagaya gaya)

| Layer | Kaam | Dependency sach |
|---|---|---|
| **Worker daemon** (`app/worker.py`) | Alag 24x7 service: schedule khud rakhta hai (collect 6 ghante, optimise/daily roz, loop/weekly hafte me), queue drain karta hai, heartbeat likhta hai, ek job fail ho to audit karke aage badhta hai — daemon kabhi nahi marta | Docker `restart: unless-stopped` — crash/host reboot par **apne aap wapas** |
| **Redis** (`app/redis_layer.py`) | Job queue + cache ki fast lane. Client **stdlib RESP protocol** se likha hai — koi pip package nahi | **Optional hai.** Redis band/unreachable ho to system SQLite queue par chal padta hai — Redis kabhi single point of failure nahi |
| **Job queue** (`app/job_queue.py`) | Redis list ya SQLite table — ek hi interface; duplicate job dobara queue nahi hota (dedupe) | — |
| **Autonomy controls** (`app/autonomy.py` + Settings page) | Owner ke toggles: AUTO_COLLECT / AUTO_RESEARCH / AUTO_CREATIVE_DRAFTS / AUTO_REPORTS / AUTO_OPTIMISE_PROPOSALS, QUIET_HOURS (jaise 23-07, tab sirf collect), WORKER_TICK_SECONDS, worker status card (heartbeat, queue backend, pending jobs) | Owner kabhi bhi koi bhi hissa band kar sakta hai |
| **AI provider layer** (`app/providers.py`) | Text/image/video generation model-agnostic hai — model naam config se aata hai | **2026–27 ke naye models bina code badle** sirf provider config/model naam badal kar plug honge. Jo technology abhi aayi hi nahi, uska daava koi nahi kar sakta — system uske liye ready hai, bas |

## Telethon wali baat — saaf sach

Telethon ek **Telegram** library hai (user accounts se Telegram
chalane ke liye). SH Ads Desk Meta Ads ka system hai — isme
Telethon ka koi kaam nahi hai, isliye use nahi lagaya gaya.
Uski jagah is system ki asal zaroorat wali advanced cheezein
lagayi gayi hain: Redis-backed queue, 24x7 worker daemon,
self-healing schedule aur model-agnostic AI layer. (Telethon
Lucifer wale Telegram tools me pehle se use ho raha hai — wahan
wo sahi jagah hai.)

## "Apne aap sab hota rahe" — do hisse, imaandari se

1. **Housekeeping — poora auto, 24x7:** data collect, competitor
   research tasks, inspiration briefs, creative drafts, policy/
   guardrail checks, winner/loser analysis, daily/weekly reports,
   fatigue par naye drafts. Ye sab paisa kharch nahi karte aur
   Meta ko kuch likhte nahi — isliye bina ruke chal sakte hain.
2. **Meta-writes — owner ke signed rules ke andar hi auto:**
   loser pause, winner scale, PAUSED draft. Ye tabhi auto honge
   jab owner ne AUTOPILOT_RULES sign kiye hon + caps bhare hon +
   AUTOMATION_MODE=AUTO_WITHIN_RULES ho. Uske bina worker sirf
   **proposals** banata hai. Ad LIVE karna, caps badhana, kill
   switch band karna, safety-stop ke baad resume — **kabhi auto
   nahi**. Ye seema kamzori nahi hai: yahi wo power hai jo owner
   ke haath me rehti hai.

## Owner ki power (customize + control)

- Settings me har auto hissa alag ON/OFF; budget caps kabhi bhi
  badlo — agla tick wahi se chalega
- Kill switch: ek click — sab rukta hai, worker idle ho jata
  hai, aur ye **apne aap kabhi resume nahi hota**
- AUTOMATION_MODE kabhi bhi wapas PROPOSE — har cheez phir
  approval se
- Har auto action audit log + daily report me dikhta hai —
  "system ne kal kya kiya" hamesha pata chalega

## Chalana

`docker compose up -d` — teen services: web, **worker**, **redis**.
Bas. Cron ki bhi zaroorat nahi (chaho to CLI jobs
(`python -m app.jobs ...`) ab bhi manual chal sakte hain).
Worker ki sehat Settings page ke "24x7 Worker — sthiti" card me
dikhti hai.

## UNTESTED (imaandari)

- Redis path unit-test codec/queue-fallback tak hai; asli Redis
  server ke saath live run owner ke VPS par pehli baar hoga
  (SQLite fallback test-verified hai, to risk kam hai).
- Worker tick ka poora cycle MOCK data par test-verified hai
  (89/89 tests). Real Meta path pehle ki tarah UNTESTED hai —
  working Meta account ke bina ho bhi nahi sakta.
