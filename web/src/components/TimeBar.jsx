import { fmtDate } from '../format.js'

const MAX_PRESETS = 4

export default function TimeBar({ meta, asOf, onChange, backtest }) {
  const on = Boolean(asOf)
  const presets = (backtest?.rows || [])
    .filter((r) => r.window && ['inside', 'early', 'late'].includes(r.outcome))
    .slice(0, MAX_PRESETS)

  return (
    <section className={`timebar ${on ? 'on' : ''}`} aria-label="Backtest: pretend it's an earlier date">
      <div className="timebar-row">
        <label htmlFor="asof" style={{ fontWeight: 600 }}>{on ? 'Pretending it’s' : 'Pretend it’s…'}</label>
        <input
          id="asof" type="date" className="num"
          min={meta?.earliest_as_of || undefined} max={meta?.snapshot_date || undefined}
          value={asOf || ''} onChange={(e) => onChange(e.target.value || null)}
        />
        {on && <button className="btn" type="button" onClick={() => onChange(null)}>Back to today</button>}
      </div>
      <p className="small muted" style={{ marginTop: 8 }}>
        {on
          ? `Lead Time is only looking at data up to ${fmtDate(asOf)}. Open a card and reveal what happened next.`
          : 'Rewind to any date and see what Lead Time would have told you then, using only the data it had.'}
      </p>
      {presets.length > 0 && (
        <div className="chips presets">
          {presets.map((r) => (
            <button key={r.concept_id} type="button" className="chip" aria-pressed={asOf === r.flagged_on}
              onClick={() => onChange(r.flagged_on)}>
              <span className="num">{fmtDate(r.flagged_on)}</span>
              <span className="muted">· just before {r.name}</span>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
