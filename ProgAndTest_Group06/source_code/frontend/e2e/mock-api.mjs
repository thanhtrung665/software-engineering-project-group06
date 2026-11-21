// Mock REST API cho test frontend: giả lập GET /api/v1/room-types của backend Python.
// Test đổi tình huống bằng POST /__scenario/<tên>, xem request cuối bằng GET /__last-request.
import http from 'node:http';

const PORT = Number(process.env.MOCK_API_PORT ?? 8765);

const ROOMS = [
  { room_type_id: 2, room_type_code: 'STANDARD', area_sqm: '25.00', bed_type: 'DOUBLE', max_adults: 2, max_children: 1,
    view_direction: null, breakfast_included: false, base_price: '900000.00', selling_status: 'ON_SALE' },
  { room_type_id: 1, room_type_code: 'DELUXE', area_sqm: '38.00', bed_type: 'KING', max_adults: 3, max_children: 1,
    view_direction: 'SEA', breakfast_included: true, base_price: '1800000.00', selling_status: 'ON_SALE' },
];

const SCENARIOS = {
  normal: () => [200, ROOMS],
  translated: () => [200, [{ ...ROOMS[1], room_type_name: 'Phòng Deluxe hướng biển',
                             description: 'Phòng rộng 38 m² có ban công nhìn ra biển.' }]],
  empty: () => [200, []],
  legacy: () => [200, { data: [ROOMS[0]] }],      // định dạng { data: [...] } của API PHP cũ
  error500: () => [500, { code: 'INTERNAL_ERROR', message: 'Lỗi máy chủ' }],
  down: () => null,                                // ngắt kết nối = backend không phản hồi
};

let scenario = 'normal';
let lastRequest = null;

http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const send = (status, body) => {
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(body));
  };
  if (req.method === 'POST' && url.pathname.startsWith('/__scenario/')) {
    const name = url.pathname.split('/').pop();
    if (!(name in SCENARIOS)) return send(400, { error: `unknown scenario ${name}` });
    scenario = name;
    return send(200, { scenario });
  }
  if (url.pathname === '/__last-request') return send(200, lastRequest);
  if (url.pathname === '/api/v1/health') return send(200, { status: 'ok' });
  if (url.pathname === '/api/v1/room-types') {
    lastRequest = { path: url.pathname, query: Object.fromEntries(url.searchParams) };
    const result = SCENARIOS[scenario]();
    if (result === null) return req.socket.destroy();
    return send(...result);
  }
  send(404, { code: 'NOT_FOUND' });
}).listen(PORT, '127.0.0.1', () => console.log(`mock api listening on ${PORT}`));
