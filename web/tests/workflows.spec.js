import { test, expect } from '@playwright/test'
import { parseBoardBackup } from '../src/backup.js'

test('first visit shows real picks without blocking on onboarding', async ({ page }) => {
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Your next bestseller/ })).toBeVisible()
  await expect(page.locator('.card')).toHaveCount(1)
  await expect(page.locator('.demo-notice')).toContainText('example dessert café')
  await expect(page.locator('.metric-card').first()).toContainText('22')
  expect(errors).toEqual([])
})

test('radar supports search, empty recovery, comparison cap, and saved filters', async ({ page }) => {
  await page.goto('/#/explore')
  await expect(page.locator('.radar-card')).toHaveCount(22)
  await page.getByRole('searchbox').fill('nothing-like-this')
  await expect(page.getByRole('heading', { name: 'No signals match those filters' })).toBeVisible()
  await page.getByRole('button', { name: 'Clear filters', exact: true }).click()
  const boxes = page.getByRole('checkbox', { name: /^Compare / })
  await boxes.nth(0).check(); await boxes.nth(1).check(); await boxes.nth(2).check()
  await expect(boxes.nth(3)).toBeDisabled()
  await page.getByRole('button', { name: 'Compare signals' }).click()
  await expect(page.getByRole('table')).toBeVisible()
  await expect(page.locator('.comparison-table thead th')).toHaveCount(4)
  await page.getByRole('button', { name: 'Close comparison' }).click()
  await page.locator('.radar-card').first().getByRole('button', { name: 'Watch', exact: true }).click()
  await page.getByLabel('On my board only').check()
  await expect(page.locator('.radar-card')).toHaveCount(1)
  await page.reload()
  await expect(page.locator('.radar-card').first().getByRole('button', { name: 'Watching', exact: true })).toHaveAttribute('aria-pressed', 'true')
})

test('metric deep link applies the intended filter', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('link', { name: /Rising overseas.*Watch before the crowd/ }).click()
  await expect(page.locator('.radar-card')).toHaveCount(1)
  await expect(page.locator('.radar-card')).toContainText('Sea salt coffee')
})

test('watch to plan to launch, log sales, archive, and restore preserves numbers', async ({ page }) => {
  await page.goto('/#/explore')
  const card = page.locator('.radar-card').filter({ hasText: 'Sea salt coffee' })
  await card.getByRole('button', { name: 'Plan', exact: true }).click()
  await page.getByRole('link', { name: /Launch board/ }).click()
  await expect(page.getByRole('region', { name: 'Planning', exact: true }).locator('.pipeline-item')).toHaveCount(1)
  await page.getByRole('link', { name: 'Ready? Record your launch' }).click()
  await expect(page.getByRole('heading', { name: 'Launched it?' })).toBeVisible()
  await page.getByLabel('Price ($)', { exact: true }).fill('6.5')
  await page.getByRole('button', { name: "I've launched Sea salt coffee" }).click()
  await page.getByLabel('Sold', { exact: true }).fill('40')
  await page.getByRole('button', { name: 'Log week' }).click()
  await expect(page.locator('#track')).toContainText('40 sold so far')
  await page.getByRole('button', { name: 'Archive launch', exact: true }).click()
  await expect(page.locator('#track')).toContainText('Your sales history is preserved')
  await page.reload()
  await expect(page.locator('#track')).toContainText('40 sold so far')
  await page.getByRole('button', { name: 'Restore to launched board' }).click()
  await page.getByRole('link', { name: /Launch board/ }).click()
  await expect(page.getByRole('region', { name: 'Launched', exact: true }).locator('.pipeline-item')).toHaveCount(1)
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download board backup' }).click()
  expect((await download).suggestedFilename()).toMatch(/^lead-time-backup-/)
})

test('history selection remains visible when navigating to the radar', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Explore history' }).click()
  await page.locator('#asof').fill('2024-07-06')
  await expect(page.locator('.history-notice')).toContainText('2024')
  await page.getByRole('link', { name: 'Trend radar', exact: true }).click()
  await expect(page.locator('.history-notice')).toBeVisible()
  await expect(page.locator('.radar-card')).toHaveCount(22)
  await page.getByRole('button', { name: 'Return to latest snapshot' }).click()
  await expect(page.locator('.history-notice')).toHaveCount(0)
})

