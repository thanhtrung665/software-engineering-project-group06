# Hotel Booking – Frontend

Next.js 16 (App Router) · React 19 · TypeScript. Giao diện khách hàng, lấy dữ liệu từ REST API Python
(`../hotel_booking_room`).

| Trang | File | Nội dung |
|---|---|---|
| `/` | `src/app/page.tsx` | Trang chủ |
| `/rooms` | `src/app/rooms/page.tsx` | Danh sách loại phòng đang bán (gọi `GET /api/v1/room-types`) |

`src/lib/api.ts` gọi API phía server (Server Component). Địa chỉ API đọc từ biến `API_BASE_URL`
(mặc định `http://localhost:8000/api/v1`).

## Chạy

```bash
npm install
npm run dev                 # http://localhost:3000 (cần API Python chạy ở cổng 8000)
# hoặc bản production
npm run build && npm start
```

## Test giao diện (Playwright)

```bash
npx playwright install chromium   # lần đầu
npm run test:e2e                  # next build + 16 test trên Chromium
```

Test chạy bản production ở cổng 3210 với mock API (`e2e/mock-api.mjs`, cổng 8765) để tạo đủ tình huống:
danh sách bình thường / có bản dịch / rỗng / định dạng cũ `{data: [...]}` / API lỗi 500 / mất kết nối.
Kết quả JUnit: `test-results/junit.xml`.

| File | Nội dung |
|---|---|
| `e2e/home.spec.ts` | FE01–FE04: trang chủ, điều hướng, trang 404 |
| `e2e/rooms.spec.ts` | FE05–FE16: thẻ phòng, bản dịch, rỗng, lỗi API, dữ liệu mới, quay lại trang chủ, màn hình 375 px |

Chạy cùng backend bằng Docker: trong `../hotel_booking_room`, `docker compose up -d --build`
(service `frontend`, cổng `FRONTEND_PORT`, mặc định 3000).

> Mã nguồn được khôi phục từ bản build dev (`.next`, source map) của nhóm, sau đó nâng Next.js 14.2 → 16.4
> vì dòng 14.x có lỗ hổng bảo mật nghiêm trọng (`npm audit`: 0 lỗ hổng sau khi nâng).
