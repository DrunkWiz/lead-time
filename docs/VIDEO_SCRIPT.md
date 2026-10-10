# Demo video: shot list and voiceover (2:52)

**Length rule:** ForgeHacks asks for 2 to 4 minutes. This cut runs 2:52.

The submitted cut was rendered from this script: the real app driven by Playwright at 1920 × 1080, with a synthetic voiceover (Kokoro, voice `af_heart`) and captions in `lead-time-demo.srt`. To record it with your own voice instead, follow the same shots; every number below was checked against the app at `as_of = 6 Jul 2024` with the example dessert café, whose model answers are cached so every screen loads in under a second.

---

## Before you hit record (5 minutes)

1. **Start the app** (one process serves the app and the API). In PowerShell, from the repo folder:
   ```powershell
   npm --prefix web run build; $env:PORT=8010; py -3.14 scripts/serve.py
   ```
   Open **http://localhost:8010** in Chrome.
2. **Window:** a desktop window about 1440 × 810 (the sidebar layout). Zoom to 110% if text looks small on video.
3. **Clean start:** in the F12 console run `localStorage.clear()`, then reload. You should see "Your next bestseller starts with a signal." and the example-café notice.
4. **Second tab:** open `docs/architecture.svg` (or `.png`) in another tab for the "How it works" beat.
5. **Recorder:** OBS or Xbox Game Bar (Win+Alt+R), 1080p. Close notifications. Hide the bookmarks bar.
6. **Dry run once**, then clear localStorage again and record for real.

Numbers to type (keep them on a sticky note): **45** sold a week; costs **0.60, 0.35, 0.45, 0.15**.

---

## Shot list

| Time | Screen | Do exactly this |
|---|---|---|
| 0:00–0:10 | Title card, then **Overview** | Hold on the title. Cut to the overview (today). |
| 0:10–0:18 | Overview | Point at **Take a look around** (the example dessert café). Scroll to **Worth your first batch** and point at **Matched against Block 216 Dessert Café**. |
| 0:18–0:22 | Your kitchen | Scroll up, tap **Personalise my picks**. Scroll down past the three questions (what you sell, equipment, price range). |
| 0:22–0:32 | Overview at 6 Jul 2024 | Tap **Cancel**. Tap **Explore history** (top right), then the chip **6 Jul 2024 · just before Korean yogurt ice cream**. Tap the date button again to fold the bar away, then scroll to **Your picks, back then**. |
| 0:32–0:38 | Overview at 6 Jul 2024 | Point at card **#1 Dubai chocolate · Arriving now**, then its first line. |
| 0:38–0:47 | Overview at 6 Jul 2024 | Point at **You can make the original**, then **Close to your Pistachio latte and Chocolate lava cake**. |
| 0:47–0:49 | Dubai chocolate | Tap **Launch plan →**. **Should you do it? Go** is at the top. |
| 0:49–0:56 | Dubai chocolate | Type **45** in **Expected sold per week**. Scroll to **What to charge** and type **0.60 · 0.35 · 0.45 · 0.15**. |
| 0:56–1:00 | Dubai chocolate | Point at **Charge about $5.20**. |
| 1:00–1:12 | Dubai chocolate | Scroll back up to **Is it worth it for you?**: **$1,150 to $1,807 profit over a typical run**, then **Stop bulk ordering by 10 Aug 2024**. |
| 1:12–1:22 | Dubai chocolate | Scroll to **Launch offer**: **First 50 free on launch day**, "You make it back after 22 full-price sales". |
| 1:22–1:28 | Dubai chocolate | Scroll to **Content plan**: **Announce · The cut**. |
| 1:28–1:31 | Dubai chocolate | Scroll up to **The evidence**, tap **Reveal what happened next**. |
| 1:31–1:38 | Dubai chocolate | Hold on "Singapore took off in June 2024. Inside the window we gave." |
| 1:38–1:44 | Korean yogurt ice cream | Tap **Trend radar** (sidebar), then **Korean yogurt ice cream**. Point at **Wait and watch**. |
| 1:44–1:52 | Korean yogurt ice cream | Tap **Reveal what happened next**: "58 weeks after the date you picked. 19 weeks later than our window." |
| 1:52–1:58 | Trend radar | Scroll up, tap **Return to latest snapshot**, then **Trend radar**. Tick **Compare** on the first three foods. |
| 1:58–2:03 | Trend radar | Tap **Compare signals** and hold on the table. |
| 2:03–2:11 | Launch board | Tap **Close comparison**. Tap **Plan** on the first food and **Watch** on the second, then open **Launch board**. |
| 2:11–2:17 | `docs/architecture.svg` | Whole diagram. |
| 2:17–2:24 | `docs/architecture.svg` | Zoom to the green **CODE** box. |
| 2:24–2:36 | `docs/architecture.svg` | Pan down to the orange **MODEL** box. |
| 2:36–2:44 | `docs/architecture.svg` | Zoom to "Every function takes as_of… 94 tests". |
| 2:44–2:51 | End card | Lead Time · lead-time-cjnn.onrender.com · github.com/DrunkWiz/lead-time |

