/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // API proxy to backend during development
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: process.env.API_URL || 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },

  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },

  // Image optimization domains
  images: {
    domains: ['localhost'],
  },
};

module.exports = nextConfig;

