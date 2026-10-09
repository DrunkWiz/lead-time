# Devpost submission: Lead Time

Copy each block into the matching Devpost field. Change "we" to "I" if you're submitting solo.

---

## Project name

**Lead Time** (recommended). Alternatives if you want one:
- Lead Time: the head start for small food shops
- Next Menu
- Trend Lag

## Tagline (short description, 200 characters max)

Tells small Singapore food businesses which overseas food trends are heading their way, whether their kitchen can make them, and how to launch, price and promote them first.

## Track

AI + Business

---

## About the project (paste into the story field)

### The problem
A café owner in an HDB estate usually finds out about the next viral dessert after every other shop already sells it. Dubai chocolate, tanghulu and Korean yogurt ice cream all took off overseas first. Big chains have trend teams. A two-person café has Instagram and a gut feeling. By the time it's on their feed, the queue has moved on, and they've bulk-bought ingredients for a trend that's already cooling.

### Who it's for
Small food businesses in Singapore: dessert cafés, bakeries, hawker drinks stalls, home bakers. People reading on a phone between orders, not data people. They want one answer: *what should I put on the menu next, and how soon?*

### What Lead Time does
Lead Time watches weekly Google search interest for 22 trending foods across Singapore, South Korea, Japan, Taiwan, the UAE, the US and Malaysia. It measures how long foods have taken to travel from abroad to Singapore, applies that to what's rising now, and matches the result against the shop's own equipment, price range and current menu.

### Key features
- **Picks:** up to three foods heading for Singapore that *this* kitchen can make, each with a chart showing where it started and whether Singapore is moving yet.
- **Should you do it?** Go / Go but late / Wait and watch / Skip, with plain reasons: timing, whether the kitchen can make it, overlap with the current menu, how long trends usually last here (7 to 13 weeks; a few run a year), and a profit range from the shop's own price and sales estimate.
- **What to charge:** type what each part costs per portion and get a suggested price and margin.
- **Stock plan:** "bulk order until 10 Aug, then buy week by week", so nobody is left holding kataifi when the trend dies.
- **Launch offer:** six offers (giveaway, discount, second half price, loyalty card, daily drop, bundle) priced against the shop's own costs, with what each costs and how many sales it takes to pay back. One is suggested for the timing.
- **Content plan:** a dated posting schedule with shot lists chosen from what the food is (a filled bar gets "the cut", a crunchy one "the crunch", a drink "the pour").
- **After launch:** log weekly sales and get push / keep / rethink / wind down, read against Singapore's search curve. If sales drop while searches are still up, the item is the problem, not the trend.
- **This week:** a weekly feed of what moved, flagged for foods the shop is watching.
- **Pretend it's…:** rewind every screen to any past date using only the data that existed then, then reveal what actually happened.

### How it works: the model reads and judges, code counts and forecasts
- **Data:** Google Trends via pytrends, every alias in its own language (탕후루, ドバイチョコ, شوكولاتة دبي…), committed as a snapshot. The app never calls Google live, and the snapshot date is shown on every screen.
- **Code (Python standard library only):** detects each region's takeoff (3× its recent baseline, sustained for 3 of the next 4 weeks), measures the lag to Singapore, builds arrival windows from past cases, measures how long trends last here, and computes every verdict, date, price and profit. Every function takes an `as_of` date. One test corrupts all data after that date and checks that nothing changes, so there's no lookahead.
- **AI:** an open model (Qwen on NUS SoCLaaS, with Gemini as fallback) judges whether a kitchen can make a food, spots overlaps with the shop's menu, and writes the launch-plan words. Every answer is schema-validated and rejected if it contains a date, a link, a quantity, a menu item the shop doesn't sell, or a popularity claim ("viral", "hottest"). A rejected answer gets one retry with the reason. It is never patched up by us. If every model fails, clearly labelled offline rules answer, so the app always works.
- **Frontend:** React 19 + Vite, hand-written SVG charts, designed phone-first.
- **93 automated tests** that run with no network and no API keys.

### Technologies used
Python (standard library runtime), React 19, Vite, hand-written SVG, Google Trends (pytrends, offline), Qwen via NUS SoCLaaS, Google Gemini, Docker, Render.

