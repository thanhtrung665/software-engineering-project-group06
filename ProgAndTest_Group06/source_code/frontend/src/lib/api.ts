// Gọi REST API Python (FastAPI). Trang /rooms là Server Component nên lệnh fetch chạy phía server Next.js:
// chạy trên máy dùng http://localhost:8000/api/v1, chạy trong Docker Compose dùng http://app:8000/api/v1.
// API_BASE_URL được đọc lúc chạy (biến NEXT_PUBLIC_* bị Next.js nhúng cố định lúc build).
const API = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export type RoomType = {
  room_type_id: number;
  room_type_code: string;
  room_type_name?: string | null;
  description?: string | null;
  area_sqm: string;
  bed_type: string;
  max_adults: number;
  max_children: number;
  view_direction: string | null;
  breakfast_included: boolean | number;
  base_price: string;
};

export async function getRoomTypes(lang = 'vi'): Promise<RoomType[]> {
  const response = await fetch(`${API}/room-types?lang=${lang}`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Không tải được danh sách phòng (${response.status})`);
  const body = await response.json();
  // API Python trả về mảng; giữ tương thích với dạng { data: [...] } của bản API cũ.
  return Array.isArray(body) ? body : body.data ?? [];
}
