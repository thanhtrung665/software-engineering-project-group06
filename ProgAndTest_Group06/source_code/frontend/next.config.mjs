import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));   // thư mục frontend, không dò lên thư mục cha

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Bản standalone chỉ dùng cho image Docker (Dockerfile đặt NEXT_STANDALONE=1).
  output: process.env.NEXT_STANDALONE === '1' ? 'standalone' : undefined,
  outputFileTracingRoot: root,
  turbopack: { root },
};
export default nextConfig;
