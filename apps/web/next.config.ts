import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return {
      // beforeFiles rewrites run before the filesystem (pages/api routes)
      beforeFiles: [],
      // afterFiles rewrites run after filesystem but before fallback
      afterFiles: [
        {
          source: "/api/tts",
          destination: "/api/tts", // handled by Next.js API route, not proxied
        },
      ],
      // fallback rewrites only run if no page/api route matches
      fallback: [
        {
          source: "/api/:path*",
          destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/:path*`,
        },
      ],
    };
  },
};

export default nextConfig;
