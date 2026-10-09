// Price helper. Plain arithmetic on costs the shop types in; nothing here comes from a model.

export const TARGET_FOOD_COST = 0.30   // cafés usually aim for ingredients at ~28–32% of price
export const ROUND_UP_TO = 0.10        // SG menu prices end in 10 cents
export const PRICE_BANDS = {           // same bands as the shop profile question
  budget: { min: 0, max: 4, label: 'under $4' },
  mid: { min: 4, max: 8, label: '$4 to $8' },
  premium: { min: 8, max: Infinity, label: 'over $8' },
}

export function roundUp(x, step = ROUND_UP_TO) {
  return Math.ceil(x / step - 1e-9) * step
}

export function suggestPrice(costPerPortion, band) {
  if (!(costPerPortion > 0)) return null
  const price = roundUp(costPerPortion / TARGET_FOOD_COST)
  const b = PRICE_BANDS[band]
  let fit = 'inside'
  if (b && price > b.max) fit = 'above'
  else if (b && price < b.min) fit = 'below'
  return { price, margin: price - costPerPortion, foodCost: costPerPortion / price, fit, band: b }
}

export function money(x) {
  return `$${x.toLocaleString('en-SG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
