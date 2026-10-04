import { describe, expect, it } from 'vitest';
import { insuranceCategory, insuranceCategoryGroups } from './insuranceCategories';

describe('insurance filter classification', () => {
  it('recognizes imported branches and health subcategories without changing source values', () => {
    const source = { category: 'ביטוח בריאות', subcategory: 'מחלות קשות' };
    expect(insuranceCategory(source)).toBe('מחלות קשות');
    expect(source.category).toBe('ביטוח בריאות');
    expect(insuranceCategory({ category: 'ביטוח רכב', subcategory: 'צד ג' })).toBe('רכב');
    expect(insuranceCategory({ category: 'ביטוח חיים', subcategory: '' })).toBe('ביטוחי חיים');
    expect(insuranceCategory({ category: 'ביטוח סיעודי', subcategory: '' })).toBe('סיעוד');
  });
  it('includes service and disability coverage in personal insurance', () => {
    const personal = insuranceCategoryGroups.find(group => group.label === 'ביטוח פרט')!;
    for (const category of ['כתב שירות', 'אבדן כושר עבודה', 'אובדן כושר עבודה']) {
      expect(personal.options).toContain(insuranceCategory({ category, subcategory: '' }));
    }
  });
  it('keeps unmapped and missing branches available', () => {
    expect(insuranceCategory({ category: 'ענף לא מוכר', subcategory: '' })).toBe('ענף לא מוכר');
    expect(insuranceCategory({ category: 'אבדן כושר עבודה', subcategory: '' })).toBe('אבדן כושר עבודה');
    expect(insuranceCategory({ category: '', subcategory: '' })).toBe('ללא ענף ביטוח');
  });
});
