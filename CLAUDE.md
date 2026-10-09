# CLAUDE.md — Lead Time

Working title. ForgeHacks Online 2026, **AI + Business** track.
Submission locks **Sat 10 Oct 2026, 12:00 pm EDT = Sun 11 Oct 00:00 SGT**. Aim to submit by Sat 18:00 SGT.

## What this is

Lead Time tells a small food business which foods are taking off overseas, whether they're heading for Singapore, roughly how long until they arrive, and which of them this particular shop can actually make.

Viral foods travel between countries with a lag. A dessert takes off in Seoul or Dubai and lands here weeks or months later. We measure that lag from history, apply it to what's rising now, and match the result against the shop's own menu and equipment. The output is three foods to try, each with its evidence and a launch plan: when to launch, what to make in this kitchen, and how to announce it.

**Demo user:** a dessert café in an HDB estate. (Open decision, see the end. A hawker drinks stall is the alternative.)

## The rule that carries the project

**The model reads and judges. Code counts and forecasts.**

- The model clusters messy titles and search terms into food concepts, and judges whether a shop can make a concept.
- Code detects takeoffs, computes lags, forecasts arrival windows and ranks results.
- **No number in a forecast ever comes from the model.** If a model output contains a number we display, that's a bug.
- In launch plans, the model writes the words. Code supplies every date, every trend fact ("taking off in Seoul since July") and every link. The model never outputs a date, a URL or a claim about popularity.
- Model outputs are categorical and schema-validated. Anything that fails validation is dropped and logged, never repaired by guessing.

This is how we answer the judging line "thoughtful integration of AI (not just a wrapper)". Every forecast can be reproduced from the snapshot files with the model switched off.

## Judging criteria (build to these)

Real-world impact · Technical implementation & AI use · Innovation · Execution & completeness · Presentation. Judges are working engineers and data scientists. They will trust a backtest over a claim.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Runtime backend | Python, **standard library only** (`urllib`, `json`, `statistics`) | Same discipline as Voucher Kaki. The maths here is small enough for pure Python. |
| Fetch scripts | `scripts/` may use `pytrends` and `requests` | Dependencies live in `scripts/requirements.txt`, never in the runtime. |
| Model | `Provider` interface: Gemini primary, Featherless fallback | Featherless is a sponsor and exposes an OpenAI-compatible API. Confirm base URL in their docs. |
| Frontend | React 19 + Vite, single app | One screen does most of the work. |
| Charts | Hand-written SVG sparklines | No chart library for two lines. |
| Deploy | Vercel: static frontend + Python functions in `api/` | Proven shape from Voucher Kaki. Add every env var to the Vercel dashboard, not just `.env`. |
| Storage | JSON snapshots committed to the repo; business profile in `localStorage` | No database, no accounts. |

**No live data calls in the request path.** The app reads snapshots only. Fetching is a script you run, and the snapshot's `fetched_at` is shown in the UI.

## Data

### Sources
1. **Google Trends** via `pytrends`: weekly interest over the last 5 years, per term, per region. Regions: `SG`, `KR`, `JP`, `TW`, `AE`, `US`, `MY`.
2. **YouTube Data API v3**: `search.list` (100 quota units) with `regionCode` and food keywords, then `videos.list` (1 unit) for view counts. Titles feed concept discovery. 10,000 units a day, so batch and cache.

**Not used:** TikTok and Instagram. Scraping them breaks their terms. Say so in the README and the video.

### Google Trends caveats (correctness, read before touching scoring)
- Values are **relative 0–100 within a single request**. Never compare magnitudes across requests or regions. Compare **timing** only.
- `pytrends` is unofficial and gets HTTP 429. Sleep between calls, retry with backoff, and cache every response to `data/raw/trends/{term}_{geo}.json` so a run can resume.
- Search for every alias of a concept, not just the English name. A Korean dessert trends in Korea under its Korean name.

### Snapshot files
```
data/raw/trends/*.json         raw pytrends responses, never edited
data/raw/youtube/*.json        raw API responses
data/concepts.json             model-clustered concepts (committed, reviewed by hand)
data/series.json               weekly series per concept per region, built from raw
data/meta.json                 fetched_at, sources, region list, term list
```

