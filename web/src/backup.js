const object = v => v && typeof v === 'object' && !Array.isArray(v)
const date = v => typeof v === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(v) && Number.isFinite(Date.parse(v))
const numeric = v => v === '' || (['number', 'string'].includes(typeof v) && Number.isFinite(Number(v)) && Number(v) >= 0)
export function parseBoardBackup(text) {
  const data = JSON.parse(text)
  if (data?.format !== 'lead-time-backup' || data.version !== 1 || !object(data.board)) throw new Error('Choose a Lead Time board backup (version 1).')
  const result = {}
  for (const [id, entry] of Object.entries(data.board)) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id) || ['constructor', 'prototype'].includes(id) || !object(entry)) throw new Error('This backup contains an invalid food.')
    if (entry.stage && !['watching', 'planned', 'launched'].includes(entry.stage)) throw new Error('This backup contains an invalid stage.')
    if (entry.since && !date(entry.since)) throw new Error('This backup contains an invalid date.')
    if (entry.costs && (!object(entry.costs) || !Object.values(entry.costs).every(numeric))) throw new Error('This backup contains invalid costs.')
    if (entry.inputs && (!object(entry.inputs) || !Object.entries(entry.inputs).every(([k, v]) => k === 'offer' ? v === null || (typeof v === 'string' && /^[a-z_]{1,60}$/.test(v)) : ['price', 'units', 'capacity'].includes(k) && (v === null || numeric(v))))) throw new Error('This backup contains invalid pricing inputs.')
    if (entry.posts && (!object(entry.posts) || !Object.values(entry.posts).every(v => typeof v === 'boolean'))) throw new Error('This backup contains an invalid checklist.')
    if (entry.launch && (!object(entry.launch) || !date(entry.launch.launched_on) || !(entry.launch.price === null || numeric(entry.launch.price)) || !Array.isArray(entry.launch.logs) || !entry.launch.logs.every(l => object(l) && date(l.week) && Number.isInteger(l.sold) && l.sold >= 0))) throw new Error('This backup contains invalid sales history.')
    result[id] = Object.fromEntries(['stage', 'since', 'costs', 'inputs', 'posts', 'launch'].filter(k => entry[k] !== undefined).map(k => [k, entry[k]]))
  }
  return result
}
