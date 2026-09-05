/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.amazonaws.com" },
      { protocol: "https", hostname: "localhost" },
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "127.0.0.1" },
      { protocol: "https", hostname: "*.cloudflarestorage.com" },
      { protocol: "https", hostname: "image.pollinations.ai" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/studio-api/:path*",
        destination: "http://127.0.0.1:7860/api/:path*",
      },
      {
        source: "/outputs/:path*",
        destination: "http://127.0.0.1:7860/outputs/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