## Pipeline

```
seed terms + YouTube titles
        ↓
CLUSTER (model, offline, once)  →  data/concepts.json
        ↓
SERIES (code)  →  weekly series per concept per region
        ↓
TAKEOFF (code)  →  first takeoff week per region
        ↓
LAG (code)  →  historical origin→SG lags  →  arrival window for current trends
        ↓
FIT (model, per request, cached)  →  can this shop make it?
        ↓
RANK (code)  →  three cards
        ↓
LAUNCH (code date + model words + code links)  →  launch plan per card
```

### Concept record (model output, schema-validated)
```json
{
  "id": "dubai-chocolate",
  "name": "Dubai chocolate",
  "aliases": {"en": ["dubai chocolate", "pistachio kunafa bar"], "ko": ["두바이 초콜릿"]},
  "description": "Chocolate bar filled with pistachio cream and toasted kataifi.",
  "category": "dessert",
  "key_ingredients": ["pistachio cream", "kataifi", "chocolate"],
  "techniques": ["tempering", "toasting"],
  "equipment": ["moulds", "stovetop"]
}
```
Clustering runs offline and its output is committed. A human reads `concepts.json` before it's used. Runtime never re-clusters.

### Takeoff detection (all constants named, each with a one-line reason)
- `BASELINE_WEEKS = 12`: trailing median used as baseline.
- `TAKEOFF_RATIO = 3.0`: a week counts if it's at least 3× baseline.
- `SUSTAIN = (3, 4)`: and 3 of the next 4 weeks also clear it, so one spike isn't a trend.
- `MIN_BASELINE = 2`: floor on the baseline so a 0→1 jump isn't infinite growth.

Tune these on the backtest set only, then freeze them. Record the values and the reason in `docs/DECISIONS.md`.

### Lag and arrival window
- Historical lag = SG takeoff week − earliest non-SG takeoff week.
- Current trend: origin has taken off, SG hasn't. Arrival window = origin takeoff + [25th, 75th percentile] of historical lags in the same category, falling back to all categories if fewer than 4 cases.
- Status, one per concept: `rising_abroad` · `arriving_now` · `already_here` · `peaked_here` · `not_travelling`.
- If there are fewer than 4 historical cases in total, show no window at all. Say "not enough history to forecast" rather than inventing one.

### No lookahead (enforced by test)
Every function that reads series takes `as_of`. Nothing may read a week after `as_of`. `tests/test_no_lookahead.py` corrupts all data after `as_of` and asserts the output doesn't change.

### Fit (model output, schema-validated)
Input: one concept + the business profile. Output:
```json
{"verdict": "make" | "adapt" | "skip",
 "adaptation": "Pistachio kunafa iced latte instead of a bar",
 "missing_equipment": [],
 "reason": "One sentence, plain English."}
```
Cache by `(concept_id, profile_hash)` in memory and on disk for the demo profiles.

### Ranking (code)
Sort by status (`arriving_now`, then `rising_abroad`), then verdict (`make` before `adapt`), then earliest arrival. Drop `skip`. Return top three, plus the next three behind a "more" link.

### Launch plan
Three parts: **when**, **what to make**, **how to announce it**.

**When (code only):**
- `LAUNCH_LEAD_WEEKS = 3`: launch this many weeks before the arrival window opens, so the shop is already selling it when people start searching.
- `rising_abroad` → launch by `window_start − LAUNCH_LEAD_WEEKS`, or "this week" if that date has passed.
- `arriving_now` → "this week. Others will be starting too."
- `already_here` / `peaked_here` → no launch date. Show "You'd be following, not leading" and skip the plan.
- No window (not enough history) → no date. Say so.
- All relative to `as_of`, so backtest mode shows the plan as it would have read then.

**What to make (model, schema-validated):** a method outline, not a recipe. Components and techniques, plus swaps for missing equipment or ingredients. No gram quantities. Always shown with the line "A starting point. Test a batch before you sell it."

**How to announce it (model, schema-validated):** three short-video hooks, one caption, one launch offer sized to the shop's price band.

**Source links (code only):** the top 3 recipe or how-to videos for the concept from the YouTube snapshot, by views, with title and channel. If there are none, show none. The model never produces a link.

