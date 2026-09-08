import type { NextConfig } from "next";

/**
 * Next.js configuration.
 *
 * Rewrites proxy /api/* requests to the FastAPI backend at localhost:8000.
 * This avoids CORS issues during development and keeps the API URL clean.
 */
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
