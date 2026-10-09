# Decisions

Every tuned constant and every judgement call, with the reason. Constants live in
`leadtime/config.py` (and a few local ones next to the code that uses them).

## Data

| Decision | Why |
|---|---|
| One Trends request per (concept, region) containing all the concept's aliases (max 5) | Aliases in one request share a 0–100 scale, so summing them is valid. Separate requests per alias would not be comparable. Raw files are `data/raw/trends/{concept_id}_{geo}.json` rather than `{term}_{geo}` for the same reason. |
| `TIMEFRAME = "today 5-y"` | The longest window Google still returns weekly. Longer ranges come back monthly, which is too coarse for lags of a few weeks. Consequence: anything that trended before Oct 2021 (dalgona coffee, croffle, Basque cheesecake) is outside the data, so it was left off the seed list. |
| Dropped native-name aliases for tanghulu (糖葫芦/糖葫蘆), Einspänner (維也納咖啡) and sea salt coffee (海鹽咖啡) | Each names an established local product in Taiwan/China rather than the trend we track, so it produced year-round seasonal noise that looked like early "takeoffs". The build step ignores the dropped columns. The remaining aliases came from the same request, so they keep a valid shared scale, just with lower resolution where the dropped term dominated (tanghulu in Taiwan). |
| Seed concepts hand-written | No model key was available when the list was made. `scripts/cluster_concepts.py` exists for model clustering of YouTube titles; its output goes to a candidates file for human review, never straight into `concepts.json`. |
| Weeks count only once finished (`week start + 6 days <= as_of`) | Strict no-lookahead. A Sunday `as_of` can't see the week that starts that day. |
| Partial (still-running) weeks from Google are dropped at build time | Their values change after the fact. |

## Takeoff detection

