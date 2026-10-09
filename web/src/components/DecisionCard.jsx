import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtDate } from '../format.js'
import { money, suggestPrice } from '../pricing.js'
import { boardStore, costTotal, useBoard } from '../store.js'

const ICON = { true: '✓', false: '✕', null: '•' }
const DEBOUNCE_MS = 350   // wait for typing to settle before asking the API again

function RunBar({ run }) {
  // Typical run (low..high weeks) on a 0..max axis, with "you are here" if it has started.
  const max = Math.max(run.high * 1.5, (run.elapsed ?? 0) + 2)
  const pct = (x) => `${(100 * x) / max}%`
  return (
    <div className="runbar" aria-hidden="true">
      <div className="runbar-track">
        <div className="runbar-band" style={{ left: pct(run.low), width: pct(run.high - run.low) }} />
        {run.elapsed != null && <div className="runbar-now" style={{ left: pct(Math.min(run.elapsed, max)) }} />}
      </div>
      <div className="runbar-labels num">
        <span>takeoff</span>
        <span style={{ left: pct(run.low) }}>{run.low} wk</span>
        <span style={{ left: pct(run.high) }}>{run.high} wk</span>
      </div>
    </div>
  )
}

export default function DecisionCard({ id, profile, asOf }) {
  const board = useBoard()
  const entry = board[id] || {}
  const cost = costTotal(entry)
  const suggested = cost ? suggestPrice(cost, profile.price_band)?.price : null
  const [price, setPrice] = useState(entry.inputs?.price ?? '')
  const [units, setUnits] = useState(entry.inputs?.units ?? '')
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const effPrice = parseFloat(price) || suggested || null
  useEffect(() => {
    let live = true
    const t = setTimeout(() => {
      api.decision(id, profile, asOf, { price: effPrice, cost, units_per_week: parseFloat(units) || null })
        .then((d) => live && (setData(d), setError(null)))
        .catch((e) => live && setError(e.message))
    }, DEBOUNCE_MS)
    return () => { live = false; clearTimeout(t) }
  }, [id, profile, asOf, effPrice, cost, units])

  const save = (k, v, set) => { set(v); boardStore.setInputs(id, { [k]: v }) }

  if (error) return <section className="block"><div className="error">{error}</div></section>
  if (!data) return <section className="block"><div className="skeleton" style={{ height: 140 }} /></section>
  const d = data.decision
  return (
    <section className={`block decision v-${d.verdict}`} aria-labelledby="decision-h">
      <p className="small muted">Should you do it?</p>
      <h2 id="decision-h" className="decision-verdict">{d.label}</h2>
      <p className="decision-headline">{d.headline}</p>
      <ul className="reasons">
        {d.reasons.map((r, i) => (
          <li key={i} className={`r-${String(r.ok)}`}><span aria-hidden="true">{ICON[String(r.ok)]}</span>{r.text}</li>
        ))}
      </ul>

      {d.run && (
        <div className="decision-part">
          <h3>How long it should last</h3>
          <RunBar run={d.run} />
          <p className="small">
            {d.run.elapsed != null
              ? `Week ${d.run.elapsed} here. Typical runs last ${d.run.low} to ${d.run.high} weeks${d.run.remaining_high ? `, so roughly ${d.run.remaining_low} to ${d.run.remaining_high} weeks left` : ''}.`
              : `Once it lands, expect roughly ${d.run.low} to ${d.run.high} weeks of strong demand.`}
          </p>
          {data.lifespan?.longest?.length > 0 && (
            <p className="small muted">Longest runs here: {data.lifespan.longest.map((l) => `${l.name} (${l.length} wk)`).join(', ')}.</p>
          )}
        </div>
      )}

      <div className="decision-part">
        <h3>Is it worth it for you?</h3>
        <div className="inline-form" style={{ marginTop: 6 }}>
          <label>Your price ($)
            <input type="number" inputMode="decimal" min="0" step="0.1" value={price} placeholder={suggested ? suggested.toFixed(2) : 'e.g. 6.50'}
              onChange={(e) => save('price', e.target.value, setPrice)} />
          </label>
          <label>Expected sold per week
            <input type="number" inputMode="numeric" min="0" step="1" value={units} placeholder="e.g. 40"
              onChange={(e) => save('units', e.target.value, setUnits)} />
          </label>
        </div>
        {cost == null && <p className="small muted" style={{ marginTop: 8 }}>Add your costs in “What to charge” below to see your margin.</p>}
        {d.money && (
          <p style={{ marginTop: 10 }}>
            {money(d.money.margin)} margin each
            {d.money.profit_low != null && (
              <> · <b className="num">{money(d.money.profit_low).replace('.00', '')} to {money(d.money.profit_high).replace('.00', '')}</b> profit over a typical run</>
            )}
          </p>
        )}
        {d.money && d.money.profit_low == null && d.verdict !== 'skip' && (
          <p className="small muted">Add how many you expect to sell each week to see a profit range.</p>
        )}
      </div>

      {d.stock && (
        <div className="decision-part">
          <h3>Stock plan</h3>
          <p>{d.stock.text}</p>
          {d.stock.bulk_until && <p className="small muted">Stop bulk ordering by {fmtDate(d.stock.bulk_until)}.</p>}
        </div>
      )}
      <p className="provider" style={{ marginTop: 12 }}>Verdict worked out by code from the trend data and your numbers. The kitchen check is the only model input.</p>
    </section>
  )
}
