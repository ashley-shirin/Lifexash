import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig(({ command, mode }) => {
  // loadEnv reads .env / .env.[mode] files AND real environment variables (the host's build settings).
  const env = loadEnv(mode, process.cwd(), "VITE_");

  // VITE_API_URL is baked into the bundle at build time. Without it, every API call would silently
  // go to the wrong place, so stop the production build instead.
  if (command === "build" && !/^https?:\/\//.test(env.VITE_API_URL ?? "")) {
    throw new Error(
      "VITE_API_URL is missing or not an http(s) URL. Set it before building, " +
        "e.g. VITE_API_URL=https://api.example.com/api",
    );
  }

  return {
    plugins: [
      react(),
      // Generates the web app manifest and a service worker at build time (not in `npm run dev`).
      VitePWA({
        // "prompt": a new version waits until the user clicks Reload (see UpdatePrompt.jsx).
        registerType: "prompt",
        includeManifestIcons: false, // the icons are already matched by globPatterns below (no duplicates)
        manifest: {
          name: "LifeXash",
          short_name: "LifeXash",
          description: "Daily planner, notes with tags and a mood journal.",
          start_url: "/dashboard",
          scope: "/",
          display: "standalone",
          theme_color: "#4f46e5",
          background_color: "#f9fafb",
          icons: [
            { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
            { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" },
            { src: "maskable-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
          ],
        },
        workbox: {
          // Precache ONLY the app shell: the built HTML, JS, CSS and icons in dist/.
          globPatterns: ["**/*.{html,js,css,svg,png}"], // the plugin adds manifest.webmanifest itself
          // No `runtimeCaching` on purpose: every other request (all API calls) goes straight to the
          // network and is never stored. API data is private and could go stale or leak on a shared device.
          // Page navigations (e.g. /notes/5) get index.html so React Router can handle them offline...
          navigateFallback: "index.html",
          // ...except anything under /api, in case the API is ever served from this same domain.
          navigateFallbackDenylist: [/^\/api\//],
          cleanupOutdatedCaches: true,
        },
      }),
    ],
    server: { port: 5173 },
  };
});