| Constant | Value | Why |
|---|---|---|
| `BASELINE_WEEKS` | 12 | A quarter's median absorbs one-off blips without hiding a real shift. |
| `TAKEOFF_RATIO` | 3.0 | Brief's starting value. 2.5 found the same cases (grid below), so the stricter bar stays. |
| `SUSTAIN` | 3 of next 4 | One spike isn't a trend. It also means a takeoff is only *confirmed* four weeks after it happens, which matters a lot (see findings). |
| `MIN_BASELINE` | 2 | A 0→1 jump isn't infinite growth. |
| `MIN_TAKEOFF_VALUE` | 10 | Below 10/100 Google's numbers are noise. |
| `SMOOTH_WEEKS` | 3 | **Tuned.** Low-volume regions (Singapore especially) come back as 0 / spike / 0 because Google zeroes weeks under its privacy threshold. A trailing 3-week mean (trailing, so no lookahead) turns a run of spikes into a level. It took the history from 7 to 13 cases. |
| `BASELINE_GAP_WEEKS` | 0 | **Tried and rejected.** A gap between baseline and tested week was meant to catch slow climbs (Korea's 2023 tanghulu ramp). It shifted takeoffs later without adding cases and didn't improve the backtest. |

Tuned with `scripts/tune.py` on the full snapshot, then frozen. With 22 concepts this is a small sample, so we only changed what moved results clearly (smoothing) and kept the brief's values otherwise.

```
TAKEOFF_RATIO  SMOOTH_WEEKS  BASELINE_WEEKS  BASELINE_GAP_WEEKS  cases  lag(med)  judged inside early late never  med_warn
(2.5, 1, 12, 0)      7         4       1      1     0    0     0  None
(2.5, 1, 12, 4)      7         5       1      0     1    0     0  None
(2.5, 1, 12, 8)      7         5       1      0     1    0     0  None
(2.5, 1, 12, 12)      7         5       1      0     1    0     0  None
(2.5, 3, 12, 0)     13         3       3      1     0    1     1  58
(2.5, 3, 12, 4)     12        15       4      0     1    1     2  58
(2.5, 3, 12, 8)     12        17       4      0     1    1     2  60
(2.5, 3, 12, 12)     12        46       4      1     1    0     2  60
(3.0, 1, 12, 0)      7         4       1      1     0    0     0  None
(3.0, 1, 12, 4)      7         5       1      0     1    0     0  None
(3.0, 1, 12, 8)      7         5       1      0     1    0     0  None
(3.0, 1, 12, 12)      7         5       1      0     1    0     0  None
(3.0, 3, 12, 0)     13         3       4      1     0    1     2  58
(3.0, 3, 12, 4)     12        14       4      0     1    1     2  58
(3.0, 3, 12, 8)     12        15       4      0     1    1     2  60
(3.0, 3, 12, 12)     12        46       4      1     1    0     2  60
```

### Findings that shaped the product

1. **Foods travel at two speeds.** Global viral hits (Dubai chocolate, tanghulu, crookie, Dubai chewy cookie) reach Singapore 1 to 5 weeks after the first country. Slower regional ones (soufflé pancakes, Einspänner, Korean yogurt ice cream, yakgwa) take 9 months to over 2 years. Pooling both gives windows like "5 to 63 weeks", which is too wide to promise a date.
2. **The fast ones beat confirmation.** A takeoff is confirmed four weeks after it starts. For 8 of 21 foods, Singapore had already taken off by then. Malaysia is often first, and often only a week or two ahead of us.
3. **What this means:** a single forecast date is the weakest part of the product. The useful part is *watching*: knowing the week a food you care about starts moving anywhere, and checking it against your kitchen. That's why the app has a watchlist with a weekly "what changed" feed, and treats the window as context, not a promise.

## Lag and window

| Constant | Value | Why |
|---|---|---|
| `MIN_CASES` | 4 | Below four past cases a percentile range is meaningless. Show "not enough history" instead. |
| `WINDOW_PERCENTILES` | 25–75 | The middle half of past lags reads naturally as "usually". |
| Only lags > 0 build the window | | A food that took off in Singapore first (or the same week) didn't travel to us, so it says nothing about travel time. Those cases still count in the backtest as `already_here`. |
| `NOT_TRAVELLING_GRACE_WEEKS` | 8 | Two months past the window's end with no Singapore takeoff: call it, don't keep promising. |
| `NO_WINDOW_STALE_WEEKS` | 52 | Without a window, a year-old origin takeoff is no longer "rising abroad". |
| `PEAK_RECENT_WEEKS`, `PEAK_DROP`, `PEAK_REVIVE` | 4, 0.4, 0.6 | Mean of the last month below 40% of the Singapore peak = cooled; back above 60% = popular again. A single threshold made the weekly feed flip "peaked" / "taken off" on noise, so status is walked forward from takeoff with the two thresholds. |
| `RISING_WEEKS` | 2 | "Singapore searches are starting to move" needs two weeks in a row above the bar. Low-volume Singapore series come back from Google as 0 / spike / 0, and a single spike fooled the first version. |

## Launch plan

| Constant | Value | Why |
|---|---|---|
| `LAUNCH_LEAD_WEEKS` | 3 | Launch before the window opens, so you're already selling when searches start. |
| Model text may not contain dates, years, URLs or quantities (g, ml, cups...) | | The model writes words only. Dates come from code; "a starting point, not a recipe". A month name on its own ("since July") is allowed, because the prompt hands the model that code-computed fact. |
| Fit text may not contain any digit | | Fit is a kitchen judgement; it has no reason to contain a number, and a number there would look like a trend claim. |
| Fit `missing_equipment` must not list anything the shop has | | Cheap consistency check that catches a model that didn't read the profile. |

## The offline rung

When no model key is set (or every model answer fails validation), the chain falls back to `offline`:
deterministic rules in `fit.offline_fit` and `launch.offline_plan`. It is labelled "offline rules" in every
response and in the UI, never passed off as a model. It exists so the app and the tests work with no keys
and no network. Offline results are not written to the disk cache, so adding a key later takes effect at once.

## Lifespan, decision and review

| Constant | Value | Why |
|---|---|---|
| First wave ends | recent 4-week mean < `PEAK_DROP` (40%) of peak so far, on the 3-week smoothed series | Same measure as "peaked here", so the app is consistent. It marks when the fade is *visible*, about 3 weeks after searches actually start falling (smoothing + 4-week mean); tests pin this. Waves still running are censored, not counted. |
| Typical run | 25th–75th percentile of finished first waves, `MIN_CASES` 4 | Same "usually" convention as the arrival window. Currently 7–13 weeks from 13 Singapore trends. |
| `CLIMBING_SHARE`, `CLIMBING_PEAK_WEEKS` | 0.9, 4 | Near its peak and the peak is recent: don't call it over. |
| `STEADY_WEEKS` | 4 | **Found by inspecting the data.** At the day a Singapore takeoff is confirmed, the three long runs (Dubai chocolate, Dubai chewy cookie, tanghulu) and New York roll had non-zero raw searches in all of the last 4 weeks; every short fad had zero weeks (Google zeroes weeks under its privacy threshold). Without it the late-entry call was "skip" every time (7/13 right, missing all the big ones); with it 11/13. In-sample on 13 cases, so it's a hypothesis to re-check as data grows, and the README says so. |
| `SETUP_WEEKS`, `MIN_SELLING_WEEKS` | 2, 3 | Joining late is worth it only if roughly 5 weeks of demand remain: 2 to test and source, 3 to sell. |
| `STOCK_SAFETY_WEEKS` | 2 | Stop bulk orders 2 weeks before the shortest typical run ends; after that, buy weekly. |
| `MIN_REVIEW_WEEKS` | 3 | Two weeks of sales can't separate a trend from launch-week curiosity. |
| `SALES_DROP`, `SALES_RISE` | 0.6, 1.1 | Recent 2-week average under 60% of the best 2 weeks = falling; last week 10%+ up = climbing. |
| Review logic | | Falling sales + Singapore cooling = wind down. Falling sales + Singapore still up = **rethink** (the item, not the trend, is the problem). Holding + cooling = keep but buy weekly. Holding or climbing + still up = push. |
| Menu overlaps | model, validated | The model may only name items copied from the shop's own menu (case-insensitive, returned in the shop's spelling); anything else fails validation. Offline rule: shares a word of 4+ letters with the food's name or key ingredients. |