```json
{"method": [{"component": "Pistachio cream", "steps": ["Blend pistachios with white chocolate until smooth"]}],
 "swaps": [{"original": "kataifi", "use": "toasted crushed feuilletine", "why": "Easier to find locally, same crunch"}],
 "hooks": ["...", "...", "..."],
 "caption": "...",
 "offer": "..."}
```
The prompt receives the code-computed trend facts and date as context so the copy can reference them. A validator rejects any output containing a date pattern or `http`. Cache by `(concept_id, profile_hash)`.

## Features

Priority order. Cut from the bottom.

1. **Recommendations screen:** three cards for the shop's profile.
2. **Evidence on every card:** sparkline of origin vs SG, takeoff weeks marked, the lag in words.
3. **Backtest mode:** "Pretend it's …" date picker. Shows what Lead Time would have said then, then reveals what happened. This is the demo's centrepiece.
4. **Business profile:** three questions, no account. Two demo profiles preloaded (dessert café, hawker drinks stall).
5. **Launch plan:** on each card's detail page. When, what to make, how to announce it, source links. If Friday runs out, cut this whole feature, not half of it.
6. **Concept detail:** aliases, where it started, sources.
7. **"How we worked this out"** panel: the method in five sentences, snapshot date, what data we don't have.
8. *Cut first:* YouTube discovery of new concepts (fall back to the hand seed list). Keep the YouTube fetch for recipe links even if discovery is cut.

**Out of scope:** live data, accounts, TikTok, sales data upload, multilingual UI, notifications, full gram-precise recipes, auto-posting to social media.

## API

```
GET  /api/meta                         snapshot date, regions, provider ladder
GET  /api/concepts?as_of=YYYY-MM-DD    all concepts with status and window
GET  /api/concepts/{id}?as_of=...      one concept with full series
POST /api/recommend                    {profile, as_of} → ranked cards
POST /api/launch                       {concept_id, profile, as_of} → launch plan
GET  /api/backtest                     every historical case: predicted vs actual
```
`as_of` defaults to the snapshot date. Each response carries `agent.attempts` showing which provider answered, as in Voucher Kaki.

## Design

### Who we're designing for
A café or stall owner reading this on a phone between orders. Not a data person. They want one decision: *what should I put on the menu next, and how soon?* Every screen answers that first and explains itself second.

### Voice
Talk like a sharp friend who reads food news, not like a dashboard.

- Yes: "Taking off in Seoul since July. Foods like this usually reach Singapore 6 to 10 weeks later."
- Yes: "You'd need a fryer for the original. Try it as a soft-serve topping instead."
- Yes: "Launch by 2 Nov. That gives you about three weeks before most shops catch on."
- No: "Cross-regional momentum score: 0.82."
- No: "Unlock viral growth."

No jargon on the main screen. "Lag", "takeoff" and "percentile" live only inside "How we worked this out". State uncertainty in words ("usually", "roughly"), never as false precision.

### Colour
Warm and food-market, not tech purple. Defined as tokens on `:root`, redefined for dark mode.

| Token | Light | Use |
|---|---|---|
| `--bg` | `#FBF7F0` (kaya cream) | page |
| `--surface` | `#FFFFFF` | cards |
| `--ink` | `#2B1E16` (kopi-o) | text |
| `--muted` | `#6E5A4B` | secondary text |
| `--accent` | `#2F7D4F` (pandan) | primary actions, origin line |
| `--now` | `#C8402B` (chilli) | `arriving_now` |
| `--soon` | `#D98E1C` (gula melaka) | `rising_abroad` |
| `--sg` | `#2B1E16` | Singapore line on sparklines |

Status is never colour alone. Every status has an icon and a word. Check AA contrast in both themes.

### Type and layout
- Headings: **Fraunces** (feels like a menu board). Body and UI: **Figtree**. Tabular numerals for weeks and dates.
- 16px minimum body, 44px minimum tap targets, single column on mobile, max width 720px on desktop.
- The card is the product. Food name large, status line, one-sentence "why", the adaptation if any, then the sparkline. Nothing else above the fold.

