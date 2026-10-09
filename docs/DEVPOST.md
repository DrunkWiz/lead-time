# Devpost submission: Lead Time

Copy each section into the matching Devpost field. Edit the "we" wording to fit your team.

---

## Project name
Lead Time

## Tagline (short description)
Tells small Singapore food businesses which overseas food trends are heading their way, whether their kitchen can make them, and how to launch, price and promote them before the shop next door.

## Track
AI + Business

---

## Inspiration
A café owner in an HDB estate usually finds out about the next viral dessert after every other shop already sells it. Dubai chocolate, tanghulu and Korean yogurt ice cream all took off overseas first. We wanted to know: is there a measurable head start, and can a small shop use it?

## What it does
Lead Time watches weekly search interest for 22 trending foods across Singapore, South Korea, Japan, Taiwan, the UAE, the US and Malaysia, then turns that into decisions for one specific shop:

- **Picks:** up to three foods heading for Singapore that this kitchen can make, with a chart showing where each started and whether Singapore is moving.
- **Should you do it?** Go / Go-but-late / Wait / Skip, with plain reasons: timing, whether your kitchen can make it, overlap with your current menu, how long trends typically last here (7 to 13 weeks; a few run a year), your margin, and a profit range from your own price and sales guess.
- **Stock plan:** bulk-order until a date, then buy week by week, so you're not left holding kataifi when the trend dies.
- **Launch offer:** six offers (giveaway, discount, second half price, loyalty card, daily drop, bundle) priced against your own costs, showing what each costs you and what you'd need to sell to break even. One is suggested for your timing.
- **Content plan:** a dated posting schedule with shot lists chosen from what the food is (a filled bar gets "the cut", a crunchy one "the crunch", a drink "the pour").
- **After launch:** log weekly sales and get keep / push / rethink / wind-down, read against Singapore's search curve. If sales fall while searches are still up, the item is the problem, not the trend.
- **This week:** a weekly feed of what changed, flagged for foods you're watching.
- **Pretend it's...:** rewind every screen to any past date, using only the data visible then, then reveal what actually happened.

## How we built it
**The rule: the model reads and judges; code counts and forecasts.**

- **Data:** Google Trends via pytrends, every alias in its own language (탕후루, ドバイチョコ, شوكولاتة دبي...), committed as a snapshot. The app never calls Google live.
- **Code (Python, standard library only):** detects each region's takeoff (3x baseline, sustained 3 of the next 4 weeks), measures the lag to Singapore, builds arrival windows from past cases, measures how long trends last here, and computes every verdict, date, price and profit figure. Every function takes an `as_of` date; a test corrupts all data after it and checks nothing changes.
- **AI:** an open model (Qwen via NUS SoCLaaS, with Gemini as fallback) judges whether a kitchen can make a food, spots overlaps with the shop's menu, and writes launch-plan copy. Every answer is schema-validated. It's rejected if it contains a date, link, quantity, a number (for kitchen checks), a menu item that isn't on the shop's menu, or a popularity claim ("viral", "hottest"). A rejected answer gets one retry with the reason; it is never patched up by us. If every model fails, clearly labelled offline rules answer, so the app always works.
- **Frontend:** React 19 + Vite, hand-written SVG charts, designed phone-first for an owner between orders.
- 93 automated tests, runnable with no network and no API keys.

## Challenges we ran into
- **The head start is smaller than we hoped, and we say so.** Global viral foods reach Singapore 1 to 5 weeks after the first country, often right after Malaysia. For 8 of 21 foods, Singapore had already taken off before a takeoff abroad could be confirmed. Slower regional foods take 9 months to 2+ years, and there the warning is real: Korean yogurt ice cream was flagged 58 weeks before it took off here. So the app leads with *watching* and decisions, and says "watch it" instead of inventing a date when past lags are too spread out.
- **"Already here, still worth joining?"** A simple rule said "skip" every time and missed every big hit. The long-running trends had one thing in common four weeks in: Singapore searched for them every single week, not in spikes. That rule gets 11 of 13 past cases right, but we found it on those same 13 cases, so we report it as untested on new data.
- **Keeping the model honest.** Early model copy said "Singapore's hottest dessert trend" and "everyone is obsessed". Popularity claims must come from data, so the validator now rejects them and the model rewrites.
- Noisy low-volume data (Google zeroes small weeks), statuses flapping week to week, Google Trends rate limits, and a retired Gemini model, all fixed and documented in `docs/DECISIONS.md`.

## Accomplishments that we're proud of
- An honest, reproducible backtest instead of a claim: every forecast can be replayed from the snapshot with the model switched off.
- AI that does real work (judging kitchens, matching menus, writing copy) inside hard guardrails, with every number and date coming from code.
- A full loop for a real owner: what to make, whether it's worth it, how to price, promote and stock it, and when to stop.

## What we learned
Food trends travel at two speeds, most Singapore food trends last about two months, and the most useful thing for a small shop isn't a forecast date: it's knowing the week something starts moving, whether their kitchen can do it, and when to get out.

## What's next
- **Data that competitors can't copy:** with opt-in accounts, logged launches and sales become outcome-based forecasts, benchmarks for shops, and ingredient-demand forecasts for suppliers (aggregate only, PDPA-compliant). Free for shops, paid for suppliers and chains.
- A scheduled weekly data refresh, more regions (Thailand, Indonesia, the Philippines, China) and more foods via automatic discovery.
- Connecting to till systems so sales log themselves.

## What works and what doesn't
- **Works end to end:** everything listed above, tested in the browser on phone and desktop.
- **Limits:** snapshot data (to 3 Oct 2026), 22 foods; only 4 arrival forecasts could be strictly checked (1 inside its window); the late-entry rule is in-sample; without a model key the copy comes from simpler offline rules; no YouTube recipe links in this snapshot; board data lives in one browser.

## Built with
python, react, vite, javascript, svg, google-trends, pytrends, qwen, soclaas, gemini, vercel

## Links
- GitHub: (add your repo URL)
- Demo video: (add your YouTube URL)
- Live demo: (add if deployed)

## Image gallery
- `docs/architecture.png` (architecture diagram)
- Screenshots: Picks, "Should you do it?", Launch offer + content plan, "Pretend it's..." reveal, This week
