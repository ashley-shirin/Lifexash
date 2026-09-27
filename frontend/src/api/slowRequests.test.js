// Unit tests for slowRequests.js with Node's built-in test runner (no extra package): `npm test`.
// mock.timers replaces setTimeout with a fake clock, so "5 seconds" passes instantly with tick().
import assert from "node:assert/strict";
import { afterEach, beforeEach, mock, test } from "node:test";

import { SLOW_AFTER_MS, isAnyRequestSlow, subscribe, trackRequest } from "./slowRequests.js";

beforeEach(() => mock.timers.enable({ apis: ["setTimeout"] }));
afterEach(() => mock.timers.reset());

test("a fast request never counts as slow", () => {
  const done = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS - 1);
  done();
  mock.timers.tick(10_000); // the timer was cleared, so nothing happens later either
  assert.equal(isAnyRequestSlow(), false);
});

test("a request pending for 5 s is slow until it finishes", () => {
  const done = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS);
  assert.equal(isAnyRequestSlow(), true);
  done();
  assert.equal(isAnyRequestSlow(), false);
});

test("stays slow until the LAST slow request finishes", () => {
  const doneA = trackRequest();
  const doneB = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS);
  doneA();
  assert.equal(isAnyRequestSlow(), true);
  doneB();
  assert.equal(isAnyRequestSlow(), false);
});

test("a fast request doesn't show the notice while an older one is still pending", () => {
  const doneOld = trackRequest();
  mock.timers.tick(3000);
  const doneFast = trackRequest();
  mock.timers.tick(1000);
  doneFast();
  assert.equal(isAnyRequestSlow(), false); // old one: 4 s, not slow yet
  mock.timers.tick(1000);
  assert.equal(isAnyRequestSlow(), true); // old one: 5 s
  doneOld();
  assert.equal(isAnyRequestSlow(), false);
});

test("calling done() twice doesn't make the count negative", () => {
  const done = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS);
  done();
  done();
  const doneNext = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS);
  assert.equal(isAnyRequestSlow(), true); // would be false if the count had gone to -1
  doneNext();
});

test("listeners are told about both changes", () => {
  let calls = 0;
  const unsubscribe = subscribe(() => calls++);
  const done = trackRequest();
  mock.timers.tick(SLOW_AFTER_MS);
  done();
  unsubscribe();
  assert.equal(calls, 2); // became slow, then not slow
});
