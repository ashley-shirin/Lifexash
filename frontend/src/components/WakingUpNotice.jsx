import { useSyncExternalStore } from "react";

import { isAnyRequestSlow, subscribe } from "../api/slowRequests.js";

/**
 * "Waking up the server…" while any API request has been pending for 5+ seconds.
 * The free Render plan puts the API to sleep; the first request after that can take about a minute.
 */
export default function WakingUpNotice() {
  // useSyncExternalStore: re-render when a value that lives outside React (slowRequests.js) changes.
  const slow = useSyncExternalStore(subscribe, isAnyRequestSlow);

  // The live region is always in the page, so screen readers reliably announce text added to it.
  return (
    <div role="status" aria-live="polite" className="wake-region">
      {slow && (
        <p className="wake-notice">
          Waking up the server… the first request after a quiet period can take up to a minute.
        </p>
      )}
    </div>
  );
}
