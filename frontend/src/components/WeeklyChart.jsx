import { useLayoutEffect, useRef, useState } from "react";

import { parseDateKey } from "../utils/date.js";
import { getMood } from "../utils/mood.js";

// A hand-drawn SVG chart (no chart library). Two small panels share the same 7 day columns:
//   top    = % of tasks done per day (bars, 0–100)
//   bottom = journal mood per day (dots joined by a line, 1–5)
// They are separate panels on purpose: one chart with two different y-scales is easy to misread.

const BAR_COLOR = "#4f46e5"; // indigo, the app's main colour
const MOOD_COLOR = "#d97706"; // amber: checked to stay distinguishable for colour-blind users
const MUTED = "#6b7280";
const GRID = "#e5e7eb";

const LEFT = 40; // room for the y-axis labels
const RIGHT = 8;
const BARS_TOP = 28;
const BARS_HEIGHT = 130;
const BASELINE = BARS_TOP + BARS_HEIGHT;
const MOOD_TOP = BASELINE + 68;
const MOOD_HEIGHT = 64;
const HEIGHT = MOOD_TOP + MOOD_HEIGHT + 12;

const shortWeekday = (key) => parseDateKey(key).toLocaleDateString(undefined, { weekday: "short" });
const shortDate = (key) => parseDateKey(key).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });

/** Bar with 4px rounded top corners, standing on the baseline. */
function barPath(x, width, height) {
  const r = Math.min(4, height, width / 2);
  const top = BASELINE - height;
  return `M${x},${BASELINE} V${top + r} Q${x},${top} ${x + r},${top} H${x + width - r} Q${x + width},${top} ${x + width},${top + r} V${BASELINE} Z`;
}

/** One line per day, used for the hover tooltip and the table. */
function describeTasks(day) {
  if (day.tasks_total === 0) return "no tasks";
  return `${day.tasks_completed} of ${day.tasks_total} done (${day.score}%)`;
}

function describeMood(day) {
  if (day.mood === null) return "no journal entry";
  const mood = getMood(day.mood);
  return `${mood.emoji} ${mood.label}`;
}

/** Short plain-text summary of the week, read by screen readers instead of the drawing. */
export function summarizeWeek(days) {
  const withTasks = days.filter((d) => d.score !== null);
  const withMood = days.filter((d) => d.mood !== null);
  const parts = [];

  if (withTasks.length === 0) {
    parts.push("No tasks this week.");
  } else {
    const average = Math.round(withTasks.reduce((sum, d) => sum + d.score, 0) / withTasks.length);
    const best = withTasks.reduce((a, b) => (b.score > a.score ? b : a)); // first day with the top score
    parts.push(
      `Tasks on ${withTasks.length} of 7 days, ${average}% done on average; best day ${shortWeekday(best.date)} (${best.score}%).`,
    );
  }

  if (withMood.length === 0) {
    parts.push("No mood logged.");
  } else {
    const average = withMood.reduce((sum, d) => sum + d.mood, 0) / withMood.length;
    parts.push(`Mood logged on ${withMood.length} of 7 days, average ${average.toFixed(1)} (${getMood(average).label}).`);
  }
  return parts.join(" ");
}

