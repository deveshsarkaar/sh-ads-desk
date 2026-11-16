# YOUTUBE_LEARNINGS.md — Owner-sent training videos, integrated

Owner (Devesh bhai) ne 16 Nov 2026 ko teen YouTube Meta Ads training
videos bheje, instruction ke saath: dekho, seekho, aur jo kaam ka hai
wo **SH Ads Desk me execute karo**. Teeno videos browser me khol kar
unke transcript panels se padhe gaye (koi download nahi, koi sign-in /
like / subscribe / comment nahi). Neeche per-video: kya seekha, system
me kya add hua, aur kya screen-out hua.

**Integration point:** saari passing strategies `app/strategy_library.py`
me data ke roop me seed hain — ids **YT1-\*** (video 1), **YT2-\***
(video 2), **YT3-\*** (video 3), plus ek screening entry **YT-DNA**.
Ye entries Growth Loop, roles aur Strategy Library page ko wahi se
milti hain jaise baki entries (Damini S*, practitioner P*, books B*,
winner habits W*, viral patterns V*) milti hain. Saari entries
**practitioner-labelled** hain — ye Meta ke official rules nahi hain;
official rules Policies/Knowledge register me alag rehte hain.

---

## Video 1 — Sabri Suby, "Learn 97% of Meta Ads in Under 19 minutes"
- Link: https://youtu.be/NTmWqnPIb2s (18:51, published 12 Jun 2026)
- **Seekha:** hook-first creative (AIDA order), simple static ads bhi
  test batch me, winning format ko clone karna (format, ad nahi),
  broad targeting jahan creative khud filtering kare, landing page
  ka headline ad ke promise se match, intent-wise structured
  retargeting ladder, gradual scaling + CBO consolidation,
  scale se pehle Pixel + Conversions API.
- **System me add (8 entries):** YT1-1 AIDA hook-first creative ·
  YT1-2 format cloning (concept only) · YT1-3 static ads in every
  test batch · YT1-4 broad targeting · YT1-5 landing-page congruence ·
  YT1-6 retargeting ladder · YT1-7 gradual CBO scaling · YT1-8
  Pixel + CAPI before scaling.

## Video 2 — HBA Services, "Master Facebook Ads in Just 40 Mints | Meta Ads Full Course 2027"
- Link: https://youtu.be/6QhaintnRFE (Hindi/Urdu beginner course;
  spoken content ~20 min, uske baad music)
- **Seekha:** pehle campaign se pehle ka setup order (Business
  Suite/Manager → ad account → Page → Pixel → payment), 6 objectives
  ka sahi chunaav (Sales/Leads/Traffic walkthroughs), Core / Custom /
  Lookalike audience blocks, Pixel-based retargeting, stable result
  ke baad hi gradual budget increase, bidding options (caps ko data
  chahiye), aur common beginner mistakes ki checklist.
- **System me add (7 entries):** YT2-1 setup order · YT2-2 objective
  from real goal · YT2-3 Core/Custom/Lookalike blocks · YT2-4
  Pixel retargeting audiences · YT2-5 gradual budget increase ·
  YT2-6 bidding options · YT2-7 beginner mistakes checklist.

## Video 3 — WsCube Tech (Himanshu Tiwari), "Master Meta Ads in 90 Minutes: AI, Targeting & Campaign Setup (2027 Edition)"
- Link: https://www.youtube.com/live/m11HrK84lxY (live-streamed
  31 Oct 2026, 1:28:55)
- **Seekha:** AI-assisted campaign setup (AI se audience research,
  copy, multiple sizes/variations me image — human approval ke
  baad launch), Special Ad Category ki galtiyon ka nuksaan
  (housing/employment/credit — Real Estate profiles ke liye seedha
  relevant), Auction vs Reservation buying, CBO vs ABO ka faisla,
  multi-ad-set × multi-creative testing structure, performance goal
  funnel event se match, Manual vs Advantage+ audience controls ka
  trade-off, aur one-week data-before-decisions rule.
- **System me add (8 entries):** YT3-1 AI-assisted workflow ·
  YT3-2 Special Ad Category · YT3-3 Auction vs Reservation ·
  YT3-4 CBO vs ABO decision rule · YT3-5 testing grid · YT3-6
  performance-goal match · YT3-7 Manual vs Advantage+ · YT3-8
  one-week data rule.

## Screened OUT (teeno videos se)
- **Creators ke apne earnings / revenue / ROAS claims** — teeno
  presenters ke apne business ke numbers unverified marketing
  claims hain. Wo benchmarks ya defaults ke roop me kahin seed
  **nahi** hue. Ye screening **YT-DNA** entry ke roop me
  DO-NOT-APPLY me darj hai.
- **Verbatim ad copying** — Video 1 ka "clone the winner" sirf
  format/concept level par liya gaya (YT1-2 par screening note);
  kisi aur ka ad, text ya asset reuse system me banned hai.
- **Numbers as defaults** — videos ke budget %, day counts
  (jaise one-week rule) practitioner rules of thumb hain; system
  me wo owner-editable settings ke through apply hote hain,
  hardcoded defaults kabhi nahi.

## Honest labels
- **VERIFIED:** teeno transcripts browser me padhe gaye; 23
  strategies + 1 DO-NOT-APPLY entry library me seed; test suite
  me inke liye dedicated test add hai.
- **PRACTITIONER:** saari YT* entries unke creators ki sikhayi
  hui tactics hain — Meta official guidance nahi. Jahan ye pehle
  ki research (Damini / winner-patterns) se milti hain, wahan
  entry me cross-reference diya hai.
- **UNTESTED:** in strategies ka koi live Meta test nahi hua —
  Meta account ki sthiti (suspended) ki wajah se koi real ad
  abhi chal hi nahi sakta. Approval gates, eligibility gate aur
  destination gate bilkul waise hi lage rehte hain.
