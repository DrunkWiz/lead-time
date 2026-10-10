import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import { fmtDate } from './format.js'
import BacktestPage from './components/BacktestPage.jsx'
import Board from './components/Board.jsx'
import Explore from './components/Explore.jsx'
import ThisWeek from './components/ThisWeek.jsx'
import Detail from './components/Detail.jsx'
import Home from './components/Home.jsx'
import Onboarding from './components/Onboarding.jsx'
import Icon from './components/Icon.jsx'
import TimeBar from './components/TimeBar.jsx'
import DEMOS from './demoProfiles.json'
import { onBoardCount, useBoard } from './store.js'

const PROFILE_KEY = 'leadtime.profile'
function loadProfile() {
  try {
    const p = JSON.parse(localStorage.getItem(PROFILE_KEY))
    return p && Array.isArray(p.sells) && Array.isArray(p.equipment) && Array.isArray(p.menu) && typeof p.name === 'string' && ['budget', 'mid', 'premium'].includes(p.price_band) ? p : null
  } catch { return null }
}
const NAV = [['home', '#/', 'Overview', 'grid'], ['explore', '#/explore', 'Trend radar', 'radar'], ['week', '#/week', 'Weekly briefing', 'activity'], ['board', '#/board', 'Launch board', 'board']]

export default function App() {
  const [profile, setProfile] = useState(loadProfile)
  const [asOf, setAsOf] = useState(null)
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState(null)
  const [backtest, setBacktest] = useState(null)
  const [backtestError, setBacktestError] = useState(null)
  const [backtestAttempt, setBacktestAttempt] = useState(0)
  const [historyOpen, setHistoryOpen] = useState(false)
  const [hash, setHash] = useState(window.location.hash)
  const [theme, setTheme] = useState(() => { try { return localStorage.getItem('leadtime.theme') || 'light' } catch { return 'light' } })
  const board = useBoard()
  const activeProfile = profile || DEMOS[0].profile
  const match = hash.match(/^#\/c\/([\w-]+)/)
  const name = match ? 'detail' : hash.match(/^#\/(explore|week|board|shop|backtest)/)?.[1] || 'home'
  const loadMeta = useCallback(() => {
    setMetaError(null)
    api.meta().then(setMeta).catch(e => setMetaError(e.message))
  }, [])
  useEffect(() => { loadMeta() }, [loadMeta])
  useEffect(() => {
    if (historyOpen || name === 'backtest') {
      setBacktestError(null)
      api.backtest().then(setBacktest).catch(e => setBacktestError(e.message))
    }
  }, [historyOpen, name, backtestAttempt])
  useEffect(() => {
    const on = () => { setHash(window.location.hash); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('leadtime.theme', theme) } catch { /* memory only */ }
  }, [theme])
  const done = useCallback(p => {
    setProfile(p)
    try { localStorage.setItem(PROFILE_KEY, JSON.stringify(p)) } catch { /* memory only */ }
    window.location.hash = '#/'
  }, [])
  let body
  if (name === 'shop') body = <Onboarding initial={profile} onDone={done} onCancel={() => { window.location.hash = '#/' }} />
  else if (name === 'detail') body = <Detail key={match[1]} id={match[1]} profile={activeProfile} asOf={asOf} />
  else if (name === 'explore') body = <Explore key={hash} asOf={asOf} />
  else if (name === 'week') body = <ThisWeek asOf={asOf} profile={activeProfile} />
  else if (name === 'board') body = <Board profile={activeProfile} asOf={asOf} />
  else if (name === 'backtest') body = backtestError ? <div className="error" role="alert">{backtestError}<button className="btn" onClick={() => setBacktestAttempt(a => a + 1)}>Retry report</button></div> : <BacktestPage backtest={backtest} onPick={setAsOf} />
  else body = <Home profile={activeProfile} asOf={asOf} meta={meta} />
  return <div className="app-shell">
    <a className="skip-link" href="#main-content" onClick={e => { e.preventDefault(); document.getElementById('main-content').focus() }}>Skip to content</a>
    <aside className="sidebar">
      <a className="brand" href="#/" aria-label="Lead Time home"><span className="brand-symbol"><Icon name="activity" size={26}/></span><span>lead time<span className="brand-dot">.</span></span></a>
      <p className="nav-caption">YOUR NEXT MENU MOVE</p>
      <nav className="side-nav" aria-label="Main navigation">{NAV.map(([key, href, label, icon]) => <a key={key} href={href} aria-current={name === key || (key === 'home' && name === 'detail') ? 'page' : undefined}><Icon name={icon}/><span>{label}</span>{key === 'board' && onBoardCount(board) > 0 && <span className="badge">{onBoardCount(board)}</span>}</a>)}</nav>
      <div className="sidebar-insight"><span className="eyebrow">FROM SIGNAL TO SPECIAL</span><p>A little earlier.<br/>A better menu.</p><span>Spot the trend. Test a batch.<br/>Make it your own.</span><a href="#/explore">Find an opportunity <Icon name="arrow" size={16}/></a></div>
      <div className="sidebar-bottom"><a href="#/backtest"><Icon name="clock"/> How reliable is this?</a><a href="#/shop" aria-label="Edit kitchen profile"><Icon name="shop"/><span>{profile?.name || 'Set up your kitchen'}<small>{profile ? 'Edit kitchen profile' : 'Get picks that fit your shop'}</small></span></a><button className="theme-toggle" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}><Icon name="sun"/>{theme === 'dark' ? 'Light appearance' : 'Dark appearance'}</button></div>
    </aside>
    <div className="workspace">
      <header className="workspace-header"><div><span className="header-location">Singapore</span><span className="header-divider">/</span><span>{NAV.find(n => n[0] === name)?.[2] || (name === 'shop' ? 'Your kitchen' : name === 'detail' ? 'Opportunity details' : 'Forecast accuracy')}</span></div><button className="btn history-button" aria-expanded={historyOpen} onClick={() => setHistoryOpen(!historyOpen)}><Icon name="clock" size={16}/>{asOf ? fmtDate(asOf) : 'Explore history'}</button></header>
      <div className="workspace-body">
        <div className="data-status"><span><i/>{meta ? 'Snapshot · ' + fmtDate(meta.snapshot_date) : 'Connecting to trend data…'}</span><span>Google Trends · {meta?.regions?.length || '—'} markets</span></div>
        {metaError && <div className="error" role="alert">{metaError} <button className="btn" onClick={loadMeta}>Retry connection</button></div>}
        {historyOpen && <TimeBar meta={meta} asOf={asOf} onChange={setAsOf} backtest={backtest}/>}
        {asOf && <div className="history-notice" role="status">Viewing evidence available on {fmtDate(asOf)}. <button onClick={() => setAsOf(null)}>Return to latest snapshot ×</button></div>}
        {!profile && name !== 'shop' && <div className="demo-notice"><span><b>Take a look around.</b> Kitchen fit and plans use our example dessert café.</span><a href="#/shop">Personalise my picks <Icon name="arrow" size={16}/></a></div>}
        <main id="main-content" tabIndex={-1}>{body}</main>
        <footer className="footer"><span>Made for independent kitchens in Singapore.</span><span>Search interest is a signal, not a sales forecast. Your board stays on this device.</span></footer>
      </div>
    </div>
  </div>
}