---

## Voiceover (about 427 words)

**Problem (0:00)**
"If you run a small café in Singapore, you usually hear about the next viral dessert after every other shop already sells it. Lead Time looks for the head start."

**Your shop (0:10)**
"No account needed. It opens on an example dessert café, with its equipment, price range and current menu."
"Or answer three quick questions to set up your own kitchen."

**Rewind (0:22)**
"Here's the honest test. We rewind to the sixth of July, 2024. Every screen now uses only the data that existed that day."

**The pick (0:32)**
"Top pick: Dubai chocolate. It's taking off in Malaysia, and Singapore searches are starting to move."
"An open model checked this kitchen. It can make the original, and it's close to the pistachio latte already on the menu."

**Should you do it? (0:47)**
"Should you do it? Go."
"Tell it you'd sell about forty-five a week, and what each part costs."
"It suggests charging about five dollars twenty."
"Most trends here last seven to eleven weeks, so that's roughly eleven hundred to eighteen hundred dollars profit over a typical run. And: stop bulk-ordering by the tenth of August."

**Launch it (1:12)**
"Then, how to launch. An offer priced on your own costs: fifty free on day one costs about seventy-eight dollars, and pays back after twenty-two sales."
"And a dated content plan, with shots picked from the food itself. A filled bar gets the cut."

**What happened (1:28)**
"Now, reveal what actually happened."
"Singapore took off in June. The forecast held. But for a global hit, the head start is weeks, not months."
"Slower trends are different. On that same day, Korean yogurt ice cream said: wait and watch."
"It reached Singapore fifty-eight weeks later. Our date window was off by nineteen weeks, and the app tells you that too."

**Plan it (1:52)**
"Back to today. The trend radar lists every food we track, with search and filters. Tick up to three,"
"and compare them side by side."
"And the launch board takes each idea from watching, to planning, to launched, then tracks your weekly sales against Singapore's searches."

**How it works (2:11)**
"The rule behind it: the model reads and judges. Code counts and forecasts."
"Code finds each country's takeoff, measures the lag to Singapore, and computes every date, price and profit."
"The model, Qwen on NUS SoCLaaS with Gemini as backup, judges kitchens and writes the copy. If its answer contains a date, a link, or a word like "viral", it's rejected."
"Ninety-four tests run with no network and no keys, including one that corrupts the future to prove nothing peeks ahead."

**Close (2:44)**
"Real Google Trends data, free to run. Lead Time: the head start, for the shops that need it most."

---

## After recording

- Upload to YouTube as **Public** (the rules ask for a public video). Title: "Lead Time: food trend head starts for Singapore food businesses (ForgeHacks 2026)". Upload `lead-time-demo.srt` under Subtitles so the captions are exact.
- Paste the link into Devpost and into the README's **Demo video** line.
