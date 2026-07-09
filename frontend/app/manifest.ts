import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "PROGNOS — Competitive Programming Analytics",
    short_name: "PROGNOS",
    description:
      "Track, analyze, and improve your competitive programming performance.",
    start_url: "/dashboard",
    scope: "/",
    display: "standalone",
    background_color: "#070B14",
    theme_color: "#070B14",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
