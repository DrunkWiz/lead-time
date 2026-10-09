import { useEffect, useState } from 'react'
import { api } from '../api.js'
import Card from './Card.jsx'
import HowPanel from './HowPanel.jsx'
import TimeBar from './TimeBar.jsx'
import Waiting from './Waiting.jsx'

export default function Home({ profile, asOf, setAsOf, meta, backtest }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [showMore, setShowMore] = useState(false)
  const [history, setHistory] = useState(null)

  useEffect(() => {
    let live = true
    setData(null); setError(null)
    api.recommend(profile, asOf).then((d) => live && setData(d)).catch((e) => live && setError(e.message))
    api.concepts(asOf).then((d) => live && setHistory(d.history_cases)).catch(() => {})
    return () => { live = false }
  }, [profile, asOf])

  return (
    <div>
      <TimeBar meta={meta} asOf={asOf} onChange={setAsOf} backtest={backtest} />

      <h3 style={{ marginBottom: 12 }}>
        {asOf ? 'What we would have told you' : `Try these next${profile.name ? `, ${profile.name}` : ''}`}
      </h3>

      {error && <div className="error" role="alert">{error}</div>}
      {!data && !error && (
        <>
          <Waiting text="Checking which foods your kitchen can make…"
            slowText="The model is checking each food against your kitchen for the first time. This can take up to a minute, then it’s saved." />
          <div className="cards" aria-busy="true"><div className="skeleton" /><div className="skeleton" /></div>
        </>
      )}
      {data && (
        <>
          {data.empty && <div className="empty">{data.empty}</div>}
          <div className="cards">
            {data.cards.map((c, i) => <Card key={c.id} card={c} rank={i + 1} asOf={data.as_of} />)}
          </div>
          {!data.empty && data.cards.length < 3 && !asOf && (
            <p className="note">
              Only {data.cards.length === 1 ? 'one food is' : `${data.cards.length} foods are`} heading this way that fits your kitchen right now.
              Watch more in <a href="#/explore">Explore</a>, or rewind with “Pretend it’s…” to see how the picks looked before past trends.
            </p>
          )}
          {data.more.length > 0 && (
            <div style={{ marginTop: 16 }}>
              {showMore
                ? <div className="cards">{data.more.map((c) => <Card key={c.id} card={c} asOf={data.as_of} />)}</div>
                : <button className="btn" type="button" onClick={() => setShowMore(true)}>{data.more.length} more idea{data.more.length === 1 ? '' : 's'}</button>}
            </div>
          )}

          {data.already_here.length > 0 && (
            <section className="section">
              <h3>Already here</h3>
              <p className="muted small" style={{ marginBottom: 8 }}>You'd be following, not leading, with these.</p>
              <ul className="list-quiet">
                {data.already_here.slice(0, 6).map((c) => (
                  <li key={c.id}>
                    <a href={`#/c/${c.id}`}>{c.name}</a>
                    <span className="muted small">{c.status === 'peaked_here' ? 'Peaked and cooling' : 'Popular now'}</span>
                  </li>
                ))}
              </ul>
              {data.already_here.length > 6 && (
                <a className="btn ghost" href="#/explore">See all {data.already_here.length} in Explore →</a>
              )}
            </section>
          )}

          {data.skipped.length > 0 && (
            <section className="section">
              <h3>Coming, but not for your kitchen</h3>
              <ul className="list-quiet">
                {data.skipped.map((s) => (
                  <li key={s.id}><a href={`#/c/${s.id}`}>{s.name}</a><span className="muted small" style={{ textAlign: 'right' }}>{s.reason}</span></li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}

      <HowPanel meta={meta} historyCases={history} />
    </div>
  )
}
