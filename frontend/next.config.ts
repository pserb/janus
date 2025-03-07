import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	output: "standalone",
	reactStrictMode: true,
	env: {
		// Default API URL (overridden in Docker by environment variable)
		NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
	},
	// Configure images domains if needed
	images: {
		domains: [],
	},
};

export default nextConfig;
