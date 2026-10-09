import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { fmtDate, fmtMonthYear, PROVIDER_LABEL, weeksBetween } from '../format.js'
import { suggestPrice } from '../pricing.js'
import { useBoard } from '../store.js'
import CostCalculator from './CostCalculator.jsx'
import DecisionCard from './DecisionCard.jsx'
import Playbook from './Playbook.jsx'
import Sparkline from './Sparkline.jsx'
import StageButtons from './StageButtons.jsx'
import Status from './Status.jsx'
import Tracker from './Tracker.jsx'

const LANG = { en: 'English', ko: 'Korean', ja: 'Japanese', zh: 'Chinese', ar: 'Arabic', vi: 'Vietnamese' }

function Reveal({ id, asOf, forecastWindow, origin }) {
  const [after, setAfter] = useState(null)
  const [err, setErr] = useState(null)
  const [open, setOpen] = useState(false)

  useEffect(() => { setAfter(null); setOpen(false) }, [id, asOf])

  const go = () => {
    setOpen(true)
    if (!after) api.concept(id).then(setAfter).catch((e) => setErr(e.message))
  }
  if (!open) {
    return <button className="btn primary" type="button" onClick={go}>Reveal what happened next</button>
  }
  if (err) return <div className="error">{err}</div>
  if (!after) return <p className="loading">Loading what happened…</p>

  const sg = after.sg_week
  let verdict = null
  if (sg && forecastWindow) {
    const inside = sg >= forecastWindow.start && sg <= forecastWindow.end
    const early = sg < forecastWindow.start
    verdict = inside
      ? <span className="verdict-good">Inside the window we gave.</span>
      : <span className="verdict-off">{early ? `${weeksBetween(sg, forecastWindow.start)} weeks earlier than our window.` : `${weeksBetween(forecastWindow.end, sg)} weeks later than our window.`}</span>
  }
  const lead = sg ? weeksBetween(asOf, sg) : null
  const originGeo = origin || after.origin
  return (
    <div className="block reveal">
      <h3>What actually happened</h3>
      <p>
        {sg
          ? <>Singapore took off in <b>{fmtMonthYear(sg)}</b>{lead > 0 ? `, ${lead} weeks after the date you picked` : ''}. {verdict}</>
          : 'It never took off in Singapore, as of our latest data.'}
      </p>
      <Sparkline
        weeks={after.series.weeks.slice(-156)}
        lines={{ [originGeo]: after.series.regions[originGeo]?.slice(-156), SG: after.series.regions.SG?.slice(-156) }}
        originGeo={originGeo} originName={after.region_names[originGeo]} takeoffs={after.takeoffs}
        window={forecastWindow} asOf={asOf} revealAfter={asOf} height={140}
        label={after.evidence}
      />
      <p className="small muted" style={{ marginTop: 8 }}>Shaded area: weeks Lead Time couldn't see on {fmtDate(asOf)}.</p>
    </div>
  )
}

