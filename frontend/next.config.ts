import type { NextConfig } from "next";

const API_ORIGIN = process.env.API_PROXY_TARGET || "http://127.0.0.1:5001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Same-origin proxy so session cookies work in local browser (cross-port otherwise breaks).
        source: "/backend/:path*",
        destination: `${API_ORIGIN}/:path*`,
      },
    ];
  },
};

export default nextConfig;
