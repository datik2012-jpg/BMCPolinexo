import { Entry, Report } from './domain';

export function startingEntry(entry: Entry): Entry {
  return { ...entry, values: { ...(entry.baseline || entry.original) }, excluded: false };
}

export function copyCoverage(report: Report, id: string): Report {
  return { ...report, entries: report.entries.map(entry => entry.id !== id || entry.copied ? entry : {
    ...startingEntry(entry), copied: true,
  }) };
}

export function mergeProposal(report: Report, proposal: Report): Report {
  const changes = new Map(proposal.entries.map(entry => [entry.id, entry]));
  return { ...report, entries: report.entries.map(entry => {
    const change = changes.get(entry.id);
    return entry.copied && change ? { ...entry, values: { ...change.values }, excluded: change.excluded } : entry;
  }) };
}

export function removeProposalCoverage(report: Report, id: string): Report {
  return { ...report, entries: report.entries.map(entry => entry.id === id && entry.copied
    ? { ...startingEntry(entry), copied: false } : entry) };
}
