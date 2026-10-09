import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api.js'
import { fmtDate } from '../format.js'
import { feedSeen, STAGE_LABEL, useBoard } from '../store.js'

const WEEK_OPTIONS = [4, 8, 26]

function brief(data, board, shopName) {
  const lines = [`Lead Time weekly brief${shopName ? ` for ${shopName}` : ''}, week ending ${fmtDate(data.as_of)}`, '']
  const mine = data.events.filter((e) => board[e.concept_id]?.stage)
  const latest = data.events.filter((e) => e.seen_on === data.as_of)
  if (mine.length) {
    lines.push('On our board:')
    mine.slice(0, 6).forEach((e) => lines.push(`• ${e.text} (${fmtDate(e.seen_on)})`))
    lines.push('')
  }
  lines.push(latest.length ? 'New this week:' : `Nothing new this week. Recent:`)
  ;(latest.length ? latest : data.events.slice(0, 5)).forEach((e) => lines.push(`• ${e.text}`))
  lines.push('', 'Source: Google Trends snapshot, read by Lead Time.')
  return lines.join('\n')
}

export default function ThisWeek({ asOf, profile }) {
  const board = useBoard()
  const [weeks, setWeeks] = useState(8)
  const [onlyMine, setOnlyMine] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)
  const lastSeen = useRef(feedSeen.get())

  useEffect(() => {
    let live = true
    setData(null); setError(null)
    api.changes(asOf, weeks).then((d) => {
      if (!live) return
      setData(d)
      if (!asOf) feedSeen.set(d.as_of)   // only real visits mark the feed as read
    }).catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [asOf, weeks])

  const groups = useMemo(() => {
    if (!data) return []
    const evs = onlyMine ? data.events.filter((e) => board[e.concept_id]?.stage) : data.events
    const byWeek = new Map()
    evs.forEach((e) => { if (!byWeek.has(e.seen_on)) byWeek.set(e.seen_on, []); byWeek.get(e.seen_on).push(e) })
    return [...byWeek.entries()]
  }, [data, onlyMine, board])

  const copy = async () => {
    const text = brief(data, board, profile?.name)
    try { await navigator.clipboard.writeText(text) } catch {
      const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select()
      document.execCommand('copy'); ta.remove()
    }
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  const watchedCount = Object.values(board).filter((e) => e.stage).length
  return (
    <div>
      <h1>This week</h1>
      <p className="muted" style={{ marginTop: 6 }}>
        What moved, checked the way you'd check it every Monday. Takeoffs show up four weeks after they start, once we're sure they're real.
      </p>

      <div className="toolbar">
        <div className="chips" role="group" aria-label="How far back">
          {WEEK_OPTIONS.map((w) => (
            <button key={w} type="button" className="chip" aria-pressed={weeks === w} onClick={() => setWeeks(w)}>
              {w === 26 ? '6 months' : `${w} weeks`}
            </button>
          ))}
        </div>
        <div className="chips">
          <button type="button" className="chip" aria-pressed={onlyMine} onClick={() => setOnlyMine(!onlyMine)} disabled={!watchedCount}>
            Only my foods{watchedCount ? ` (${watchedCount})` : ''}
          </button>
          <button type="button" className="btn" onClick={copy} disabled={!data}>{copied ? 'Copied' : 'Copy brief for staff'}</button>
        </div>
      </div>

      {error && <div className="error" role="alert">{error}</div>}
      {!data && !error && <div className="skeleton" aria-busy="true" />}
      {data && groups.length === 0 && (
        <div className="empty">
          {onlyMine ? 'Nothing changed for the foods on your board in this period. Try a longer range.' : 'Nothing changed in this period. Try a longer range.'}
        </div>
      )}
      {groups.map(([week, evs]) => (
        <section key={week} className="feed-week">
          <h3 className="num">Week ending {fmtDate(week)}</h3>
          <ul className="feed">
            {evs.map((e, i) => {
              const stage = board[e.concept_id]?.stage
              const isNew = !asOf && lastSeen.current && e.seen_on > lastSeen.current
              return (
                <li key={i} className={`feed-item imp-${e.importance}`}>
                  <span className={`dot ${e.kind === 'takeoff' ? (e.geo === 'SG' ? 'sg' : 'abroad') : e.to}`} aria-hidden="true" />
                  <div>
                    <a href={`#/c/${e.concept_id}`}>{e.text}</a>
                    <div className="feed-tags">
                      {isNew && <span className="tag new">New</span>}
                      {stage && <span className="tag mine">{STAGE_LABEL[stage]}</span>}
                    </div>
                  </div>
                </li>
              )
            })}
          </ul>
        </section>
      ))}
      {!watchedCount && data && (
        <p className="muted small" style={{ marginTop: 20 }}>Tip: tap Watch on any food and it gets flagged here when it moves.</p>
      )}
    </div>
  )
}
