export type KeystrokeType = 'down' | 'up';

export interface KeystrokeEventRec {
  type: KeystrokeType;
  key: string;
  t: number; // ms timestamp (performance.now)
}

export function startCapture(target: HTMLElement) {
  const events: KeystrokeEventRec[] = [];
  const onKeyDown = (e: KeyboardEvent) => {
    if (e.isComposing) return;
    const key = e.key;
    events.push({ type: 'down', key, t: performance.now() });
  };
  const onKeyUp = (e: KeyboardEvent) => {
    if (e.isComposing) return;
    const key = e.key;
    events.push({ type: 'up', key, t: performance.now() });
  };
  target.addEventListener('keydown', onKeyDown);
  target.addEventListener('keyup', onKeyUp);
  return {
    stop() {
      target.removeEventListener('keydown', onKeyDown);
      target.removeEventListener('keyup', onKeyUp);
      return { events };
    },
  };
}

function quantizeMs(ms: number, nBits = 12, maxMs = 4095) {
  const clamped = Math.max(0, Math.min(ms, maxMs));
  const maxVal = (1 << nBits) - 1;
  // 1 ms per unit up to maxMs (fits in 12 bits up to 4095)
  const q = Math.round((clamped / maxMs) * maxVal);
  return Math.max(0, Math.min(q, maxVal));
}

export function computeFeatureVector(
  challenge: string,
  events: KeystrokeEventRec[],
  N = 64,
) {
  // Extract per-position keydown and keyup times for printable chars only
  const downs: number[] = [];
  const ups: number[] = [];

  for (const ev of events) {
    // Consider only single-character keys
    if (ev.key.length !== 1) continue;
    if (ev.type === 'down') downs.push(ev.t);
    else ups.push(ev.t);
  }

  const L = Math.min(challenge.length, downs.length, ups.length);
  const dwell: number[] = [];
  for (let i = 0; i < L; i++) {
    dwell.push(Math.max(0, ups[i] - downs[i]));
  }

  const inter: number[] = [];
  for (let i = 0; i + 1 < L; i++) {
    inter.push(Math.max(0, downs[i + 1] - downs[i]));
  }

  // Build [dwell0, inter0, dwell1, inter1, ...]
  const combined: number[] = [];
  for (let i = 0; i < L; i++) {
    combined.push(quantizeMs(dwell[i] || 0));
    combined.push(quantizeMs(inter[i] || 0));
  }

  // Pad or truncate to N
  while (combined.length < N) combined.push(0);
  return combined.slice(0, N);
}


