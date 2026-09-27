// Draws the LifeXash "LX" app icons into public/ using only Node's built-in modules (no image library).
// Run from frontend/ after changing the design:  node scripts/make-icons.mjs
import { mkdirSync, writeFileSync } from "node:fs";
import { crc32, deflateSync } from "node:zlib";

const INDIGO = [79, 70, 229]; // #4f46e5, the navbar colour
const WHITE = [255, 255, 255];

// The letters as thick lines with round ends, on a 100 × 100 grid (the SVG below uses the same numbers).
const STROKE = 9;
const LINES = [
  [26.5, 32, 26.5, 68], // L: down
  [26.5, 68, 37.5, 68], // L: foot
  [51.5, 32, 73.5, 68], // X: "\"
  [73.5, 32, 51.5, 68], // X: "/"
];

// Normal icons: rounded square, letters 25% bigger.
// Maskable/Apple: full square (the OS crops it to its own shape), letters at 1× so they stay inside the
// "safe zone": the central circle with 40% radius that every mask shape keeps.
const ICONS = [
  { file: "pwa-192x192.png", size: 192, rounded: true, scale: 1.25 },
  { file: "pwa-512x512.png", size: 512, rounded: true, scale: 1.25 },
  { file: "maskable-512x512.png", size: 512, rounded: false, scale: 1 },
  { file: "apple-touch-icon.png", size: 180, rounded: false, scale: 1.25 },
];

// Shortest distance from point (px, py) to the line segment (x1, y1)–(x2, y2).
function distanceToSegment(px, py, [x1, y1, x2, y2]) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

// Is grid point (x, y) inside a 100 × 100 square with corner radius r?
function insideRoundedSquare(x, y, r) {
  const dx = Math.max(Math.abs(x - 50) - (50 - r), 0);
  const dy = Math.max(Math.abs(y - 50) - (50 - r), 0);
  return dx * dx + dy * dy <= r * r;
}

// Returns RGBA pixels. Each pixel is sampled 4 × 4 times and averaged, which smooths the edges (anti-aliasing).
function drawIcon({ size, rounded, scale }) {
  const SAMPLES = 4;
  const pixels = Buffer.alloc(size * size * 4);
  for (let py = 0; py < size; py++) {
    for (let px = 0; px < size; px++) {
      let r = 0, g = 0, b = 0, a = 0;
      for (let sy = 0; sy < SAMPLES; sy++) {
        for (let sx = 0; sx < SAMPLES; sx++) {
          const x = ((px + (sx + 0.5) / SAMPLES) / size) * 100;
          const y = ((py + (sy + 0.5) / SAMPLES) / size) * 100;
          if (rounded && !insideRoundedSquare(x, y, 22)) continue; // transparent corner
          // Undo the letter scaling around the centre, then check if we're on a letter stroke.
          const lx = 50 + (x - 50) / scale;
          const ly = 50 + (y - 50) / scale;
          const onLetter = LINES.some((line) => distanceToSegment(lx, ly, line) <= STROKE / 2);
          const [cr, cg, cb] = onLetter ? WHITE : INDIGO;
          r += cr; g += cg; b += cb; a += 1;
        }
      }
      const i = (py * size + px) * 4;
      if (a > 0) {
        pixels[i] = Math.round(r / a);
        pixels[i + 1] = Math.round(g / a);
        pixels[i + 2] = Math.round(b / a);
        pixels[i + 3] = Math.round((a / (SAMPLES * SAMPLES)) * 255);
      }
    }
  }
  return pixels;
}

// A PNG file is a signature followed by "chunks": each is length + type + data + CRC checksum.
function chunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
}

function encodePng(size, pixels) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(size, 0); // width
  header.writeUInt32BE(size, 4); // height
  header[8] = 8; // 8 bits per channel
  header[9] = 6; // colour type 6 = RGBA
  // Image data: every row starts with a filter byte (0 = none), then the whole thing is zlib-compressed.
  const rows = [];
  for (let y = 0; y < size; y++) {
    rows.push(Buffer.from([0]), pixels.subarray(y * size * 4, (y + 1) * size * 4));
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", header),
    chunk("IDAT", deflateSync(Buffer.concat(rows), { level: 9 })),
    chunk("IEND", Buffer.alloc(0)),
  ]);
}

const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="22" fill="#4f46e5"/>
  <g transform="translate(50 50) scale(1.25) translate(-50 -50)" fill="none" stroke="#fff" stroke-width="${STROKE}" stroke-linecap="round" stroke-linejoin="round">
    <path d="M26.5 32V68H37.5M51.5 32L73.5 68M73.5 32L51.5 68"/>
  </g>
</svg>
`;

const outDir = new URL("../public/", import.meta.url);
mkdirSync(outDir, { recursive: true });
writeFileSync(new URL("icon.svg", outDir), svg);
console.log("wrote public/icon.svg");
for (const icon of ICONS) {
  writeFileSync(new URL(icon.file, outDir), encodePng(icon.size, drawIcon(icon)));
  console.log(`wrote public/${icon.file}`);
}
