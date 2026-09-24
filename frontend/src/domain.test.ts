import { describe, it, expect } from "vitest";
import { Entry, Fields, groups, issues, premium, totals } from "./domain";
const values: Fields = {
  insured_id: "TEST",
  category: "בריאות",
  subcategory: "",
  product_type: "כיסוי",
  insurer: "חברה",
  period: "מתחדש",
  additional_details: "",
  premium: "0.10",
  frequency: "monthly",
  policy_number: "000123",
  classification: "",
};
function entry(id: string, changes: Partial<Fields> = {}): Entry {
  const v = { ...values, ...changes };
  return {
    id,
    source_sheet: "דוח",
    source_row: Number(id),
    values: v,
    original: { ...v },
    issues: [],
  };
}
describe("portfolio domain", () => {
  it("rejects malformed amount grouping", () => {
    expect(premium("1,2")).toBeNull();
    expect(premium("1 2")).toBeNull();
    expect(premium("1,200.25")?.toString()).toBe("1200.25");
  });
  it("groups paid and zero coverages, preserving periods and categories", () => {
    expect(
      groups([
        entry("1"),
        entry("2", { premium: "0", category: "חיים", period: "2025" }),
      ]),
    ).toHaveLength(1);
  });
  it("separates insurers and incomplete keys", () => {
    expect(
      groups([
        entry("1"),
        entry("2", { insurer: "אחר" }),
        entry("3", { policy_number: "" }),
        entry("4", { policy_number: "" }),
        entry("5", { insured_id: "" }),
      ]),
    ).toHaveLength(5);
  });
  it("uses exact separate decimals", () => {
    const t = totals([
      entry("1"),
      entry("2", { premium: "0.20" }),
      entry("3", { premium: "100", frequency: "annual" }),
    ]);
    expect(t.monthly.toString()).toBe("0.3");
    expect(t.annual.toString()).toBe("100");
  });
  it("retains and flags duplicates, supports exclusion and restoration", () => {
    const a = entry("1"),
      b = entry("2");
    expect(issues(a, [a, b]).join()).toContain("כפולה");
    expect(totals([a, b]).monthly.toString()).toBe("0.2");
    b.excluded = true;
    expect(totals([a, b]).monthly.toString()).toBe("0.1");
    expect(totals([a, b], true).monthly.toString()).toBe("0.2");
    b.excluded = false;
    expect(totals([a, b]).monthly.toString()).toBe("0.2");
  });
  it("marks missing/invalid premiums and unknown frequency incomplete", () => {
    for (const changes of [
      { premium: "" },
      { premium: "abc" },
      { frequency: "לא ידוע" },
    ])
      expect(totals([entry("1", changes)]).incomplete).toBe(true);
    expect(premium("0")?.toString()).toBe("0");
    expect(premium("-3")).toBeNull();
  });
  it("recalculates corrected totals and grouping without mutating original", () => {
    const a = entry("1"),
      b = entry("2");
    b.values = {
      ...b.values,
      policy_number: "different",
      premium: "20",
      frequency: "annual",
    };
    expect(groups([a, b])).toHaveLength(2);
    expect(totals([a, b]).annual.toString()).toBe("20");
    expect(totals([a, b], true).monthly.toString()).toBe("0.2");
  });
});
