import type { Fields } from './domain';

export const insuranceCategoryGroups = [
  { label: 'ביטוח אלמנטרי (ביטוח כללי)', options: ['רכב', 'דירה', 'עסק', 'רכוש ואחריות כלפי צד שלישי'] },
  { label: 'ביטוח פרט', options: ['ביטוחי חיים', 'בריאות', 'מחלות קשות', 'סיעוד', 'תאונות אישיות', 'כתב שירות', 'אבדן כושר עבודה'] },
];
export const insuranceCategories = insuranceCategoryGroups.flatMap(group => group.options);

// Display-only classification; imported category values remain untouched.
export function insuranceCategory(values: Pick<Fields, 'category' | 'subcategory'>): string {
  const category = values.category.trim();
  const text = `${category} ${values.subcategory.trim()}`;
  if (/כתב שירות|כתבי שירות/.test(category)) return 'כתב שירות';
  if (/א[בו]דן כושר עבודה|אובדן כושר עבודה/.test(category)) return 'אבדן כושר עבודה';
  if (/מחלות קשות/.test(text)) return 'מחלות קשות';
  if (/תאונות אישיות/.test(text)) return 'תאונות אישיות';
  if (/סיעוד/.test(category)) return 'סיעוד';
  if (/רכב/.test(category)) return 'רכב';
  if (/דירה|דירות/.test(category)) return 'דירה';
  if (/עסק|עסקים/.test(category)) return 'עסק';
  if (/רכוש|אחריות|צד שלישי|צד ג/.test(category)) return 'רכוש ואחריות כלפי צד שלישי';
  if (/חיים/.test(category)) return 'ביטוחי חיים';
  if (/בריאות/.test(category)) return 'בריאות';
  return category || 'ללא ענף ביטוח';
}
