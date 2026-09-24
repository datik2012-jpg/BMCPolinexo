import { describe, expect, it } from "vitest";
import { findInsurerBrand, insurerBrands } from "./insurers";

describe("insurer logo matching", () => {
  it.each([
    ['מנורה מבטחים ביטוח בע"מ', "menora"],
    ['איי.אי.ג׳י ישראל חברה לביטוח בע״מ', "aig"],
    ['איי.די.איי. חברה לביטוח בע"מ', "direct"],
    ['ש. שלמה חברה לביטוח בע"מ', "shlomo"],
    ['ביטוח חקלאי אגודה שיתופית מרכזית בע"מ', "haklai"],
    ['  WE-SURE Insurance Ltd. ', "wesure"],
    ['אי.אמ.איי עזר חברה לביטוח משכנתאות בע"מ', "emi"],
    ['בסס״ח החברה הישראלית לביטוח אשראי בע״מ', "bss"],
    ['שירביט מבית הראל חברה לביטוח בע"מ', "shirbit"],
    ['דיויד שילד חברה לביטוח בע"מ', "davidshield"],
  ])("matches legal-name variants: %s", (value, expected) => {
    expect(findInsurerBrand(value)?.id).toBe(expected);
  });

  it("does not guess logos from unrelated substrings, agencies, or missing values", () => {
    for (const name of ["", "   ", "כללית", "מגדלי העיר", "סוכנות מנורה", "הראל סוכנות לביטוח", "חברה חדשה", "מנורה / הראל"])
      expect(findInsurerBrand(name)).toBeUndefined();
  });

  it("keeps related brands distinct and resolves every alias without collisions", () => {
    for (const brand of insurerBrands) {
      for (const alias of brand.aliases)
        expect(findInsurerBrand(alias)?.id, alias).toBe(brand.id);
      expect(brand.logo).toMatch(/^\/insurers\/[a-z]+\.(png|svg)$/);
    }
    expect(findInsurerBrand("שומרה")?.id).not.toBe(findInsurerBrand("מנורה")?.id);
    expect(findInsurerBrand("ביטוח 9")?.id).not.toBe(findInsurerBrand("ביטוח ישיר")?.id);
  });
});
