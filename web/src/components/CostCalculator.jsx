import { useState } from 'react'
import { money, PRICE_BANDS, suggestPrice, TARGET_FOOD_COST } from '../pricing.js'
import { boardStore, useBoard } from '../store.js'

// Shop types its own cost per portion for each ingredient; code does the arithmetic.
export default function CostCalculator({ id, ingredients, priceBand }) {
  const board = useBoard()
  const saved = board[id]?.costs || {}
  const rows = [...ingredients, 'packaging']
  const [costs, setCosts] = useState(() => Object.fromEntries(rows.map((r) => [r, saved[r] ?? ''])))

  const set = (k, v) => {
    const next = { ...costs, [k]: v }
    setCosts(next)
    boardStore.setCosts(id, next)
  }
  const total = rows.reduce((s, r) => s + (parseFloat(costs[r]) || 0), 0)
  const s = suggestPrice(total, priceBand)

  return (
    <section className="block" id="costs">
      <h3>What to charge</h3>
      <p className="small muted">Type roughly what each part costs you per portion. We'll suggest a price.</p>
      <div className="cost-grid">
        {rows.map((r) => (
          <label key={r} className="cost-row">
            <span>{r}</span>
            <span className="money-input">
              <span aria-hidden="true">$</span>
              <input type="number" inputMode="decimal" min="0" step="0.05" value={costs[r]}
                onChange={(e) => set(r, e.target.value)} aria-label={`${r} cost per portion`} />
            </span>
          </label>
        ))}
      </div>
      {s ? (
        <div className="price-out">
          <p>
            Cost per portion <b className="num">{money(total)}</b>. Charge about <b className="num price-big">{money(s.price)}</b>{' '}
            <span className="muted">to keep ingredients near {Math.round(TARGET_FOOD_COST * 100)}% of the price ({money(s.margin)} margin each).</span>
          </p>
          {s.fit !== 'inside' && (
            <p className="note">
              That's {s.fit} your usual range ({PRICE_BANDS[priceBand].label}).{' '}
              {s.fit === 'above' ? 'Try a smaller portion or cheaper swaps from the plan above.' : 'You have room for a premium version.'}
            </p>
          )}
        </div>
      ) : <p className="small muted" style={{ marginTop: 10 }}>Fill in at least one cost to see a price.</p>}
    </section>
  )
}
