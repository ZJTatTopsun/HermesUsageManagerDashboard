import { test, expect } from './fixtures';

test('prototype session drawer aligns bubbles, expands content and tools, and restores focus', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.route('**/sessions/*/timeline?**', async (route) => {
    const result = await (await route.fetch()).json();
    result.data.session.title = '涉水裤产品规划策略分析';
    result.data.session.source_id = 'test-session-prototype';
    result.data.messages = [
      { id: 'user', kind: 'user', text: '这是用于核对原型的虚构长消息。'.repeat(45), time: '2026-10-15T02:00:00+00:00', tools: [] },
      { id: 'tools', kind: 'tools', text: '', tools: [{ id: 'tool1', name: 'mcp__sellersprite__product_research', success: null, args: '[工具参数未读取]', result: '[工具结果已隐藏]' }] },
      { id: 'assistant', kind: 'assistant', text: '这是模拟分析回复，不读取真实账号数据。', tools: [] },
      { id: 'user2', kind: 'user', text: '把分析结果发给我', tools: [] },
    ];
    result.data.pagination = { offset: 0, limit: 100, has_more: false, returned: 4 };
    await route.fulfill({ json: result });
  });
  await page.goto('/?hum_page=sessions');
  const trigger = page.locator('.hum-row-link').first();
  await trigger.click();
  const drawer = page.getByRole('dialog', { name: '对话详情', exact: true });
  await expect(drawer.getByRole('heading', { name: '涉水裤产品规划策略分析' })).toBeVisible();
  await expect(drawer).toContainText('test-session-prototype');
  await expect(drawer).toHaveCSS('margin-right', '0px');
  await expect(drawer.getByRole('region', { name: '对话记录' })).toHaveCSS('overflow-y', 'auto');
  expect(await drawer.evaluate((element) => getComputedStyle(element, '::backdrop').backgroundColor)).toBe('rgba(29, 27, 32, 0.4)');
  await expect(page.locator('html')).toHaveCSS('overflow-y', 'hidden');
  await expect(page.locator('body')).toHaveCSS('overflow-y', 'hidden');
  await expect(drawer.locator('.hum-message-user').first()).toHaveCSS('align-items', 'flex-end');
  await expect(drawer.locator('.hum-message-assistant')).toHaveCSS('align-items', 'flex-start');
  await expect(drawer.locator('.hum-message-user time')).toHaveCount(1);
  await expect(drawer.locator('.hum-message-assistant time')).toHaveCount(0);
  await expect(drawer.getByRole('button', { name: '展开完整内容' })).toHaveAttribute('aria-expanded', 'false');
  await drawer.getByRole('button', { name: '展开完整内容' }).click();
  await expect(drawer.locator('.hum-message-collapsed')).toHaveCount(0);
  await drawer.getByRole('button', { name: '收起内容' }).click();
  await drawer.locator('.hum-tool-group>summary').click();
  await drawer.locator('.hum-tool-item>summary').click();
  await expect(drawer.getByText('[工具结果已隐藏]', { exact: true })).toBeVisible();
  await expect(drawer.getByLabel('状态未知', { exact: true })).toBeVisible();
  await page.screenshot({ path: '../build/m3/session-drawer-desktop.png', fullPage: true });
  await page.keyboard.press('Escape');
  await expect(drawer).toHaveCount(0);
  await expect(trigger).toBeFocused();
  expect(await page.locator('html').evaluate((element) => element.style.overflowY)).toBe('');
  expect(await page.locator('body').evaluate((element) => element.style.overflowY)).toBe('');
});

test('drawer locks host scroll containers and long transcripts scroll only inside the white region', async ({ page }) => {
  await page.setViewportSize({ width: 1273, height: 828 });
  await page.route('**/sessions/*/timeline?**', async (route) => {
    const result = await (await route.fetch()).json();
    result.data.messages = Array.from({ length: 80 }, (_, index) => ({ id: String(index), kind: index % 2 ? 'assistant' : 'user', text: `用于滚动验证的模拟消息 ${index}`, tools: [] }));
    result.data.pagination = { offset: 0, limit: 100, has_more: false, returned: 80 };
    await route.fulfill({ json: result });
  });
  await page.goto('/?hum_page=sessions');
  const host = page.locator('main.hum-content');
  await host.evaluate((element) => { element.style.height = '600px'; element.style.overflowY = 'scroll'; element.style.setProperty('overflow-x', 'auto', 'important'); });
  await page.locator('.hum-row-link').first().click();
  const drawer = page.getByRole('dialog', { name: '对话详情', exact: true });
  const conversation = drawer.getByRole('region', { name: '对话记录' });
  await expect(conversation.locator('.hum-message')).toHaveCount(80);
  await expect(host).toHaveCSS('overflow-y', 'hidden');
  await expect(drawer.locator('.hum-pagination')).toHaveCount(0);
  const heading = await drawer.getByRole('heading', { name: '对话详情', exact: true }).boundingBox();
  const before = await page.evaluate(() => window.scrollY);
  await conversation.hover();
  await page.mouse.wheel(0, 700);
  await expect.poll(() => conversation.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await page.mouse.move(80, 400);
  await page.mouse.wheel(0, 700);
  expect(await page.evaluate(() => window.scrollY)).toBe(before);
  expect(await host.evaluate((element) => element.scrollTop)).toBe(0);
  expect(await drawer.getByRole('heading', { name: '对话详情', exact: true }).boundingBox()).toEqual(heading);
  await page.screenshot({ path: '../build/m3/session-drawer-scroll-mask.png', fullPage: true });
  await drawer.getByRole('button', { name: '关闭对话详情' }).click();
  await expect(host).toHaveCSS('overflow-y', 'scroll');
  expect(await host.evaluate((element) => element.style.getPropertyPriority('overflow-x'))).toBe('important');
  await host.hover();
  await page.mouse.wheel(0, 500);
  await expect.poll(() => host.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
});

test('session drawer fits mobile without horizontal overflow and closes with its arrow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/?hum_page=sessions');
  await page.locator('.hum-row-link').first().click();
  const drawer = page.getByRole('dialog', { name: '对话详情', exact: true });
  await expect(drawer.getByRole('region', { name: '对话记录' })).toBeVisible();
  const bounds = await drawer.boundingBox();
  expect(bounds?.x).toBe(0);
  expect(bounds?.width).toBe(390);
  expect(await drawer.evaluate((element) => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: '../build/m3/session-drawer-mobile.png', fullPage: true });
  await drawer.getByRole('button', { name: '关闭对话详情' }).click();
  await expect(drawer).toHaveCount(0);
});

test('closing a loading drawer aborts its request and restores background scrolling', async ({ page }) => {
  let release: () => void = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  await page.route('**/sessions/*/timeline?**', async (route) => {
    await gate;
    await route.fulfill({ status: 503, json: { error: { code: 'TEST_ONLY', message: '测试延迟', request_id: 'test' } } }).catch(() => {});
  });
  await page.goto('/?hum_page=sessions');
  const requested = page.waitForRequest((request) => request.url().includes('/timeline?'));
  await page.locator('.hum-row-link').first().click();
  await requested;
  const aborted = page.waitForEvent('requestfailed', { predicate: (request) => request.url().includes('/timeline?') });
  await page.getByRole('button', { name: '关闭对话详情' }).click();
  await aborted;
  release();
  expect(await page.locator('html').evaluate((element) => element.style.overflowY)).toBe('');
  expect(await page.locator('body').evaluate((element) => element.style.overflowY)).toBe('');
  await expect(page.getByRole('dialog')).toHaveCount(0);
});