### What we found (honestly)
- **Foods travel at two speeds.** Global viral hits reach Singapore 1 to 5 weeks after the first country, often right after Malaysia. For 8 of 21 foods, Singapore had already taken off before a takeoff abroad could be confirmed. Slower regional foods take 9 months to 2+ years, and there the warning is real: Korean yogurt ice cream was flagged as rising in Korea 58 weeks before it took off here. Our date window for it was still 19 weeks too early, and the app shows that.
- **So Lead Time leads with watching and deciding, not promising dates.** When past lags are too spread out, it says "watch it" instead of inventing a date.
- **Backtest, unedited in the README:** of 4 arrival forecasts we could strictly check, 1 landed inside its window. The "already here, still worth joining?" rule gets 11 of 13 past cases right, but we found it on those same cases, so we label it untested on new data.

### Challenges
- Early model copy said "Singapore's hottest dessert trend" and "everyone is obsessed". Popularity claims must come from data, so the validator rejects them and the model rewrites. During the final cache build it happened 4 times out of 16 plans, and all 4 retries came back clean.
- Noisy low-volume data (Google zeroes small weeks), statuses flipping week to week, Google Trends rate limits, and a retired Gemini model. All fixed and documented in `docs/DECISIONS.md`.

### What we learned
Most Singapore food trends last about two months. For a small shop, the most useful thing isn't a forecast date. It's knowing the week something starts moving, whether their kitchen can do it, what it's worth to them, and when to get out.

### What's next
- **Data competitors can't copy:** with opt-in accounts, logged launches and sales become outcome-based forecasts, shop benchmarks, and ingredient-demand forecasts for suppliers (aggregate only, PDPA-compliant). Free for shops, paid for suppliers and chains.
- A scheduled weekly data refresh, more regions (Thailand, Indonesia, the Philippines, China) and automatic discovery of new foods.
- Connecting to till systems so sales log themselves.

### What works and what doesn't
- **Works end to end:** everything listed above, tested in the browser on phone and desktop.
- **Limits:** snapshot data to 3 Oct 2026; 22 foods; only 4 arrival forecasts could be strictly checked; the late-entry rule is in-sample; no TikTok or Instagram data (scraping breaks their terms); no YouTube recipe links in this snapshot; the board lives in one browser.

### Try it
- **Live demo:** (Render URL). *Hosted on Render's free tier: if nobody has used it for 15 minutes, the first load takes up to a minute while the server wakes up. After that it's instant.* Tap **Dessert café**, then the **6 Jul 2024** chip under "Pretend it's…".
- **Run locally:** see the README (one command after building the frontend).

---

## Built with (tags)
python, react, vite, javascript, svg, google-trends, pytrends, qwen, soclaas, gemini, docker, render

## Links
- GitHub repo: https://github.com/DrunkWiz/lead-time
- Demo video (YouTube, public): (add URL)
- Live demo: (add Render URL)

---

## Image gallery: screenshot checklist

Capture in Chrome at iPhone 12 Pro size (F12 → Ctrl+Shift+M). To save: DevTools **⋮** menu → **Capture screenshot**, or **Capture full size screenshot** for long pages. Use the Dessert café demo shop.

1. **Welcome screen:** "What should you put on the menu next?" with the two demo shop cards.
2. **Picks at 6 Jul 2024:** the Pretend bar set to 6 Jul 2024, card #1 Dubai chocolate · Arriving now, with its chart and "Kitchen check: SoCLaaS".
3. **Should you do it? Go:** after typing 45 a week and costs 0.60 / 0.35 / 0.45 / 0.15, showing "$1,150 to $1,807 profit over a typical run" and the stock plan.
4. **Launch offer + Content plan:** "First 50 free on launch day" and the dated shot list (Announce · The cut).
5. **The reveal:** Korean yogurt ice cream at 6 Jul 2024 after **Reveal what happened next** ("58 weeks after the date you picked"), with the shaded chart.
6. **Architecture:** `docs/architecture.png` (already made).

Put the architecture diagram or screenshot 2 first, since the first image is the project thumbnail.