test('API failure can be retried without losing the screen', async ({ page }) => {
  await page.route('**/api/concepts', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ error: 'Temporarily unavailable' }) }))
  await page.goto('/#/explore')
  await expect(page.getByRole('alert')).toContainText('Temporarily unavailable')
  await page.unroute('**/api/concepts')
  await page.getByRole('button', { name: 'Try again' }).click()
  await expect(page.locator('.radar-card')).toHaveCount(22)
})

test('malformed top-level saved state does not crash and appearance persists', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('leadtime.board', 'null'); localStorage.setItem('leadtime.profile', '[]') })
  await page.goto('/')
  await expect(page.locator('.card')).toHaveCount(1)
  await page.getByRole('button', { name: 'Dark appearance' }).click()
  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
})

for (const width of [375, 768, 1440]) test('responsive layout at ' + width, async ({ page }) => {
  await page.setViewportSize({ width, height: 900 })
  for (const route of ['/', '/#/explore', '/#/board', '/#/c/sea-salt-coffee']) {
    await page.goto(route)
    await expect(page.locator('main')).not.toBeEmpty()
    await page.waitForLoadState('networkidle')
    const sizes = await page.evaluate(() => ({ body: document.documentElement.scrollWidth, view: innerWidth }))
    expect(sizes.body).toBeLessThanOrEqual(sizes.view + 1)
  }
})

test('backup validation rejects broken sales and accepts an exported board', () => {
  const backup = board => JSON.stringify({ format: 'lead-time-backup', version: 1, board })
  expect(parseBoardBackup(backup({ coffee: { stage: 'watching' } }))).toEqual({ coffee: { stage: 'watching' } })
  expect(() => parseBoardBackup(backup({ coffee: { launch: { logs: [{ sold: -2 }] } } }))).toThrow('invalid sales')
  expect(() => parseBoardBackup('{"board":[]}')).toThrow()
})


test('backup restores missing foods, keeps existing values, and rejects invalid input', async ({ page }) => {
  await page.goto('/#/board')
  const upload = page.getByLabel('Import board backup')
  const payload = { format: 'lead-time-backup', version: 1, board: { 'sea-salt-coffee': { stage: 'watching', inputs: { price: '6.50', offer: 'limited_drop' } } } }
  await upload.setInputFiles({ name:'backup.json', mimeType:'application/json', buffer:Buffer.from(JSON.stringify(payload)) })
  await expect(page.getByRole('status')).toContainText('1 foods restored')
  await expect(page.getByRole('region', { name: 'Watching', exact: true }).locator('.pipeline-item')).toHaveCount(1)
  payload.board['sea-salt-coffee'].inputs.price = '999'
  await upload.setInputFiles({ name:'backup.json', mimeType:'application/json', buffer:Buffer.from(JSON.stringify(payload)) })
  await expect(page.getByRole('status')).toContainText('0 foods restored')
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('leadtime.board'))['sea-salt-coffee'].inputs.price)).toBe('6.50')
  await upload.setInputFiles({ name:'bad.json', mimeType:'application/json', buffer:Buffer.from('{"board":[]}') })
  await expect(page.getByRole('alert')).toContainText('Choose a Lead Time board backup')
})

test('plan limit prevents a thirteenth food and board changes sync between tabs', async ({ page, context }) => {
  await page.goto('/#/explore')
  await expect(page.locator('.radar-card')).toHaveCount(22)
  const ids = await page.locator('.radar-title').evaluateAll(links => links.slice(0, 12).map(l => l.getAttribute('href').split('/').pop()))
  await page.evaluate(ids => localStorage.setItem('leadtime.board', JSON.stringify(Object.fromEntries(ids.map(id => [id, { stage:'planned' }])))), ids)
  await page.reload()
  await expect(page.locator('.radar-card').nth(12).getByRole('button', { name: 'Plan', exact: true })).toBeDisabled()
  const second = await context.newPage()
  await second.goto('/#/board')
  await expect(second.getByRole('region', { name:'Planning', exact:true }).locator('.pipeline-item')).toHaveCount(12)
  await page.locator('.radar-card').first().getByRole('button', { name:'In your plan', exact:true }).click()
  await expect(second.getByRole('region', { name:'Planning', exact:true }).locator('.pipeline-item')).toHaveCount(11)
  await expect(page.locator('.radar-card').nth(12).getByRole('button', { name:'Plan', exact:true })).toBeEnabled()
})
