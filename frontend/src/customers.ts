import { Report } from './domain';

export type CustomerDetails = {
  relationship: string;
  firstName: string;
  lastName: string;
  identity: string;
  birthDate: string;
  gender: string;
  maritalStatus: string;
  smoking: string;
};
export type Customer = { id: string; details: CustomerDetails; report: Report | null; revision?: number };
export function newCustomer(relationship = ''): Customer {
  return { id: crypto.randomUUID(), report: null, details: {
    relationship, firstName: '', lastName: '', identity: '', birthDate: '', gender: '', maritalStatus: '', smoking: '',
  } };
}
export function validBirthDate(value: string, today = new Date()): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(value + 'T00:00:00');
  return Number.isFinite(date.getTime()) && date.getFullYear() >= 1900 &&
    date.getFullYear() === Number(value.slice(0, 4)) &&
    date.getMonth() + 1 === Number(value.slice(5, 7)) &&
    date.getDate() === Number(value.slice(8, 10)) && date <= today;
}
export function customerReady(d: CustomerDetails): boolean {
  return Boolean(d.firstName.trim() && d.lastName.trim() && d.gender.trim() && d.maritalStatus.trim()) &&
    /^\d{9}$/.test(d.identity) && (!d.birthDate || validBirthDate(d.birthDate));
}
export function insuranceAge(birthDate: string, today = new Date()): number | null {
  if (!validBirthDate(birthDate, today)) return null;
  const birth = new Date(birthDate + 'T00:00:00');
  const beforeBirthday = today.getMonth() < birth.getMonth() ||
    (today.getMonth() === birth.getMonth() && today.getDate() < birth.getDate());
  return today.getFullYear() - birth.getFullYear() - Number(beforeBirthday);
}
export function sameIdentity(a: string, b: string): boolean {
  return /^\d{1,9}$/.test(a.trim()) && /^\d{1,9}$/.test(b.trim()) &&
    a.trim().padStart(9, '0') === b.trim().padStart(9, '0');
}
