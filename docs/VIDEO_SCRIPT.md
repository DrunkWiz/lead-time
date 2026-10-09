# Demo video script (target 3:00, limit 2–4 min)

**Before recording**
- Start both servers (API on 8787, app on 5174), with the SoCLaaS key set.
- Open the app once and click through the Dubai chocolate page at **6 Jul 2024**, so model answers are warm.
- Clear the board: open the browser console and run `localStorage.removeItem('leadtime.board')`.
- Phone-sized window (about 400 px wide) or the browser's mobile view; zoom 110–125% so text is readable.
- Pre-fill nothing. Have these numbers ready: costs 0.60 / 0.35 / 0.45 / 0.15, expected 45 a week.

---

## 0:00–0:20 · The problem
**Screen:** the first screen of the app.
**Say:** "If you run a small café in Singapore, you usually hear about the next viral dessert after every other shop already sells it. Dubai chocolate, tanghulu, Korean yogurt ice cream: they all took off overseas first. Lead Time asks: is there a head start, and can a small shop actually use it?"

## 0:20–0:45 · Set up the shop
**Do:** tap **Dessert café**. Point at the profile: equipment, price range, current menu.
**Say:** "No account. Three questions, or a demo shop. Lead Time knows what this kitchen has and what's already on the menu."

## 0:45–1:35 · The centrepiece: rewind to July 2024
**Do:** under "Pretend it's…", tap **6 Jul 2024** (the chip says "just before Korean yogurt ice cream").
**Say:** "Let's rewind to 6 July 2024, using only data that existed that day."
**Do:** open the top card, **Dubai chocolate**. Show "Should you do it? Go".
**Say:** "It took off in Malaysia in May, and Singapore searches are just starting to move. Verdict: Go. The kitchen check, done by an open model, says this café can make the original, and flags it's close to their pistachio latte."
**Do:** type the costs into "What to charge" and 45 a week into "Should you do it?". Show the profit range and the stock plan.
**Say:** "Typical trends here last 7 to 13 weeks: about $1,150 to $1,800 profit over the run, and stop bulk-ordering by 10 August."
**Do:** scroll to **Launch offer** ("First 50 free costs about $78 and pays back after 22 sales") and the **Content plan** (dated posts, "the cut", "the crunch").
**Do:** tap **Reveal what happened next**.
**Say:** "What happened: Singapore's takeoff had already started in early June. That's the honest lesson: global hits give you weeks, not months, so you have to be watching."
**Do:** open **Explore** (still July 2024), tap **Korean yogurt ice cream**, show "Wait and watch", then **Reveal**.
**Say:** "But slower trends are different. On the same day, Korean yogurt ice cream said: watch it. Singapore took off in August 2025, more than a year later. That's a real head start."

## 1:35–2:05 · After launch, and every week
**Do:** mark it launched, log three weeks (38, 52, 61). Show **Push it**. Open **This week**, then **My board**.
**Say:** "Once it's on the menu, log weekly sales. It reads your sales against Singapore's curve: keep pushing, buy weekly, or wind it down before you're stuck with stock. And every week: what moved, for the foods you're watching."

## 2:05–2:40 · How it works (show `docs/architecture.png`)
**Say:** "The rule that carries the project: the model reads and judges, code counts and forecasts. Code finds each country's takeoff, measures the lag to Singapore, and computes every date, price and profit. The model judges kitchens, matches menus and writes the copy, and every answer is checked: no dates, no links, no made-up popularity claims, or it's rejected and rewritten. 93 tests, and a no-lookahead test that corrupts the future and checks nothing changes."

## 2:40–3:00 · What's real and what we learned
**Do:** open the "How we worked this out" panel or the backtest page.
**Say:** "Honest results: global viral foods reach Singapore in one to five weeks, often after Malaysia, so the head start is short. Slower regional foods give months of warning. That's why Lead Time focuses on watching and deciding, not promising a date. It's Google Trends data, not TikTok, which we don't scrape. Next: real sales data from shops, turned into forecasts and ingredient-demand insights for suppliers. Lead Time: the head start, for the shops that need it most."

---

**After recording:** upload to YouTube as **Public** or **Unlisted** (the rules say public, so use Public to be safe), and paste the link into Devpost and the README.
