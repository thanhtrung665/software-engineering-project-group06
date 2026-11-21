import type { Metadata } from 'next';
import './style.css';
export const metadata: Metadata = { title:'Hotel Booking', description:'Đặt phòng khách sạn trực tuyến' };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="vi"><body>{children}</body></html>; }
