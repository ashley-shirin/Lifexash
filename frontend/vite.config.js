import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

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
    plugins: [react()],
    server: { port: 5173 },
  };
});