### Approachability
- First screen asks three questions with chips, not forms: what you sell, what equipment you have, your price range. Or "use a demo shop".
- Empty and error states say what happened and what to do next, in one sentence.
- Snapshot date is always visible: "Trend data as of 3 Oct 2026."

## Repo layout
```
api/                 Vercel Python functions (thin; call into leadtime/)
leadtime/
  providers.py       Provider interface, Gemini, Featherless, chain
  concepts.py        load + validate concepts.json
  series.py          build weekly series
  takeoff.py         takeoff detection
  forecast.py        lag, window, status
  fit.py             fit prompt, schema, cache
  rank.py
  launch.py          launch date (code), plan prompt + schema, source links
scripts/
  fetch_trends.py
  fetch_youtube.py
  cluster_concepts.py
  build_series.py
  requirements.txt   script-only dependencies
data/
web/                 React app
tests/
docs/DECISIONS.md    every tuned constant and why
```

## Environment
```
LT_PROVIDER_CHAIN=gemini,featherless
GEMINI_API_KEY=
GEMINI_MODEL=
FEATHERLESS_API_KEY=
FEATHERLESS_MODEL=
YOUTUBE_API_KEY=          scripts only
```
Keys are server-side only. Nothing with a key goes in the browser bundle.

## Testing
- `python -m unittest` must pass with **no network and no keys**. Use a fake provider and fixture series.
- Required: takeoff detection on hand-made series (spike, sustained rise, flat, zero baseline); lag maths; no lookahead; schema rejection of malformed model output; ranking order; "not enough history" path; launch date for each status, including a date already in the past; launch-plan validator rejects dates and URLs in model output.
- `scripts/backtest_report.py` prints predicted vs actual for every historical case. Its output goes in the README unedited.

## Working rules for Claude Code
- Don't add runtime dependencies. If you think one is needed, stop and ask.
- Don't call a live model or API in tests.
- Every magic number gets a name and a reason.
- After writing a file, confirm it landed on disk before reporting success.
- When a result looks too good in the backtest, look for lookahead first.

## Schedule

| Day (SGT) | Ships | Gate |
|---|---|---|
| Tue 6 Oct | Fetch Trends for the seed list. Hand-check 3 known cases. | **If there's no visible lead time in at least 2 of 3 cases, stop and rethink the pitch.** |
| Wed 7 Oct | Concepts, series, takeoff, forecast, backtest report, tests. | Backtest report prints. |
| Thu 8 Oct | Fit, rank, API, recommendations screen. | Demo profile gets three sensible cards. |
| Fri 9 Oct | Backtest mode UI, evidence sparklines, launch plan, deploy, README. | Live URL works on a phone. Launch plan cut if not done by 18:00. |
| Sat 10 Oct | Video (2–4 min, YouTube), Devpost text, architecture diagram, submit. | Submitted by 18:00 SGT. |

### Seed cases to verify on Tuesday
Candidates only. Check each against the data before trusting it: Dubai chocolate, tanghulu, Korean salt bread, croffle, Basque burnt cheesecake, dalgona coffee (likely a counterexample, since it went global almost at once, which is useful to show honestly).

## Video beats (aim for 3:00)
1. **0:00–0:25** A café owner who found out about a viral dessert after every other shop already had it.
2. **0:25–1:10** Enter the shop, get three cards. Open one: launch date, the version this kitchen can make, three hooks.
3. **1:10–2:00** Backtest: set the date to before a known trend, show the forecast, reveal what happened.
4. **2:00–2:35** The rule: model reads and judges, code forecasts. One diagram.
5. **2:35–3:00** What's real, what's a snapshot, what data we don't have.

## Submission checklist
- [ ] Public repo, clear README, licence
- [ ] Video 2–4 min, public on YouTube
- [ ] Track: AI + Business
- [ ] Description: problem and users, technical approach, real-world impact
- [ ] Screenshots + architecture diagram + live link
- [ ] Every team member listed on Devpost

## Open decisions
- **Demo user:** dessert café (default) or hawker drinks stall.
- **Name:** "Lead Time" is a working title. It's the head start you get, and it's the lag we measure.
- **Team:** solo or with the Voucher Kaki team. Changes how much of Thursday–Friday is realistic.
