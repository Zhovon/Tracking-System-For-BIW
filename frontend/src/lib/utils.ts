import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ── Timezone helpers ──────────────────────────────────────────────
// The backend stores timestamps as naive UTC (datetime.utcnow). The business
// operates in Dhaka, Bangladesh, which is a fixed UTC+6 offset (no DST), so all
// times are displayed in Asia/Dhaka regardless of the viewer's device timezone.
export const DHAKA_TZ = "Asia/Dhaka";

/** Parse a backend timestamp, treating a tz-less value as UTC. */
export function parseServerDate(value: string): Date {
  const hasTz = /[zZ]$/.test(value) || /[+-]\d{2}:?\d{2}$/.test(value);
  return new Date(hasTz ? value : value + "Z");
}

/** Format a backend timestamp as a Dhaka date + time (e.g. "28 Jun 2026, 05:33 pm"). */
export function formatDhakaDateTime(value: string): string {
  return parseServerDate(value).toLocaleString("en-GB", {
    timeZone: DHAKA_TZ,
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Format a backend timestamp as a short Dhaka date (e.g. "28 Jun"). */
export function formatDhakaShortDate(value: string): string {
  return parseServerDate(value).toLocaleDateString("en-GB", {
    timeZone: DHAKA_TZ,
    day: "2-digit",
    month: "short",
  });
}

/** Convert a UTC timestamp to a `datetime-local` input value in Dhaka wall-clock. */
export function toDhakaDatetimeLocal(value: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: DHAKA_TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
    .formatToParts(parseServerDate(value))
    .reduce((acc, p) => ((acc[p.type] = p.value), acc), {} as Record<string, string>);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

/** Interpret a `datetime-local` value as Dhaka wall-clock and return a UTC ISO string. */
export function dhakaDatetimeLocalToUtc(local: string): string {
  return new Date(`${local}:00+06:00`).toISOString();
}
