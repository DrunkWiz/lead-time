import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtDate, fmtDayMonth } from '../format.js'
import { money } from '../pricing.js'
import { boardStore, costTotal, todayIso, useBoard } from '../store.js'

const W = 380   // narrow viewBox keeps labels readable on a phone
const H = 170
const PAD = { l: 8, r: 8, t: 16, b: 24 }

// Weekly sales the shop logs, against Singapore search interest where our snapshot overlaps.
function SalesChart({ logs, sgWeeks, sgValues }) {
  if (!logs.length) return null
  const first = logs[0].week
  const last = logs[logs.length - 1].week
  const t0 = Date.parse(first) - 3.5 * 864e5
  const t1 = Date.parse(last) + 3.5 * 864e5
  const span = Math.max(t1 - t0, 7 * 864e5)
  const x = (iso) => PAD.l + ((Date.parse(iso) - t0) / span) * (W - PAD.l - PAD.r)
  const maxSold = Math.max(1, ...logs.map((l) => l.sold))
  const barW = Math.max(6, Math.min(40, (W - PAD.l - PAD.r) / (logs.length * 1.6)))
  const y = (v, max) => PAD.t + (1 - v / max) * (H - PAD.t - PAD.b)

  const overlap = (sgWeeks || []).map((w, i) => [w, sgValues[i]]).filter(([w, v]) => v != null && Date.parse(w) >= t0 && Date.parse(w) <= t1)
  const maxSg = Math.max(1, ...overlap.map(([, v]) => v))
  const path = overlap.map(([w, v], i) => `${i ? 'L' : 'M'}${x(w).toFixed(1)},${y(v, maxSg).toFixed(1)}`).join('')

  return (
    <figure style={{ margin: '12px 0 0' }}>
      <svg className="spark" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Weekly sales, ${logs.length} weeks logged`}>
        {logs.map((l) => (
          <g key={l.week}>
            <rect x={x(l.week) - barW / 2} y={y(l.sold, maxSold)} width={barW} height={H - PAD.b - y(l.sold, maxSold)} rx="3" fill="var(--accent)" opacity="0.85" />
            <text x={x(l.week)} y={y(l.sold, maxSold) - 4} fontSize="11" textAnchor="middle" fill="var(--ink)" className="num">{l.sold}</text>
            <text x={x(l.week)} y={H - 6} fontSize="11" textAnchor="middle" fill="var(--muted)" className="num">{fmtDayMonth(l.week)}</text>
          </g>
        ))}
        {overlap.length > 1 && <path d={path} fill="none" stroke="var(--sg)" strokeWidth="2" strokeDasharray="5 3" />}
      </svg>
      <figcaption className="spark-legend">
        <span className="key"><i style={{ background: 'var(--accent)' }} />Sold per week</span>
        {overlap.length > 1
          ? <span className="key"><i className="dash" />Singapore searches</span>
          : <span>Singapore search data stops at our snapshot, so it can't overlap these weeks yet.</span>}
      </figcaption>
    </figure>
  )
}

function Review({ id, asOf, launch, cost }) {
  const [r, setR] = useState(null)
  const logsKey = JSON.stringify(launch.logs)
  useEffect(() => {
    let live = true
    api.review(id, asOf, launch.logs, launch.price, cost).then((d) => live && setR(d)).catch(() => live && setR(null))
    return () => { live = false }
  }, [id, asOf, logsKey, launch.price, cost])   // eslint-disable-line react-hooks/exhaustive-deps
  if (!r) return null
  const rv = r.review
  return (
    <div className={`review v-${rv.verdict}`}>
      <p className="review-label">{rv.label}</p>
      <p>{rv.text}</p>
      {rv.metrics.profit != null && <p className="small muted num">Profit so far: {money(rv.metrics.profit)}</p>}
    </div>
  )
}

export default function Tracker({ id, name, asOf, sgWeeks, sgValues, suggestedPrice }) {
  const board = useBoard()
  const entry = board[id]
  const launch = entry?.launch
  const today = asOf || todayIso()
  const [launchedOn, setLaunchedOn] = useState(today)
  const [price, setPrice] = useState(suggestedPrice ? suggestedPrice.toFixed(2) : '')
  const [week, setWeek] = useState(today)
  const [sold, setSold] = useState('')

  if (!launch) {
    return (
      <section className="block" id="track">
        <h3>Launched it?</h3>
        <p className="small muted">Log it here and track weekly sales. Saved on this device only.</p>
        <form className="inline-form" onSubmit={(e) => {
          e.preventDefault()
          boardStore.setLaunch(id, { launched_on: launchedOn, price: price !== '' ? Number(price) : suggestedPrice ?? null })
        }}>
          <label>Launch date<input type="date" value={launchedOn} onChange={(e) => setLaunchedOn(e.target.value)} required /></label>
          <label>Price ($)<input type="number" inputMode="decimal" min="0" step="0.1" value={price} onChange={(e) => setPrice(e.target.value)} placeholder={suggestedPrice ? suggestedPrice.toFixed(2) : 'e.g. 6.50'} /></label>
          <button className="btn primary" type="submit">I've launched {name}</button>
        </form>
      </section>
    )
  }

  const logs = launch.logs || []
  const total = logs.reduce((s, l) => s + l.sold, 0)
  const best = logs.reduce((b, l) => (l.sold > (b?.sold ?? -1) ? l : b), null)
  return (
    <section className="block" id="track">
      <h3>How it's selling</h3>
      <p className="small">
        Launched {fmtDate(launch.launched_on)}{launch.price ? ` at ${money(launch.price)}` : ''}.
        {logs.length > 0 && <> {total} sold so far{launch.price ? ` (${money(total * launch.price)})` : ''}. Best week: {fmtDayMonth(best.week)}, {best.sold} sold.</>}
      </p>
      <Review id={id} asOf={asOf} launch={launch} cost={costTotal(entry)} />
      <SalesChart logs={logs} sgWeeks={sgWeeks} sgValues={sgValues} />
      <form className="inline-form" onSubmit={(e) => {
        e.preventDefault()
        const n = parseInt(sold, 10)
        if (Number.isFinite(n) && n >= 0) { boardStore.logSales(id, week, n); setSold('') }
      }}>
        <label>Week ending<input type="date" value={week} onChange={(e) => setWeek(e.target.value)} required /></label>
        <label>Sold<input type="number" inputMode="numeric" min="0" step="1" value={sold} onChange={(e) => setSold(e.target.value)} required placeholder="e.g. 40" /></label>
        <button className="btn primary" type="submit">Log week</button>
      </form>
      {logs.length > 0 && (
        <ul className="list-quiet small" style={{ marginTop: 8 }}>
          {[...logs].reverse().map((l) => (
            <li key={l.week}>
              <span className="num">Week ending {fmtDate(l.week)}: <b>{l.sold}</b></span>
              <button type="button" className="btn ghost" onClick={() => boardStore.logSales(id, l.week, null)} aria-label={`Remove week ending ${fmtDate(l.week)}`}>Remove</button>
            </li>
          ))}
        </ul>
      )}
      <button type="button" className="btn ghost" style={{ marginTop: 8 }}
        onClick={() => boardStore.setStage(id, entry.stage === 'launched' ? null : 'launched', today)}>
        {entry.stage === 'launched' ? 'Archive launch' : 'Restore to launched board'}
      </button>
      <p className="small muted">{entry.stage === 'launched' ? 'Archiving removes this food from the board and keeps your sales history.' : 'This launch is archived. Your sales history is preserved.'}</p>
    </section>
  )
}
