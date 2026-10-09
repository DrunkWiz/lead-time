import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import { fmtDate } from './format.js'
import BacktestPage from './components/BacktestPage.jsx'
import Board from './components/Board.jsx'
import Explore from './components/Explore.jsx'
import ThisWeek from './components/ThisWeek.jsx'
import Detail from './components/Detail.jsx'
import Home from './components/Home.jsx'
import Onboarding from './components/Onboarding.jsx'
import { feedSeen, onBoardCount, useBoard } from './store.js'

const PROFILE_KEY = 'leadtime.profile'

function loadProfile() {
  try { return JSON.parse(localStorage.getItem(PROFILE_KEY)) } catch { return null }
}
function saveProfile(p) {
  try { localStorage.setItem(PROFILE_KEY, JSON.stringify(p)) } catch { /* private mode: keep in memory */ }
}

function useHash() {
  const [hash, setHash] = useState(window.location.hash)
  useEffect(() => {
    const on = () => setHash(window.location.hash)
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return hash
}

export default function App() {
  const [profile, setProfile] = useState(loadProfile)
  const [asOf, setAsOf] = useState(null)
  const [meta, setMeta] = useState(null)
  const [metaError, setMetaError] = useState(null)
  const [backtest, setBacktest] = useState(null)
  const hash = useHash()
  const board = useBoard()
  const boardCount = onBoardCount(board)

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setMetaError(e.message))
    api.backtest().then(setBacktest).catch(() => {})
  }, [])

  const route = useMemo(() => {
    const m = hash.match(/^#\/c\/([\w-]+)/)
    if (m) return { name: 'detail', id: m[1] }
    if (hash.startsWith('#/backtest')) return { name: 'backtest' }
    if (hash.startsWith('#/shop')) return { name: 'shop' }
    if (hash.startsWith('#/week')) return { name: 'week' }
    if (hash.startsWith('#/explore')) return { name: 'explore' }
    if (hash.startsWith('#/board')) return { name: 'board' }
    return { name: 'home' }
  }, [hash])

  const done = useCallback((p) => {
    setProfile(p); saveProfile(p); window.location.hash = '#/'
  }, [])

  let body
  if (!profile || route.name === 'shop') {
    body = <Onboarding initial={profile} onDone={done} onCancel={profile ? () => { window.location.hash = '#/' } : null} />
  } else if (route.name === 'detail') {
    body = <Detail id={route.id} profile={profile} asOf={asOf} />
  } else if (route.name === 'week') {
    body = <ThisWeek asOf={asOf} profile={profile} />
  } else if (route.name === 'explore') {
    body = <Explore asOf={asOf} />
  } else if (route.name === 'board') {
    body = <Board profile={profile} asOf={asOf} />
  } else if (route.name === 'backtest') {
    body = <BacktestPage backtest={backtest} onPick={setAsOf} />
  } else {
    body = <Home profile={profile} asOf={asOf} setAsOf={setAsOf} meta={meta} backtest={backtest} />
  }

  return (
    <div className="wrap">
      <header className="top">
        <a className="brand" href="#/" aria-label="Lead Time home">
          <svg className="brand-mark" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="var(--accent)" />
            <path d="M7 21 L13 15 L17 18 L25 10" stroke="var(--bg)" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx="25" cy="10" r="2.5" fill="var(--soon-line)" />
          </svg>
          <span className="brand-name" style={{ color: 'var(--ink)' }}>Lead Time</span>
        </a>
        {profile && route.name !== 'shop' && (
          <a className="btn" href="#/shop">{profile.name && profile.name.length < 22 ? profile.name : 'Your shop'} · edit</a>
        )}
      </header>
      {profile && route.name !== 'shop' && (
        <nav className="tabs" aria-label="Sections">
          {[
            ['home', '#/', 'Picks'],
            ['week', '#/week', 'This week'],
            ['explore', '#/explore', 'Explore'],
            ['board', '#/board', 'My board'],
          ].map(([name, href, label]) => {
            const current = route.name === name || (name === 'home' && route.name === 'detail')
            const unread = name === 'week' && meta && !asOf && (feedSeen.get() || '') < meta.snapshot_date
            return (
              <a key={name} href={href} className="tab" aria-current={current ? 'page' : undefined}>
                {label}
                {unread && route.name !== 'week' && <span className="badge-dot" aria-label="new" />}
                {name === 'board' && boardCount > 0 && <span className="badge num">{boardCount}</span>}
              </a>
            )
          })}
        </nav>
      )}
      <div className="asof">
        {metaError
          ? <span role="alert">{metaError}</span>
          : <span>Trend data as of <b className="num">{meta ? fmtDate(meta.snapshot_date) : '…'}</b></span>}
        {asOf && <span style={{ color: 'var(--soon)', fontWeight: 600 }}>Backtest mode: pretending it's {fmtDate(asOf)}</span>}
      </div>
      <main>{body}</main>
      <footer className="footer">
        Lead Time reads Google Trends snapshots; it never scrapes TikTok or Instagram. Search interest is a signal, not a promise.
        Built for ForgeHacks 2026.
      </footer>
    </div>
  )
}
