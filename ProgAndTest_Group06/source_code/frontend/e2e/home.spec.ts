import { expect, test } from '@playwright/test';

test.describe('Trang chủ', () => {
  test('FE01 home page shows title, brand and call to action', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.status()).toBe(200);
    await expect(page).toHaveTitle('Hotel Booking');
    await expect(page.locator('html')).toHaveAttribute('lang', 'vi');
    await expect(page.getByText('HOTEL BOOKING', { exact: true })).toBeVisible();
    await expect(page.getByText('ĐẶT PHÒNG TRỰC TUYẾN')).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(/Trải nghiệm kỳ nghỉ\s*theo cách của bạn\./);
    await expect(page.getByRole('link', { name: 'Khám phá phòng' })).toBeVisible();
  });

  test('FE02 clicking "Khám phá phòng" opens the room list', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Khám phá phòng' }).click();
    await expect(page).toHaveURL(/\/rooms$/);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Danh sách loại phòng');
  });

  test('FE03 clicking menu "Danh sách phòng" opens the room list', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('navigation').getByRole('link', { name: 'Danh sách phòng' }).click();
    await expect(page).toHaveURL(/\/rooms$/);
  });

  test('FE04 unknown URL shows 404 page', async ({ page }) => {
    const response = await page.goto('/khong-ton-tai');
    expect(response?.status()).toBe(404);
    await expect(page.getByText('This page could not be found.')).toBeVisible();
  });
});
