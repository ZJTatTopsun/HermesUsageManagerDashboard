import { test as base, expect } from '@playwright/test';

export const test = base.extend({
  context: async ({ context }, use, info) => {
    await context.setExtraHTTPHeaders({ 'x-hum-test-case': `${info.testId}:${info.retry}` });
    await use(context);
  },
});
export { expect };
