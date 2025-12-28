/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Environment variables available at runtime
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8300/api/v1",
  },
};

export default nextConfig;
