import { fmtDate, PROVIDER_LABEL } from '../format.js'

const TIMES = { 2: 'twice', 2.5: 'two and a half times', 3: 'three times', 4: 'four times' }

export default function HowPanel({ meta, historyCases }) {
  const ladder = meta?.agent?.ladder || []
  const m = meta?.method || {}
  const times = TIMES[m.takeoff_ratio] || `${m.takeoff_ratio}×`
  const baseline = m.baseline_gap_weeks
    ? `their level a couple of months earlier`
    : 'their usual level'
  const [pLo, pHi] = m.window_percentiles || [25, 75]
  return (
    <details className="panel">
      <summary>How we worked this out</summary>
      <div>
        <p>
          We pull weekly Google search interest for {meta?.concept_count ?? 'each'} foods, in each food's own languages,
          across {meta?.regions?.map((r) => r.name).join(', ')}. Code finds each region's <b>takeoff</b>: the first week
          searches hit {times} {baseline} and stay there for {m.sustain ? `${m.sustain[0]} of the next ${m.sustain[1]} weeks` : 'most of the next month'}.
        </p>
        <p>
          The gap between the first takeoff abroad and Singapore's takeoff is the <b>lag</b>. For a food rising abroad
          now, the arrival window is its takeoff date plus the middle half ({pLo}th to {pHi}th percentile) of past lags,
          using the same kind of food when we have at least {m.min_cases ?? 4} past cases.
          {historyCases != null && ` Right now that history has ${historyCases} cases.`} With fewer, we don't
          guess a window at all.
        </p>
        <p>
          A language model does two jobs only: it judges whether your kitchen can make a food, and it writes the launch
          plan's words. Every date, trend fact, number and link comes from code, and the model's answers are checked
          against a strict format. Anything that fails is thrown away.
          The fallback order is {ladder.map((r) => `${PROVIDER_LABEL[r.provider] || r.provider}${r.configured ? '' : ' (not set up)'}`).join(' → ')}.
        </p>
        <p>
          Trend data as of {fmtDate(meta?.snapshot_date)} (fetched {fmtDate(meta?.fetched_at)}). The app never calls
          Google live. Every forecast can be rebuilt from the snapshot files with the model switched off.
        </p>
        <p><b>What we don't have:</b></p>
        <ul>
          <li>TikTok and Instagram. Scraping them breaks their terms, so we don't.</li>
          <li>Sales data. Search interest is a proxy for demand, not a measure of it.</li>
          <li>Neighbourhood detail. Google Trends is country-level for Singapore.</li>
          <li>Comparable volumes between regions. Each line is scaled to its own peak; we only compare timing.</li>
        </ul>
        <p><a href="#/backtest">See every past case: what we would have said vs what happened →</a></p>
      </div>
    </details>
  )
}
