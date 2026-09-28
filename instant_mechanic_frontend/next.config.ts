import type { NextConfig } from "next";

// The API client calls NEXT_PUBLIC_API_BASE_URL directly (Django handles CORS),
// so no rewrites/proxy are needed here.
const nextConfig: NextConfig = {};

export default nextConfig;