## Offers and content

| Constant | Value | Why |
|---|---|---|
| `GIVEAWAY_DEFAULT` | 50 | Enough free portions to make a visible line; small enough that a small shop can afford it. |
| `DISCOUNT_DEFAULT` | 20% | Noticeable without training customers to wait for sales. |
| `LOYALTY_DEFAULT` | buy 5, 6th free | Short enough to finish during a trend that lasts a couple of months. |
| `DROP_DEFAULT`, `DAYS_OPEN` | 40 a day, 6 days | Sells out by mid-afternoon in a small shop; most small F&B shops open six days. Capped by the shop's own daily capacity if given. |
| `BUNDLE_SHARE`, `BUNDLE_MIN_OFF` | 10%, $0.50 | Saving people notice, paid for by selling something already on the menu. |
| `STRETCH_LIFT` | 1.5x | Needing 1.5x normal sales just to break even is flagged "hard to make back" and never suggested. |
| Suggested offer | by verdict | Go (early): giveaway, because the line is the content. Go-but-late: second-half-price / bundle, a reason to pick you. Wait: daily drop / loyalty, protect margin. First non-stretch option wins; no offer if the item loses money. |
| Payback rounding | round to 6 dp before ceil | 18 / 0.2 is 90.000...01 in floating point, which would have said 91. Test pins it. |
| Content formats | keyword triggers on the concept record | The cut, crunch, pull, pour and build, chosen by how many trigger words appear in the food's techniques, ingredients and description; top two kept. No model involved. |
| Post schedule | day −7, −3, 0, +2, +7 | Tease, announce, launch, reactions, follow-up: one week of build-up and one week after. |
| `ANNOUNCE_DAYS` | 3 | "Launch this week" still needs a few days' notice: launch day moves 3 days out and posts that would fall in the past are dropped, with a note saying so. |
| On-screen text | code templates + model hooks | The launch-day line reuses the model's first hook (already validated); everything else is a code template, and a test runs all of it through the launch-plan validator (no dates, links or quantities). |

## Ranking

Status (`arriving_now` then `rising_abroad`), then verdict (`make` then `adapt`), then earliest window start;
concepts with no window sort after dated ones. Skips and unjudged concepts are dropped. Top 3, plus 3 behind "more".

## Model providers

| Decision | Why |
|---|---|
| Chain `soclaas,gemini`, then offline rules | SoCLaaS (NUS SoC, OpenAI-compatible, free for students) answered fit in under a second and full launch plans in about 4–7 s in testing. Gemini's free tier returned 503 / timeouts during the same test, so it's the fallback. Featherless stays supported but out of the default chain (the event code stopped working). |
| `GEMINI_MODEL = gemini-3.8-flash` | Google closed `gemini-2.5-flash` to new keys (HTTP 404 with a message saying so). |
| `<think>` blocks stripped before parsing | Qwen3-family models reason in a `<think>` block first; braces inside it would otherwise confuse the JSON extraction. |
| `RETRIES_ON_INVALID = 1` | An answer that fails validation is dropped, and the same provider is asked once more *with the rejection reason*. The model writes the fix and it is validated from scratch, so this is not repair by guessing. Transport errors (timeouts, 5xx) skip straight to the next provider. In testing, SoCLaaS's first launch plan used "everyone"; the retry came back clean. |
| Limits stated in the prompt | The validator's limits (steps per component, hook count, lengths) are now in the prompt. The first live SoCLaaS plan was rejected for six steps in one component because the prompt never said five. |
| `CAPTION_MAX = 500` | 300 was arbitrary and rejected reasonable captions. |
| `HYPE` words rejected | `CLAUDE.md`: the model never makes a popularity claim. Live output said "hottest", "viral", "everyone is obsessed". Words like these now fail validation; popularity facts come only from code. |
