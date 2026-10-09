import { fmtMonthYear } from '../format.js'

const PAD = { l: 4, r: 4, t: 14, b: 22 }
const DAY = 864e5

/**
 * Two lines: where it started (pandan) and Singapore (kopi-o). Each line is
 * scaled to its own peak, because Google Trends numbers are only comparable
 * within one region's request. Only timing is compared.
 */
export default function Sparkline({
  weeks, lines, originGeo, originName, takeoffs = {}, window: win, asOf, height = 120,
  revealAfter, label, width: W = 640,
}) {
  if (!weeks?.length) return null
  const H = height
  const t0 = Date.parse(weeks[0])
  const tEnd = Math.max(
    Date.parse(weeks[weeks.length - 1]) + 7 * DAY,
    win ? Date.parse(win.end) + 7 * DAY : 0,
    asOf ? Date.parse(asOf) : 0,
  )
  const x = (iso) => PAD.l + ((Date.parse(iso) - t0) / (tEnd - t0)) * (W - PAD.l - PAD.r)
  const yFor = (values) => {
    const max = Math.max(1, ...values.map((v) => v || 0))
    return (v) => PAD.t + (1 - (v || 0) / max) * (H - PAD.t - PAD.b)
  }

  const path = (values) => {
    const y = yFor(values)
    return values.map((v, i) => `${i ? 'L' : 'M'}${x(weeks[i]).toFixed(1)},${y(v).toFixed(1)}`).join('')
  }
  const dot = (geo, values) => {
    const wk = takeoffs[geo]
    const i = wk ? weeks.indexOf(wk) : -1
    if (i < 0) return null
    const y = yFor(values)
    return <circle cx={x(wk)} cy={y(values[i])} r="5" fill="var(--surface)" stroke={geo === 'SG' ? 'var(--sg)' : 'var(--accent)'} strokeWidth="2.5" />
  }

  const origin = lines[originGeo]
  const sg = lines.SG
  // year ticks
  const years = []
  for (let yr = new Date(t0).getUTCFullYear() + 1; Date.UTC(yr, 0, 1) < tEnd; yr++) years.push(yr)

  return (
    <figure style={{ margin: 0 }}>
      <svg className="spark" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label || 'Search interest over time'}>
        {win && (
          <g>
            <rect x={x(win.start)} y={PAD.t - 6} width={Math.max(3, x(win.end) - x(win.start) + 6)} height={H - PAD.t - PAD.b + 6} fill="var(--window)" rx="4" />
          </g>
        )}
        {years.map((yr) => {
          const iso = `${yr}-01-01`
          return (
            <g key={yr}>
              <line x1={x(iso)} x2={x(iso)} y1={PAD.t} y2={H - PAD.b} stroke="var(--line)" strokeWidth="1" />
              <text x={x(iso) + 3} y={H - 6} fontSize="12" fill="var(--muted)" className="num">{yr}</text>
            </g>
          )
        })}
        {origin && <path d={path(origin)} fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinejoin="round" />}
        {sg && <path d={path(sg)} fill="none" stroke="var(--sg)" strokeWidth="2" strokeLinejoin="round" strokeDasharray="5 3" />}
        {origin && dot(originGeo, origin)}
        {sg && dot('SG', sg)}
        {revealAfter && (
          <rect x={x(revealAfter)} y={PAD.t - 6} width={Math.max(0, W - PAD.r - x(revealAfter))} height={H - PAD.t - PAD.b + 6}
            fill="var(--soon-soft)" opacity="0.45" />
        )}
        {asOf && (
          <g>
            <line x1={x(asOf)} x2={x(asOf)} y1={PAD.t - 8} y2={H - PAD.b} stroke="var(--now)" strokeWidth="1.5" />
            <text x={Math.min(x(asOf), W - 40)} y={10} fontSize="11" fill="var(--now)" fontWeight="700" textAnchor={x(asOf) > W - 40 ? 'start' : 'middle'}>today</text>
          </g>
        )}
      </svg>
      <figcaption className="spark-legend">
        {origin && <span className="key"><i style={{ background: 'var(--accent)' }} />{originName}</span>}
        {sg && <span className="key"><i className="dash" />Singapore</span>}
        {win && <span className="key"><i className="band" />{win.wide ? 'past foods arrived ' : 'usually arrives '}{fmtMonthYear(win.start)}{win.start.slice(0, 7) !== win.end.slice(0, 7) ? `–${fmtMonthYear(win.end)}` : ''}</span>}
        <span>○ took off</span>
      </figcaption>
    </figure>
  )
}
