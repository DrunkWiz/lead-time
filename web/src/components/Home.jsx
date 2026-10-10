import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { idsAt, useBoard } from '../store.js'
import Card from './Card.jsx'
import HowPanel from './HowPanel.jsx'
import Waiting from './Waiting.jsx'
import Icon from './Icon.jsx'

export default function Home({ profile, asOf, meta }) {
  const [data, setData] = useState(null)
  const [catalog, setCatalog] = useState(null)
  const [error, setError] = useState(null)
  const [attempt, setAttempt] = useState(0)
  const [showMore, setShowMore] = useState(false)
  const board = useBoard()
  useEffect(() => {
    let live = true
    setData(null); setCatalog(null); setError(null); setShowMore(false)
    api.recommend(profile, asOf).then(d => live && setData(d)).catch(e => live && setError(e.message))
    api.concepts(asOf).then(d => live && setCatalog(d)).catch(() => {})
    return () => { live = false }
  }, [profile, asOf, attempt])
  const count = status => catalog ? catalog.concepts.filter(c => c.status === status).length : '—'
  const planned = idsAt(board, 'planned')
  return <div className="dashboard">
    <section className="overview-hero">
      <div><span className="eyebrow">THE OPPORTUNITY IS EARLY</span><h1>Your next bestseller<br/>starts with a <em>signal.</em></h1><p>Discover what’s rising overseas.<br/>Find what fits your kitchen. Get ready to launch.</p><a className="btn primary" href="#/explore">Explore the trend radar <Icon name="arrow" size={18}/></a></div>
      <div className="signal-map" aria-hidden="true"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="orbit orbit-three"/><span className="map-city city-seoul">Seoul <i/></span><span className="map-city city-tokyo">Tokyo <i/></span><span className="map-city city-dubai">Dubai <i/></span><span className="map-city city-taipei">Taipei <i/></span><div className="map-center"><Icon name="radar" size={30}/><b>Singapore</b><span>YOUR NEXT MOVE</span></div><span className="map-caption">Good ideas travel. Be ready.</span></div>
    </section>
    <div className="metric-grid">
      {[['Foods on the radar', catalog?.concepts.length ?? meta?.concept_count ?? '—', 'Across the tracked markets', '#/explore', 'radar'], ['Rising overseas', count('rising_abroad'), 'Watch before the crowd', '#/explore?status=rising_abroad', 'activity'], ['Arriving in Singapore', count('arriving_now'), 'Time to test a small batch', '#/explore?status=arriving_now', 'clock'], ['In your launch plan', planned.length, planned.length ? 'Keep your next launch moving' : 'Save an idea to get started', '#/board', 'board']].map(([label, value, note, href, icon]) => <a className="metric-card" href={href} key={label}><span className="metric-label">{label}<Icon name={icon} size={18}/></span><strong>{value}</strong><span className="metric-note">{note}<span>↗</span></span></a>)}
    </div>
    <div className="section-heading"><div><span className="eyebrow">CURATED FOR YOUR KITCHEN</span><h2>{asOf ? 'Your picks, back then' : 'Worth your first batch'}</h2><p>Matched to {profile.name} · timing, equipment and menu fit.</p></div><a className="text-link" href="#/shop">Edit kitchen <Icon name="arrow" size={16}/></a></div>
    {error && <div className="error" role="alert">{error} <button className="btn" onClick={() => setAttempt(a => a + 1)}>Try again</button></div>}
    {!data && !error && <><Waiting text="Finding opportunities for your kitchen…" slowText="The first kitchen check can take up to a minute. You can explore the trend radar while it finishes."/><div className="cards"><div className="skeleton"/><div className="skeleton"/></div></>}
    {data && <>
      {data.empty && <div className="empty"><h3>No strong matches right now</h3><p>{data.empty}</p><a className="btn primary" href="#/explore">Build your watchlist <Icon name="arrow" size={16}/></a></div>}
      <div className="cards">{data.cards.map((c, i) => <Card key={c.id} card={c} rank={i + 1} asOf={data.as_of}/>)}{data.cards.length === 1 && <aside className="kitchen-brief"><span className="eyebrow">YOUR KITCHEN BRIEF</span><h2>One good idea is<br/>a good place to start.</h2><p>Only one tracked food currently matches your kitchen and timing. Here’s how to turn that signal into a considered decision.</p><ol><li><b>Read the evidence</b><span>Check the overseas signal and Singapore’s response before committing.</span><a href={'#/c/' + data.cards[0].id}>Open the opportunity →</a></li><li><b>Make the numbers work</b><span>Enter ingredient costs to find a price and compare launch offers.</span></li><li><b>Test, then decide</b><span>Plan a small batch, record sales, and follow the keep-or-rethink guidance.</span><a href="#/board">See your launch board →</a></li></ol><div className="kitchen-summary"><span className="eyebrow">MATCHED AGAINST</span><b>{profile.name}</b><p>{profile.equipment.length} pieces of equipment · {profile.menu.length} menu items</p><a href="#/shop">Fine-tune your kitchen profile →</a></div></aside>}</div>
      {data.more.length > 0 && <div className="more-picks"><button className="btn" aria-expanded={showMore} onClick={() => setShowMore(!showMore)}>{showMore ? 'Show fewer ideas' : 'See ' + data.more.length + ' more opportunities'}</button>{showMore && <div className="cards">{data.more.map(c => <Card key={c.id} card={c} asOf={data.as_of}/>)}</div>}</div>}
      <div className="dashboard-bottom">
        <section className="market-panel"><div className="section-heading"><div><span className="eyebrow">THE LOCAL PICTURE</span><h2>Already on the menu</h2></div><a href="#/explore?status=already_here" className="text-link">View radar ↗</a></div><p className="muted small">These have reached Singapore. Check the evidence before joining in.</p><ul className="market-list">{data.already_here.slice(0, 5).map((c, i) => <li key={c.id}><span className="market-number">0{i + 1}</span><a href={'#/c/' + c.id}>{c.name}<small>{c.status === 'peaked_here' ? 'Cooling down · approach carefully' : 'Established locally · check the runway'}</small></a><Icon name="arrow" size={18}/></li>)}</ul>{!data.already_here.length && <p className="muted">No local takeoffs identified at this date.</p>}</section>
        <section className="next-step-panel"><span className="eyebrow">MAKE THE SIGNAL USEFUL</span><h2>Small batch.<br/>Real feedback.<br/>Better decisions.</h2><p>{planned.length ? 'Your plan is taking shape. Review ingredients and equipment before your first batch.' : 'Save a promising food, check the costs, then plan a small launch. Track sales to decide what deserves a permanent spot.'}</p><a className="btn primary" href={planned.length ? '#/board' : '#/explore'}>{planned.length ? 'Open your launch board' : 'Find your first idea'}<Icon name="arrow" size={16}/></a></section>
      </div>
      {data.skipped.length > 0 && <details className="panel"><summary>{data.skipped.length} opportunities need a different kitchen</summary><div><ul className="list-quiet">{data.skipped.map(s => <li key={s.id}><a href={'#/c/' + s.id}>{s.name}</a><span className="muted small">{s.reason}</span></li>)}</ul></div></details>}
    </>}
    <HowPanel meta={meta} historyCases={catalog?.history_cases}/>
  </div>
}
