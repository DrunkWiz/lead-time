import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import { fmtDate, fmtDayMonth } from '../format.js'
import { money } from '../pricing.js'
import { boardStore, costTotal, idsAt, todayIso, useBoard } from '../store.js'
import Status from './Status.jsx'

function salesSummary(launch) {
  const logs = launch?.logs || []
  const total = logs.reduce((s, l) => s + l.sold, 0)
  const last = logs[logs.length - 1]
  const prev = logs[logs.length - 2]
  let trend = null
  if (last && prev) trend = last.sold > prev.sold ? 'up' : last.sold < prev.sold ? 'down' : 'flat'
  return { total, last, trend, weeks: logs.length, revenue: launch?.price ? total * launch.price : null }
}

function exportCsv(board, names) {
  const rows = [['food', 'launched_on', 'price', 'week', 'sold']]
  Object.entries(board).forEach(([id, b]) => {
    (b.launch?.logs || []).forEach((l) => rows.push([names[id] || id, b.launch.launched_on, b.launch.price ?? '', l.week, l.sold]))
  })
  const csv = rows.map((r) => r.map((x) => `"${String(x).replace(/"/g, '""')}"`).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
  const a = document.createElement('a')
  a.href = url; a.download = 'lead-time-sales.csv'; a.click()
  URL.revokeObjectURL(url)
}

function ReviewBadge({ id, asOf, entry }) {
  const [r, setR] = useState(null)
  const logsKey = JSON.stringify(entry.launch?.logs || [])
  useEffect(() => {
    let live = true
    api.review(id, asOf, entry.launch?.logs || [], entry.launch?.price, costTotal(entry))
      .then((d) => live && setR(d.review)).catch(() => {})
    return () => { live = false }
  }, [id, asOf, logsKey])   // eslint-disable-line react-hooks/exhaustive-deps
  if (!r) return null
  return (
    <div className={`review compact v-${r.verdict}`}>
      <span className="review-label">{r.label}</span> <span className="small">{r.text}</span>
    </div>
  )
}

export default function Board({ profile, asOf }) {
  const board = useBoard()
  const watching = idsAt(board, 'watching')
  const planned = idsAt(board, 'planned')
  const launched = idsAt(board, 'launched')
  const [concepts, setConcepts] = useState(null)
  const [plan, setPlan] = useState(null)
  const [error, setError] = useState(null)
  const plannedKey = [...planned].sort().join(',')

  useEffect(() => {
    let live = true
    api.concepts(asOf).then((d) => live && setConcepts(d.concepts)).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [asOf])

  useEffect(() => {
    let live = true
    setPlan(null)
    if (!plannedKey) return undefined
    api.plan(plannedKey.split(','), profile, asOf).then((d) => live && setPlan(d)).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [plannedKey, profile, asOf])

  const byId = useMemo(() => Object.fromEntries((concepts || []).map((c) => [c.id, c])), [concepts])
  const names = Object.fromEntries((concepts || []).map((c) => [c.id, c.name]))
  const empty = !watching.length && !planned.length && !launched.length

  return (
    <div>
      <h1>My board</h1>
      <p className="muted" style={{ marginTop: 6 }}>Watch foods, plan the ones you'll make, then track how they sell. Saved on this device.</p>
      {error && <div className="error" role="alert" style={{ marginTop: 16 }}>{error}</div>}

      {empty && (
        <div className="empty" style={{ marginTop: 20 }}>
          Nothing here yet. Open <a href="#/">your picks</a> or <a href="#/explore">explore every food</a> and tap Watch or Add to plan.
        </div>
      )}

      {planned.length > 0 && (
        <section className="section">
          <h2>Planned</h2>
          {!plan && <div className="skeleton" style={{ height: 120, marginTop: 12 }} />}
          {plan && (
            <>
              <ol className="timeline">
                {plan.items.map((it) => (
                  <li key={it.id}>
                    <div className="tl-date num">{it.launch.date ? fmtDayMonth(it.launch.date) : '—'}</div>
                    <div className="tl-body">
                      <a href={`#/c/${it.id}`} className="tl-name">{it.name}</a>
                      <Status status={it.status} label={it.status_label} />
                      <p className="small" style={{ marginTop: 4 }}>{it.launch.text}</p>
                      {it.fit?.verdict === 'adapt' && <p className="small muted">Your version: {it.fit.adaptation}</p>}
                      {it.fit?.verdict === 'skip' && <p className="small" style={{ color: 'var(--now)' }}>Kitchen check says skip: {it.fit.reason}</p>}
                    </div>
                  </li>
                ))}
              </ol>
              <div className="grid2" style={{ marginTop: 16 }}>
                <div className="block" style={{ marginTop: 0 }}>
                  <h3>Shopping list</h3>
                  <ul className="list-quiet small">
                    {plan.shopping.map((s) => (
                      <li key={s.ingredient}><span>{s.ingredient}</span><span className="muted" style={{ textAlign: 'right' }}>{s.for.join(', ')}</span></li>
                    ))}
                  </ul>
                </div>
                <div className="block" style={{ marginTop: 0 }}>
                  <h3>Kit you're missing</h3>
                  {plan.missing_equipment.length === 0
                    ? <p className="small muted">Nothing. Your kitchen covers everything planned.</p>
                    : (
                      <ul className="list-quiet small">
                        {plan.missing_equipment.map((m) => (
                          <li key={m.equipment}><span>{m.equipment}</span><span className="muted" style={{ textAlign: 'right' }}>{m.for.join(', ')}</span></li>
                        ))}
                      </ul>
                    )}
                  <p className="small muted" style={{ marginTop: 8 }}>The plan for each food has swaps if you'd rather not buy.</p>
                </div>
              </div>
            </>
          )}
        </section>
      )}

      {launched.length > 0 && (
        <section className="section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <h2>Launched</h2>
            <button type="button" className="btn" onClick={() => exportCsv(board, names)}>Export sales (CSV)</button>
          </div>
          {(() => {
            let revenue = 0, profit = 0, profitKnown = true, sold = 0
            launched.forEach((id) => {
              const b = board[id], s = salesSummary(b.launch), c = costTotal(b)
              sold += s.total
              revenue += s.revenue || 0
              if (b.launch?.price && c != null) profit += s.total * (b.launch.price - c)
              else profitKnown = false
            })
            return sold > 0 && (
              <div className="stat-row">
                <div className="stat"><span className="stat-n num">{sold}</span><span className="stat-l">sold</span></div>
                <div className="stat"><span className="stat-n num">{money(revenue).replace('.00', '')}</span><span className="stat-l">revenue</span></div>
                <div className="stat"><span className="stat-n num">{profitKnown ? money(profit).replace('.00', '') : '—'}</span>
                  <span className="stat-l">{profitKnown ? 'profit' : 'profit (add costs)'}</span></div>
              </div>
            )
          })()}
          <ul className="list-quiet" style={{ marginTop: 8 }}>
            {launched.map((id) => {
              const b = board[id]
              const s = salesSummary(b.launch)
              return (
                <li key={id} style={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <a href={`#/c/${id}#track`}><b>{names[id] || id}</b></a>
                    <span className="muted small num">since {fmtDate(b.launch?.launched_on)}</span>
                  </div>
                  <span className="small num">
                    {s.weeks === 0 ? 'No sales logged yet. Log your first week.' : (
                      <>
                        {s.total} sold over {s.weeks} week{s.weeks === 1 ? '' : 's'}
                        {s.revenue != null && ` · ${money(s.revenue)} revenue`}
                        {s.trend && ` · last week ${s.trend === 'up' ? 'up ▲' : s.trend === 'down' ? 'down ▼' : 'flat'}`}
                      </>
                    )}
                  </span>
                  <ReviewBadge id={id} asOf={asOf} entry={b} />
                </li>
              )
            })}
          </ul>
        </section>
      )}

      {watching.length > 0 && (
        <section className="section">
          <h2>Watching</h2>
          <p className="muted small" style={{ marginTop: 4 }}>Changes to these are flagged in <a href="#/week">This week</a>.</p>
          <ul className="list-quiet" style={{ marginTop: 8 }}>
            {watching.map((id) => {
              const c = byId[id]
              return (
                <li key={id} style={{ alignItems: 'center' }}>
                  <a href={`#/c/${id}`} style={{ display: 'grid', gap: 2 }}>
                    <b>{c?.name || id}</b>
                    {c && <span className="small muted">{c.why}</span>}
                  </a>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                    {c && <Status status={c.status} label={c.status_label} />}
                    <button type="button" className="btn ghost" onClick={() => boardStore.setStage(id, 'planned', asOf || todayIso())} aria-label={`Plan ${c?.name || id}`}>Plan →</button>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      )}
    </div>
  )
}
