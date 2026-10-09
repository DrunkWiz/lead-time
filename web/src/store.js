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

let board = read(KEY, {})
const listeners = new Set()
function emit() { write(KEY, board); listeners.forEach((l) => l()) }

export const boardStore = {
  subscribe(l) { listeners.add(l); return () => listeners.delete(l) },
  get() { return board },
  setStage(id, stage, today) {
    if (!stage) {
      // leaving the board keeps the shop's own numbers (costs, price, units) for next time
      const { [id]: prev, ...rest } = board
      const kept = prev && (prev.costs || prev.inputs) ? { costs: prev.costs, inputs: prev.inputs, posts: prev.posts } : null
      board = kept ? { ...rest, [id]: kept } : rest
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
    const prev = board[id]
    if (!prev?.launch) return
    const logs = prev.launch.logs.filter((l) => l.week !== week)
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
  const vals = Object.values(entry?.costs || {}).map((v) => parseFloat(v)).filter((v) => v >= 0)
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
