// The 5 moods of a journal entry. The backend only stores the number (1–5).
export const MOODS = [
  { value: 1, emoji: "😞", label: "Awful" },
  { value: 2, emoji: "🙁", label: "Bad" },
  { value: 3, emoji: "😐", label: "Okay" },
  { value: 4, emoji: "🙂", label: "Good" },
  { value: 5, emoji: "😄", label: "Great" },
];

/** 4 → { value: 4, emoji: "🙂", label: "Good" }. Rounds, so an average like 3.8 also works. */
export const getMood = (value) => MOODS[Math.round(value) - 1];
