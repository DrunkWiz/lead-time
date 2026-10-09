import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtDate } from '../format.js'
import { money, suggestPrice } from '../pricing.js'
import { boardStore, costTotal, useBoard } from '../store.js'

const DEBOUNCE_MS = 350
const DAY_LABEL = (d) => (d === 0 ? 'Launch day' : d < 0 ? `${-d} days before` : `${d} days after`)

function shotListText(name, posts) {
  return [`${name}: content plan`, '']
    .concat(posts.flatMap((p) => [
      `${p.date ? fmtDate(p.date) : DAY_LABEL(p.day)} · ${p.label} (${p.format_name}, ~${p.length_seconds}s)`,
      `  On screen: ${p.on_screen}`,
      ...p.shots.map((s) => `  - ${s.what} (${s.seconds}s)`),
      `  Tip: ${p.tip}`, '',
    ])).join('\n')
}

function OfferRow({ o, chosen, recommended, onPick }) {
  return (
    <li className={`offer ${chosen ? 'chosen' : ''}`}>
      <div className="offer-head">
        <b>{o.title}</b>
        <span className="offer-tags">
          {recommended && <span className="tag mine">Suggested</span>}
          {o.stretch && <span className="tag new">Hard to make back</span>}
        </span>
      </div>
      <p className="small">{o.plain}</p>
      <p className="small muted">{o.why}</p>
      <button type="button" className="chip" aria-pressed={chosen} onClick={onPick}>{chosen ? 'Using this offer' : 'Use this offer'}</button>
    </li>
  )
}

export default function Playbook({ id, name, profile, asOf, hooks, caption }) {
  const board = useBoard()
  const entry = board[id] || {}
  const cost = costTotal(entry)
  const suggested = cost ? suggestPrice(cost, profile.price_band)?.price : null
  const price = parseFloat(entry.inputs?.price) || suggested || null
  const units = parseFloat(entry.inputs?.units) || null
  const [capacity, setCapacity] = useState(entry.inputs?.capacity ?? '')
  const [showAll, setShowAll] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)
  const offerType = entry.inputs?.offer || null

  useEffect(() => {
    let live = true
    const t = setTimeout(() => {
      api.playbook(id, profile, asOf, { price, cost, units_per_week: units, capacity_per_day: parseFloat(capacity) || null }, offerType)
        .then((d) => live && (setData(d), setError(null)))
        .catch((e) => live && setError(e.message))
    }, DEBOUNCE_MS)
    return () => { live = false; clearTimeout(t) }
  }, [id, profile, asOf, price, cost, units, capacity, offerType])

  if (error) return <section className="block"><div className="error">{error}</div></section>
  if (!data) return <section className="block"><div className="skeleton" style={{ height: 160 }} /></section>

  const { offers, content } = data
  const chosen = offers.offers?.find((o) => o.type === offers.chosen)
  const done = entry.posts || {}
  const doneCount = content.posts.filter((p) => done[p.day]).length

  const copy = async () => {
    const text = shotListText(name, content.posts)
    try { await navigator.clipboard.writeText(text) } catch {
      const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select()
      document.execCommand('copy'); ta.remove()
    }
    setCopied(true); setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <section className="block" aria-labelledby="offer-h">
        <h3 id="offer-h">Launch offer</h3>
        {!offers.ready ? (
          <p className="small muted">{offers.message}</p>
        ) : (
          <>
            {chosen && (
              <div className="offer-hero">
                <p className="small muted">{offers.chosen === offers.recommended?.type ? 'Suggested for you' : 'Your pick'}</p>
                <p className="offer-title">{chosen.title}</p>
                <p>{chosen.plain}</p>
                {offers.recommended && offers.chosen === offers.recommended.type && <p className="small muted">{offers.recommended.why}</p>}
              </div>
            )}
            <div className="inline-form">
              <label>Most you can make a day (optional)
                <input type="number" inputMode="numeric" min="1" step="1" value={capacity} placeholder="e.g. 60"
                  onChange={(e) => { setCapacity(e.target.value); boardStore.setInputs(id, { capacity: e.target.value }) }} />
              </label>
            </div>
            <button type="button" className="btn ghost" style={{ marginTop: 8 }} onClick={() => setShowAll(!showAll)}>
              {showAll ? 'Hide other offers' : `Compare all ${offers.offers.length} offers`}
            </button>
            {showAll && (
              <ul className="offers">
                {offers.offers.map((o) => (
                  <OfferRow key={o.type} o={o} chosen={o.type === offers.chosen} recommended={o.type === offers.recommended?.type}
                    onPick={() => boardStore.setInputs(id, { offer: o.type })} />
                ))}
              </ul>
            )}
            {!units && <p className="small muted" style={{ marginTop: 8 }}>Add expected sales per week above to see weekly costs.</p>}
          </>
        )}
      </section>

      <section className="block" aria-labelledby="content-h">
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'baseline', flexWrap: 'wrap' }}>
          <h3 id="content-h">Content plan</h3>
          <span className="small muted num">{doneCount} of {content.posts.length} done</span>
        </div>
        <p className="small">{content.when_text} Best formats for {name}: {content.formats.map((f) => f.name.toLowerCase()).join(' and ')}.</p>
        <ol className="posts">
          {content.posts.map((p) => (
            <li key={p.day} className={done[p.day] ? 'done' : ''}>
              <div className="post-head">
                <label className="post-check">
                  <input type="checkbox" checked={Boolean(done[p.day])} onChange={() => boardStore.togglePost(id, p.day)} />
                  <span>
                    <b>{p.label}</b> · <span className="num">{p.date ? fmtDate(p.date) : DAY_LABEL(p.day)}</span>
                  </span>
                </label>
                <span className="tag">{p.format_name} · ~{p.length_seconds}s</span>
              </div>
              <p className="small muted">{p.goal}</p>
              <p className="on-screen">“{p.on_screen}”</p>
              <ul className="shots">
                {p.shots.map((s, i) => <li key={i}><span className="num muted">{s.seconds}s</span> {s.what}</li>)}
              </ul>
              <p className="small muted">Tip: {p.tip}</p>
            </li>
          ))}
        </ol>
        <button type="button" className="btn" onClick={copy}>{copied ? 'Copied' : 'Copy shot list'}</button>
        {(hooks?.length > 0 || caption) && (
          <div className="decision-part">
            {hooks?.length > 0 && (
              <>
                <h3>More opening lines</h3>
                <ol className="hooks">{hooks.map((h, i) => <li key={i}>{h}</li>)}</ol>
              </>
            )}
            {caption && (
              <>
                <p className="small muted" style={{ marginTop: 12 }}>Caption</p>
                <p className="quote">{caption}</p>
              </>
            )}
          </div>
        )}
      </section>
    </>
  )
}
