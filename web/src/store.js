// The shop's board: which foods it is watching, planning or has launched, plus
// weekly sales it logs. Lives in this browser only (no accounts, by design).
import { useSyncExternalStore } from 'react'

const KEY = 'leadtime.board'
const SEEN_KEY = 'leadtime.feedSeen'
export const STAGES = ['watching', 'planned', 'launched']
export const STAGE_LABEL = { watching: 'Watching', planned: 'Planned', launched: 'Launched' }

function read(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
function write(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* private mode: memory only */ }
}

function validBoard(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}
  return Object.fromEntries(Object.entries(value).filter(([id, entry]) =>
    /^[a-z0-9-]+$/.test(id) && entry && typeof entry === 'object' && !Array.isArray(entry)
    && (!entry.stage || STAGES.includes(entry.stage))))
}
let board = validBoard(read(KEY, {}))
const listeners = new Set()
function emit() { write(KEY, board); listeners.forEach((l) => l()) }

export const boardStore = {
  subscribe(l) { listeners.add(l); return () => listeners.delete(l) },
  get() { return board },
  restoreMissing(imported) {
    const additions = Object.fromEntries(Object.entries(imported).filter(([id]) => !Object.hasOwn(board, id)))
    const next = { ...board, ...additions }
    if (idsAt(next, 'planned').length > 12) throw new Error('This would exceed the 12-food plan limit. Make room in your plan first.')
    board = next
    emit()
    return Object.keys(additions).length
  },
  setStage(id, stage, today) {
    if (stage && !STAGES.includes(stage)) return
    if (stage === 'planned' && board[id]?.stage !== 'planned' && idsAt(board, 'planned').length >= 12) return
    if (!stage) {
      // Removing a stage must never erase sales, costs or content progress.
      const { [id]: prev, ...rest } = board
      const { stage: oldStage, since, ...kept } = prev || {}
      board = Object.keys(kept).length ? { ...rest, [id]: kept } : rest
    } else {
      const prev = board[id] || {}
      board = { ...board, [id]: { ...prev, stage, since: prev.stage === stage ? prev.since : today } }
    }
    emit()
  },
  setLaunch(id, launch) {
    const prev = board[id] || {}
    board = { ...board, [id]: { ...prev, stage: 'launched', since: prev.since || launch.launched_on, launch: { logs: [], ...prev.launch, ...launch } } }
    emit()
  },
  logSales(id, week, sold) {
    if (sold !== null && (!Number.isFinite(sold) || sold < 0 || !Number.isInteger(sold))) return
    const prev = board[id]
    if (!prev?.launch) return
    const logs = (prev.launch.logs || []).filter((l) => l.week !== week)
    if (sold !== null) logs.push({ week, sold })
    logs.sort((a, b) => a.week.localeCompare(b.week))
    board = { ...board, [id]: { ...prev, launch: { ...prev.launch, logs } } }
    emit()
  },
  setInputs(id, inputs) {
    const prev = board[id] || {}
    board = { ...board, [id]: { ...prev, inputs: { ...prev.inputs, ...inputs } } }
    emit()
  },
  togglePost(id, day) {
    const prev = board[id] || {}
    const posts = { ...(prev.posts || {}) }
    posts[day] = !posts[day]
    board = { ...board, [id]: { ...prev, posts } }
    emit()
  },
  setCosts(id, costs) {
    const prev = board[id] || {}
    board = { ...board, [id]: { ...prev, costs } }
    emit()
  },
}

export function useBoard() {
  return useSyncExternalStore(boardStore.subscribe, boardStore.get, boardStore.get)
}

// Cost per portion the shop typed into the price helper, or null.
export function costTotal(entry) {
  const vals = Object.values(entry?.costs || {}).map((v) => parseFloat(v)).filter((v) => Number.isFinite(v) && v >= 0)
  return vals.length ? vals.reduce((a, b) => a + b, 0) : null
}

export function onBoardCount(b) {
  return Object.values(b).filter((e) => e.stage).length
}

export function idsAt(b, stage) {
  return Object.keys(b).filter((id) => b[id].stage === stage)
}

export const feedSeen = {
  get: () => read(SEEN_KEY, null),
  set: (iso) => write(SEEN_KEY, iso),
}

export function todayIso() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

// Keep multiple open tabs consistent without writing the event back to storage.
if (typeof window !== 'undefined') window.addEventListener('storage', event => {
  if (event.key === KEY || event.key === null) {
    board = validBoard(read(KEY, {}))
    listeners.forEach(l => l())
  }
})
