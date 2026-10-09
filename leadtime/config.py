"""Every tuned constant, with its reason. Values and tuning notes: docs/DECISIONS.md."""

# --- Takeoff detection -------------------------------------------------------
BASELINE_WEEKS = 12      # trailing median over a quarter smooths seasonal blips
BASELINE_GAP_WEEKS = 0   # baseline ends this many weeks before the tested week (slow climbs)
TAKEOFF_RATIO = 3.0      # a week counts as takeoff at >= 3x its baseline
SUSTAIN = (3, 4)         # ...and 3 of the next 4 weeks clear the same bar: one spike isn't a trend
MIN_BASELINE = 2         # floor so a 0 -> 1 jump isn't infinite growth
MIN_TAKEOFF_VALUE = 10   # takeoff week must reach 10/100; below that Google's numbers are noise
SMOOTH_WEEKS = 3         # trailing 3-week mean before detection: Google returns low-volume weeks as 0/spike/0 (tuned: 6 -> 11 cases)
RISING_WEEKS = 2         # "starting to move" needs 2 weeks in a row above the bar; one week is noise

# --- Lag and arrival window --------------------------------------------------
HOME = "SG"
MIN_CASES = 4                    # fewer historical cases than this: show no window at all
WINDOW_PERCENTILES = (25, 75)    # middle half of past lags = "usually"
NOT_TRAVELLING_GRACE_WEEKS = 8   # past window end + this with no SG takeoff: it didn't travel
NO_WINDOW_STALE_WEEKS = 52       # with no window, an origin takeoff older than a year is stale
WIDE_WINDOW_WEEKS = 20           # past lags spread wider than ~5 months: too wide to give a date, say "watch it"

# --- Status inside Singapore ---------------------------------------------------
PEAK_RECENT_WEEKS = 4    # "now" = mean of the last 4 weeks, so one quiet week isn't a crash
PEAK_DROP = 0.4          # now below 40% of the SG peak since takeoff = peaked here
PEAK_REVIVE = 0.6        # ...and only "popular again" once back above 60%: the gap stops week-to-week flapping

# --- Launch plan -------------------------------------------------------------
LAUNCH_LEAD_WEEKS = 3    # launch this far before the window opens so you're selling when searches start

# --- Decision and review -----------------------------------------------------
CLIMBING_SHARE = 0.9     # recent mean within 90% of the peak...
CLIMBING_PEAK_WEEKS = 4  # ...and the peak no more than 4 weeks ago = still climbing; don't call it over
STEADY_WEEKS = 4         # searched (non-zero) in every one of the last 4 raw weeks = steady demand, not spikes
SETUP_WEEKS = 2          # typical time to test a recipe, source stock and launch
MIN_SELLING_WEEKS = 3    # not worth setting up for less than ~3 weeks of selling
STOCK_SAFETY_WEEKS = 2   # stop bulk orders this long before the shortest typical run ends
MIN_REVIEW_WEEKS = 3     # need three weeks of sales before calling keep / push / drop
SALES_DROP = 0.6         # recent 2-week average below 60% of the best 2 weeks = falling
SALES_RISE = 1.1         # last week 10%+ above the week before = climbing

# --- Ranking -----------------------------------------------------------------
TOP_N = 3                # cards shown
MORE_N = 3               # cards behind "more"
