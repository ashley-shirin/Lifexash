// Tracks API requests that take longer than SLOW_AFTER_MS, so the UI can say "Waking up the server…".
// No React and no axios in here: plain JavaScript, so it can be unit-tested with `node --test`.

export const SLOW_AFTER_MS = 5000;

let slowCount = 0; // requests that are still pending AND have been pending for 5 s or more
const listeners = new Set();

function setSlowCount(value) {
  slowCount = value;
  listeners.forEach((listener) => listener());
}

/** True while at least one request has been pending for 5 seconds or more. */
export const isAnyRequestSlow = () => slowCount > 0;

/** Call `listener` whenever isAnyRequestSlow() may have changed. Returns an unsubscribe function. */
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/**
 * Call when a request starts. Returns done(): call it when the request finishes (success or error).
 * Each request gets its own timer, so a fast request never shows the notice, even while another runs.
 */
export function trackRequest() {
  let becameSlow = false;
  let finished = false;
  const timer = setTimeout(() => {
    becameSlow = true;
    setSlowCount(slowCount + 1);
  }, SLOW_AFTER_MS);

  return function done() {
    if (finished) return; // safe to call twice
    finished = true;
    clearTimeout(timer);
    if (becameSlow) setSlowCount(slowCount - 1);
  };
}
