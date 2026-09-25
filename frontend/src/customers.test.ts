import { describe, expect, it } from 'vitest';
import { customerReady, insuranceAge, sameIdentity, validBirthDate, displayBirthDate, parseBirthDateInput } from './customers';

describe('day-first birth date input', () => {
  it('keeps day and month unambiguous and preserves partial input', () => {
    expect(parseBirthDateInput('05/09/1990')).toBe('1990-09-05');
    expect(displayBirthDate('1990-09-05')).toBe('05/09/1990');
    expect(displayBirthDate(parseBirthDateInput('05/0'))).toBe('05/0');
    expect(parseBirthDateInput('')).toBe('');
    expect(validBirthDate(parseBirthDateInput('31/02/1990'))).toBe(false);
    expect(validBirthDate(parseBirthDateInput('29/02/2000'))).toBe(true);
    expect(validBirthDate(parseBirthDateInput('29/02/2001'))).toBe(false);
  });
});

describe('customer upload validation', () => {
  const details = { relationship: 'לקוח ראשי', firstName: 'בדיקה', lastName: 'סינתטי', identity: '999999999', birthDate: '1990-09-25', gender: 'זכר', maritalStatus: 'נשוי/אה', smoking: 'לא מעשן/ת' };
  it('requires names, ID, gender and marital status while allowing empty optional fields', () => {
    expect(customerReady(details)).toBe(true);
    for (const key of ['firstName', 'lastName', 'identity', 'gender', 'maritalStatus']) expect(customerReady({ ...details, [key]: '' })).toBe(false);
    expect(customerReady({ ...details, maritalStatus: '   ' })).toBe(false);
    expect(customerReady({ ...details, relationship: '', birthDate: '', smoking: '' })).toBe(true);
    expect(customerReady({ ...details, birthDate: '2999-01-01' })).toBe(false);
    expect(customerReady({ ...details, identity: '12x' })).toBe(false);
  });
  it('rejects impossible and future birth dates', () => {
    expect(validBirthDate('2025-02-30')).toBe(false);
    expect(validBirthDate('2999-01-01')).toBe(false);
  });
  it('uses last birthday including birthday boundaries', () => {
    expect(insuranceAge(details.birthDate, new Date(2026, 8, 24))).toBe(35);
    expect(insuranceAge(details.birthDate, new Date(2026, 8, 25))).toBe(36);
    expect(insuranceAge('2024-02-29', new Date(2025, 1, 28))).toBe(0);
    expect(insuranceAge('2024-02-29', new Date(2025, 2, 1))).toBe(1);
    expect(insuranceAge('')).toBeNull();
  });
  it('compares IDs with Excel leading zero loss without changing source values', () => {
    expect(sameIdentity('000000123', '123')).toBe(true);
    expect(sameIdentity('', '')).toBe(false);
    expect(sameIdentity('999999999', '888888888')).toBe(false);
  });
});