/** Width of an element in pixels, kept up to date when the window is resized. */
function useWidth(ref, fallback) {
  const [width, setWidth] = useState(fallback);
  // useLayoutEffect runs after the DOM exists but before the browser paints, so the first
  // frame already has the right width (no jump from the fallback).
  useLayoutEffect(() => {
    if (!ref.current) return;
    setWidth(ref.current.clientWidth);
    // ResizeObserver is built into the browser: it calls us whenever the element changes size.
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}

export default function WeeklyChart({ days, today }) {
  const wrapperRef = useRef(null);
  // We draw in real pixels (not a scaled viewBox) so text stays readable on a phone.
  const width = Math.max(useWidth(wrapperRef, 640), 280);

  const colWidth = (width - LEFT - RIGHT) / days.length;
  const colX = (i) => LEFT + i * colWidth;
  const colCenter = (i) => colX(i) + colWidth / 2;
  const barWidth = Math.min(36, colWidth * 0.5);
  const moodY = (mood) => MOOD_TOP + ((5 - mood) / 4) * MOOD_HEIGHT;
  const narrow = colWidth < 64;

  // Join mood dots only between days that are next to each other; a missing day leaves a gap.
  const moodSegments = [];
  days.forEach((day, i) => {
    const prev = days[i - 1];
    if (i > 0 && day.mood !== null && prev.mood !== null) {
      moodSegments.push({ x1: colCenter(i - 1), y1: moodY(prev.mood), x2: colCenter(i), y2: moodY(day.mood) });
    }
  });

  return (
    <figure className="weekly-chart">
      <div ref={wrapperRef} className="weekly-chart-canvas">
        {/* aria-hidden: screen readers get the summary + table below, which say the same thing. */}
        <svg width={width} height={HEIGHT} aria-hidden="true" focusable="false">
          {/* ---- Tasks panel ---- */}
          <text x={0} y={14} className="chart-panel-title">Tasks done</text>
          {[0, 50, 100].map((pct) => {
            const y = BASELINE - (pct / 100) * BARS_HEIGHT;
            return (
              <g key={pct}>
                <line x1={LEFT} x2={width - RIGHT} y1={y} y2={y} stroke={GRID} strokeWidth={1} />
                <text x={LEFT - 6} y={y + 4} textAnchor="end" className="chart-axis">{pct}%</text>
              </g>
            );
          })}

          {days.map((day, i) => {
            const x = colCenter(i) - barWidth / 2;
            if (day.score === null) {
              // No tasks = no score. Leave a gap with a label instead of drawing a 0% bar.
              return (
                <text key={day.date} x={colCenter(i)} y={BASELINE - 8} textAnchor="middle" className="chart-note">
                  {narrow ? (
                    <>
                      <tspan x={colCenter(i)} dy={-14}>no</tspan>
                      <tspan x={colCenter(i)} dy={14}>tasks</tspan>
                    </>
                  ) : (
                    "no tasks"
                  )}
                </text>
              );
            }
            // 0% (tasks, none done) still gets a thin 2px stub, so it looks different from "no tasks".
            const height = Math.max((day.score / 100) * BARS_HEIGHT, 2);
            return <path key={day.date} d={barPath(x, barWidth, height)} fill={BAR_COLOR} />;
          })}

          {/* Selective label: only today's value is written on the chart. */}
          {days.map((day, i) =>
            day.date === today && day.score !== null ? (
              <text
                key={day.date}
                x={colCenter(i)}
                y={BASELINE - Math.max((day.score / 100) * BARS_HEIGHT, 2) - 6}
                textAnchor="middle"
                className="chart-value"
              >
                {day.score}%
              </text>
            ) : null,
          )}

          {/* ---- Day labels (shared by both panels) ---- */}
          {days.map((day, i) => (
            <text
              key={day.date}
              x={colCenter(i)}
              y={BASELINE + 18}
              textAnchor="middle"
              className={day.date === today ? "chart-day today" : "chart-day"}
            >
              <tspan x={colCenter(i)}>{day.date === today ? "Today" : shortWeekday(day.date)}</tspan>
              <tspan x={colCenter(i)} dy={15} className="chart-axis">{Number(day.date.slice(8))}</tspan>
            </text>
          ))}

          {/* ---- Mood panel ---- */}
          <text x={0} y={MOOD_TOP - 14} className="chart-panel-title">Mood</text>
          {[1, 3, 5].map((mood) => (
            <g key={mood}>
              <line x1={LEFT} x2={width - RIGHT} y1={moodY(mood)} y2={moodY(mood)} stroke={GRID} strokeWidth={1} />
              <text x={LEFT - 8} y={moodY(mood) + 5} textAnchor="end" className="chart-emoji">
                {getMood(mood).emoji}
              </text>
            </g>
          ))}
          {moodSegments.map((s) => (
            <line key={`${s.x1}`} {...s} stroke={MOOD_COLOR} strokeWidth={2} strokeLinecap="round" />
          ))}
          {days.map((day, i) =>
            day.mood !== null ? (
              // White ring keeps the dot readable where it sits on a line or gridline.
              <circle key={day.date} cx={colCenter(i)} cy={moodY(day.mood)} r={5} fill={MOOD_COLOR} stroke="#fff" strokeWidth={2} />
            ) : null,
          )}

          {/* ---- Hover areas: a full-height column per day with a native tooltip ---- */}
          {days.map((day, i) => (
            <rect key={day.date} x={colX(i)} y={BARS_TOP - 8} width={colWidth} height={HEIGHT - BARS_TOP} className="chart-hover">
              <title>{`${shortDate(day.date)}\nTasks: ${describeTasks(day)}\nMood: ${describeMood(day)}`}</title>
            </rect>
          ))}
        </svg>
      </div>

      <figcaption className="chart-summary">{summarizeWeek(days)}</figcaption>

      <details className="chart-table">
        <summary>Show as a table</summary>
        <table>
          <thead>
            <tr>
              <th scope="col">Day</th>
              <th scope="col">Tasks</th>
              <th scope="col">Mood</th>
            </tr>
          </thead>
          <tbody>
            {days.map((day) => (
              <tr key={day.date}>
                <th scope="row">{shortDate(day.date)}</th>
                <td>{describeTasks(day)}</td>
                <td>{describeMood(day)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </figure>
  );
}
