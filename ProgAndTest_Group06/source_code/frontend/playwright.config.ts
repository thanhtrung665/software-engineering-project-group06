import { defineConfig, devices } from '@playwright/test';

// Chạy: npm run test:e2e  (build production rồi chạy test trên Chromium thật).
// Frontend chạy ở cổng 3210, mock API ở 8765 – tránh đụng cổng 3000/8000 đang dùng cho môi trường dev.
const FRONTEND_PORT = 3210;
const MOCK_API_PORT = 8765;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,                       // các test dùng chung 1 mock API (đổi tình huống tuần tự)
  retries: 0,
  reporter: [['list'], ['junit', { outputFile: 'test-results/junit.xml' }]],
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    locale: 'vi-VN',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: 'node e2e/mock-api.mjs',
      url: `http://127.0.0.1:${MOCK_API_PORT}/api/v1/health`,
      env: { MOCK_API_PORT: String(MOCK_API_PORT) },
      reuseExistingServer: false,
    },
    {
      command: `npx next start -p ${FRONTEND_PORT} -H 127.0.0.1`,
      url: `http://127.0.0.1:${FRONTEND_PORT}/`,
      env: { API_BASE_URL: `http://127.0.0.1:${MOCK_API_PORT}/api/v1`, NEXT_TELEMETRY_DISABLED: '1' },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
