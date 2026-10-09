import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import Status from './Status.jsx'
import StageButtons from './StageButtons.jsx'

const FILTERS = [
  ['all', 'All'], ['arriving_now', 'Arriving now'], ['rising_abroad', 'Coming soon'],
  ['already_here', 'Already here'], ['peaked_here', 'Peaked'], ['not_travelling', 'Not heading here'],
]
const CATEGORIES = [['all', 'Everything'], ['dessert', 'Desserts'], ['bakery', 'Bakes'], ['drink', 'Drinks']]
const ORDER = { arriving_now: 0, rising_abroad: 1, already_here: 2, peaked_here: 3, not_travelling: 4 }

export default function Explore({ asOf }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState('all')
  const [cat, setCat] = useState('all')
  const [q, setQ] = useState('')
  const [life, setLife] = useState(null)

  useEffect(() => {
    let live = true
    setData(null); setError(null)
    api.concepts(asOf).then((d) => live && setData(d)).catch((e) => live && setError(e.message))
    api.lifespan(asOf).then((d) => live && setLife(d)).catch(() => {})
    return () => { live = false }
  }, [asOf])

  const counts = useMemo(() => {
    const c = {}
    data?.concepts.forEach((x) => { c[x.status] = (c[x.status] || 0) + 1 })
    return c
  }, [data])

  const shown = useMemo(() => {
    if (!data) return []
    const needle = q.trim().toLowerCase()
    return data.concepts
      .filter((c) => status === 'all' || c.status === status)
      .filter((c) => cat === 'all' || c.category === cat)
      .filter((c) => !needle || c.name.toLowerCase().includes(needle) || c.description.toLowerCase().includes(needle))
      .sort((a, b) => ORDER[a.status] - ORDER[b.status] || a.name.localeCompare(b.name))
  }, [data, status, cat, q])

  return (
    <div>
      <h1>Explore</h1>
      <p className="muted" style={{ marginTop: 6 }}>Every food we track, where it is now, and whether it's heading for Singapore.</p>
      {life?.typical && (
        <div className="insight">
          <p className="small muted">How long trends last here</p>
          <p>
            Most food trends stay hot in Singapore for <b className="num">{life.typical.low} to {life.typical.high} weeks</b> once they land
            {life.longest?.length > 0 && <>. The long ones: {life.longest.map((l) => `${l.name} (${l.length} wk)`).join(', ')}</>}.
          </p>
          <p className="small muted">From {life.n_cases} past Singapore trends. Each food's page tells you how much of its run is left.</p>
        </div>
      )}
      <div className="toolbar" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
        <label className="sr-only" htmlFor="explore-q">Search foods</label>
        <input id="explore-q" className="text-input" type="search" placeholder="Search, e.g. croissant" value={q} onChange={(e) => setQ(e.target.value)} />
        <div className="chips" role="group" aria-label="Filter by status">
          {FILTERS.map(([v, label]) => (
            <button key={v} type="button" className="chip" aria-pressed={status === v} onClick={() => setStatus(v)}>
              {label}{v !== 'all' && counts[v] ? <span className="muted num"> {counts[v]}</span> : null}
            </button>
          ))}
        </div>
        <div className="chips" role="group" aria-label="Filter by type">
          {CATEGORIES.map(([v, label]) => (
            <button key={v} type="button" className="chip" aria-pressed={cat === v} onClick={() => setCat(v)}>{label}</button>
          ))}
        </div>
      </div>
      {error && <div className="error" role="alert">{error}</div>}
      {!data && !error && <div className="skeleton" aria-busy="true" />}
      {data && shown.length === 0 && <div className="empty">No foods match. Clear a filter to see more.</div>}
      <ul className="explore-list">
        {shown.map((c) => (
          <li key={c.id} className="explore-row">
            <a href={`#/c/${c.id}`} className="explore-main">
              <span className="explore-name">{c.name}</span>
              <Status status={c.status} label={c.status_label} />
              <span className="muted small">{c.why}</span>
            </a>
            <StageButtons id={c.id} compact asOf={asOf} />
          </li>
        ))}
      </ul>
    </div>
  )
}
