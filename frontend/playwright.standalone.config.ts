import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './standalone-tests', testMatch: '*.spec.ts', workers: 1,
  use: { baseURL: 'http://127.0.0.1:9120', headless: true },
  webServer: { command: 'node scripts/test-standalone-server.mjs', url: 'http://127.0.0.1:9120', reuseExistingServer: false },
});
