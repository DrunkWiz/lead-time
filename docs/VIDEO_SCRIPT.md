# Demo video: shot list and voiceover (target 2:15)

**Length rule:** ForgeHacks asks for 2 to 4 minutes. Aim for 2:15 so a fast read never drops under 2:00. If you run long, cut beat 7 first.

Every number below was checked against the app at `as_of = 6 Jul 2024` with the Dessert café demo shop. Model answers for that shop are cached, so every screen loads in under a second.

---

## Before you hit record (5 minutes)

1. **Start the app** (one process serves the app and the API). In PowerShell, from the repo folder:
   ```powershell
   npm --prefix web run build; $env:PORT=8010; py -3.14 scripts/serve.py
   ```
   Open **http://localhost:8010** in Chrome.
2. **Phone view:** press F12 → device toolbar (Ctrl+Shift+M) → **iPhone 12 Pro** (390 × 844). Zoom the page to 125% so text reads on video.
3. **Clean start:** in the F12 console run `localStorage.clear()`, then reload. You should see "What should you put on the menu next?"
4. **Second tab:** open `docs/architecture.png` in another Chrome tab for beat 8.
5. **Recorder:** OBS or Xbox Game Bar (Win+Alt+R), 1080p. Close notifications. Hide the bookmarks bar.
6. **Dry run once**, then clear localStorage again and record for real.

Numbers to type (keep them on a sticky note): **45** sold a week; costs **0.60, 0.35, 0.45, 0.15**.

---

## Shot list

| Time | Screen | Do exactly this |
|---|---|---|
| 0:00–0:12 | Welcome screen | Nothing. Let the headline sit. |
| 0:12–0:22 | Welcome screen | Tap **Dessert café** (first demo card). |
| 0:22–0:32 | Picks | Under **Pretend it's…**, tap the chip **6 Jul 2024 · just before Korean yogurt ice cream**. Wait for the cards. |
| 0:32–0:44 | Picks | Hover over card **#1 Dubai chocolate · Arriving now**. Point at "Close to your Pistachio latte". Tap **Launch plan →**. |
| 0:44–1:08 | Dubai chocolate page | Show **Should you do it? Go**. Type **45** in **Expected sold per week**. Scroll down to **What to charge** and type **0.60 · 0.35 · 0.45 · 0.15**. Scroll back up to show **$1,150 to $1,807 profit over a typical run** and **Stop bulk ordering by 10 Aug 2024**. |
| 1:08–1:22 | Same page | Scroll down to **Launch offer** ("First 50 free on launch day") and the **Content plan** (Announce · The cut). |
| 1:22–1:36 | Same page | Scroll up to **The evidence**, tap **Reveal what happened next**. Hold on "Singapore took off in June 2024. Inside the window we gave." |
| 1:36–1:52 | Explore | Tap **Explore** (top tab). Tap **Korean yogurt ice cream**. Show **Wait and watch**. Tap **Reveal what happened next**: "58 weeks after the date you picked. 19 weeks later than our window." |
| 1:52–2:08 | `architecture.png` tab | Switch tabs. Slowly move the cursor from the green **CODE** box to the orange **MODEL** box. |
| 2:08–2:18 | App | Switch back. Tap **Back to today** in the Pretend bar. End on the Picks screen. |

---

## Voiceover (about 370 words: 2:15 to 2:30 at a normal pace)

**1 · Problem (0:00)**
"If you run a small café in Singapore, you usually hear about the next viral dessert after every other shop already sells it. Lead Time looks for the head start."

**2 · Your shop (0:12)**
"No account. Pick a demo shop, or answer three questions: what you sell, your equipment and your price range. It knows your current menu too."

**3 · Rewind (0:22)**
"Here's the honest test. We rewind to the sixth of July, 2024. Every screen now uses only the data that existed that day."

**4 · The pick (0:32)**
"Top pick: Dubai chocolate. It's taking off in Malaysia, and Singapore searches are starting to move. An open model checked this kitchen: it can make the original, and it's close to the pistachio latte already on the menu."

**5 · Should you do it? (0:44)**
"Should you do it? Go. Tell it you'd sell about forty-five a week and what each part costs. It suggests charging about five dollars twenty, and estimates eleven hundred to eighteen hundred dollars profit over a typical run, because most trends here last seven to eleven weeks. So: stop bulk-ordering by the tenth of August."

**6 · Launch it (1:08)**
"Then how to launch: an offer priced on your own costs. Fifty free on day one costs about seventy-eight dollars and pays back after twenty-two sales. And a dated content plan, with shots picked from the food itself. A filled bar gets the cut."

**7 · What happened (1:22)**
"Now reveal what actually happened. Singapore took off in June. The forecast held, but for a global hit the head start is weeks, not months."

"Slower trends are different. That same day, Korean yogurt ice cream said: wait and watch. It reached Singapore fifty-eight weeks later. Our date window was off by nineteen weeks, and the app tells you that too."

**8 · How it works (1:52)**
"The rule behind it: the model reads and judges, code counts and forecasts. Code finds each country's takeoff, measures the lag to Singapore, and computes every date, price and profit. The model, Qwen on NUS SoCLaaS with Gemini as backup, judges kitchens and writes the copy. If its answer contains a date, a link or a word like 'viral', it's rejected. Ninety-three tests, including one that corrupts the future to prove nothing peeks ahead."

**9 · Close (2:08)**
"Real Google Trends data, free to run. Lead Time: the head start, for the shops that need it most."

---

## After recording

- Trim dead air at the start and end. Check the length is **over 2:00**.
- Upload to YouTube as **Public** (the rules ask for a public video). Title: "Lead Time: food trend head starts for Singapore food businesses (ForgeHacks 2026)".
- Paste the link into Devpost and into the README's top section.
