export function percent(value: number | null | undefined) { return value == null ? '—' : `${(value * 100).toFixed(1)}%`; }
export function millis(value: number | null | undefined) { return value == null ? '—' : `${value.toFixed(2)} ms`; }
