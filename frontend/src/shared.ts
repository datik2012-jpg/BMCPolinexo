import { Customer } from './customers';
import { Entry, Report } from './domain';

export const sharedEntryId = (customerId: string, entryId: string) => JSON.stringify([customerId, entryId]);

export function sharedReport(customers: Customer[]): Report {
  return {
    instance_id: customers[0]?.report?.instance_id || '',
    report_date: null,
    warnings: customers.flatMap(c => (c.report?.warnings || []).map(w => `${c.details.firstName} ${c.details.lastName}: ${w}`)),
    entries: customers.flatMap(c => (c.report?.entries || []).map(e => ({ ...e, id: sharedEntryId(c.id, e.id) }))),
  };
}

export function applySharedReport(customers: Customer[], selected: string[], report: Report): Customer[] {
  const updated = new Map(report.entries.map(e => [e.id, e]));
  return customers.map(c => !selected.includes(c.id) || !c.report ? c : {
    ...c, report: { ...c.report, entries: c.report.entries.map(e => {
      const change = updated.get(sharedEntryId(c.id, e.id));
      return change ? { ...e, values: change.values, excluded: change.excluded } : e;
    }) },
  });
}

export function entryOwner(entry: Entry, customers: Customer[]): Customer {
  const [customerId] = JSON.parse(entry.id) as [string, string];
  return customers.find(c => c.id === customerId)!;
}
