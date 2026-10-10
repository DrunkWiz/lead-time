import { boardStore, idsAt, todayIso } from '../store.js'
import StageButtons from './StageButtons.jsx'
import Status from './Status.jsx'
import { useRef, useState } from 'react'
import { parseBoardBackup } from '../backup.js'

function downloadBackup(board, profile) {
  const blob = new Blob([JSON.stringify({ format: 'lead-time-backup', version: 1, exported_at: new Date().toISOString(), profile, board }, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'lead-time-backup-' + todayIso() + '.json'; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
const STAGES = [['watching', '01', 'Watching', 'Keep interesting foods here while you follow the signals.'], ['planned', '02', 'Planning', 'Move a food into your plan to build a launch timeline and shopping list.'], ['launched', '03', 'Launched', 'Open a food and record its launch date to start tracking real sales.']]
export default function BoardPipeline({ board, concepts, asOf, profile }) {
  const fileInput = useRef(null)
  const [notice, setNotice] = useState('')
  const [restoreError, setRestoreError] = useState('')
  const restore = async event => {
    const file = event.target.files?.[0]
    if (!file) return
    setRestoreError(''); setNotice('')
    try {
      if (file.size > 2 * 1024 * 1024) throw new Error('Choose a backup smaller than 2 MB.')
      const imported = parseBoardBackup(await file.text())
      const count = boardStore.restoreMissing(imported)
      setNotice(count + ' foods restored. Existing foods and their saved numbers were kept unchanged.')
    } catch (e) { setRestoreError(e.message) }
    event.target.value = ''
  }
  const byId = Object.fromEntries((concepts || []).map(c => [c.id, c]))
  return <>
    <div className="board-actions"><a className="btn primary" href="#/explore">+ Find an opportunity</a><button className="btn" onClick={() => downloadBackup(board, profile)}>Download board backup</button><button className="btn" onClick={() => fileInput.current.click()}>Restore missing foods</button><input ref={fileInput} className="sr-only" type="file" accept=".json,application/json" aria-label="Import board backup" onChange={restore}/><span className="small muted">Restore adds missing foods; existing entries and your kitchen profile stay unchanged.</span></div>
    {notice && <p className="insight small" role="status">{notice}</p>}
    {restoreError && <p className="error" role="alert">{restoreError}</p>}
    <div className="pipeline">{STAGES.map(([stage, n, label, hint]) => <section key={stage} className="pipeline-column" aria-label={label}><div className="pipeline-title"><h2>{n} · {label}</h2><span>{idsAt(board, stage).length}{stage === 'planned' ? ' / 12' : ''}</span></div>{!idsAt(board, stage).length && <p className="pipeline-empty">{hint}</p>}{idsAt(board, stage).map(id => {
      const c = byId[id], entry = board[id]
      return <article key={id} className="pipeline-item"><a href={'#/c/' + id}>{c?.name || id}</a>{c && <Status status={c.status} label={c.status_label}/>}<p>{stage === 'launched' ? (entry.launch?.logs?.length || 0) + ' weeks of sales logged' : c?.why || 'Loading the latest signal…'}</p><StageButtons id={id} compact asOf={asOf}/>{stage === 'planned' && <a className="text-link" style={{ marginTop: 14 }} href={'#/c/' + id + '#track'}>Ready? Record your launch →</a>}<button className="text-button" onClick={() => boardStore.setStage(id, null, asOf || todayIso())}>Remove from board</button></article>
    })}</section>)}</div>
  </>
}
