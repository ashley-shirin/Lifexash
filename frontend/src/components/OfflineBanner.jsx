import { useEffect, useState } from "react";

/** Shows a banner while the browser has no network connection. */
export default function OfflineBanner() {
  const [online, setOnline] = useState(navigator.onLine);

  // The browser fires "online" / "offline" events on window when the connection changes.
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  if (online) return null;
  return (
    <div className="app-banner offline-banner" role="status">
      You're offline. Changes can't be saved right now.
    </div>
  );
}
