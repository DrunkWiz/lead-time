import { useEffect, useMemo, useState } from 'react'
import { api } from '../api.js'
import { fmtDate } from '../format.js'
import { useBoard } from '../store.js'
import Status from './Status.jsx'
import StageButtons from './StageButtons.jsx'
import FoodArt from './FoodArt.jsx'
import Icon from './Icon.jsx'

const FILTERS = [['all', 'All signals'], ['arriving_now', 'Arriving now'], ['rising_abroad', 'Rising overseas'], ['already_here', 'Already here'], ['peaked_here', 'Cooling down'], ['not_travelling', 'No travel signal']]
const ORDER = { arriving_now: 0, rising_abroad: 1, already_here: 2, peaked_here: 3, not_travelling: 4 }
export default function Explore({ asOf }) {
  const params = new URLSearchParams(window.location.hash.split('?')[1] || '')
  const [status, setStatus] = useState(FILTERS.some(([v]) => v === params.get('status')) ? params.get('status') : 'all')
  const [cat, setCat] = useState('all')
  const [q, setQ] = useState('')
  const [sort, setSort] = useState('signal')
  const [saved, setSaved] = useState(false)
  const [selected, setSelected] = useState([])
  const [comparing, setComparing] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [attempt, setAttempt] = useState(0)
  const board = useBoard()
  useEffect(() => {
    let live = true
    setData(null); setError(null)
    api.concepts(asOf).then(d => live && setData(d)).catch(e => live && setError(e.message))
    return () => { live = false }
  }, [asOf, attempt])
  const shown = useMemo(() => (data?.concepts || [])
    .filter(c => (status === 'all' || c.status === status) && (cat === 'all' || c.category === cat) && (!saved || board[c.id]?.stage))
    .filter(c => [c.name, c.description, c.origin_name].join(' ').toLowerCase().includes(q.trim().toLowerCase()))
    .sort((a, b) => sort === 'name' ? a.name.localeCompare(b.name) : (ORDER[a.status] - ORDER[b.status] || a.name.localeCompare(b.name))), [data, status, cat, saved, board, q, sort])
  const chosen = selected.map(id => data?.concepts.find(c => c.id === id)).filter(Boolean)
  const clearFilters = () => { setStatus('all'); setCat('all'); setQ(''); setSaved(false); setSort('signal') }
  const toggle = id => setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 3 ? [...prev, id] : prev)
  return <div>
    <div className="section-heading page-heading"><div><span className="eyebrow">LOOK BEYOND YOUR MENU</span><h1>The trend radar</h1><p>Follow the signals. Compare the possibilities. Find your next move.</p></div><span className="catalog-count">{data?.concepts.length ?? '—'} foods tracked</span></div>
    <div className="radar-toolbar">
      <div className="search-field"><Icon name="search"/><label className="sr-only" htmlFor="explore-q">Search foods or origins</label><input id="explore-q" type="search" placeholder="Search a food, ingredient or origin…" value={q} onChange={e => setQ(e.target.value)}/></div>
      <div className="filter-selects"><label>Category<select value={cat} onChange={e => setCat(e.target.value)}><option value="all">All categories</option><option value="dessert">Desserts</option><option value="bakery">Bakery</option><option value="drink">Drinks</option></select></label><label>Sort by<select value={sort} onChange={e => setSort(e.target.value)}><option value="signal">Opportunity first</option><option value="name">Name A–Z</option></select></label></div>
    </div>
    <div className="signal-filters" role="group" aria-label="Filter by trend status">{FILTERS.map(([v, label]) => <button key={v} className="chip" aria-pressed={status === v} onClick={() => setStatus(v)}>{label}<span>{data ? data.concepts.filter(c => v === 'all' || c.status === v).length : '—'}</span></button>)}</div>
    <div className="results-bar"><span role="status">{data ? shown.length + ' matching foods' : 'Reading the signals…'}</span><label><input type="checkbox" checked={saved} onChange={e => setSaved(e.target.checked)}/> On my board only</label><button className="text-button" onClick={clearFilters}>Reset filters</button></div>
    {error && <div className="error" role="alert">{error} <button className="btn" onClick={() => setAttempt(x => x + 1)}>Try again</button></div>}
    {!data && !error && <div className="radar-grid" aria-busy="true"><div className="skeleton"/><div className="skeleton"/><div className="skeleton"/></div>}
    {data && !shown.length && <div className="empty"><Icon name="search" size={32}/><h3>No signals match those filters</h3><p>Try another food or include a few more categories.</p><button className="btn" onClick={clearFilters}>Clear filters</button></div>}
    {comparing && chosen.length > 0 && <section className="comparison-panel" aria-label="Food comparison"><div className="section-heading"><h2>Find the better fit</h2><button className="btn" onClick={() => setComparing(false)}>Close comparison</button></div><div className="table-scroll"><table className="comparison-table"><caption>Evidence at the selected snapshot. Arrival windows are estimates, not promises.</caption><thead><tr><th scope="col">Signal</th>{chosen.map(c => <th key={c.id} scope="col"><a href={'#/c/' + c.id}>{c.name}</a></th>)}</tr></thead><tbody>{[['Status', c => c.status_label], ['Category', c => c.category], ['First takeoff', c => c.origin_name || 'Not identified'], ['Arrival window', c => c.window ? fmtDate(c.window.start) + ' – ' + fmtDate(c.window.end) : 'Not enough evidence for a window'], ['Why it matters', c => c.why], ['Next step', c => <StageButtons id={c.id} asOf={asOf}/>]].map(([label, value]) => <tr key={label}><th scope="row">{label}</th>{chosen.map(c => <td key={c.id}>{value(c)}</td>)}</tr>)}</tbody></table></div></section>}
    <div className="radar-grid">{shown.map(c => <article className={'radar-card' + (selected.includes(c.id) ? ' is-selected' : '')} key={c.id}><a className="radar-art-link" href={'#/c/' + c.id} tabIndex={-1} aria-hidden="true"><FoodArt id={c.id} category={c.category}/></a><div className="radar-card-body"><div className="radar-card-meta"><span>{c.category}</span><label className="compare-check"><input type="checkbox" aria-label={'Compare ' + c.name} checked={selected.includes(c.id)} disabled={selected.length >= 3 && !selected.includes(c.id)} onChange={() => toggle(c.id)}/> Compare</label></div><a className="radar-title" href={'#/c/' + c.id}><h2>{c.name}</h2><Icon name="arrow" size={18}/></a><Status status={c.status} label={c.status_label}/><p>{c.why}</p><div className="origin-label"><Icon name="activity" size={15}/>{c.origin_name ? 'First takeoff · ' + c.origin_name : 'No overseas takeoff identified'}</div><StageButtons id={c.id} compact asOf={asOf}/></div></article>)}</div>
    {selected.length > 0 && <div className="compare-tray"><span><b>{selected.length} of 3 selected</b><small>{chosen.map(c => c.name).join(' · ')}</small></span><button className="text-button" onClick={() => { setSelected([]); setComparing(false) }}>Clear</button><button className="btn primary" disabled={selected.length < 2} onClick={() => { setComparing(true); requestAnimationFrame(() => document.querySelector('.comparison-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })) }}>Compare signals <Icon name="arrow" size={16}/></button></div>}
  </div>
}
