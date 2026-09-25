import { describe, expect, it } from 'vitest';
import { newCustomer } from './customers';
import { Entry, Fields, groups, totals } from './domain';
import { applySharedReport, entryOwner, sharedReport } from './shared';

const fields: Fields = { insured_id: '111111111', insurer: 'חברה', policy_number: '00123', category: 'בריאות', subcategory: '', product_type: 'כיסוי', period: 'מתחדש', additional_details: '', premium: '10', frequency: 'monthly', classification: '' };
function customer(identity: string) {
  const c = newCustomer();
  const values = { ...fields, insured_id: identity };
  const e: Entry = { id: 'same-import-id', source_sheet: 'מקור', source_row: 2, original: { ...values }, values, issues: [] };
  return { ...c, report: { instance_id: 'test', report_date: null, entries: [e], warnings: [] } };
}
describe('shared portfolio', () => {
  it('groups only complete matching policies across owners without changing normal grouping', () => {
    const a = customer('111111111'), b = customer('222222222');
    const report = sharedReport([a, b]);
    expect(new Set(report.entries.map(e => e.id)).size).toBe(2);
    expect(groups(report.entries)).toHaveLength(2);
    expect(groups(report.entries, true)).toHaveLength(1);
    expect(entryOwner(report.entries[1], [a, b]).id).toBe(b.id);
    for (const change of [{ insurer: 'אחר' }, { policy_number: '123' }, { policy_number: '' }, { insured_id: '' }, { insurer: '' }]) {
      const changed = report.entries.map((e, i) => i ? { ...e, values: { ...e.values, ...change } } : e);
      expect(groups(changed, true)).toHaveLength(2);
    }
  });
  it('routes edits and exclusions only to their owner, preserving source and original IDs', () => {
    const a = customer('111111111'), b = customer('222222222'), c = customer('333333333');
    const report = sharedReport([a, b]);
    report.entries[1] = { ...report.entries[1], values: { ...report.entries[1].values, premium: '99', frequency: 'annual' }, excluded: true };
    const updated = applySharedReport([a, b, c], [a.id, b.id], report);
    expect(updated[0].report!.entries[0]).toEqual(a.report.entries[0]);
    expect(updated[2]).toBe(c);
    const edited = updated[1].report!.entries[0];
    expect(edited.id).toBe('same-import-id');
    expect(edited.original).toEqual(b.report.entries[0].original);
    expect(edited.source_row).toBe(2);
    expect(totals([edited]).annual.toString()).toBe('0');
    expect(totals([{ ...edited, excluded: false }]).annual.toString()).toBe('99');
    expect(totals([{ ...edited, excluded: false }]).monthly.toString()).toBe('0');
    expect(b.report.entries[0].values.premium).toBe('10');
  });
});
