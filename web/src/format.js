const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
  'October', 'November', 'December']

function parts(iso) {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return { y, m, d }
}

export function fmtDate(iso) {
  if (!iso) return ''
  const { y, m, d } = parts(iso)
  return `${d} ${MONTHS[m - 1]} ${y}`
}

export function fmtDayMonth(iso) {
  if (!iso) return ''
  const { m, d } = parts(iso)
  return `${d} ${MONTHS[m - 1]}`
}

export function fmtMonthYear(iso) {
  if (!iso) return ''
  const { y, m } = parts(iso)
  return `${LONG[m - 1]} ${y}`
}

export function weeksBetween(a, b) {
  return Math.round((Date.parse(b) - Date.parse(a)) / (7 * 864e5))
}

export const PROVIDER_LABEL = {
  soclaas: 'SoCLaaS',
  gemini: 'Gemini',
  featherless: 'Featherless',
  offline: 'offline rules (no model key set)',
}
