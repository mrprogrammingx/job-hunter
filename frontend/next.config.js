/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      // /api/auth/* is handled by the NextAuth App Router catch-all — don't proxy it
      {
        source: "/api/:path((?!auth/).*)",
        destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
