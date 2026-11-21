import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

const MOCK = 'http://127.0.0.1:8765';
const HINT = 'Hãy kiểm tra backend và cấu hình API.';

async function scenario(request: APIRequestContext, name: string) {
  const r = await request.post(`${MOCK}/__scenario/${name}`);
  expect(r.ok()).toBeTruthy();
}

const cards = (page: Page) => page.locator('article.room');

test.describe('Danh sách loại phòng', () => {
  test.afterEach(async ({ request }) => scenario(request, 'normal'));

  test('FE05 room list shows one card per room type from the API', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.goto('/rooms');
    await expect(page.getByText('Dữ liệu được tải trực tiếp từ REST API (Python · FastAPI) và MySQL.')).toBeVisible();
    await expect(cards(page)).toHaveCount(2);
    await expect(cards(page).nth(0).locator('.roomtop')).toHaveText('STANDARD');   // giữ thứ tự API (giá tăng dần)
    await expect(cards(page).nth(1).locator('.roomtop')).toHaveText('DELUXE');
    await expect(page.locator('.error')).toHaveCount(0);
  });

  test('FE06 room card shows area, bed, capacity, breakfast and price', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.goto('/rooms');
    const deluxe = cards(page).filter({ hasText: 'DELUXE' });
    await expect(deluxe).toContainText('Diện tích: 38.00 m²');
    await expect(deluxe).toContainText('Loại giường: KING');
    await expect(deluxe).toContainText('Sức chứa: 3 người lớn, 1 trẻ em');
    await expect(deluxe).toContainText('Bao gồm bữa sáng');
    await expect(deluxe.locator('strong')).toHaveText('1.800.000 VND / đêm');
    const standard = cards(page).filter({ hasText: 'STANDARD' });
    await expect(standard).toContainText('Không bao gồm bữa sáng');
    await expect(standard.locator('strong')).toHaveText('900.000 VND / đêm');
  });

  test('FE07 room without translation shows code and placeholder description', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.goto('/rooms');
    const standard = cards(page).filter({ hasText: 'STANDARD' });
    await expect(standard.getByRole('heading', { level: 2 })).toHaveText('STANDARD');
    await expect(standard).toContainText('Thông tin phòng đang được cập nhật.');
  });

  test('FE08 room with translation shows its name and description', async ({ page, request }) => {
    await scenario(request, 'translated');
    await page.goto('/rooms');
    await expect(cards(page)).toHaveCount(1);
    await expect(cards(page).getByRole('heading', { level: 2 })).toHaveText('Phòng Deluxe hướng biển');
    await expect(cards(page)).toContainText('Phòng rộng 38 m² có ban công nhìn ra biển.');
  });

  test('FE09 page requests room types in Vietnamese', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.goto('/rooms');
    const last = await (await request.get(`${MOCK}/__last-request`)).json();
    expect(last).toEqual({ path: '/api/v1/room-types', query: { lang: 'vi' } });
  });

  test('FE10 empty list shows "no room types" message', async ({ page, request }) => {
    await scenario(request, 'empty');
    await page.goto('/rooms');
    await expect(cards(page)).toHaveCount(0);
    await expect(page.getByText('Chưa có loại phòng đang kinh doanh trong cơ sở dữ liệu.')).toBeVisible();
  });

  test('FE11 API error 500 shows error message instead of crashing', async ({ page, request }) => {
    await scenario(request, 'error500');
    const response = await page.goto('/rooms');
    expect(response?.status()).toBe(200);
    await expect(page.locator('.error')).toHaveText(`Không tải được danh sách phòng (500). ${HINT}`);
    await expect(cards(page)).toHaveCount(0);
    await expect(page.getByText('Chưa có loại phòng đang kinh doanh')).toHaveCount(0);
  });

  test('FE12 backend unreachable shows error message', async ({ page, request }) => {
    await scenario(request, 'down');
    const response = await page.goto('/rooms');
    expect(response?.status()).toBe(200);
    await expect(page.locator('.error')).toContainText(HINT);
    await expect(cards(page)).toHaveCount(0);
  });

  test('FE13 legacy { data: [...] } response format is still supported', async ({ page, request }) => {
    await scenario(request, 'legacy');
    await page.goto('/rooms');
    await expect(cards(page)).toHaveCount(1);
    await expect(cards(page).locator('.roomtop')).toHaveText('STANDARD');
  });

  test('FE14 data is reloaded on every visit (no stale cache)', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.goto('/rooms');
    await expect(cards(page)).toHaveCount(2);
    await scenario(request, 'empty');
    await page.reload();
    await expect(cards(page)).toHaveCount(0);
  });

  test('FE15 "← Trang chủ" link goes back to home page', async ({ page }) => {
    await page.goto('/rooms');
    await page.getByRole('link', { name: '← Trang chủ' }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('link', { name: 'Khám phá phòng' })).toBeVisible();
  });

  test('FE16 room list fits a mobile screen (375 px) in one column', async ({ page, request }) => {
    await scenario(request, 'normal');
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto('/rooms');
    const [a, b] = [await cards(page).nth(0).boundingBox(), await cards(page).nth(1).boundingBox()];
    expect(a && b).toBeTruthy();
    expect(b!.y).toBeGreaterThan(a!.y + a!.height - 1);             // xếp dọc, không cùng hàng
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);                         // không cuộn ngang
  });
});
