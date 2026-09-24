import Decimal from "decimal.js";
export const labels = {
  insured_id: "מספר מבוטח",
  category: "ענף ביטוח",
  subcategory: "ענף משני",
  product_type: "מוצר / כיסוי",
  insurer: "חברת ביטוח",
  period: "תקופת ביטוח",
  additional_details: "פרטים נוספים",
  premium: "פרמיה",
  frequency: "תדירות תשלום",
  policy_number: "מספר פוליסה",
  classification: "סיווג",
};
export type Fields = Record<keyof typeof labels, string>;
export type Entry = {
  id: string;
  source_sheet: string;
  source_row: number;
  original: Fields;
  values: Fields;
  issues: string[];
  excluded?: boolean;
};
export type Report = {
  instance_id: string;
  report_date: string | null;
  entries: Entry[];
  warnings: string[];
};
export function frequency(s: string) {
  const v = s.trim();
  return ["monthly", "חודשי", "חודשית"].includes(v)
    ? "monthly"
    : ["annual", "שנתי", "שנתית"].includes(v)
      ? "annual"
      : "unknown";
}
export function premium(s: string): Decimal | null {
  const input = s.trim().replace(/^₪\s*/, "");
  if (!/^(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/.test(input)) return null;
  try {
    const value = new Decimal(input.replace(/,/g, ""));
    return value.lte("999999999999") ? value : null;
  } catch {
    return null;
  }
}
export function issues(entry: Entry, entries: Entry[]): string[] {
  const v = entry.values;
  const result: string[] = entry.issues.filter(
    (i) => i.includes("אפסים מובילים") || i.includes("נוסח"),
  );
  if (!v.insured_id || !v.insurer.trim() || !v.policy_number.trim())
    result.push("חסרים פרטים לזיהוי הפוליסה");
  if (!premium(v.premium)) result.push("פרמיה חסרה או לא תקינה");
  if (frequency(v.frequency) === "unknown")
    result.push("תדירות התשלום אינה ידועה");
  const signature = JSON.stringify(v);
  if (
    entries.some(
      (e) =>
        e.id !== entry.id &&
        !e.excluded &&
        JSON.stringify(e.values) === signature,
    )
  )
    result.push("חשד לשורה כפולה — נכללת בחישוב");
  return result;
}
export function totals(entries: Entry[], original = false) {
  let monthly = new Decimal(0),
    annual = new Decimal(0);
  let monthlyIncomplete = false,
    annualIncomplete = false;
  for (const e of entries) {
    if (!original && e.excluded) continue;
    const v = original ? e.original : e.values;
    const amount = premium(v.premium);
    const f = frequency(v.frequency);
    if (f === "unknown") {
      monthlyIncomplete = true;
      annualIncomplete = true;
      continue;
    }
    if (amount === null) {
      if (f === "monthly") monthlyIncomplete = true;
      else annualIncomplete = true;
      continue;
    }
    if (f === "monthly") monthly = monthly.plus(amount);
    else annual = annual.plus(amount);
  }
  return {
    monthly,
    annual,
    incomplete: monthlyIncomplete || annualIncomplete,
    monthlyIncomplete,
    annualIncomplete,
  };
}
export function isChanged(e: Entry) {
  return (Object.keys(labels) as (keyof Fields)[]).some((k) => {
    if (k === "frequency" && frequency(e.values[k]) !== "unknown")
      return frequency(e.values[k]) !== frequency(e.original[k]);
    if (k === "premium") {
      const a = premium(e.values[k]),
        b = premium(e.original[k]);
      if (a && b) return !a.eq(b);
    }
    return e.values[k] !== e.original[k];
  });
}
export function groups(entries: Entry[]) {
  const map = new Map<string, Entry[]>();
  for (const e of entries) {
    const v = e.values;
    const key =
      v.insured_id && v.insurer.trim() && v.policy_number.trim()
        ? JSON.stringify([
            v.insured_id,
            v.insurer.trim(),
            v.policy_number.trim(),
          ])
        : e.id;
    map.set(key, [...(map.get(key) || []), e]);
  }
  return [...map.entries()];
}
export const money = (value: Decimal) =>
  `${value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} ₪`;
export const frequencyLabel = (value: string) =>
  frequency(value) === "monthly"
    ? "חודשית"
    : frequency(value) === "annual"
      ? "שנתית"
      : value || "לא ידועה";
