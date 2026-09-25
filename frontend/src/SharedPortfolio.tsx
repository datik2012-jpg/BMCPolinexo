import { Customer } from './customers';
import { CustomerPortfolio } from './CustomerPortfolio';
import { applySharedReport, entryOwner, sharedReport } from './shared';

export function SharedPortfolio({ customers, available, setCustomers }: {
  customers: Customer[]; available: boolean;
  setCustomers: (update: (all: Customer[]) => Customer[]) => void;
}) {
  const selected = customers.map(c => c.id);
  return <CustomerPortfolio customer={{ ...customers[0], report: sharedReport(customers) }}
    members={customers} ownerOf={entry => entryOwner(entry, customers)} available={available}
    setReport={value => setCustomers(all => {
      const current = sharedReport(all.filter(c => selected.includes(c.id)));
      const next = typeof value === 'function' ? value(current) : value;
      return next ? applySharedReport(all, selected, next) : all;
    })} />;
}