export default function Detail({ id, profile, asOf }) {
  const [plan, setPlan] = useState(null)
  const [concept, setConcept] = useState(null)
  const [error, setError] = useState(null)
  const board = useBoard()

  useEffect(() => {
    let live = true
    setPlan(null); setConcept(null); setError(null)
    api.concept(id, asOf).then((c) => live && setConcept(c)).catch((e) => live && setError(e.message))
    api.launch(id, profile, asOf).then((p) => live && setPlan(p)).catch((e) => live && setError(e.message))
    window.scrollTo(0, 0)
    return () => { live = false }
  }, [id, profile, asOf])

  // #/c/<id>#track jumps to the sales tracker once the page has rendered
  useEffect(() => {
    if (concept && window.location.hash.endsWith('#track')) {
      document.getElementById('track')?.scrollIntoView({ block: 'start' })
    }
  }, [concept])

  if (error) return <div><a className="btn ghost back" href="#/">← All picks</a><div className="error" role="alert">{error}</div></div>
  if (!concept) return <div><a className="btn ghost back" href="#/">← All picks</a><div className="skeleton" /></div>

  const origin = concept.origin || Object.keys(concept.series.regions).find((g) => g !== 'SG')
  const fit = plan?.fit
  const p = plan?.plan
  const costs = board[id]?.costs || {}
  const costTotal = Object.values(costs).reduce((t, v) => t + (parseFloat(v) || 0), 0)
  const suggested = suggestPrice(costTotal, profile.price_band)?.price

  return (
    <div>
      <a className="btn ghost back" href="#/">← All picks</a>
      <header className="detail-head">
        <h1>{concept.name}</h1>
        <Status status={concept.status} label={concept.status_label} />
        <p className="desc">{concept.description}</p>
        <div style={{ marginTop: 12 }}><StageButtons id={id} asOf={asOf} /></div>
      </header>

      <DecisionCard key={`d-${id}`} id={id} profile={profile} asOf={asOf} />

      <section className="block">
        <h3>The evidence</h3>
        <p>{concept.why}</p>
        <p className="muted" style={{ marginTop: 6 }}>{concept.evidence}</p>
        <Sparkline
          weeks={concept.series.weeks.slice(-130)}
          lines={{ [origin]: concept.series.regions[origin]?.slice(-130), SG: concept.series.regions.SG?.slice(-130) }}
          originGeo={origin} originName={concept.region_names[origin]} takeoffs={concept.takeoffs}
          window={concept.window} asOf={concept.as_of} height={150} label={concept.evidence}
        />
        <p className="small muted" style={{ marginTop: 6 }}>Weekly Google searches, each line scaled to its own peak.</p>
      </section>

      {asOf && (
        <section className="section">
          <Reveal id={id} asOf={concept.as_of} forecastWindow={concept.window} origin={origin} />
        </section>
      )}

      <section className="block">
        <h3>When</h3>
        {!plan ? <p className="loading">Working out your plan…</p> : <p className="when-big">{plan.when.text}</p>}
      </section>

      {plan && fit && (
        <section className="block">
          <h3>What to make in your kitchen</h3>
          <p>
            {fit.verdict === 'make' && <b>You can make the original. </b>}
            {fit.verdict === 'adapt' && <b>{fit.adaptation}. </b>}
            {fit.verdict === 'skip' && <b>Probably not one for you. </b>}
            {fit.reason}
          </p>
          {fit.overlaps?.length > 0 && (
            <p className="small" style={{ marginTop: 6 }}>Close to what you already sell: <b>{fit.overlaps.join(', ')}</b>. Think about whether it replaces it or sits beside it.</p>
          )}
          {fit.missing_equipment.length > 0 && (
            <p className="small muted" style={{ marginTop: 6 }}>Missing for the original: {fit.missing_equipment.join(', ')}</p>
          )}
          {p && (
            <>
              <ol className="method" style={{ marginTop: 12 }}>
                {p.method.map((m, i) => (
                  <li key={i}><b>{m.component}</b><ul>{m.steps.map((s, j) => <li key={j}>{s}</li>)}</ul></li>
                ))}
              </ol>
              {p.swaps.length > 0 && (
                <>
                  <h3 style={{ marginTop: 16, fontSize: 17 }}>Swaps</h3>
                  <ul className="method">
                    {p.swaps.map((s, i) => <li key={i}><b>{s.original}</b> → {s.use}. <span className="muted">{s.why}</span></li>)}
                  </ul>
                </>
              )}
              <p className="note">{plan.disclaimer}</p>
            </>
          )}
        </section>
      )}

      {fit && fit.verdict !== 'skip' && (
        <CostCalculator key={id} id={id} ingredients={concept.key_ingredients} priceBand={profile.price_band} />
      )}

      {fit && fit.verdict !== 'skip' && (
        <Playbook key={`p-${id}`} id={id} name={concept.name} profile={profile} asOf={asOf}
          hooks={p?.hooks} caption={p?.caption} />
      )}
      {p && (
        <p className="provider">Opening lines, caption and method by {PROVIDER_LABEL[plan.plan_provider] || plan.plan_provider}. Offer maths, dates, formats and trend facts by code.</p>
      )}

      <Tracker key={`t-${id}`} id={id} name={concept.name} asOf={asOf}
        sgWeeks={concept.series.weeks} sgValues={concept.series.regions.SG} suggestedPrice={suggested} />

      {plan && plan.links.length > 0 && (
        <section className="block">
          <h3>Learn from these</h3>
          <ul className="list-quiet">
            {plan.links.map((l) => (
              <li key={l.url}><a href={l.url} target="_blank" rel="noreferrer">{l.title}</a><span className="muted small">{l.channel}</span></li>
            ))}
          </ul>
        </section>
      )}

      <div className="grid2" style={{ marginTop: 16 }}>
        <section className="block" style={{ marginTop: 0 }}>
          <h3>Also searched as</h3>
          {Object.entries(concept.aliases).map(([lang, names]) => (
            <p key={lang} className="small"><span className="muted">{LANG[lang] || lang}:</span> {names.join(', ')}</p>
          ))}
        </section>
        <section className="block" style={{ marginTop: 0 }}>
          <h3>Where it took off</h3>
          <ul className="list-quiet small">
            {Object.entries(concept.takeoffs).sort((a, b) => a[1].localeCompare(b[1])).map(([g, w]) => (
              <li key={g}><span>{concept.region_names[g]}</span><span className="num">{fmtMonthYear(w)}</span></li>
            ))}
            {Object.keys(concept.takeoffs).length === 0 && <li>No clear takeoff yet in any region we track.</li>}
          </ul>
        </section>
      </div>
      <p className="small muted" style={{ marginTop: 12 }}>Source: Google Trends, weekly, as of {fmtDate(concept.as_of)}.</p>
    </div>
  )
}
