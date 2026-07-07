import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow loading the dev server over the LAN (e.g. testing on a phone) — Next 16
  // blocks cross-origin /_next dev resources by default, which leaves the page
  // showing only the background because the client JS never runs.
  allowedDevOrigins: ["192.168.0.23"],
};

export default nextConfig;
