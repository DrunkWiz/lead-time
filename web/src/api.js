async function call(path, options = {}) {
  let res
  try {
    res = await fetch(path, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    })
  } catch {
    throw new Error("Can't reach Lead Time. Check your connection and try again.")
  }
  let body = {}
  try { body = await res.json() } catch { /* empty body */ }
  if (!res.ok) throw new Error(body.error || `Something went wrong (${res.status}). Try again.`)
  return body
}

const q = (asOf) => (asOf ? `?as_of=${encodeURIComponent(asOf)}` : '')

export const api = {
  meta: () => call('/api/meta'),
  concepts: (asOf) => call(`/api/concepts${q(asOf)}`),
  concept: (id, asOf) => call(`/api/concepts/${encodeURIComponent(id)}${q(asOf)}`),
  recommend: (profile, asOf) =>
    call('/api/recommend', { method: 'POST', body: JSON.stringify({ profile, as_of: asOf || null }) }),
  launch: (conceptId, profile, asOf) =>
    call('/api/launch', {
      method: 'POST',
      body: JSON.stringify({ concept_id: conceptId, profile, as_of: asOf || null }),
    }),
  backtest: () => call('/api/backtest'),
  changes: (asOf, weeks = 8) =>
    call(`/api/changes?weeks=${weeks}${asOf ? `&as_of=${encodeURIComponent(asOf)}` : ''}`),
  decision: (conceptId, profile, asOf, inputs) =>
    call('/api/decision', {
      method: 'POST',
      body: JSON.stringify({ concept_id: conceptId, profile, as_of: asOf || null, inputs }),
    }),
  review: (conceptId, asOf, logs, price, cost) =>
    call('/api/review', {
      method: 'POST',
      body: JSON.stringify({ concept_id: conceptId, as_of: asOf || null, logs, price, cost }),
    }),
  playbook: (conceptId, profile, asOf, inputs, offerType) =>
    call('/api/playbook', {
      method: 'POST',
      body: JSON.stringify({ concept_id: conceptId, profile, as_of: asOf || null, inputs, offer_type: offerType || null }),
    }),
  lifespan: (asOf) => call(`/api/lifespan${q(asOf)}`),
  plan: (conceptIds, profile, asOf) =>
    call('/api/plan', {
      method: 'POST',
      body: JSON.stringify({ concept_ids: conceptIds, profile, as_of: asOf || null }),
    }),
}
