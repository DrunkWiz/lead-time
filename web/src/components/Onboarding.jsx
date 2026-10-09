import { useState } from 'react'
import DEMOS from '../demoProfiles.json'

const SELLS = [
  ['dessert', 'Desserts'], ['bakery', 'Bakes & bread'], ['drink', 'Drinks'], ['savoury', 'Savoury'],
]
const EQUIPMENT = [
  ['oven', 'Oven'], ['stovetop', 'Stove'], ['fryer', 'Deep fryer'], ['griddle', 'Griddle'],
  ['mixer', 'Stand mixer'], ['blender', 'Blender'], ['espresso machine', 'Espresso machine'],
  ['fridge', 'Fridge'], ['freezer', 'Freezer'], ['soft-serve machine', 'Soft-serve machine'], ['moulds', 'Moulds'],
]
const PRICES = [['budget', 'Under $4'], ['mid', '$4 to $8'], ['premium', 'Over $8']]
const MAX_MENU = 30   // matches the API's limit

function Chips({ options, value, onToggle, multi = true }) {
  return (
    <div className="chips">
      {options.map(([v, label]) => {
        const on = multi ? value.includes(v) : value === v
        return (
          <button type="button" key={v} className="chip" aria-pressed={on} onClick={() => onToggle(v)}>
            {label}
          </button>
        )
      })}
    </div>
  )
}

export default function Onboarding({ initial, onDone, onCancel }) {
  const [name, setName] = useState(initial?.name || '')
  const [sells, setSells] = useState(initial?.sells || [])
  const [equipment, setEquipment] = useState(initial?.equipment || ['fridge'])
  const [price, setPrice] = useState(initial?.price_band || '')
  const [menu, setMenu] = useState(initial?.menu || [])
  const [item, setItem] = useState('')
  const addItem = () => {
    const v = item.trim()
    if (v && menu.length < MAX_MENU && !menu.some((m) => m.toLowerCase() === v.toLowerCase())) setMenu([...menu, v])
    setItem('')
  }
  const toggle = (list, set) => (v) => set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v])
  const ready = sells.length > 0 && price

  return (
    <div>
      <div className="intro">
        <h1>What should you put on the menu next?</h1>
        <p>We watch which foods are taking off in Korea, Japan, Dubai and beyond, work out when they usually reach Singapore, and pick the ones your kitchen can make.</p>
      </div>

      <h3 style={{ marginBottom: 12 }}>Try it with a demo shop</h3>
      <div className="demo-shops">
        {DEMOS.map((d) => (
          <button key={d.id} type="button" className="demo-shop" onClick={() => onDone(d.profile)}>
            <strong>{d.label}</strong>
            <span className="muted small">{d.blurb}</span>
          </button>
        ))}
      </div>

      <div className="divider">or tell us about your shop</div>

      <form onSubmit={(e) => { e.preventDefault(); if (ready) onDone({ name: name.trim() || 'Your shop', sells, equipment, price_band: price, menu }) }}>
        <fieldset className="q">
          <legend>What do you sell?</legend>
          <Chips options={SELLS} value={sells} onToggle={toggle(sells, setSells)} />
        </fieldset>
        <fieldset className="q">
          <legend>What's in your kitchen?</legend>
          <p className="hint">Pick everything you have. We'll suggest swaps for what you don't.</p>
          <Chips options={EQUIPMENT} value={equipment} onToggle={toggle(equipment, setEquipment)} />
        </fieldset>
        <fieldset className="q">
          <legend>What do most items cost?</legend>
          <Chips options={PRICES} value={price} onToggle={setPrice} multi={false} />
        </fieldset>
        <div className="q">
          <label className="legend" htmlFor="menu-item">What's on your menu now? <span className="muted small">(optional)</span></label>
          <p className="hint">We'll flag new foods that are close to something you already sell.</p>
          <div style={{ display: 'flex', gap: 8 }}>
            <input id="menu-item" className="text-input" value={item} maxLength={60} placeholder="e.g. Pistachio latte"
              onChange={(e) => setItem(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addItem() } }} />
            <button type="button" className="btn" onClick={addItem} disabled={!item.trim()}>Add</button>
          </div>
          {menu.length > 0 && (
            <div className="chips" style={{ marginTop: 10 }}>
              {menu.map((m) => (
                <button key={m} type="button" className="chip" onClick={() => setMenu(menu.filter((x) => x !== m))} aria-label={`Remove ${m}`}>
                  {m} <span aria-hidden="true" className="muted">×</span>
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="q">
          <label className="legend" htmlFor="shop-name">Shop name <span className="muted small">(optional)</span></label>
          <input id="shop-name" className="text-input" value={name} maxLength={60} onChange={(e) => setName(e.target.value)} placeholder="e.g. Kaya Corner" />
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button className="btn primary" type="submit" disabled={!ready}>Show me what to make</button>
          {onCancel && <button className="btn" type="button" onClick={onCancel}>Cancel</button>}
        </div>
        {!ready && <p className="muted small" style={{ marginTop: 8 }}>Pick what you sell and a price range to continue.</p>}
      </form>
    </div>
  )
}
