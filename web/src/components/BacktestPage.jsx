import { fmtDate, fmtMonthYear } from '../format.js'

const OUTCOME = {
  inside: 'Inside window',
  early: 'Came early',
  late: 'Came late',
  never_arrived: "Didn't come",
  already_here: 'Singapore was first or too fast',
  no_forecast: 'Not enough history then',
  pending: 'Still waiting',
}

export default function BacktestPage({ backtest, onPick }) {
  if (!backtest) return <p className="loading">Loading the backtest…</p>
  const s = backtest.summary
  return (
    <div>
      <a className="btn ghost back" href="#/">← All picks</a>
      <h1>Every past case</h1>
      <p className="muted" style={{ marginTop: 8 }}>
        For each food that took off abroad, we rewound to the first day we could have spotted it, forecast using only
        the data visible that day, then checked what Singapore actually did.
      </p>
      <div className="block">
        <p>
          <b className="num">{s.inside_window}</b> of <b className="num">{s.forecasts_judged}</b> forecasts we could check landed inside the window.
          {s.median_warning_weeks != null && <> Median warning before Singapore took off: <b className="num">{s.median_warning_weeks} weeks</b>.</>}
          {s.median_miss_weeks != null && <> Median miss: <b className="num">{s.median_miss_weeks} weeks</b>.</>}
        </p>
        <p className="small muted" style={{ marginTop: 6 }}>
          {Object.entries(s.outcomes).filter(([, n]) => n).map(([k, n]) => `${OUTCOME[k]}: ${n}`).join(' · ')}
        </p>
      </div>
      <div className="block table-wrap">
        <table>
          <thead>
            <tr><th>Food</th><th>Started</th><th>Spotted</th><th>Window then</th><th>Singapore</th><th>Result</th></tr>
          </thead>
          <tbody>
            {backtest.rows.map((r) => (
              <tr key={r.concept_id}>
                <td><a href={`#/c/${r.concept_id}`} onClick={() => onPick(r.flagged_on)}>{r.name}</a></td>
                <td className="num">{r.origin} {fmtMonthYear(r.origin_week)}</td>
                <td className="num">{fmtDate(r.flagged_on)}</td>
                <td className="num">{r.window ? `${fmtDate(r.window.start)} – ${fmtDate(r.window.end)}` : '—'}</td>
                <td className="num">{r.actual_sg_week ? fmtMonthYear(r.actual_sg_week) : '—'}</td>
                <td>{OUTCOME[r.outcome]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="small muted" style={{ marginTop: 12 }}>Clicking a food opens it as of the day it was spotted.</p>
    </div>
  )
}
