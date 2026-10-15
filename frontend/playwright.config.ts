import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests', testMatch: '*.spec.ts', workers: 1,
  use: { baseURL: 'http://127.0.0.1:8765', headless: true },
  webServer: { command: 'node scripts/test-server.mjs', url: 'http://127.0.0.1:8765', reuseExistingServer: false },
});
