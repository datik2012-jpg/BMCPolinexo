import { describe, expect, it } from 'vitest';
import { Entry, Fields, Report, totals } from './domain';
import { copyCoverage, mergeProposal, removeProposalCoverage, startingEntry } from './workspace';
import { newCustomer } from './customers';
import { sharedReport, applySharedReport } from './shared';
const fields: Fields = { insured_id: '111111111', insurer: 'test', policy_number: '1', category: '', subcategory: '', product_type: '', period: '', additional_details: 'detail', premium: '10.25', frequency: 'monthly', classification: '' };
const entry: Entry = { id: '1', source_sheet: 'test', source_row: 2, original: { ...fields, frequency: 'raw' }, baseline: { ...fields }, values: { ...fields }, issues: [] };
const report: Report = { instance_id: 'test', report_date: null, warnings: [], entries: [entry, { ...entry, id: '2', values: { ...fields, premium: '0' }, baseline: { ...fields, premium: '0' } }] };
describe('original and proposed workspace', () => {
  it('starts empty and copies once without changing the imported snapshot', () => {
    expect(report.entries.filter(e => e.copied)).toHaveLength(0);
    const copied = copyCoverage(copyCoverage(report, '1'), '1');
    expect(copied.entries.filter(e => e.copied)).toHaveLength(1);
    const edited = mergeProposal(copied, { ...copied, entries: [{ ...copied.entries[0], values: { ...fields, premium: '99', frequency: 'annual' } }] });
    expect(startingEntry(edited.entries[0]).values).toEqual(fields);
    expect(edited.entries[0].original.frequency).toBe('raw');
    expect(edited.entries[0].source_row).toBe(2);
    expect(totals(edited.entries.filter(e => e.copied)).annual.toString()).toBe('99');
    expect(totals(edited.entries.map(startingEntry)).monthly.toString()).toBe('10.25');
    expect(copyCoverage(edited, '1').entries[0].values.premium).toBe('99');
    expect(report.entries[0].values.premium).toBe('10.25');
  });
  it('preserves ownership on shared copy and keeps zero-premium rows', () => {
    const a = { ...newCustomer(), report }, b = { ...newCustomer(), report };
    const shared = sharedReport([a, b]);
    const copied = copyCoverage(shared, shared.entries[3].id);
    const updated = applySharedReport([a, b], [a.id, b.id], copied);
    expect(updated[0].report!.entries.some(e => e.copied)).toBe(false);
    expect(updated[1].report!.entries[1].copied).toBe(true);
    expect(updated[1].report!.entries[1].values.premium).toBe('0');
    expect(updated[1].report!.entries).toHaveLength(2);
  });
  it('excludes only the proposal and refuses edits to uncopied rows', () => {
    const copied = copyCoverage(report, '1');
    const edited = mergeProposal(copied, { ...copied, entries: copied.entries.map(e => ({ ...e, excluded: true })) });
    expect(edited.entries[1].excluded).toBeUndefined();
    expect(totals(edited.entries).monthly.toString()).toBe('0');
    expect(totals(edited.entries.map(startingEntry)).monthly.toString()).toBe('10.25');
  });
});

it('removes an edited excluded proposal and allows a fresh copy without losing source or ownership', () => {
  const a = { ...newCustomer(), report }, b = { ...newCustomer(), report };
  const shared = sharedReport([a, b]);
  const id = shared.entries[2].id;
  const copied = copyCoverage(copyCoverage(shared, shared.entries[0].id), id);
  const edited = mergeProposal(copied, { ...copied, entries: copied.entries.map(e => e.id === id
    ? { ...e, values: { ...e.values, premium: '99', frequency: 'annual' }, excluded: true } : e) });
  const removed = removeProposalCoverage(edited, id);
  const updated = applySharedReport([a, b], [a.id, b.id], removed);
  expect(updated[0].report!.entries[0].copied).toBe(true);
  expect(updated[1].report!.entries).toHaveLength(2);
  expect(updated[1].report!.entries[0]).toEqual({ ...entry, copied: false, excluded: false });
  expect(removed.entries.filter(e => e.copied)).toHaveLength(1);
  expect(totals(removed.entries.filter(e => e.copied)).annual.toString()).toBe('0');
  const fresh = copyCoverage(removed, id).entries[2];
  expect(fresh.values).toEqual(fields);
  expect(fresh.excluded).toBe(false);
  expect(fresh.copied).toBe(true);
  expect(edited.entries[2].values.premium).toBe('99');
});
